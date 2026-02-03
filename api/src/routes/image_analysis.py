"""Image Analysis API routes for single image analysis.

Endpoints for uploading images and retrieving visual analysis results.
"""
import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from api.celery_app import celery_app
from api.src.tasks.image_analysis_tasks import run_single_image_task

image_analysis_bp = Blueprint('image_analysis', __name__)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@image_analysis_bp.route('/upload', methods=['POST'])
def upload_image():
    """Upload an image for visual analysis.

    Accepts multipart/form-data with:
    - file: Image file (required)
    - brand: Brand name (optional, default: "Unknown")
    - product_name: Product name (optional, default: "Unknown Product")

    Returns:
        JSON with job_id and status
    """
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    # Check if filename is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Check file extension
    if not allowed_file(file.filename):
        return jsonify({
            'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    # Get optional parameters
    brand = request.form.get('brand', 'Unknown')
    product_name = request.form.get('product_name', 'Unknown Product')

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Create output directory for uploaded images
    output_dir = current_app.config.get('OUTPUT_DIR', '/app/output')
    upload_dir = Path(output_dir) / 'single_analysis' / 'images'
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file with job_id prefix for uniqueness
    original_filename = secure_filename(file.filename)
    file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'png'
    saved_filename = f"{job_id}.{file_ext}"
    file_path = upload_dir / saved_filename

    try:
        file.save(str(file_path))
    except Exception as e:
        current_app.logger.error(f"Failed to save uploaded file: {e}")
        return jsonify({'error': 'Failed to save uploaded file'}), 500

    # Enqueue Celery task
    try:
        task = run_single_image_task.apply_async(
            args=[job_id, str(file_path), brand, product_name],
            task_id=job_id  # Use job_id as task_id for easy lookup
        )

        return jsonify({
            'job_id': job_id,
            'status': 'pending',
            'message': 'Image uploaded and analysis started'
        }), 202

    except Exception as e:
        current_app.logger.error(f"Failed to enqueue analysis task: {e}")
        # Clean up uploaded file
        try:
            file_path.unlink()
        except:
            pass
        return jsonify({'error': 'Failed to start analysis task'}), 500


@image_analysis_bp.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id: str):
    """Get status of an image analysis job.

    Args:
        job_id: Job identifier

    Returns:
        JSON with job status and progress information
    """
    try:
        task = celery_app.AsyncResult(job_id)

        response = {
            'job_id': job_id,
            'state': task.state
        }

        if task.state == 'PENDING':
            response['status'] = 'Analysis en attente de démarrage'
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
            response['status'] = f'État: {task.state}'

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get job status: {e}")
        return jsonify({'error': 'Failed to retrieve job status'}), 500


@image_analysis_bp.route('/list', methods=['GET'])
def list_analyses():
    """List all completed single image analyses.

    Returns:
        JSON with list of analyses containing job_id, brand, product_name, etc.
    """
    import json
    
    try:
        output_dir = current_app.config.get('OUTPUT_DIR', '/app/output')
        single_analysis_dir = Path(output_dir) / 'single_analysis'
        api_base_url = os.getenv('API_BASE_URL', '')
        
        if not single_analysis_dir.exists():
            return jsonify({'analyses': []}), 200
        
        analyses = []
        
        for json_file in single_analysis_dir.glob("*.json"):
            # Skip hidden files
            if json_file.name.startswith('.'):
                continue
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Only include successful analyses
                if data.get('status') == 'success' and data.get('analysis'):
                    # Build image URL
                    image_path = data.get('image_path', '')
                    image_url = None
                    if image_path:
                        filename = Path(image_path).name
                        image_url = f"{api_base_url}/images/single_analysis/images/{filename}"
                    
                    analyses.append({
                        'job_id': data.get('job_id'),
                        'brand': data.get('brand', 'Unknown'),
                        'product_name': data.get('product_name', 'Unknown Product'),
                        'image_url': image_url,
                        'hierarchy_clarity_score': data.get('hierarchy_clarity_score'),
                        'analyzed_at': data.get('analyzed_at')
                    })
            except (json.JSONDecodeError, IOError):
                continue
        
        # Sort by analyzed_at (newest first)
        analyses.sort(key=lambda x: x.get('analyzed_at', ''), reverse=True)
        
        return jsonify({'analyses': analyses}), 200
    
    except Exception as e:
        current_app.logger.error(f"Failed to list analyses: {e}")
        return jsonify({'error': 'Failed to list analyses'}), 500


@image_analysis_bp.route('/result/<job_id>', methods=['GET'])
def get_analysis_result(job_id: str):
    """Get the full analysis result for a completed job.

    Args:
        job_id: Job identifier

    Returns:
        JSON with full analysis data
    """
    import json as json_module
    
    try:
        output_dir = current_app.config.get('OUTPUT_DIR', '/app/output')
        api_base_url = os.getenv('API_BASE_URL', '')
        
        # First, check if result JSON file exists (for completed analyses)
        result_file = Path(output_dir) / 'single_analysis' / f'{job_id}.json'
        
        if result_file.exists():
            # Load from saved file - this is a completed analysis
            with open(result_file, 'r', encoding='utf-8') as f:
                result = json_module.load(f)
            
            if result and result.get('status') == 'success':
                # Transform image paths to API URLs
                original_path = result.get('image_path', '')
                heatmap_path = result.get('heatmap_path', '')

                if original_path:
                    filename = Path(original_path).name
                    result['image_url'] = f"{api_base_url}/images/single_analysis/images/{filename}"

                if heatmap_path:
                    heatmap_filename = Path(heatmap_path).name
                    result['heatmap_url'] = f"{api_base_url}/images/single_analysis/images/{heatmap_filename}"

                return jsonify(result), 200
            else:
                return jsonify({
                    'error': 'Analysis failed',
                    'job_id': job_id,
                    'errors': result.get('errors', ['Unknown error']) if result else ['No result']
                }), 500
        
        # No saved file - check Celery task status (for in-progress jobs)
        task = celery_app.AsyncResult(job_id)

        if task.state == 'PENDING':
            return jsonify({
                'error': 'Job not found or not started',
                'job_id': job_id,
                'state': 'PENDING'
            }), 404

        if task.state == 'FAILURE':
            return jsonify({
                'error': 'Analysis failed',
                'job_id': job_id,
                'state': 'FAILURE',
                'details': str(task.info) if task.info else 'Unknown error'
            }), 500

        if task.state != 'SUCCESS':
            return jsonify({
                'error': 'Analysis not yet complete',
                'job_id': job_id,
                'state': task.state,
                'progress': task.info.get('progress_percent', 0) if task.info else 0
            }), 202

        # Task completed - return result from Celery
        result = task.result

        if result and result.get('status') == 'success':
            # Transform image path to API URL
            original_path = result.get('image_path', '')
            heatmap_path = result.get('heatmap_path', '')

            if original_path:
                filename = Path(original_path).name
                result['image_url'] = f"{api_base_url}/images/single_analysis/images/{filename}"

            if heatmap_path:
                heatmap_filename = Path(heatmap_path).name
                result['heatmap_url'] = f"{api_base_url}/images/single_analysis/images/{heatmap_filename}"

            return jsonify(result), 200
        else:
            return jsonify({
                'error': 'Analysis failed',
                'job_id': job_id,
                'errors': result.get('errors', ['Unknown error']) if result else ['No result']
            }), 500

    except Exception as e:
        current_app.logger.error(f"Failed to get analysis result: {e}")
        return jsonify({'error': 'Failed to retrieve analysis result'}), 500
