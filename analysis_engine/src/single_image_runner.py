"""Single image analysis runner - standalone visual analysis for a single uploaded image.

This module provides a simplified interface to run visual analysis on a single image
without going through the full category discovery pipeline.

Reuses the VisualAnalyzer.analyze_image() method from visual_analyzer.py
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from .visual_analyzer import VisualAnalyzer
from .config import get_config, DiscoveryConfig


def run_single_image_analysis(
    image_path: str,
    job_id: str,
    brand: str = "Unknown",
    product_name: str = "Unknown Product",
    output_dir: str = "output",
    progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    config: Optional[DiscoveryConfig] = None,
    generate_heatmap: bool = True
) -> Dict[str, Any]:
    """Run visual analysis on a single image.

    This is the core function that can be called from:
    - Web API (via Flask routes)
    - Task queue (via Celery workers)

    Args:
        image_path: Path to the image file to analyze
        job_id: Unique identifier for this analysis job
        brand: Brand name for context (default: "Unknown")
        product_name: Product name for context (default: "Unknown Product")
        output_dir: Output directory path (default: "output")
        progress_callback: Optional callback function called during processing
                          callback(status: str, meta: dict)
        config: Optional configuration. Uses global config if not provided.
        generate_heatmap: Whether to generate eye-tracking heatmap (default: True)

    Returns:
        dict: Result with the following structure:
            {
                'status': 'success' | 'error',
                'job_id': str,
                'image_path': str,
                'heatmap_path': str | None,
                'brand': str,
                'product_name': str,
                'analysis': dict | None,  # VisualHierarchyAnalysis as dict
                'output_file': str | None,
                'errors': List[str]  # Only present if status == 'error'
            }

    Example:
        >>> result = run_single_image_analysis(
        ...     "/path/to/image.jpg",
        ...     job_id="abc123",
        ...     brand="Diptyque",
        ...     product_name="Baies Candle"
        ... )
        >>> if result['status'] == 'success':
        ...     print(f"Analysis complete: {result['analysis']['visual_anchor']}")
    """
    # Load configuration
    if config is None:
        config = get_config()

    # Validate image path
    image_file = Path(image_path)
    if not image_file.exists():
        return {
            'status': 'error',
            'job_id': job_id,
            'image_path': str(image_path),
            'errors': [f'Image file not found: {image_path}']
        }

    # Check file extension
    supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    if image_file.suffix.lower() not in supported_formats:
        return {
            'status': 'error',
            'job_id': job_id,
            'image_path': str(image_path),
            'errors': [f'Unsupported image format: {image_file.suffix}. Supported: {supported_formats}']
        }

    # Setup output directory for single image analysis results
    output_path = Path(output_dir)
    single_analysis_dir = output_path / "single_analysis"
    single_analysis_dir.mkdir(parents=True, exist_ok=True)

    # Notify progress
    if progress_callback:
        progress_callback('analyzing', {
            'status': 'Analyse de l\'image avec Gemini Vision',
            'progress_percent': 10,
            'job_id': job_id
        })

    print(f"[SingleImageAnalysis] Starting analysis for job: {job_id}")
    print(f"  Image: {image_file.name}")
    print(f"  Brand: {brand}")
    print(f"  Product: {product_name}")

    # Initialize analyzer and run analysis
    try:
        analyzer = VisualAnalyzer(config=config)

        if progress_callback:
            progress_callback('analyzing', {
                'status': 'Analyse de la hiérarchie visuelle en cours',
                'progress_percent': 30,
                'job_id': job_id
            })

        # Call the core analysis method
        analysis = analyzer.analyze_image(
            image_path=image_file,
            brand=brand,
            product_name=product_name,
            category=""  # No category for single image analysis
        )

        if analysis is None:
            return {
                'status': 'error',
                'job_id': job_id,
                'image_path': str(image_path),
                'brand': brand,
                'product_name': product_name,
                'errors': ['Visual analysis failed - no result returned from AI model']
            }

        # Convert analysis to dict
        analysis_dict = analysis.model_dump()

        # Generate heatmap if requested
        heatmap_path = None
        if generate_heatmap:
            if progress_callback:
                progress_callback('heatmap', {
                    'status': 'Génération de la heatmap d\'attention',
                    'progress_percent': 70,
                    'job_id': job_id
                })

            print(f"[SingleImageAnalysis] Generating heatmap...")
            
            # Create heatmap output path
            heatmap_filename = f"{job_id}_heatmap{image_file.suffix}"
            heatmap_output = single_analysis_dir / "images" / heatmap_filename
            heatmap_output.parent.mkdir(parents=True, exist_ok=True)

            try:
                generated_heatmap = analyzer.generate_heatmap(
                    image_path=image_file,
                    analysis=analysis_dict,
                    output_path=heatmap_output,
                    brand=brand,
                    product_name=product_name
                )
                
                if generated_heatmap:
                    heatmap_path = str(generated_heatmap)
                    print(f"  Heatmap saved to: {heatmap_path}")
                else:
                    print(f"  [!] Heatmap generation failed (non-critical)")
            except Exception as heatmap_error:
                print(f"  [!] Heatmap generation error (non-critical): {heatmap_error}")

        if progress_callback:
            progress_callback('processing', {
                'status': 'Finalisation des résultats',
                'progress_percent': 90,
                'job_id': job_id
            })

        # Build result
        result = {
            'status': 'success',
            'job_id': job_id,
            'image_path': str(image_path),
            'heatmap_path': heatmap_path,
            'brand': brand,
            'product_name': product_name,
            'analysis': analysis_dict,
            'analysis_success': True,
            'hierarchy_clarity_score': analysis.hierarchy_clarity_score,
            'analyzed_at': datetime.now().isoformat()
        }

        # Save result to file
        output_file = single_analysis_dir / f"{job_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        result['output_file'] = str(output_file)

        print(f"[SingleImageAnalysis] Analysis complete")
        print(f"  Hierarchy clarity score: {analysis.hierarchy_clarity_score}/10")
        print(f"  Output saved to: {output_file}")

        if progress_callback:
            progress_callback('complete', {
                'status': 'Analyse terminée avec succès',
                'progress_percent': 100,
                'job_id': job_id,
                'hierarchy_clarity_score': analysis.hierarchy_clarity_score
            })

        return result

    except Exception as e:
        error_msg = f'Analysis failed: {str(e)}'
        print(f"[SingleImageAnalysis] Error: {error_msg}")

        if progress_callback:
            progress_callback('error', {
                'status': error_msg,
                'progress_percent': 0,
                'job_id': job_id
            })

        return {
            'status': 'error',
            'job_id': job_id,
            'image_path': str(image_path),
            'brand': brand,
            'product_name': product_name,
            'errors': [error_msg]
        }


def get_analysis_result(job_id: str, output_dir: str = "output") -> Optional[Dict[str, Any]]:
    """Retrieve a previously saved analysis result.

    Args:
        job_id: The job identifier
        output_dir: Output directory path

    Returns:
        Analysis result dict or None if not found
    """
    output_path = Path(output_dir)
    result_file = output_path / "single_analysis" / f"{job_id}.json"

    if not result_file.exists():
        return None

    with open(result_file, 'r', encoding='utf-8') as f:
        return json.load(f)
