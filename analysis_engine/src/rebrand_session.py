"""Rebrand Session orchestrator.

Orchestrates multiple rebrand operations for a category analysis.
Each product with a valid image in the analysis gets rebranded using
the user's source image and brand identity.

This module handles session state management and product discovery.
Actual rebrand execution is delegated to individual Celery tasks.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from .models import (
    RebrandSession,
    RebrandSessionProgress,
    ProductRebrandEntry,
)


def find_products_with_images(analysis_dir: Path, analysis_id: str) -> List[Dict[str, Any]]:
    """Find all products with valid cropped images from an analysis.
    
    Args:
        analysis_dir: Base output directory
        analysis_id: Full analysis ID (e.g., "Lait_davoine_20260124_162127")
        
    Returns:
        List of products with their image paths
    """
    products = []
    
    # Parse analysis_id to extract category_slug and run_id
    # Format: {category_slug}_{YYYYMMDD}_{HHMMSS}
    parts = analysis_id.rsplit('_', 2)
    if len(parts) >= 3:
        category_slug = '_'.join(parts[:-2])
        run_id = '_'.join(parts[-2:])
    else:
        # Fallback: use as-is
        category_slug = analysis_id
        run_id = ""
    
    # Try multiple file patterns to find the products with images
    possible_files = [
        # Visual analysis file (preferred - has full product data)
        analysis_dir / "analysis" / f"{category_slug}_visual_analysis_{run_id}.json",
        # With_images file from Step 4
        analysis_dir / f"{category_slug}_with_images_{run_id}.json",
    ]
    
    data_file = None
    for pattern in possible_files:
        if pattern.exists():
            data_file = pattern
            print(f"[✓] Found analysis data: {pattern}")
            break
    
    if not data_file:
        print(f"[!] No analysis data found.")
        print(f"    Analysis ID: {analysis_id}")
        print(f"    Parsed: category_slug={category_slug}, run_id={run_id}")
        # List available files for debugging
        if (analysis_dir / "analysis").exists():
            print(f"    Available files in {analysis_dir / 'analysis'}:")
            for f in sorted((analysis_dir / "analysis").glob("*.json"))[:20]:
                print(f"      - {f.name}")
        return products
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both array format (visual analysis) and object format (with_images)
        if isinstance(data, list):
            # Visual analysis format: array of products
            products_data = data
        else:
            # Object format with 'products' or 'results' key
            products_data = data.get('products', data.get('results', []))
        
        for idx, product in enumerate(products_data):
            # Look for image path - try multiple fields
            image_path = (
                product.get('cropped_image_path') or 
                product.get('local_image_path') or
                product.get('image_path')
            )
            
            if not image_path:
                continue
            
            # Handle Docker paths - map /app/data/output to local analysis_dir
            # Docker path: /app/data/output/images/...
            # Local path: {analysis_dir}/images/...
            path_obj = Path(image_path)
            
            if str(image_path).startswith('/app/data/output/'):
                # Map Docker path to local path
                relative_part = str(image_path).replace('/app/data/output/', '')
                path_obj = analysis_dir / relative_part
            elif str(image_path).startswith('/app/output/'):
                # Alternative Docker path
                relative_part = str(image_path).replace('/app/output/', '')
                path_obj = analysis_dir / relative_part
            elif not path_obj.is_absolute():
                # Relative path - resolve against analysis_dir
                path_obj = analysis_dir / image_path
            
            # Check if file exists
            if path_obj.exists():
                products.append({
                    'index': idx,
                    'name': product.get('brand', product.get('name', f'Product {idx}')),
                    'product_name': product.get('full_name', product.get('product_name', '')),
                    'image_path': str(path_obj),
                })
            else:
                print(f"    [!] Image not found: {path_obj} (original: {image_path})")
                    
    except (json.JSONDecodeError, IOError) as e:
        print(f"[!] Error loading analysis data: {e}")
    
    print(f"[✓] Found {len(products)} products with valid images")
    return products


def create_session(
    session_id: str,
    analysis_id: str,
    category: str,
    source_image_path: str,
    brand_identity: str,
    products: List[Dict[str, Any]],
    output_dir: str = "output",
) -> RebrandSession:
    """Create a new rebrand session with pending entries for each product.
    
    Args:
        session_id: Unique session identifier
        analysis_id: Reference to the category analysis
        category: Product category name
        source_image_path: Path to user's source image
        brand_identity: Brand identity and constraints text
        products: List of products with image paths
        output_dir: Base output directory
        
    Returns:
        New RebrandSession with pending entries
    """
    output_path = Path(output_dir)
    session_dir = output_path / "rebrand_sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Create entries for each product
    rebrands: List[ProductRebrandEntry] = []
    for product in products:
        rebrands.append(ProductRebrandEntry(
            product_index=product['index'],
            product_name=product['name'],
            inspiration_image_path=product['image_path'],
            status="pending"
        ))
    
    progress = RebrandSessionProgress(
        total=len(products),
        completed=0,
        failed=0,
        current_product=None
    )
    
    session = RebrandSession(
        session_id=session_id,
        analysis_id=analysis_id,
        category=category,
        source_image_path=source_image_path,
        brand_identity=brand_identity,
        status="pending",
        created_at=datetime.utcnow().isoformat(),
        rebrands=rebrands,
        progress=progress,
    )
    
    save_session(session, output_dir)
    return session


def save_session(session: RebrandSession, output_dir: str = "output") -> None:
    """Save session state to disk."""
    session_dir = Path(output_dir) / "rebrand_sessions" / session.session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    result_file = session_dir / "session.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(session.model_dump(), f, indent=2)


def load_session(session_id: str, output_dir: str = "output") -> Optional[RebrandSession]:
    """Load a session from disk.
    
    Args:
        session_id: Session identifier
        output_dir: Base output directory
        
    Returns:
        RebrandSession if found, None otherwise
    """
    session_file = Path(output_dir) / "rebrand_sessions" / session_id / "session.json"
    
    if not session_file.exists():
        return None
    
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return RebrandSession(**data)
    except (json.JSONDecodeError, IOError, TypeError) as e:
        print(f"[!] Error loading session: {e}")
        return None


def update_rebrand_entry(
    session_id: str,
    product_index: int,
    task_id: str,
    status: str,
    generated_image_path: Optional[str] = None,
    error: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    output_dir: str = "output",
) -> Optional[RebrandSession]:
    """Update a specific rebrand entry in the session.
    
    Args:
        session_id: Session identifier
        product_index: Index of the product in rebrands list
        task_id: Celery task ID for this rebrand
        status: New status (pending, in_progress, completed, failed)
        generated_image_path: Path to generated image (if completed)
        error: Error message (if failed)
        result: Full result dict (if completed)
        output_dir: Base output directory
        
    Returns:
        Updated RebrandSession or None if not found
    """
    session = load_session(session_id, output_dir)
    if not session:
        return None
    
    # Find and update the entry
    for entry in session.rebrands:
        if entry.product_index == product_index:
            entry.rebrand_job_id = task_id
            entry.status = status
            if generated_image_path:
                entry.generated_image_path = generated_image_path
            if error:
                entry.error = error
            if result:
                entry.result = result
            break
    
    # Update progress counts
    completed = sum(1 for e in session.rebrands if e.status == "completed")
    failed = sum(1 for e in session.rebrands if e.status == "failed")
    in_progress = sum(1 for e in session.rebrands if e.status == "in_progress")
    
    session.progress.completed = completed
    session.progress.failed = failed
    
    # Update session status
    if completed + failed == session.progress.total:
        session.completed_at = datetime.utcnow().isoformat()
        if failed == session.progress.total:
            session.status = "failed"
        elif completed == session.progress.total:
            session.status = "completed"
        else:
            session.status = "partial"
    elif in_progress > 0 or completed > 0:
        session.status = "in_progress"
    
    save_session(session, output_dir)
    return session


def get_session_for_analysis(analysis_id: str, output_dir: str = "output") -> Optional[RebrandSession]:
    """Find the rebrand session for a given analysis.
    
    Args:
        analysis_id: The analysis run_id to find session for
        output_dir: Base output directory
        
    Returns:
        RebrandSession if found, None otherwise
    """
    sessions_dir = Path(output_dir) / "rebrand_sessions"
    
    if not sessions_dir.exists():
        return None
    
    # Search through all sessions to find one matching the analysis_id
    for session_dir in sessions_dir.iterdir():
        if not session_dir.is_dir():
            continue
        
        session_file = session_dir / "session.json"
        if not session_file.exists():
            continue
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get('analysis_id') == analysis_id:
                return RebrandSession(**data)
        except (json.JSONDecodeError, IOError, TypeError):
            continue
    
    return None
