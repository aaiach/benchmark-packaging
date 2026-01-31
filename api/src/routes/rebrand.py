"""Rebrand API routes for 4-step rebrand pipeline.

Endpoints for:
- Starting a rebrand job with source, inspiration images and brand identity
- Checking job status with verbose step-by-step progress
- Retrieving complete results with all intermediate step data
"""
import os
import json
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from api.celery_app import celery_app
from api.src.tasks.rebrand_tasks import run_rebrand_task

rebrand_bp = Blueprint('rebrand', __name__)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@rebrand_bp.route('/start', methods=['POST'])
def start_rebrand():
    """Start a rebrand job with two images and brand identity text.

    Accepts multipart/form-data with:
    - source_image: Source brand packaging image (required)
    - inspiration_image: Inspiration/target layout image (required)
    - brand_identity: Brand identity and constraints text (required)

    Returns:
        JSON with job_id and status
    """
    # Check required files
    if 'source_image' not in request.files:
        return jsonify({'error': 'No source_image provided'}), 400
    
    if 'inspiration_image' not in request.files:
        return jsonify({'error': 'No inspiration_image provided'}), 400
    
    source_file = request.files['source_image']
    inspiration_file = request.files['inspiration_image']
    
    # Check filenames
    if source_file.filename == '':
        return jsonify({'error': 'No source image selected'}), 400
    
    if inspiration_file.filename == '':
        return jsonify({'error': 'No inspiration image selected'}), 400
    
    # Check file extensions
    if not allowed_file(source_file.filename):
        return jsonify({
            'error': f'Invalid source image type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    if not allowed_file(inspiration_file.filename):
        return jsonify({
            'error': f'Invalid inspiration image type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    # Get brand identity text
    brand_identity = request.form.get('brand_identity', '')
    if not brand_identity.strip():
        return jsonify({'error': 'brand_identity text is required'}), 400
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create upload directory
    output_dir = current_app.config.get('OUTPUT_DIR', '/app/output')
    job_dir = Path(output_dir) / 'rebrand' / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Save source image
    source_ext = source_file.filename.rsplit('.', 1)[1].lower() if '.' in source_file.filename else 'png'
    source_filename = f"source.{source_ext}"
    source_path = job_dir / source_filename
    
    # Save inspiration image
    insp_ext = inspiration_file.filename.rsplit('.', 1)[1].lower() if '.' in inspiration_file.filename else 'png'
    inspiration_filename = f"inspiration.{insp_ext}"
    inspiration_path = job_dir / inspiration_filename
    
    try:
        source_file.save(str(source_path))
        inspiration_file.save(str(inspiration_path))
    except Exception as e:
        current_app.logger.error(f"Failed to save uploaded files: {e}")
        return jsonify({'error': 'Failed to save uploaded files'}), 500
    
    # Enqueue Celery task
    try:
        task = run_rebrand_task.apply_async(
            args=[
                job_id,
                str(source_path),
                str(inspiration_path),
                brand_identity
            ],
            task_id=job_id
        )
        
        return jsonify({
            'job_id': job_id,
            'status': 'pending',
            'message': 'Rebrand pipeline started'
        }), 202
        
    except Exception as e:
        current_app.logger.error(f"Failed to enqueue rebrand task: {e}")
        # Clean up uploaded files
        try:
            source_path.unlink()
            inspiration_path.unlink()
        except:
            pass
        return jsonify({'error': 'Failed to start rebrand task'}), 500


@rebrand_bp.route('/status/<job_id>', methods=['GET'])
def get_rebrand_status(job_id: str):
    """Get status of a rebrand job with verbose step information.

    Args:
        job_id: Job identifier

    Returns:
        JSON with job status, current step, and step details
    """
    try:
        task = celery_app.AsyncResult(job_id)
        
        response = {
            'job_id': job_id,
            'state': task.state
        }
        
        if task.state == 'PENDING':
            response['status'] = 'Rebrand en attente'
            response['progress'] = 0
            response['current_step'] = None
            
        elif task.state == 'STARTED':
            response['status'] = 'Pipeline démarré'
            response['progress'] = 5
            response['current_step'] = 'initializing'
            if task.info:
                response.update(task.info)
                
        elif task.state == 'PROGRESS':
            response['status'] = 'Pipeline en cours'
            if task.info:
                response.update(task.info)
                # Calculate progress based on completed steps
                completed_steps = task.info.get('completed_steps', 0)
                response['progress'] = min(25 * completed_steps, 95)
                
        elif task.state == 'SUCCESS':
            response['status'] = 'Rebrand terminé avec succès'
            response['progress'] = 100
            response['result'] = task.result
            
        elif task.state == 'FAILURE':
            response['status'] = 'Échec du rebrand'
            response['progress'] = 0
            response['error'] = str(task.info) if task.info else 'Erreur inconnue'
            
        else:
            response['status'] = f'État: {task.state}'
        
        return jsonify(response), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to get rebrand status: {e}")
        return jsonify({'error': 'Failed to retrieve job status'}), 500


@rebrand_bp.route('/result/<job_id>', methods=['GET'])
def get_rebrand_result(job_id: str):
    """Get the complete rebrand result with all intermediate step data.

    Args:
        job_id: Job identifier

    Returns:
        JSON with full rebrand result including:
        - All step results with cropped images
        - Element extractions
        - Mapping details
        - Generated image URL
    """
    try:
        output_dir = current_app.config.get('OUTPUT_DIR', '/app/output')
        api_base_url = os.getenv('API_BASE_URL', '')
        
        # Check if result JSON file exists
        result_file = Path(output_dir) / 'rebrand' / job_id / 'result.json'
        
        if result_file.exists():
            # Load from saved file
            with open(result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            # Transform image paths to API URLs
            result = _transform_image_urls(result, job_id, api_base_url)
            
            return jsonify(result), 200
        
        # No saved file - check Celery task status
        task = celery_app.AsyncResult(job_id)
        
        if task.state == 'PENDING':
            return jsonify({
                'error': 'Job not found or not started',
                'job_id': job_id,
                'state': 'PENDING'
            }), 404
        
        if task.state == 'FAILURE':
            return jsonify({
                'error': 'Rebrand failed',
                'job_id': job_id,
                'state': 'FAILURE',
                'details': str(task.info) if task.info else 'Unknown error'
            }), 500
        
        if task.state != 'SUCCESS':
            return jsonify({
                'error': 'Rebrand not yet complete',
                'job_id': job_id,
                'state': task.state,
                'current_step': task.info.get('current_step') if task.info else None,
                'completed_steps': task.info.get('completed_steps', 0) if task.info else 0
            }), 202
        
        # Task completed - return result
        result = task.result
        
        if result:
            result = _transform_image_urls(result, job_id, api_base_url)
            return jsonify(result), 200
        else:
            return jsonify({
                'error': 'No result returned',
                'job_id': job_id
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Failed to get rebrand result: {e}")
        return jsonify({'error': 'Failed to retrieve rebrand result'}), 500


@rebrand_bp.route('/list', methods=['GET'])
def list_rebrands():
    """List all rebrand jobs.

    Returns:
        JSON with list of rebrand jobs
    """
    try:
        output_dir = current_app.config.get('OUTPUT_DIR', '/app/output')
        rebrand_dir = Path(output_dir) / 'rebrand'
        api_base_url = os.getenv('API_BASE_URL', '')
        
        if not rebrand_dir.exists():
            return jsonify({'jobs': []}), 200
        
        jobs = []
        
        for job_dir in rebrand_dir.iterdir():
            if not job_dir.is_dir():
                continue
            
            result_file = job_dir / 'result.json'
            if not result_file.exists():
                continue
            
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Find actual image file extensions
                job_id = data.get('job_id')
                source_file = _find_image_file(job_dir, 'source')
                inspiration_file = _find_image_file(job_dir, 'inspiration')
                
                # Build summary entry
                jobs.append({
                    'job_id': job_id,
                    'status': data.get('status'),
                    'created_at': data.get('created_at'),
                    'completed_at': data.get('completed_at'),
                    'brand_identity': data.get('brand_identity', '')[:100] + '...' if data.get('brand_identity') else '',
                    'source_image_url': f"{api_base_url}/images/rebrand/{job_id}/{source_file}",
                    'inspiration_image_url': f"{api_base_url}/images/rebrand/{job_id}/{inspiration_file}",
                    'generated_image_url': data.get('generated_image_path'),
                    'steps_completed': sum(1 for s in data.get('steps', []) if s.get('status') == 'complete'),
                    'total_steps': 4
                })
            except (json.JSONDecodeError, IOError):
                continue
        
        # Sort by created_at (newest first)
        jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({'jobs': jobs}), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to list rebrands: {e}")
        return jsonify({'error': 'Failed to list rebrand jobs'}), 500


def _find_image_file(job_dir: Path, base_name: str) -> str:
    """Find an image file with any supported extension.
    
    Args:
        job_dir: Path to the job directory
        base_name: Base filename without extension (e.g., 'source', 'inspiration')
        
    Returns:
        Filename with actual extension, or base_name.png as fallback
    """
    for ext in ALLOWED_EXTENSIONS:
        candidate = job_dir / f"{base_name}.{ext}"
        if candidate.exists():
            return f"{base_name}.{ext}"
    return f"{base_name}.png"  # fallback


def _transform_image_urls(result: dict, job_id: str, api_base_url: str) -> dict:
    """Transform file paths to API URLs in the result.
    
    Args:
        result: Result dictionary to transform
        job_id: Job identifier
        api_base_url: Base URL for API
        
    Returns:
        Transformed result with URLs
    """
    output_dir = current_app.config.get('OUTPUT_DIR', '/app/output')
    job_dir = Path(output_dir) / 'rebrand' / job_id
    
    # Transform generated image path
    if result.get('generated_image_path'):
        # Already in URL format from pipeline
        if not result['generated_image_path'].startswith('http'):
            result['generated_image_url'] = f"{api_base_url}{result['generated_image_path']}"
        else:
            result['generated_image_url'] = result['generated_image_path']
    
    # Transform source/inspiration paths - find actual file extensions
    source_file = _find_image_file(job_dir, 'source')
    inspiration_file = _find_image_file(job_dir, 'inspiration')
    
    result['source_image_url'] = f"{api_base_url}/images/rebrand/{job_id}/{source_file}"
    result['inspiration_image_url'] = f"{api_base_url}/images/rebrand/{job_id}/{inspiration_file}"
    
    # Transform cropped image URLs in steps
    if 'steps' in result:
        for step in result['steps']:
            if 'cropped_images' in step:
                step['cropped_image_urls'] = [
                    f"{api_base_url}{url}" if not url.startswith('http') else url
                    for url in step['cropped_images']
                ]
    
    return result
