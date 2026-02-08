"""Competitor scraper API routes.

Endpoints for triggering competitor packaging scraper jobs and
checking their status.
"""
import uuid
import json
from flask import Blueprint, request, jsonify, current_app
from api.celery_app import celery_app
from api.src.tasks.competitor_scraper_tasks import run_competitor_scraper_task

competitor_scraper_bp = Blueprint('competitor_scraper', __name__)

# Redis key prefix for draft jobs
DRAFT_PREFIX = 'competitor_draft_job:'
DRAFT_EXPIRY = 3600  # 1 hour


@competitor_scraper_bp.route('/init', methods=['POST'])
def init_competitor_scraper():
    """Initialize a competitor scraper job in draft state.
    
    Request body:
        {
            "target_brands": ["Alpro", "Oatly", "Bjorg"],  # Optional
            "category": "plant-based milk",  # Optional
            "countries": ["Belgium", "France"],  # Optional
            "enable_amazon": true,  # Optional
            "enable_retailers": true,  # Optional
            "enable_google_images": true  # Optional
        }
    
    Returns:
        {
            "job_id": "uuid",
            "status": "draft",
            "message": "Job initialized..."
        }
    """
    data = request.get_json() or {}
    
    # Create draft job ID
    job_id = str(uuid.uuid4())
    
    # Store job parameters in Redis
    redis_client = celery_app.backend.client
    
    job_data = {
        'target_brands': data.get('target_brands', ["Alpro", "Oatly", "Bjorg", "Roa Ra", "Hély"]),
        'category': data.get('category', 'plant-based milk'),
        'countries': data.get('countries', ["Belgium", "France"]),
        'enable_amazon': data.get('enable_amazon', True),
        'enable_retailers': data.get('enable_retailers', True),
        'enable_google_images': data.get('enable_google_images', True),
        'status': 'DRAFT',
        'created_at': str(uuid.uuid1().time)
    }
    
    try:
        redis_client.setex(
            f"{DRAFT_PREFIX}{job_id}",
            DRAFT_EXPIRY,
            json.dumps(job_data)
        )
        
        return jsonify({
            'job_id': job_id,
            'status': 'draft',
            'target_brands': job_data['target_brands'],
            'category': job_data['category'],
            'message': 'Job initialized. Ready to start.'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Failed to create draft job: {e}")
        return jsonify({'error': 'Failed to initialize job'}), 500


@competitor_scraper_bp.route('/start/<job_id>', methods=['POST'])
def start_competitor_scraper(job_id):
    """Start an initialized competitor scraper job.
    
    Args:
        job_id: The draft job ID from /init
    
    Returns:
        {
            "job_id": "uuid",
            "status": "pending",
            "message": "Job started successfully"
        }
    """
    # Retrieve job params
    redis_client = celery_app.backend.client
    draft_key = f"{DRAFT_PREFIX}{job_id}"
    draft_data_json = redis_client.get(draft_key)
    
    if not draft_data_json:
        # Check if job is already running/completed in Celery
        try:
            task = celery_app.AsyncResult(job_id)
            if task.state != 'PENDING':
                return jsonify({'error': 'Job already started or invalid ID'}), 409
        except:
            pass
        return jsonify({'error': 'Job ID not found or expired'}), 404
    
    draft_data = json.loads(draft_data_json)
    
    # Start Celery task with the SAME ID
    try:
        task = run_competitor_scraper_task.apply_async(
            kwargs={
                'target_brands': draft_data['target_brands'],
                'category': draft_data['category'],
                'countries': draft_data['countries'],
                'enable_amazon': draft_data['enable_amazon'],
                'enable_retailers': draft_data['enable_retailers'],
                'enable_google_images': draft_data['enable_google_images'],
                'job_id': job_id
            },
            task_id=job_id  # Force the task ID to match our draft ID
        )
        
        # Cleanup draft
        redis_client.delete(draft_key)
        
        return jsonify({
            'job_id': job_id,
            'status': 'pending',
            'message': 'Job started successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to start job {job_id}: {e}")
        return jsonify({'error': 'Failed to start job'}), 500


@competitor_scraper_bp.route('/run', methods=['POST'])
def run_competitor_scraper():
    """Trigger new competitor scraper run (Direct mode).
    
    Request body:
        {
            "target_brands": ["Alpro", "Oatly"],  # Optional
            "category": "oat milk",  # Optional
            "countries": ["Belgium"],  # Optional
            "enable_amazon": true,  # Optional
            "enable_retailers": true,  # Optional
            "enable_google_images": true  # Optional
        }
    
    Returns:
        {
            "job_id": "uuid",
            "status": "pending",
            "message": "Job queued successfully"
        }
    """
    data = request.get_json() or {}
    
    # Extract parameters with defaults
    target_brands = data.get('target_brands', ["Alpro", "Oatly", "Bjorg", "Roa Ra", "Hély"])
    category = data.get('category', 'plant-based milk')
    countries = data.get('countries', ["Belgium", "France"])
    enable_amazon = data.get('enable_amazon', True)
    enable_retailers = data.get('enable_retailers', True)
    enable_google_images = data.get('enable_google_images', True)
    
    # Validate brands list
    if not isinstance(target_brands, list) or len(target_brands) == 0:
        return jsonify({'error': 'target_brands must be a non-empty list'}), 400
    
    # Enqueue task
    try:
        task = run_competitor_scraper_task.apply_async(
            kwargs={
                'target_brands': target_brands,
                'category': category,
                'countries': countries,
                'enable_amazon': enable_amazon,
                'enable_retailers': enable_retailers,
                'enable_google_images': enable_google_images
            }
        )
        
        return jsonify({
            'job_id': task.id,
            'status': 'pending',
            'target_brands': target_brands,
            'category': category,
            'message': 'Job queued successfully'
        }), 202
        
    except Exception as e:
        current_app.logger.error(f'Failed to enqueue task: {e}')
        return jsonify({'error': 'Failed to queue job'}), 500


@competitor_scraper_bp.route('/status/<job_id>', methods=['GET'])
def get_competitor_job_status(job_id):
    """Get status of competitor scraper job.
    
    Args:
        job_id: Job identifier
    
    Returns:
        {
            "job_id": "uuid",
            "state": "PROGRESS",
            "status": "Scraping Alpro...",
            "progress": {
                "current_brand": "Alpro",
                "brands_completed": 1,
                "brands_total": 5,
                "products_collected": 3,
                "images_downloaded": 25,
                "progress_percent": 20
            }
        }
    """
    try:
        # Check draft status first
        redis_client = celery_app.backend.client
        draft_data = redis_client.get(f"{DRAFT_PREFIX}{job_id}")
        
        if draft_data:
            return jsonify({
                'job_id': job_id,
                'state': 'DRAFT',
                'status': 'Waiting to start...',
                'progress_percent': 0
            }), 200
        
        task = celery_app.AsyncResult(job_id)
        
        response = {
            'job_id': job_id,
            'state': task.state
        }
        
        if task.state == 'PENDING':
            response['status'] = 'Job queued, waiting to start'
            response['progress_percent'] = 0
        
        elif task.state == 'STARTED':
            response['status'] = 'Job started'
            response['progress_percent'] = 5
            if task.info:
                response.update(task.info)
        
        elif task.state == 'PROGRESS':
            response['status'] = 'Scraping in progress'
            if task.info:
                response.update(task.info)
        
        elif task.state == 'SUCCESS':
            response['status'] = 'Scraping completed successfully'
            response['progress_percent'] = 100
            response['result'] = task.result
        
        elif task.state == 'FAILURE':
            response['status'] = 'Scraping failed'
            response['progress_percent'] = 0
            response['error'] = str(task.info) if task.info else 'Unknown error'
        
        else:
            response['status'] = f'Unknown state: {task.state}'
        
        return jsonify(response), 200
        
    except Exception as e:
        current_app.logger.error(f'Failed to get job status: {e}')
        return jsonify({'error': 'Failed to retrieve job status'}), 500


@competitor_scraper_bp.route('/datasets', methods=['GET'])
def list_competitor_datasets():
    """List all competitor scraper datasets.
    
    Returns:
        {
            "datasets": [
                {
                    "dataset_id": "competitor_scrape_20260208_120000",
                    "category": "plant-based milk",
                    "total_products": 15,
                    "total_images": 127,
                    "created_at": "2026-02-08T12:00:00",
                    "metadata_file": "/path/to/metadata.json"
                },
                ...
            ]
        }
    """
    try:
        import os
        from pathlib import Path
        import json
        
        output_dir = Path(os.getenv('OUTPUT_DIR', '/app/output')) / 'competitor_packaging'
        
        if not output_dir.exists():
            return jsonify({'datasets': []}), 200
        
        datasets = []
        
        for dataset_dir in output_dir.iterdir():
            if not dataset_dir.is_dir():
                continue
            
            # Look for metadata file
            metadata_files = list(dataset_dir.glob('*_metadata.json'))
            
            if metadata_files:
                metadata_file = metadata_files[0]
                
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    datasets.append({
                        'dataset_id': metadata.get('dataset_id'),
                        'category': metadata.get('category'),
                        'target_brands': metadata.get('target_brands', []),
                        'total_products': metadata.get('total_products', 0),
                        'total_images': metadata.get('total_images', 0),
                        'total_reviews': metadata.get('total_reviews', 0),
                        'created_at': metadata.get('created_at'),
                        'metadata_file': str(metadata_file)
                    })
                except Exception as e:
                    current_app.logger.error(f"Failed to read metadata from {metadata_file}: {e}")
        
        # Sort by creation date (newest first)
        datasets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({'datasets': datasets}), 200
        
    except Exception as e:
        current_app.logger.error(f'Failed to list datasets: {e}')
        return jsonify({'error': 'Failed to list datasets'}), 500


@competitor_scraper_bp.route('/dataset/<dataset_id>', methods=['GET'])
def get_competitor_dataset(dataset_id):
    """Get detailed information about a specific dataset.
    
    Args:
        dataset_id: Dataset identifier
    
    Returns:
        Complete dataset metadata including all products.
    """
    try:
        import os
        from pathlib import Path
        import json
        
        output_dir = Path(os.getenv('OUTPUT_DIR', '/app/output')) / 'competitor_packaging'
        dataset_dir = output_dir / dataset_id
        
        if not dataset_dir.exists():
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Find metadata file
        metadata_files = list(dataset_dir.glob('*_metadata.json'))
        
        if not metadata_files:
            return jsonify({'error': 'Metadata file not found'}), 404
        
        metadata_file = metadata_files[0]
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        return jsonify(metadata), 200
        
    except Exception as e:
        current_app.logger.error(f'Failed to get dataset: {e}')
        return jsonify({'error': 'Failed to retrieve dataset'}), 500
