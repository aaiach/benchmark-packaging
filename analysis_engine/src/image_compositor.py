"""Image composition module for rebrand pipeline Step 4.

This module uses Gemini 3 Pro Image to generate the final rebranded packaging
image from cropped elements and composition instructions.

Key input: Cropped element images + textual composition description
NOT: Full source or inspiration images

Uses Gemini 3 Pro Image for final image generation.
"""
import base64
from pathlib import Path
from typing import Dict, List, Optional

from google import genai
from google.genai import types
from PIL import Image

from .config import get_config, DiscoveryConfig
from .models import (
    RebrandMapping,
    InspirationExtraction,
    SourceExtraction,
    ElementMappingEntry,
)
from .utils import load_prompt


# =============================================================================
# Composition Text Generation
# =============================================================================

def coords_to_natural_position(xmin: int, ymin: int, xmax: int, ymax: int) -> str:
    """Convert normalized coordinates to natural language position description.
    
    Args:
        xmin, ymin, xmax, ymax: Coordinates in 0-1000 scale
        
    Returns:
        Natural language description like "top-left corner" or "center of the image"
    """
    # Calculate center point
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2
    
    # Determine vertical position
    if cy < 250:
        v_pos = "top"
    elif cy < 400:
        v_pos = "upper"
    elif cy < 600:
        v_pos = "middle"
    elif cy < 750:
        v_pos = "lower"
    else:
        v_pos = "bottom"
    
    # Determine horizontal position
    if cx < 250:
        h_pos = "left"
    elif cx < 400:
        h_pos = "left-center"
    elif cx < 600:
        h_pos = "center"
    elif cx < 750:
        h_pos = "right-center"
    else:
        h_pos = "right"
    
    # Combine into natural description
    if v_pos == "middle" and h_pos == "center":
        return "centered in the middle of the image"
    elif h_pos == "center":
        return f"horizontally centered in the {v_pos} area"
    elif v_pos == "middle":
        return f"vertically centered on the {h_pos} side"
    else:
        return f"in the {v_pos}-{h_pos} area"


def coords_to_size_description(xmin: int, ymin: int, xmax: int, ymax: int) -> str:
    """Convert coordinates to size description.
    
    Args:
        xmin, ymin, xmax, ymax: Coordinates in 0-1000 scale
        
    Returns:
        Size description like "small element" or "large, spanning most of the width"
    """
    width_pct = (xmax - xmin) / 10
    height_pct = (ymax - ymin) / 10
    
    # Determine size category
    area = width_pct * height_pct / 100  # as fraction of total
    
    if area < 2:
        size = "very small"
    elif area < 5:
        size = "small"
    elif area < 15:
        size = "medium-sized"
    elif area < 30:
        size = "large"
    else:
        size = "very large"
    
    # Add specific dimensions
    return f"{size} (about {width_pct:.0f}% wide × {height_pct:.0f}% tall)"


def format_mapping_for_generation(
    mapping: RebrandMapping,
    inspiration: InspirationExtraction,
    source: SourceExtraction,
    inspiration_crops: Dict[str, Path],
    source_crops: Dict[str, Path]
) -> str:
    """Format the mapping into natural language composition instructions.
    
    Uses natural language positioning (recommended for Gemini image generation)
    rather than numeric coordinates.
    
    Args:
        mapping: The element-by-element mapping
        inspiration: Original inspiration extraction
        source: Original source extraction
        inspiration_crops: Dict mapping element_id to cropped image paths (inspiration)
        source_crops: Dict mapping element_id to cropped image paths (source)
        
    Returns:
        Natural language composition instruction string
    """
    lines = ["# PACKAGING DESIGN COMPOSITION", ""]
    
    # Packaging format with actual description from extraction
    lines.append("## PACKAGING FORMAT")
    fmt_choice = getattr(mapping, 'packaging_format_choice', 'inspiration')
    fmt_desc = getattr(mapping, 'packaging_format_description', '')
    if fmt_desc:
        lines.append(f"{fmt_desc}")
    else:
        lines.append(f"(Follow the {fmt_choice} image's packaging shape, size, material, and finish)")
    lines.append("")
    
    # Overall description
    lines.append("## OVERALL LAYOUT")
    lines.append(mapping.composition_description)
    lines.append("")

    # Color scheme
    lines.append("## COLOR SCHEME")
    lines.append(f"- Primary brand color: {mapping.color_scheme.primary}")
    lines.append(f"- Secondary color: {mapping.color_scheme.secondary}")
    lines.append(f"- Background color: {mapping.color_scheme.background}")
    lines.append(f"- Text color: {mapping.color_scheme.text_primary}")
    if mapping.color_scheme.accent:
        lines.append(f"- Accent color: {mapping.color_scheme.accent}")
    lines.append("")
    
    # Build element placement instructions
    lines.append("## ELEMENT PLACEMENT")
    lines.append("")
    lines.append("Place each element as follows:")
    lines.append("")
    
    # Get element lookups
    insp_lookup = {e.element_id: e for e in inspiration.elements}
    src_lookup = {e.element_id: e for e in source.elements}
    
    # Track element order for the model
    element_num = 1
    
    for entry in mapping.mappings:
        insp_elem = insp_lookup.get(entry.inspiration_element_id)
        if not insp_elem:
            continue
        
        bbox = insp_elem.bounding_box
        position = coords_to_natural_position(bbox.xmin, bbox.ymin, bbox.xmax, bbox.ymax)
        size = coords_to_size_description(bbox.xmin, bbox.ymin, bbox.xmax, bbox.ymax)
        
        if entry.action == "adapt" or entry.action == "keep":
            # ADAPT: Recreate element in source style - DO NOT copy original
            lines.append(f"**Element {element_num}: {insp_elem.element_type.upper()} (CREATE NEW)**")
            lines.append(f"- Position: {position}")
            lines.append(f"- Size: {size}")
            
            # Describe what to create conceptually
            concept = entry.adaptation_concept if hasattr(entry, 'adaptation_concept') and entry.adaptation_concept else insp_elem.content
            lines.append(f"- Concept: Create a NEW {insp_elem.element_type} representing \"{concept}\"")
            lines.append(f"- **IMPORTANT: DO NOT copy the original - design fresh artwork in the target brand style**")
            
            if entry.styling_notes:
                lines.append(f"- Style requirements: {entry.styling_notes}")
            else:
                lines.append(f"- Style: Match the target brand's visual language and color scheme")
            
        elif entry.action == "replace":
            lines.append(f"**Element {element_num}: {insp_elem.element_type.upper()} (REPLACED)**")
            lines.append(f"- Position: {position}")
            lines.append(f"- Size: {size}")
            lines.append(f"- New content: \"{entry.replacement_content}\"")
            
            if entry.replacement_source and entry.replacement_source in source_crops:
                lines.append(f"- Use the provided source brand image for this element")
            else:
                lines.append(f"- Render this text in the specified style")
            
            if entry.styling_notes:
                lines.append(f"- Style notes: {entry.styling_notes}")
            
        elif entry.action == "omit":
            # Don't include omitted elements in the count
            lines.append(f"**[OMIT]** The {insp_elem.element_type} that was {position} should be removed.")
            lines.append(f"- Fill this area with the background color ({mapping.color_scheme.background})")
            element_num -= 1  # Don't count omitted elements
        
        lines.append("")
        element_num += 1
    
    # Assembly notes
    if mapping.assembly_notes:
        lines.append("## ADDITIONAL INSTRUCTIONS")
        lines.append(mapping.assembly_notes)
        lines.append("")
    
    # Final instruction
    lines.append("## CRITICAL REQUIREMENTS")
    lines.append("- **NEVER COPY** decorative elements, illustrations, or patterns from references")
    lines.append("- CREATE ALL decorative elements FRESH in the target brand's style")
    lines.append("- Only use provided source brand images (logos, product images) directly")
    lines.append("- Maintain the relative positions of all elements as described")
    lines.append("- Ensure text is crisp and readable")
    lines.append("- The final design should look authentically created for the target brand")
    
    return "\n".join(lines)


def select_crops_for_generation(
    mapping: RebrandMapping,
    inspiration_crops: Dict[str, Path],
    source_crops: Dict[str, Path]
) -> List[Path]:
    """Select which cropped images to send to the image generation model.
    
    Returns only the crops that are actually needed based on the mapping.
    
    IMPORTANT: For "adapt" actions, we do NOT send the inspiration crop.
    The model should CREATE NEW artwork, not copy existing elements.
    Only "replace" actions with source references get their crops included.
    
    Args:
        mapping: The element-by-element mapping
        inspiration_crops: All inspiration crop paths (NOT USED for adapt actions)
        source_crops: All source crop paths
        
    Returns:
        List of paths to include in generation (only source brand assets)
    """
    needed_crops = []
    
    for entry in mapping.mappings:
        if entry.action == "adapt" or entry.action == "keep":
            # DO NOT send inspiration crops for adapt actions
            # The model must create new artwork, not copy
            pass
                
        elif entry.action == "replace":
            # Only send source crop if it's a brand asset (logo, product image)
            if entry.replacement_source and entry.replacement_source in source_crops:
                needed_crops.append(source_crops[entry.replacement_source])
    
    return needed_crops


def load_images_for_generation(crop_paths: List[Path]) -> List:
    """Load cropped images for sending to Gemini.
    
    Args:
        crop_paths: List of paths to cropped images
        
    Returns:
        List of PIL Images ready for Gemini
    """
    images = []
    
    for path in crop_paths:
        if path.exists():
            try:
                img = Image.open(path)
                images.append(img)
            except Exception as e:
                print(f"    [!] Failed to load crop {path}: {e}")
    
    return images


# =============================================================================
# Step 4: Image Generation
# =============================================================================

def generate_rebranded_image(
    mapping: RebrandMapping,
    inspiration: InspirationExtraction,
    source: SourceExtraction,
    inspiration_crops: Dict[str, Path],
    source_crops: Dict[str, Path],
    output_path: Path,
    config: Optional[DiscoveryConfig] = None
) -> tuple[Optional[Path], dict]:
    """Step 4: Generate the final rebranded image using Gemini.
    
    Takes only cropped elements and composition description - NOT full images.
    The model assembles the final packaging using:
    - Cropped elements (logos, icons, product images)
    - Textual composition instructions
    - Color scheme and styling notes
    
    Args:
        mapping: Element mapping from Step 3
        inspiration: Extraction from inspiration (for position reference)
        source: Extraction from source (for element content)
        inspiration_crops: Dict mapping element_id to cropped paths
        source_crops: Dict mapping element_id to cropped paths
        output_path: Where to save the generated image
        config: Optional configuration
        
    Returns:
        Tuple of (Path to generated image or None, debug_info dict)
    """
    debug_info = {
        "model": "",
        "system_prompt": "",
        "user_prompt": "",
        "full_prompt": "",
        "composition_text": "",
        "input_images": [],
        "input_image_count": 0,
        "target_dimensions": {},
        "error": None,
    }
    if config is None:
        config = get_config()
    
    print("[Step 4] Generating rebranded image...")
    
    # Initialize Gemini client for image generation
    client = genai.Client(api_key=config.gemini_image_gen.api_key)
    debug_info["model"] = config.gemini_image_gen.model
    
    # Format composition instructions
    composition_text = format_mapping_for_generation(
        mapping=mapping,
        inspiration=inspiration,
        source=source,
        inspiration_crops=inspiration_crops,
        source_crops=source_crops
    )
    debug_info["composition_text"] = composition_text
    
    print(f"  Composition instruction length: {len(composition_text)} chars")
    
    # Select needed crops
    crop_paths = select_crops_for_generation(
        mapping=mapping,
        inspiration_crops=inspiration_crops,
        source_crops=source_crops
    )
    
    # Store image paths for debug
    debug_info["input_images"] = [str(p) for p in crop_paths]
    debug_info["input_image_count"] = len(crop_paths)
    
    print(f"  Input crops: {len(crop_paths)}")
    
    # Load crop images
    crop_images = load_images_for_generation(crop_paths)
    print(f"  Loaded images: {len(crop_images)}")
    
    # Load prompts
    system_prompt = load_prompt("image_composition_system.txt")
    user_prompt_template = load_prompt("image_composition_user.txt")
    
    # Get dimensions from inspiration if available
    width = inspiration.image_dimensions.get('width', 800) if inspiration.image_dimensions else 800
    height = inspiration.image_dimensions.get('height', 1000) if inspiration.image_dimensions else 1000
    debug_info["target_dimensions"] = {"width": width, "height": height}
    
    # Format user prompt
    user_prompt = user_prompt_template.format(
        composition_instructions=composition_text,
        target_width=width,
        target_height=height,
        num_crops=len(crop_images)
    )
    
    # Combine prompts
    full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
    
    # Store prompts for debug
    debug_info["system_prompt"] = system_prompt
    debug_info["user_prompt"] = user_prompt
    debug_info["full_prompt"] = full_prompt
    
    try:
        # Build content list: images first, then prompt
        contents = []
        for img in crop_images:
            contents.append(img)
        contents.append(full_prompt)
        
        # Configure for image generation with Gemini 3 Pro Image
        gen_config = types.GenerateContentConfig(
            temperature=config.gemini_image_gen.temperature,
            response_modalities=["image", "text"],
        )
        
        # Call Gemini 3 Pro Image model
        print(f"  Using model: {config.gemini_image_gen.model}")
        response = client.models.generate_content(
            model=config.gemini_image_gen.model,
            contents=contents,
            config=gen_config
        )
        
        # Process response - look for generated image
        generated_image = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Found image data
                image_data = part.inline_data.data
                mime_type = part.inline_data.mime_type
                
                # Decode base64 if needed
                if isinstance(image_data, str):
                    image_bytes = base64.b64decode(image_data)
                else:
                    image_bytes = image_data
                
                # Determine extension from mime type
                ext = '.png'
                if mime_type == 'image/jpeg':
                    ext = '.jpg'
                elif mime_type == 'image/webp':
                    ext = '.webp'
                
                # Update output path with correct extension
                output_path = output_path.with_suffix(ext)
                
                # Save image
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(image_bytes)
                
                generated_image = output_path
                print(f"  [✓] Generated image saved: {output_path.name}")
                break
        
        if not generated_image:
            # Check for text response (might indicate an error)
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    print(f"  [!] Model response (no image): {part.text[:500]}")
                    debug_info["error"] = f"Model returned text instead of image: {part.text[:500]}"
            return None, debug_info
        
        return generated_image, debug_info
        
    except Exception as e:
        print(f"  [!] Image generation error: {e}")
        debug_info["error"] = str(e)
        return None, debug_info


def generate_with_fallback(
    mapping: RebrandMapping,
    inspiration: InspirationExtraction,
    source: SourceExtraction,
    inspiration_crops: Dict[str, Path],
    source_crops: Dict[str, Path],
    output_path: Path,
    config: Optional[DiscoveryConfig] = None,
    max_retries: int = 3
) -> tuple[Optional[Path], dict]:
    """Generate image with retry logic and fallback options.
    
    Args:
        mapping: Element mapping from Step 3
        inspiration: Extraction from inspiration
        source: Extraction from source
        inspiration_crops: Dict mapping element_id to cropped paths
        source_crops: Dict mapping element_id to cropped paths
        output_path: Where to save the generated image
        config: Optional configuration
        max_retries: Maximum retry attempts
        
    Returns:
        Tuple of (Path to generated image or None, debug_info dict)
    """
    last_debug_info = {}
    
    for attempt in range(max_retries):
        print(f"  Generation attempt {attempt + 1}/{max_retries}...")
        
        result, debug_info = generate_rebranded_image(
            mapping=mapping,
            inspiration=inspiration,
            source=source,
            inspiration_crops=inspiration_crops,
            source_crops=source_crops,
            output_path=output_path,
            config=config
        )
        
        last_debug_info = debug_info
        last_debug_info["attempt"] = attempt + 1
        
        if result:
            return result, last_debug_info
        
        # If failed, maybe try with fewer crops
        if attempt < max_retries - 1:
            print(f"  Retrying with adjusted parameters...")
    
    return None, last_debug_info
