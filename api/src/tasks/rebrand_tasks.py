"""Celery tasks for 4-step rebrand pipeline.

This module wraps the analysis engine's rebrand_pipeline with Celery task management,
providing verbose progress tracking for each of the 4 steps.
"""
import sys
import os

# Add analysis_engine to Python path for imports
sys.path.insert(0, '/app/analysis_engine')

from api.celery_app import celery_app


@celery_app.task(bind=True, name='rebrand.run_pipeline')
def run_rebrand_task(
    self,
    job_id: str,
    source_image_path: str,
    inspiration_image_path: str,
    brand_identity: str
):
    """Execute 4-step rebrand pipeline as Celery task.

    This task wraps the analysis_engine rebrand_pipeline function and adds
    Celery progress tracking for real-time job monitoring with verbose step output.

    Pipeline Steps:
        1. Inspiration extraction (Gemini) - Extract all visual elements
        2. Source extraction (Gemini) - Extract brand elements using constraints
        3. Element mapping (Opus 4.5) - Create element-by-element mapping
        4. Image generation (Gemini) - Generate final rebranded image

    Args:
        self: Celery task instance (bound)
        job_id: Unique identifier for this rebrand job
        source_image_path: Path to source brand packaging image
        inspiration_image_path: Path to inspiration/target layout image
        brand_identity: Brand identity and constraints text

    Returns:
        dict: RebrandResult as dictionary with:
            - status: 'success', 'error', or 'partial'
            - steps: List of step results with verbose output
            - generated_image_path: URL to final image (if successful)
            - errors: List of error messages

    Example:
        >>> task = run_rebrand_task.apply_async(
        ...     args=["abc123", "/path/source.jpg", "/path/insp.jpg", "Brand: Quinoa..."],
        ...     task_id="abc123"
        ... )
        >>> result = task.get()
        >>> print(result['status'])
        'success'
    """
    from analysis_engine.src.rebrand_pipeline import run_rebrand_pipeline

    # Get output directory from environment
    output_dir = os.getenv('OUTPUT_DIR', '/app/output')

    # Update initial state
    self.update_state(
        state='STARTED',
        meta={
            'status': 'Initializing rebrand pipeline',
            'progress_percent': 0,
            'job_id': job_id,
            'current_step': 'initializing',
            'completed_steps': 0,
            'total_steps': 4
        }
    )

    # Step-to-progress mapping
    step_progress = {
        'inspiration_extraction': (1, 25, 'Extracting inspiration elements...'),
        'source_extraction': (2, 50, 'Extracting source elements...'),
        'element_mapping': (3, 75, 'Creating element mapping...'),
        'image_generation': (4, 95, 'Generating final image...')
    }

    # Define progress callback for pipeline
    def progress_callback(step_name: str, step_data: dict):
        """Called by pipeline during each step progress."""
        step_info = step_progress.get(step_name, (0, 0, 'Processing...'))
        step_num, progress, status_msg = step_info
        
        completed = step_num - 1 if step_data.get('status') == 'in_progress' else step_num
        
        meta = {
            'status': status_msg,
            'progress_percent': progress if step_data.get('status') == 'complete' else progress - 15,
            'job_id': job_id,
            'current_step': step_name,
            'completed_steps': completed,
            'total_steps': 4,
            'step_status': step_data.get('status'),
        }
        
        # Include step result if complete
        if step_data.get('status') == 'complete' and step_data.get('result'):
            meta['last_step_result'] = step_data['result']
        
        self.update_state(state='PROGRESS', meta=meta)

    # Execute pipeline with progress tracking
    try:
        result = run_rebrand_pipeline(
            job_id=job_id,
            source_image_path=source_image_path,
            inspiration_image_path=inspiration_image_path,
            brand_identity=brand_identity,
            output_dir=output_dir,
            progress_callback=progress_callback
        )

        # Convert Pydantic model to dict if needed
        if hasattr(result, 'model_dump'):
            result_dict = result.model_dump()
        else:
            result_dict = result

        # Update final state
        if result_dict.get('status') == 'success':
            self.update_state(
                state='PROGRESS',
                meta={
                    'status': 'Rebrand completed successfully',
                    'progress_percent': 100,
                    'job_id': job_id,
                    'current_step': 'complete',
                    'completed_steps': 4,
                    'total_steps': 4,
                    'generated_image': result_dict.get('generated_image_path')
                }
            )
        elif result_dict.get('status') == 'partial':
            completed = sum(1 for s in result_dict.get('steps', []) if s.get('status') == 'complete')
            self.update_state(
                state='PROGRESS',
                meta={
                    'status': 'Rebrand partially completed',
                    'progress_percent': 25 * completed,
                    'job_id': job_id,
                    'current_step': 'partial',
                    'completed_steps': completed,
                    'total_steps': 4,
                    'errors': result_dict.get('errors', [])
                }
            )

        return result_dict

    except Exception as e:
        # Log error and return failure result
        error_msg = f'Rebrand pipeline failed: {str(e)}'

        return {
            'status': 'error',
            'job_id': job_id,
            'source_image_path': source_image_path,
            'inspiration_image_path': inspiration_image_path,
            'brand_identity': brand_identity[:100] + '...' if len(brand_identity) > 100 else brand_identity,
            'steps': [],
            'generated_image_path': None,
            'errors': [error_msg],
            'created_at': None,
            'completed_at': None
        }
