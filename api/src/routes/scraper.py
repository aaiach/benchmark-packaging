"""Scraper API routes for job management.

Endpoints for triggering scraper jobs and checking their status.
"""
from flask import Blueprint, request, jsonify, current_app
from api.celery_app import celery_app
from api.src.tasks.scraper_tasks import run_pipeline_task

scraper_bp = Blueprint('scraper', __name__)


@scraper_bp.route('/run', methods=['POST'])
def run_scraper():
    """Trigger new scraper pipeline run.

    Request body:
        {
            "category": "lait d'avoine",  // required
            "country": "France",          // optional, default: "France"
            "count": 30,                  // optional, default: 30
            "steps": "1-7"                // optional, default: "1-7"
        }

    Returns:
        JSON response:
            {
                "job_id": "uuid-string",
                "status": "pending",
                "category": "lait d'avoine"
            }

    Status codes:
        202: Job accepted and queued
        400: Invalid request (missing category or invalid parameters)
    """
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
    """Get status of scraper job.

    Args:
        job_id: Celery task ID

    Returns:
        JSON response with job status:
            {
                "job_id": "uuid-string",
                "state": "PENDING|STARTED|PROGRESS|SUCCESS|FAILURE",
                "status": "description",
                "progress": 50,           // if state is PROGRESS
                "current_step": 3,        // if state is PROGRESS
                "step_name": "scraping",  // if state is PROGRESS
                "result": {...}           // if state is SUCCESS
                "error": "message"        // if state is FAILURE
            }

    Status codes:
        200: Status retrieved successfully
        404: Job ID not found
    """
    try:
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
    """Resume existing scraper pipeline run.

    Request body:
        {
            "run_id": "20260120_184854",  // required
            "steps": "5-7"                // optional, default: "1-7"
        }

    Returns:
        JSON response:
            {
                "job_id": "uuid-string",
                "status": "pending",
                "run_id": "20260120_184854"
            }

    Status codes:
        202: Job accepted and queued
        400: Invalid request (missing run_id)
    """
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
