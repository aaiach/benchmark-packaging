"""Rebrand Session API routes.

Endpoints for rebrand sessions linked to category analyses.
Allows users to rebrand their product against all competitors.
"""
import os
import json
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from api.celery_app import celery_app
from api.src.tasks.rebrand_session_tasks import start_rebrand_session_task

rebrand_session_bp = Blueprint('rebrand_session', __name__)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _update_session_with_results(session: dict, api_base_url: str, output_dir: str) -> dict:
    """Update session with actual results from disk or Celery.
    
    Priority order (most durable first):
    1. Check if result.json exists on disk for the job
    2. Check if generated_image_path from session.json points to existing file
    3. Fall back to Celery task state (may expire from Redis)
    
    Args:
        session: Session dictionary from file
        api_base_url: Base URL for API
        output_dir: Base output directory
        
    Returns:
        Session with updated status
    """
    session_id = session.get('session_id', '')
    rebrands = session.get('rebrands', [])
    rebrand_dir = Path(output_dir) / 'rebrand'
    
    completed = 0
    failed = 0
    in_progress = 0
    
    for rebrand in rebrands:
        product_index = rebrand.get('product_index', 0)
        task_id = f"{session_id}_product_{product_index}"
        job_dir = rebrand_dir / task_id
        result_file = job_dir / 'result.json'
        
        # Priority 1: Check for result.json on disk (most durable)
        if result_file.exists():
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                result_status = result.get('status', 'unknown')
                if result_status == 'success':
                    rebrand['status'] = 'completed'
                    rebrand['generated_image_path'] = result.get('generated_image_path')
                    if rebrand.get('generated_image_path') and not rebrand['generated_image_path'].startswith('http'):
                        rebrand['generated_image_url'] = f"{api_base_url}{rebrand['generated_image_path']}"
                    completed += 1
                    continue
                elif result_status == 'error':
                    rebrand['status'] = 'failed'
                    rebrand['error'] = '; '.join(result.get('errors', ['Unknown error']))
                    failed += 1
                    continue
            except (json.JSONDecodeError, IOError):
                pass  # Fall through to other checks
        
        # Priority 2: Check if session.json already has a valid generated_image_path
        existing_path = rebrand.get('generated_image_path')
        if existing_path:
            # Convert URL path to file path and check if file exists
            # Path format: /images/rebrand/{job_id}/final_rebrand.jpg
            if existing_path.startswith('/images/rebrand/'):
                rel_path = existing_path.replace('/images/rebrand/', '')
                file_path = rebrand_dir / rel_path
                if file_path.exists():
                    rebrand['status'] = 'completed'
                    if not existing_path.startswith('http'):
                        rebrand['generated_image_url'] = f"{api_base_url}{existing_path}"
                    completed += 1
                    continue
        
        # Priority 3: Fall back to Celery (may have expired results)
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'SUCCESS':
            result = task.result or {}
            result_status = result.get('status', 'unknown')
            
            if result_status == 'success':
                rebrand['status'] = 'completed'
                rebrand['generated_image_path'] = result.get('generated_image_path')
                if rebrand.get('generated_image_path') and not rebrand['generated_image_path'].startswith('http'):
                    rebrand['generated_image_url'] = f"{api_base_url}{rebrand['generated_image_path']}"
                completed += 1
            else:
                rebrand['status'] = 'failed'
                errors = result.get('errors', [])
                for step in result.get('steps', []):
                    if step.get('error_message'):
                        errors.append(f"{step.get('step_name')}: {step.get('error_message')}")
                rebrand['error'] = '; '.join(errors) if errors else 'Rebrand failed'
                failed += 1
                
        elif task.state == 'FAILURE':
            rebrand['status'] = 'failed'
            rebrand['error'] = str(task.info) if task.info else 'Unknown error'
            failed += 1
            
        elif task.state in ('STARTED', 'PROGRESS'):
            rebrand['status'] = 'in_progress'
            in_progress += 1
            
        elif task.state == 'PENDING':
            # PENDING could mean task never started OR results expired
            # Keep existing status if we have generated_image_path (results expired case)
            if rebrand.get('generated_image_path'):
                # We already checked if file exists above, so this is truly pending
                pass
            rebrand['status'] = 'pending'
    
    total = len(rebrands)
    
    # Determine overall session status
    if completed + failed == total and total > 0:
        if failed == total:
            session['status'] = 'failed'
        elif completed == total:
            session['status'] = 'completed'
        else:
            session['status'] = 'partial'
    elif in_progress > 0 or completed > 0:
        session['status'] = 'in_progress'
    else:
        session['status'] = 'pending'
    
    # Update progress info
    session['progress'] = {
        'total': total,
        'completed': completed,
        'failed': failed,
        'current_product': None,
    }
    
    return session


@rebrand_session_bp.route('/analysis/<analysis_id>/rebrand-session/start', methods=['POST'])
def start_rebrand_session(analysis_id: str):
    """Start a rebrand session for a category analysis.

    This will rebrand the user's product against all competitors
    found in the specified category analysis.

    Accepts multipart/form-data with:
    - source_image: User's product packaging image (required)
    - brand_identity: Brand identity and constraints text (required)
    - category: Category name (required)

    Args:
        analysis_id: The category analysis run_id

    Returns:
        JSON with session_id and status
    """
    # Check required file
    if 'source_image' not in request.files:
        return jsonify({'error': 'No source_image provided'}), 400
    
    source_file = request.files['source_image']
    
    if source_file.filename == '':
        return jsonify({'error': 'No source image selected'}), 400
    
    if not allowed_file(source_file.filename):
        return jsonify({
            'error': f'Invalid source image type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    # Get required parameters
    brand_identity = request.form.get('brand_identity', '')
    if not brand_identity.strip():
        return jsonify({'error': 'brand_identity text is required'}), 400
    
    category = request.form.get('category', '')
    if not category.strip():
        return jsonify({'error': 'category is required'}), 400
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Create session directory
    output_dir = current_app.config.get('OUTPUT_DIR', '/app/output')
    session_dir = Path(output_dir) / 'rebrand_sessions' / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Save source image
    source_ext = source_file.filename.rsplit('.', 1)[1].lower() if '.' in source_file.filename else 'png'
    source_filename = f"source.{source_ext}"
    source_path = session_dir / source_filename
    
    try:
        source_file.save(str(source_path))
    except Exception as e:
        current_app.logger.error(f"Failed to save uploaded file: {e}")
        return jsonify({'error': 'Failed to save uploaded file'}), 500
    
    # Check if there's an existing session for this analysis and delete it (override)
    existing_session = _find_existing_session(analysis_id, output_dir)
    if existing_session:
        current_app.logger.info(f"Overriding existing session {existing_session} for analysis {analysis_id}")
        # We don't delete the old session directory, just let the new one take over
    
    # Enqueue Celery task - parallelism is controlled by worker concurrency
    try:
        task = start_rebrand_session_task.apply_async(
            args=[
                session_id,
                analysis_id,
                category,
                str(source_path),
                brand_identity,
            ],
            task_id=session_id
        )
        
        return jsonify({
            'session_id': session_id,
            'analysis_id': analysis_id,
            'status': 'pending',
            'message': 'Rebrand session started'
        }), 202
        
    except Exception as e:
        current_app.logger.error(f"Failed to enqueue rebrand session task: {e}")
        try:
            source_path.unlink()
        except:
            pass
        return jsonify({'error': 'Failed to start rebrand session'}), 500


@rebrand_session_bp.route('/analysis/<analysis_id>/rebrand-session', methods=['GET'])
def get_analysis_rebrand_session(analysis_id: str):
    """Get the rebrand session for a category analysis.

    Queries Celery for actual task status to return up-to-date data,
    not stale data from session.json file.

    Args:
        analysis_id: The category analysis run_id

    Returns:
        JSON with session data or 404 if no session exists
    """
    output_dir = current_app.config.get('OUTPUT_DIR', '/app/output')
    api_base_url = os.getenv('API_BASE_URL', '')
    
    session_id = _find_existing_session(analysis_id, output_dir)
    
    if not session_id:
        return jsonify({
            'error': 'No rebrand session found for this analysis',
            'analysis_id': analysis_id
        }), 404
    
    session_file = Path(output_dir) / 'rebrand_sessions' / session_id / 'session.json'
    
    if not session_file.exists():
        return jsonify({
            'error': 'Session file not found',
            'session_id': session_id
        }), 404
    
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session = json.load(f)
        
        # Update with actual results from disk or Celery (disk takes priority)
        session = _update_session_with_results(session, api_base_url, output_dir)
        
        # Transform remaining image paths to URLs
        session = _transform_session_urls(session, api_base_url, output_dir)
        
        return jsonify(session), 200
        
    except (json.JSONDecodeError, IOError) as e:
        current_app.logger.error(f"Failed to load session: {e}")
        return jsonify({'error': 'Failed to load session'}), 500


@rebrand_session_bp.route('/rebrand-session/<session_id>/status', methods=['GET'])
def get_session_status(session_id: str):
    """Get status of a rebrand session with progress information.

    Queries Celery directly for each individual task's status.

    Args:
        session_id: Session identifier

    Returns:
        JSON with session status and progress
    """
    try:
        output_dir = current_app.config.get('OUTPUT_DIR', '/app/output')
        api_base_url = os.getenv('API_BASE_URL', '')
        session_file = Path(output_dir) / 'rebrand_sessions' / session_id / 'session.json'
        
        if not session_file.exists():
            # Check if launcher task is still pending
            task = celery_app.AsyncResult(session_id)
            if task.state == 'PENDING':
                return jsonify({
                    'session_id': session_id,
                    'status': 'pending',
                    'progress_percent': 0,
                }), 200
            elif task.state == 'FAILURE':
                return jsonify({
                    'session_id': session_id,
                    'status': 'failed',
                    'error': str(task.info) if task.info else 'Unknown error',
                }), 200
            return jsonify({'error': 'Session not found'}), 404
        
        # Load session from file
        with open(session_file, 'r', encoding='utf-8') as f:
            session = json.load(f)
        
        # Update with actual results from disk or Celery (disk takes priority)
        session = _update_session_with_results(session, api_base_url, output_dir)
        
        # Transform inspiration image paths to URLs
        rebrands = session.get('rebrands', [])
        for rebrand in rebrands:
            insp_path = rebrand.get('inspiration_image_path', '')
            if insp_path:
                if '/images/' in insp_path:
                    parts = insp_path.split('/images/')
                    if len(parts) > 1:
                        rel_path = parts[1].lstrip('/')
                        rebrand['inspiration_image_url'] = f"{api_base_url}/images/{rel_path}"
                    else:
                        rebrand['inspiration_image_url'] = f"{api_base_url}/images/{Path(insp_path).name}"
                elif not insp_path.startswith('http'):
                    rebrand['inspiration_image_url'] = f"{api_base_url}/images/{Path(insp_path).name}"
        
        # Get counts from updated session
        completed = session.get('progress', {}).get('completed', 0)
        failed = session.get('progress', {}).get('failed', 0)
        in_progress = sum(1 for r in rebrands if r.get('status') == 'in_progress')
        
        total = len(rebrands)
        progress_percent = int(((completed + failed) / total) * 100) if total > 0 else 0
        
        # Determine overall status
        if completed + failed == total:
            if failed == total:
                overall_status = 'failed'
            elif completed == total:
                overall_status = 'completed'
            else:
                overall_status = 'partial'
        elif in_progress > 0 or completed > 0:
            overall_status = 'in_progress'
        else:
            overall_status = 'pending'
        
        return jsonify({
            'session_id': session_id,
            'status': overall_status,
            'progress_percent': progress_percent,
            'total': total,
            'completed': completed,
            'failed': failed,
            'in_progress': in_progress,
            'rebrands': rebrands,
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to get session status: {e}")
        return jsonify({'error': 'Failed to retrieve session status'}), 500


@rebrand_session_bp.route('/rebrand-session/<session_id>/result', methods=['GET'])
def get_session_result(session_id: str):
    """Get the complete result of a rebrand session.

    Args:
        session_id: Session identifier

    Returns:
        JSON with complete session data including all rebrand results
    """
    try:
        output_dir = current_app.config.get('OUTPUT_DIR', '/app/output')
        api_base_url = os.getenv('API_BASE_URL', '')
        
        # Check if session file exists
        session_file = Path(output_dir) / 'rebrand_sessions' / session_id / 'session.json'
        
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                session = json.load(f)
            
            session = _transform_session_urls(session, api_base_url, output_dir)
            return jsonify(session), 200
        
        # No saved file - check Celery task
        task = celery_app.AsyncResult(session_id)
        
        if task.state == 'PENDING':
            return jsonify({
                'error': 'Session not found or not started',
                'session_id': session_id,
                'state': 'PENDING'
            }), 404
        
        if task.state == 'FAILURE':
            return jsonify({
                'error': 'Session failed',
                'session_id': session_id,
                'state': 'FAILURE',
                'details': str(task.info) if task.info else 'Unknown error'
            }), 500
        
        if task.state != 'SUCCESS':
            return jsonify({
                'error': 'Session not yet complete',
                'session_id': session_id,
                'state': task.state,
                'progress': task.info if task.info else {}
            }), 202
        
        # Task completed - return result
        result = task.result
        
        if result:
            result = _transform_session_urls(result, api_base_url, output_dir)
            return jsonify(result), 200
        else:
            return jsonify({
                'error': 'No result returned',
                'session_id': session_id
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Failed to get session result: {e}")
        return jsonify({'error': 'Failed to retrieve session result'}), 500


def _find_existing_session(analysis_id: str, output_dir: str) -> str | None:
    """Find the most recent existing session for the given analysis.
    
    Args:
        analysis_id: The analysis run_id
        output_dir: Base output directory
        
    Returns:
        Session ID if found, None otherwise
    """
    sessions_dir = Path(output_dir) / 'rebrand_sessions'
    
    if not sessions_dir.exists():
        return None
    
    matching_sessions = []
    
    for session_dir in sessions_dir.iterdir():
        if not session_dir.is_dir():
            continue
        
        session_file = session_dir / 'session.json'
        if not session_file.exists():
            continue
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get('analysis_id') == analysis_id:
                # Add to list with timestamp for sorting
                created_at = data.get('created_at', '')
                matching_sessions.append((data.get('session_id'), created_at))
        except (json.JSONDecodeError, IOError):
            continue
    
    if not matching_sessions:
        return None
    
    # Sort by created_at descending (newest first)
    # If created_at is missing, it will be empty string and sort to end (oldest)
    matching_sessions.sort(key=lambda x: x[1], reverse=True)
    
    return matching_sessions[0][0]


def _transform_session_urls(session: dict, api_base_url: str, output_dir: str) -> dict:
    """Transform file paths to API URLs in the session data.
    
    Args:
        session: Session dictionary to transform
        api_base_url: Base URL for API
        output_dir: Base output directory
        
    Returns:
        Transformed session with URLs
    """
    session_id = session.get('session_id', '')
    
    # Transform source image path
    source_path = session.get('source_image_path', '')
    if source_path:
        source_filename = Path(source_path).name
        session['source_image_url'] = f"{api_base_url}/images/rebrand_sessions/{session_id}/{source_filename}"
    
    # Transform rebrand results
    if 'rebrands' in session:
        for rebrand in session['rebrands']:
            # Transform generated image path
            if rebrand.get('generated_image_path'):
                path = rebrand['generated_image_path']
                if not path.startswith('http'):
                    rebrand['generated_image_url'] = f"{api_base_url}{path}"
                else:
                    rebrand['generated_image_url'] = path
            
            # Transform inspiration image path
            if rebrand.get('inspiration_image_path'):
                insp_path = rebrand['inspiration_image_path']
                
                if '/images/' in insp_path:
                     # It's likely in the main images directory
                    parts = insp_path.split('/images/')
                    if len(parts) > 1:
                        rel_path = parts[1].lstrip('/')
                        rebrand['inspiration_image_url'] = f"{api_base_url}/images/{rel_path}"
                    else:
                        rebrand['inspiration_image_url'] = f"{api_base_url}/images/{Path(insp_path).name}"
                elif not insp_path.startswith('http'):
                    rebrand['inspiration_image_url'] = f"{api_base_url}/images/{Path(insp_path).name}"
    
    return session
