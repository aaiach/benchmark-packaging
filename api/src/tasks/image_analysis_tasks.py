"""Celery tasks for single image analysis.

This module wraps the analysis engine's single_image_runner with Celery task management,
providing progress tracking and asynchronous execution.
"""
import sys
import os

# Add analysis_engine to Python path for imports
sys.path.insert(0, '/app/analysis_engine')

from api.celery_app import celery_app


@celery_app.task(bind=True, name='image_analysis.run_single')
def run_single_image_task(
    self,
    job_id: str,
    image_path: str,
    brand: str = 'Unknown',
    product_name: str = 'Unknown Product'
):
    """Execute single image visual analysis as Celery task.

    This task wraps the analysis_engine single_image_runner function and adds
    Celery progress tracking for real-time job monitoring.

    Args:
        self: Celery task instance (bound)
        job_id: Unique identifier for this analysis job
        image_path: Path to the image file to analyze
        brand: Brand name for context
        product_name: Product name for context

    Returns:
        dict: Result with status, analysis data, and metadata

    Example:
        >>> task = run_single_image_task.apply_async(
        ...     args=["abc123", "/path/to/image.jpg", "Diptyque", "Baies Candle"],
        ...     task_id="abc123"
        ... )
        >>> result = task.get()
        >>> print(result['status'])
        'success'
    """
    from analysis_engine.src.single_image_runner import run_single_image_analysis

    # Get output directory from environment
    output_dir = os.getenv('OUTPUT_DIR', '/app/output')

    # Update initial state
    self.update_state(
        state='STARTED',
        meta={
            'status': 'Initializing visual analysis',
            'progress_percent': 0,
            'job_id': job_id,
            'brand': brand,
            'product_name': product_name
        }
    )

    # Define progress callback for runner
    def progress_callback(status_type: str, meta: dict):
        """Called by runner during analysis progress."""
        self.update_state(
            state='PROGRESS',
            meta={
                **meta,
                'brand': brand,
                'product_name': product_name
            }
        )

    # Execute analysis with progress tracking
    try:
        result = run_single_image_analysis(
            image_path=image_path,
            job_id=job_id,
            brand=brand,
            product_name=product_name,
            output_dir=output_dir,
            progress_callback=progress_callback
        )

        # Update final state
        if result['status'] == 'success':
            self.update_state(
                state='PROGRESS',
                meta={
                    'status': 'Analysis completed successfully',
                    'progress_percent': 100,
                    'job_id': job_id,
                    'brand': brand,
                    'product_name': product_name,
                    'hierarchy_clarity_score': result.get('hierarchy_clarity_score')
                }
            )

        return result

    except Exception as e:
        # Log error and return failure result
        error_msg = f'Analysis execution failed: {str(e)}'

        return {
            'status': 'error',
            'job_id': job_id,
            'image_path': image_path,
            'brand': brand,
            'product_name': product_name,
            'errors': [error_msg]
        }
