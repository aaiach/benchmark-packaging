"""Celery tasks for rebrand session orchestration.

This module orchestrates multi-product rebrand sessions by:
1. Creating a session with all products
2. Launching individual run_rebrand_task for each product

Parallelization is controlled by Celery worker concurrency settings.
Status is queried directly from Celery by the API routes.
"""
import sys
import os
from pathlib import Path

# Add analysis_engine to Python path for imports
sys.path.insert(0, '/app/analysis_engine')

from api.celery_app import celery_app
from api.src.tasks.rebrand_tasks import run_rebrand_task


@celery_app.task(bind=True, name='rebrand_session.start')
def start_rebrand_session_task(
    self,
    session_id: str,
    analysis_id: str,
    category: str,
    source_image_path: str,
    brand_identity: str,
):
    """Start a rebrand session by launching individual rebrand tasks.
    
    This task:
    1. Finds products with valid images in the analysis
    2. Creates a session tracking all products
    3. Launches individual run_rebrand_task for each product
    4. Returns immediately - status is tracked via Celery
    
    Parallelization is determined by Celery worker concurrency.
    
    Args:
        session_id: Unique session identifier
        analysis_id: Analysis ID (e.g., "Lait_davoine_20260124_162127")
        category: Product category name
        source_image_path: Path to source image
        brand_identity: Brand constraints text
        
    Returns:
        dict with session info and launched task IDs
    """
    from analysis_engine.src.rebrand_session import (
        find_products_with_images,
        create_session,
        save_session,
    )
    
    output_dir = os.getenv('OUTPUT_DIR', '/app/data/output')
    output_path = Path(output_dir)
    
    print(f"\n{'='*60}")
    print(f"REBRAND SESSION START - {session_id}")
    print(f"{'='*60}")
    print(f"Analysis ID: {analysis_id}")
    print(f"Category: {category}")
    print(f"Source Image: {source_image_path}")
    print(f"{'='*60}")
    
    # Update task state
    self.update_state(
        state='STARTED',
        meta={
            'status': 'Finding products with images...',
            'session_id': session_id,
            'phase': 'discovery',
        }
    )
    
    # Find products with valid images
    products = find_products_with_images(output_path, analysis_id)
    
    if not products:
        print("[!] No products with valid images found")
        return {
            'session_id': session_id,
            'status': 'failed',
            'error': 'No products with valid images found in analysis',
            'task_ids': [],
            'total_products': 0,
        }
    
    print(f"[✓] Found {len(products)} products with images")
    
    # Create the session
    session = create_session(
        session_id=session_id,
        analysis_id=analysis_id,
        category=category,
        source_image_path=source_image_path,
        brand_identity=brand_identity,
        products=products,
        output_dir=output_dir,
    )
    
    # Update session status to in_progress
    session.status = "in_progress"
    save_session(session, output_dir)
    
    self.update_state(
        state='PROGRESS',
        meta={
            'status': f'Launching {len(products)} rebrand tasks...',
            'session_id': session_id,
            'phase': 'launching',
            'total_products': len(products),
        }
    )
    
    # Launch individual rebrand tasks
    task_ids = []
    for idx, product in enumerate(products):
        # Generate task ID that includes session and product info
        task_id = f"{session_id}_product_{product['index']}"
        
        print(f"  [→] Launching task for {product['name']}: {task_id}")
        
        # Launch the existing working rebrand task
        run_rebrand_task.apply_async(
            args=[
                task_id,  # job_id
                source_image_path,  # source_image_path
                product['image_path'],  # inspiration_image_path
                brand_identity,  # brand_identity
            ],
            task_id=task_id,
        )
        
        task_ids.append({
            'task_id': task_id,
            'product_index': product['index'],
            'product_name': product['name'],
        })
    
    print(f"\n[✓] Launched {len(task_ids)} rebrand tasks")
    print(f"{'='*60}")
    
    return {
        'session_id': session_id,
        'status': 'launched',
        'task_ids': task_ids,
        'total_products': len(products),
    }
