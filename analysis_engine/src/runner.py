"""Core pipeline runner function - importable by API/Celery.

This module provides a pure function interface to run the analysis pipeline
without CLI dependencies, making it easy to import from web APIs and task queues.
"""
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

from .pipeline import Pipeline, PipelineContext, STEPS, parse_steps_arg
from .config import get_config


def run_pipeline(
    category: Optional[str] = None,
    country: str = "France",
    count: int = 30,
    output_dir: str = "output",
    steps: str = "1-7",
    run_id: Optional[str] = None,
    progress_callback: Optional[Callable[[int, str, Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """Run the analysis pipeline.

    This is the core pipeline execution function that can be called from:
    - CLI (via main.py)
    - Web API (via Flask routes)
    - Task queue (via Celery workers)

    Args:
        category: Product category (e.g., "lait d'avoine"). Optional when resuming with run_id.
        country: Target country (default: "France")
        count: Number of products to discover (default: 30)
        output_dir: Output directory path (default: "output")
        steps: Steps to execute (e.g., "1-7", "1-4", "3,5-6") (default: "1-7")
        run_id: Optional run_id to resume existing run
        progress_callback: Optional callback function called after each step
                          callback(step_num: int, step_name: str, meta: dict)

    Returns:
        dict: Result with the following structure:
            {
                'status': 'success' | 'error',
                'run_id': str,
                'category': str,
                'category_slug': str,
                'country': str,
                'count': int,
                'completed_steps': List[int],
                'output_files': List[str],
                'errors': List[str]  # Only present if status == 'error'
            }

    Example:
        >>> result = run_pipeline("lait d'avoine", count=20, steps="1-5")
        >>> if result['status'] == 'success':
        ...     print(f"Pipeline completed: {result['run_id']}")
    """
    # Validate: either category or run_id must be provided
    if not category and not run_id:
        return {
            'status': 'error',
            'errors': ['Either category or run_id must be provided'],
            'run_id': 'unknown'
        }

    # Load configuration
    config = get_config()

    # Create or resume context
    output_path = Path(output_dir)

    if run_id:
        ctx = PipelineContext.from_run_id(run_id, output_path)
        if not ctx:
            return {
                'status': 'error',
                'errors': [f'Run ID not found: {run_id}'],
                'run_id': run_id
            }

        # Update count/country if different from defaults
        if count != 30:  # config.default_count
            ctx.count = count
        if country != "France":  # config.default_country
            ctx.country = country
    else:
        ctx = PipelineContext.create_new(
            category=category,
            country=country,
            count=count,
            output_dir=output_path
        )

    # Parse steps
    max_step = max(STEPS.keys())
    try:
        step_numbers = parse_steps_arg(steps, max_step)
    except ValueError as e:
        return {
            'status': 'error',
            'errors': [f'Invalid steps argument: {e}'],
            'run_id': ctx.run_id,
            'category': ctx.category
        }

    # Create pipeline
    pipeline = Pipeline(STEPS, config)

    # Validate execution plan
    is_valid, validation_errors = pipeline.validate_execution_plan(step_numbers, ctx)
    if not is_valid:
        return {
            'status': 'error',
            'errors': validation_errors,
            'run_id': ctx.run_id,
            'category': ctx.category,
            'category_slug': ctx.category_slug
        }

    # Ensure output directory exists
    ctx.output_dir.mkdir(parents=True, exist_ok=True)

    # Execute steps
    completed_steps = []

    for i, step_num in enumerate(step_numbers):
        step = STEPS[step_num]

        # Call progress callback if provided
        if progress_callback:
            progress_meta = {
                'current_step': step_num,
                'step_name': step.name,
                'total_steps': len(step_numbers),
                'completed_steps': completed_steps,
                'progress_percent': int((i / len(step_numbers)) * 100)
            }
            progress_callback(step_num, step.name, progress_meta)

        # Execute step
        try:
            if step.executor:
                result = step.executor(ctx, config)
                ctx.data[f"step_{step_num}_result"] = result
                completed_steps.append(step_num)
            else:
                return {
                    'status': 'error',
                    'errors': [f'No executor for step {step_num}'],
                    'run_id': ctx.run_id,
                    'category': ctx.category,
                    'category_slug': ctx.category_slug,
                    'completed_steps': completed_steps
                }
        except Exception as e:
            return {
                'status': 'error',
                'errors': [f'Step {step_num} ({step.name}) failed: {str(e)}'],
                'run_id': ctx.run_id,
                'category': ctx.category,
                'category_slug': ctx.category_slug,
                'failed_step': step_num,
                'completed_steps': completed_steps
            }

    # Call final progress callback
    if progress_callback:
        progress_meta = {
            'current_step': None,
            'step_name': 'Complete',
            'total_steps': len(step_numbers),
            'completed_steps': completed_steps,
            'progress_percent': 100
        }
        progress_callback(None, 'Complete', progress_meta)

    # Collect output files
    output_files = []
    for step_num in completed_steps:
        output_file = STEPS[step_num].get_output_file(ctx)
        if output_file.exists():
            # Store relative path
            try:
                rel_path = output_file.relative_to(ctx.output_dir)
                output_files.append(str(rel_path))
            except ValueError:
                # File is not relative to output_dir, use absolute path
                output_files.append(str(output_file))

    # Return success result
    return {
        'status': 'success',
        'run_id': ctx.run_id,
        'category': ctx.category,
        'category_slug': ctx.category_slug,
        'country': ctx.country,
        'count': ctx.count,
        'completed_steps': completed_steps,
        'output_files': output_files
    }
