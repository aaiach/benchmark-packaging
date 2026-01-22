"""Celery tasks for scraper pipeline execution.

This module wraps the analysis engine's runner.py with Celery task management,
providing progress tracking and asynchronous execution.
"""
import sys
import os

# Add analysis_engine to Python path for imports
sys.path.insert(0, '/app/analysis_engine')

from api.celery_app import celery_app


@celery_app.task(bind=True, name='scraper.run_pipeline')
def run_pipeline_task(self, category: str = None, country: str = 'France', count: int = 30, steps: str = '1-7', run_id: str = None):
    """Execute scraper pipeline as Celery task.

    This task wraps the analysis_engine runner.py function and adds
    Celery progress tracking for real-time job monitoring.

    Args:
        self: Celery task instance (bound)
        category: Product category (e.g., "lait d'avoine"). Optional when resuming with run_id.
        country: Target country (default: "France")
        count: Number of products to discover (default: 30)
        steps: Steps to execute (e.g., "1-7", "1-4") (default: "1-7")
        run_id: Optional run_id to resume existing run

    Returns:
        dict: Result with status, run_id, and output files

    Example:
        >>> task = run_pipeline_task.apply_async(args=["lait d'avoine", "France", 20, "1-5"])
        >>> result = task.get()
        >>> print(result['status'])
        'success'
    """
    from analysis_engine.src.runner import run_pipeline

    # Validate: either category or run_id must be provided
    if not category and not run_id:
        return {
            'status': 'error',
            'errors': ['Either category or run_id must be provided'],
            'run_id': 'unknown'
        }

    # Get output directory from environment
    output_dir = os.getenv('OUTPUT_DIR', '/app/output')

    # Update initial state
    self.update_state(
        state='STARTED',
        meta={
            'status': 'Initializing pipeline',
            'progress_percent': 0,
            'category': category or 'resuming',
            'run_id': run_id or 'new'
        }
    )

    # Define progress callback for runner
    def progress_callback(step_num, step_name, meta):
        """Called by runner after each step completion."""
        self.update_state(
            state='PROGRESS',
            meta={
                **meta,
                'category': category,
                'run_id': meta.get('run_id', run_id or 'new')
            }
        )

    # Execute pipeline with progress tracking
    try:
        result = run_pipeline(
            category=category,
            country=country,
            count=count,
            output_dir=output_dir,
            steps=steps,
            run_id=run_id,
            progress_callback=progress_callback
        )

        # Update final state
        if result['status'] == 'success':
            self.update_state(
                state='PROGRESS',
                meta={
                    'status': 'Pipeline completed successfully',
                    'progress_percent': 100,
                    'category': category,
                    'run_id': result['run_id'],
                    'completed_steps': result['completed_steps']
                }
            )

        return result

    except Exception as e:
        # Log error and return failure result
        error_msg = f'Pipeline execution failed: {str(e)}'

        return {
            'status': 'error',
            'errors': [error_msg],
            'category': category,
            'run_id': run_id or 'unknown'
        }
