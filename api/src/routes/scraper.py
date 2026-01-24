"""Scraper API routes for job management.

Endpoints for triggering scraper jobs and checking their status.
"""
import uuid
import json
from flask import Blueprint, request, jsonify, current_app
from api.celery_app import celery_app
from api.src.tasks.scraper_tasks import run_pipeline_task
from api.src.services.email_service import validate_and_store_email

scraper_bp = Blueprint('scraper', __name__)

# Redis key prefix for draft jobs
DRAFT_PREFIX = 'draft_job:'
DRAFT_EXPIRY = 3600  # 1 hour

@scraper_bp.route('/init', methods=['POST'])
def init_scraper():
    """Initialize a scraper job in draft state.
    
    Returns a job_id but does not start processing.
    User must subsequently call /start with a valid email.
    """
    data = request.get_json()
    if not data or 'category' not in data:
        return jsonify({'error': 'category is required'}), 400

    # Create draft job ID
    job_id = str(uuid.uuid4())
    
    # Store job parameters in Redis
    redis_client = celery_app.backend.client
    
    job_data = {
        'category': data['category'],
        'country': data.get('country', 'France'),
        'count': data.get('count', 30),
        'steps': data.get('steps', '1-7'),
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
            'category': data['category'],
            'message': 'Job initialized. Waiting for email validation.'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Failed to create draft job: {e}")
        return jsonify({'error': 'Failed to initialize job'}), 500

@scraper_bp.route('/start/<job_id>', methods=['POST'])
def start_scraper(job_id):
    """Start an initialized scraper job.
    
    Requires valid email in body.
    """
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'email is required'}), 400
        
    # Validate email
    validation = validate_and_store_email(data['email'])
    if not validation['valid']:
        return jsonify(validation), 400
        
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
        task = run_pipeline_task.apply_async(
            args=[
                draft_data['category'],
                draft_data['country'],
                draft_data['count'],
                draft_data['steps']
            ],
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

@scraper_bp.route('/run', methods=['POST'])
def run_scraper():
    """Trigger new scraper pipeline run (Direct mode)."""
    data = request.get_json()

    # Validate required fields
    if not data or 'category' not in data:
        return jsonify({'error': 'category is required'}), 400

    category = data['category']
    country = data.get('country', 'France')
    count = data.get('count', 30)
    steps = data.get('steps', '1-7')

    # Validate count
    if not isinstance(count, int) or count < 1 or count > 100:
        return jsonify({'error': 'count must be an integer between 1 and 100'}), 400

    # Enqueue task
    try:
        task = run_pipeline_task.apply_async(
            args=[category, country, count, steps]
        )

        return jsonify({
            'job_id': task.id,
            'status': 'pending',
            'category': category,
            'message': 'Job queued successfully'
        }), 202

    except Exception as e:
        current_app.logger.error(f'Failed to enqueue task: {e}')
        return jsonify({'error': 'Failed to queue job'}), 500


@scraper_bp.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get status of scraper job."""
    try:
        # Check draft status first
        redis_client = celery_app.backend.client
        draft_data = redis_client.get(f"{DRAFT_PREFIX}{job_id}")
        
        if draft_data:
            return jsonify({
                'job_id': job_id,
                'state': 'DRAFT',
                'status': 'Waiting for email verification...',
                'progress': 0
            }), 200
    
        task = celery_app.AsyncResult(job_id)

        response = {
            'job_id': job_id,
            'state': task.state
        }

        if task.state == 'PENDING':
            response['status'] = 'Analyse en attente de démarrage'
            response['progress'] = 0

        elif task.state == 'STARTED':
            response['status'] = 'Analyse démarrée'
            response['progress'] = 5
            if task.info:
                response.update(task.info)

        elif task.state == 'PROGRESS':
            response['status'] = 'Analyse en cours'
            if task.info:
                response.update(task.info)
                response['progress'] = task.info.get('progress_percent', 0)

        elif task.state == 'SUCCESS':
            response['status'] = 'Analyse terminée avec succès'
            response['progress'] = 100
            response['result'] = task.result

        elif task.state == 'FAILURE':
            response['status'] = 'Échec de l\'analyse'
            response['progress'] = 0
            response['error'] = str(task.info) if task.info else 'Erreur inconnue'

        else:
            response['status'] = f'État inconnu : {task.state}'

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f'Failed to get job status: {e}')
        return jsonify({'error': 'Failed to retrieve job status'}), 500


@scraper_bp.route('/resume', methods=['POST'])
def resume_scraper():
    """Resume existing scraper pipeline run."""
    data = request.get_json()

    if not data or 'run_id' not in data:
        return jsonify({'error': 'run_id is required'}), 400

    run_id = data['run_id']
    steps = data.get('steps', '1-7')

    # Enqueue task with run_id (will resume existing run)
    try:
        task = run_pipeline_task.apply_async(
            kwargs={'run_id': run_id, 'steps': steps}
        )

        return jsonify({
            'job_id': task.id,
            'status': 'pending',
            'run_id': run_id,
            'message': 'Resume job queued successfully'
        }), 202

    except Exception as e:
        current_app.logger.error(f'Failed to enqueue resume task: {e}')
        return jsonify({'error': 'Failed to queue resume job'}), 500
