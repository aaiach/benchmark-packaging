"""Main rebrand pipeline orchestrator.

Executes the 4-step rebrand pipeline with verbose output for frontend visualization:

Step 1: Extract ALL elements from inspiration image (Gemini)
Step 2: Extract source elements using brand identity (Gemini)
Step 3: Create element-by-element mapping (Opus 4.5)
Step 4: Generate final rebranded image (Gemini Image)

Each step produces verbose output that can be displayed in the frontend.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List

from .config import get_config, DiscoveryConfig
from .models import (
    RebrandStepResult,
    RebrandResult,
    InspirationExtraction,
    SourceExtraction,
    RebrandMapping,
)
from .element_extractor import (
    extract_inspiration_elements,
    extract_source_elements,
)
from .element_mapper import (
    create_element_mapping,
    validate_mapping,
)
from .image_compositor import (
    generate_with_fallback,
)


# =============================================================================
# Step Result Builders
# =============================================================================

def build_step_result(
    step_name: str,
    step_number: int,
    status: str,
    input_summary: str,
    output_summary: str,
    details: Dict[str, Any],
    cropped_images: List[str] = None,
    duration_ms: int = None,
    error_message: str = None
) -> RebrandStepResult:
    """Build a verbose step result for frontend display."""
    return RebrandStepResult(
        step_name=step_name,
        step_number=step_number,
        status=status,
        duration_ms=duration_ms,
        input_summary=input_summary,
        output_summary=output_summary,
        details=details,
        cropped_images=cropped_images or [],
        error_message=error_message
    )


def paths_to_relative_urls(
    paths: Dict[str, Path],
    job_id: str,
    prefix: str
) -> List[str]:
    """Convert file paths to relative URLs for frontend."""
    urls = []
    for element_id, path in paths.items():
        # Build relative URL
        relative_url = f"/images/rebrand/{job_id}/{prefix}/{path.name}"
        urls.append(relative_url)
    return urls


# =============================================================================
# Main Pipeline
# =============================================================================

def run_rebrand_pipeline(
    job_id: str,
    source_image_path: str,
    inspiration_image_path: str,
    brand_identity: str,
    output_dir: str = "output",
    progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    config: Optional[DiscoveryConfig] = None
) -> RebrandResult:
    """Execute the complete 4-step rebrand pipeline.
    
    Args:
        job_id: Unique identifier for this job
        source_image_path: Path to source image
        inspiration_image_path: Path to inspiration image
        brand_identity: User-provided brand identity and constraints text
        output_dir: Base output directory
        progress_callback: Optional callback(step_name, step_data) for progress updates
        config: Optional configuration
        
    Returns:
        RebrandResult with all step outputs and final image
    """
    if config is None:
        config = get_config()
    
    # Setup paths
    source_path = Path(source_image_path)
    inspiration_path = Path(inspiration_image_path)
    job_output_dir = Path(output_dir) / "rebrand" / job_id
    job_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize result tracking
    steps_output: List[RebrandStepResult] = []
    errors: List[str] = []
    created_at = datetime.utcnow().isoformat()
    
    print(f"\n{'='*60}")
    print(f"REBRAND PIPELINE - Job {job_id}")
    print(f"{'='*60}")
    print(f"Source: {source_path.name}")
    print(f"Inspiration: {inspiration_path.name}")
    print(f"Brand Identity: {brand_identity[:100]}...")
    print(f"{'='*60}\n")
    
    # Track cropped image paths
    inspiration_crops: Dict[str, Path] = {}
    source_crops: Dict[str, Path] = {}
    inspiration_extraction: Optional[InspirationExtraction] = None
    source_extraction: Optional[SourceExtraction] = None
    mapping: Optional[RebrandMapping] = None
    final_image_path: Optional[Path] = None
    
    # =========================================================================
    # STEP 1: Inspiration Element Extraction
    # =========================================================================
    step_name = "inspiration_extraction"
    step_number = 1
    print(f"\n[STEP {step_number}] {step_name.upper()}")
    
    if progress_callback:
        progress_callback(step_name, {"status": "in_progress"})
    
    start_time = time.time()
    
    try:
        inspiration_extraction, inspiration_crops = extract_inspiration_elements(
            image_path=inspiration_path,
            output_dir=job_output_dir,
            config=config
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        if inspiration_extraction:
            crop_urls = paths_to_relative_urls(inspiration_crops, job_id, "inspiration_crops")
            
            step_result = build_step_result(
                step_name=step_name,
                step_number=step_number,
                status="complete",
                input_summary=f"Inspiration image: {inspiration_path.name}",
                output_summary=f"Extracted {inspiration_extraction.total_elements} elements, cropped {len(inspiration_crops)}",
                details={
                    "total_elements": inspiration_extraction.total_elements,
                    "elements": [e.model_dump() for e in inspiration_extraction.elements],
                    "composition": inspiration_extraction.composition.model_dump(),
                    "color_palette": [c.model_dump() for c in inspiration_extraction.color_palette],
                },
                cropped_images=crop_urls,
                duration_ms=duration_ms
            )
            steps_output.append(step_result)
        else:
            errors.append("Step 1 failed: No elements extracted from inspiration")
            step_result = build_step_result(
                step_name=step_name,
                step_number=step_number,
                status="error",
                input_summary=f"Inspiration image: {inspiration_path.name}",
                output_summary="Extraction failed",
                details={},
                error_message="Failed to extract elements from inspiration image"
            )
            steps_output.append(step_result)
            
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Step 1 exception: {str(e)}"
        errors.append(error_msg)
        step_result = build_step_result(
            step_name=step_name,
            step_number=step_number,
            status="error",
            input_summary=f"Inspiration image: {inspiration_path.name}",
            output_summary="Exception occurred",
            details={"exception": str(e)},
            duration_ms=duration_ms,
            error_message=error_msg
        )
        steps_output.append(step_result)
    
    if progress_callback:
        progress_callback(step_name, {"status": "complete", "result": step_result.model_dump()})
    
    # =========================================================================
    # STEP 2: Source Element Extraction
    # =========================================================================
    step_name = "source_extraction"
    step_number = 2
    print(f"\n[STEP {step_number}] {step_name.upper()}")
    
    if progress_callback:
        progress_callback(step_name, {"status": "in_progress"})
    
    start_time = time.time()
    
    try:
        source_extraction, source_crops = extract_source_elements(
            image_path=source_path,
            brand_identity=brand_identity,
            output_dir=job_output_dir,
            config=config
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        if source_extraction:
            crop_urls = paths_to_relative_urls(source_crops, job_id, "source_crops")
            
            step_result = build_step_result(
                step_name=step_name,
                step_number=step_number,
                status="complete",
                input_summary=f"Source image: {source_path.name}, Brand identity provided",
                output_summary=f"Extracted {source_extraction.total_elements} elements, brand: {source_extraction.brand_name}",
                details={
                    "total_elements": source_extraction.total_elements,
                    "brand_name": source_extraction.brand_name,
                    "product_name": source_extraction.product_name,
                    "available_claims": source_extraction.available_claims,
                    "elements": [e.model_dump() for e in source_extraction.elements],
                    "color_palette": [c.model_dump() for c in source_extraction.color_palette],
                },
                cropped_images=crop_urls,
                duration_ms=duration_ms
            )
            steps_output.append(step_result)
        else:
            errors.append("Step 2 failed: No elements extracted from source")
            step_result = build_step_result(
                step_name=step_name,
                step_number=step_number,
                status="error",
                input_summary=f"Source image: {source_path.name}",
                output_summary="Extraction failed",
                details={},
                error_message="Failed to extract elements from source image"
            )
            steps_output.append(step_result)
            
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Step 2 exception: {str(e)}"
        errors.append(error_msg)
        step_result = build_step_result(
            step_name=step_name,
            step_number=step_number,
            status="error",
            input_summary=f"Source image: {source_path.name}",
            output_summary="Exception occurred",
            details={"exception": str(e)},
            duration_ms=duration_ms,
            error_message=error_msg
        )
        steps_output.append(step_result)
    
    if progress_callback:
        progress_callback(step_name, {"status": "complete", "result": step_result.model_dump()})
    
    # Check if we can proceed to Step 3
    if not inspiration_extraction or not source_extraction:
        print("\n[!] Cannot proceed to mapping - extraction failed")
        return RebrandResult(
            status="error",
            job_id=job_id,
            steps=steps_output,
            generated_image_path=None,
            source_image_path=str(source_path),
            inspiration_image_path=str(inspiration_path),
            brand_identity=brand_identity,
            created_at=created_at,
            completed_at=datetime.utcnow().isoformat(),
            errors=errors
        )
    
    # =========================================================================
    # STEP 3: Element Mapping (Opus 4.5)
    # =========================================================================
    step_name = "element_mapping"
    step_number = 3
    print(f"\n[STEP {step_number}] {step_name.upper()}")
    
    if progress_callback:
        progress_callback(step_name, {"status": "in_progress"})
    
    start_time = time.time()
    
    try:
        mapping, mapping_debug = create_element_mapping(
            inspiration=inspiration_extraction,
            source=source_extraction,
            brand_identity=brand_identity,
            config=config
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        if mapping:
            # Validate mapping
            is_valid, warnings = validate_mapping(mapping, inspiration_extraction)
            
            step_result = build_step_result(
                step_name=step_name,
                step_number=step_number,
                status="complete",
                input_summary=f"{inspiration_extraction.total_elements} inspiration elements, {source_extraction.total_elements} source elements",
                output_summary=f"Created {len(mapping.mappings)} mappings",
                details={
                    "total_mappings": len(mapping.mappings),
                    "mappings": [m.model_dump() for m in mapping.mappings],
                    "composition_description": mapping.composition_description,
                    "color_scheme": mapping.color_scheme.model_dump(),
                    "assembly_notes": mapping.assembly_notes,
                    "validation": {
                        "is_valid": is_valid,
                        "warnings": warnings
                    },
                    # Debug info - prompts and responses
                    "llm_debug": {
                        "model": mapping_debug.get("model", ""),
                        "system_prompt": mapping_debug.get("system_prompt", ""),
                        "user_prompt": mapping_debug.get("user_prompt", ""),
                        "raw_response": mapping_debug.get("raw_response", ""),
                    }
                },
                duration_ms=duration_ms
            )
            steps_output.append(step_result)
        else:
            errors.append("Step 3 failed: Mapping creation failed")
            step_result = build_step_result(
                step_name=step_name,
                step_number=step_number,
                status="error",
                input_summary=f"{inspiration_extraction.total_elements} inspiration, {source_extraction.total_elements} source",
                output_summary="Mapping failed",
                details={
                    # Include debug info even on error
                    "llm_debug": {
                        "model": mapping_debug.get("model", ""),
                        "system_prompt": mapping_debug.get("system_prompt", ""),
                        "user_prompt": mapping_debug.get("user_prompt", ""),
                        "raw_response": mapping_debug.get("raw_response", ""),
                    }
                },
                error_message="Failed to create element mapping"
            )
            steps_output.append(step_result)
            
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Step 3 exception: {str(e)}"
        errors.append(error_msg)
        step_result = build_step_result(
            step_name=step_name,
            step_number=step_number,
            status="error",
            input_summary="Extraction results from steps 1 & 2",
            output_summary="Exception occurred",
            details={"exception": str(e)},
            duration_ms=duration_ms,
            error_message=error_msg
        )
        steps_output.append(step_result)
    
    if progress_callback:
        progress_callback(step_name, {"status": "complete", "result": step_result.model_dump()})
    
    # Check if we can proceed to Step 4
    if not mapping:
        print("\n[!] Cannot proceed to generation - mapping failed")
        return RebrandResult(
            status="error",
            job_id=job_id,
            steps=steps_output,
            generated_image_path=None,
            source_image_path=str(source_path),
            inspiration_image_path=str(inspiration_path),
            brand_identity=brand_identity,
            created_at=created_at,
            completed_at=datetime.utcnow().isoformat(),
            errors=errors
        )
    
    # =========================================================================
    # STEP 4: Image Generation (Gemini)
    # =========================================================================
    step_name = "image_generation"
    step_number = 4
    print(f"\n[STEP {step_number}] {step_name.upper()}")
    
    if progress_callback:
        progress_callback(step_name, {"status": "in_progress"})
    
    start_time = time.time()
    
    try:
        output_image_path = job_output_dir / "final_rebrand.png"
        
        final_image_path, gen_debug = generate_with_fallback(
            mapping=mapping,
            inspiration=inspiration_extraction,
            source=source_extraction,
            inspiration_crops=inspiration_crops,
            source_crops=source_crops,
            output_path=output_image_path,
            config=config,
            max_retries=3
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Convert input image paths to URLs for frontend
        input_image_urls = []
        for img_path in gen_debug.get("input_images", []):
            # Extract just the filename and build URL
            path_obj = Path(img_path)
            if "inspiration_crops" in str(path_obj):
                input_image_urls.append(f"/images/rebrand/{job_id}/inspiration_crops/{path_obj.name}")
            elif "source_crops" in str(path_obj):
                input_image_urls.append(f"/images/rebrand/{job_id}/source_crops/{path_obj.name}")
        
        if final_image_path:
            final_image_url = f"/images/rebrand/{job_id}/{final_image_path.name}"
            
            step_result = build_step_result(
                step_name=step_name,
                step_number=step_number,
                status="complete",
                input_summary=f"{len(mapping.mappings)} mappings, {len(inspiration_crops)} + {len(source_crops)} crops",
                output_summary=f"Generated: {final_image_path.name}",
                details={
                    "generated_image": final_image_url,
                    "input_crops_count": len(inspiration_crops) + len(source_crops),
                    # Debug info - prompts and input images
                    "llm_debug": {
                        "model": gen_debug.get("model", ""),
                        "system_prompt": gen_debug.get("system_prompt", ""),
                        "user_prompt": gen_debug.get("user_prompt", ""),
                        "full_prompt": gen_debug.get("full_prompt", ""),
                        "composition_text": gen_debug.get("composition_text", ""),
                        "input_image_urls": input_image_urls,
                        "input_image_count": gen_debug.get("input_image_count", 0),
                        "target_dimensions": gen_debug.get("target_dimensions", {}),
                        "attempt": gen_debug.get("attempt", 1),
                    }
                },
                duration_ms=duration_ms
            )
            steps_output.append(step_result)
        else:
            errors.append("Step 4 failed: Image generation failed")
            step_result = build_step_result(
                step_name=step_name,
                step_number=step_number,
                status="error",
                input_summary=f"Mapping with {len(mapping.mappings)} entries",
                output_summary="Generation failed",
                details={
                    # Include debug info even on error
                    "llm_debug": {
                        "model": gen_debug.get("model", ""),
                        "system_prompt": gen_debug.get("system_prompt", ""),
                        "user_prompt": gen_debug.get("user_prompt", ""),
                        "full_prompt": gen_debug.get("full_prompt", ""),
                        "composition_text": gen_debug.get("composition_text", ""),
                        "input_image_urls": input_image_urls,
                        "input_image_count": gen_debug.get("input_image_count", 0),
                        "target_dimensions": gen_debug.get("target_dimensions", {}),
                        "error": gen_debug.get("error", "Unknown error"),
                    }
                },
                error_message="Failed to generate rebranded image"
            )
            steps_output.append(step_result)
            
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Step 4 exception: {str(e)}"
        errors.append(error_msg)
        step_result = build_step_result(
            step_name=step_name,
            step_number=step_number,
            status="error",
            input_summary="Mapping and cropped elements",
            output_summary="Exception occurred",
            details={"exception": str(e)},
            duration_ms=duration_ms,
            error_message=error_msg
        )
        steps_output.append(step_result)
    
    if progress_callback:
        progress_callback(step_name, {"status": "complete", "result": step_result.model_dump()})
    
    # =========================================================================
    # Build Final Result
    # =========================================================================
    completed_at = datetime.utcnow().isoformat()
    
    # Determine overall status
    if final_image_path:
        status = "success"
    elif len(errors) > 0 and any(s.status == "complete" for s in steps_output):
        status = "partial"
    else:
        status = "error"
    
    # Convert final image path to URL
    final_image_url = None
    if final_image_path:
        final_image_url = f"/images/rebrand/{job_id}/{final_image_path.name}"
    
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE - Status: {status.upper()}")
    print(f"{'='*60}")
    
    result = RebrandResult(
        status=status,
        job_id=job_id,
        steps=steps_output,
        generated_image_path=final_image_url,
        source_image_path=str(source_path),
        inspiration_image_path=str(inspiration_path),
        brand_identity=brand_identity,
        created_at=created_at,
        completed_at=completed_at,
        errors=errors
    )
    
    # Save result JSON
    result_json_path = job_output_dir / "result.json"
    with open(result_json_path, 'w') as f:
        json.dump(result.model_dump(), f, indent=2)
    
    print(f"Result saved: {result_json_path}")
    
    return result
