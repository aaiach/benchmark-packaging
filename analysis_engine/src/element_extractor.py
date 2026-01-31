"""Element extraction module for rebrand pipeline Steps 1 & 2.

Uses a UNIFIED approach: one LLM call that returns both element identification
AND bounding box coordinates together. This eliminates ID mismatch issues
between separate identification and location steps.

Follows Gemini cookbook best practices:
- Simple JSON array output: [{"box_2d": [y,x,y,x], "label": "...", ...}]
- Coordinates normalized to 0-1000 scale
- box_2d format: [ymin, xmin, ymax, xmax]
"""
import json
import re
import traceback
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from google import genai
from google.genai import types
from PIL import Image

from .config import get_config, DiscoveryConfig
from .models import (
    ExtractedElement,
    ElementBoundingBox,
    InspirationExtraction,
    SourceExtraction,
    CompositionDescription,
    ColorInfo,
)
from .utils import invoke_with_retry


# =============================================================================
# Constants
# =============================================================================

SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MIN_CROP_SIZE = 10  # Minimum crop dimension in pixels


# =============================================================================
# Unified Extraction Prompt (identification + location in ONE call)
# =============================================================================

UNIFIED_EXTRACTION_PROMPT = """Analyze this packaging image and detect ALL visual elements with their bounding boxes.

For EACH element, return:
- box_2d: bounding box as [ymin, xmin, ymax, xmax] normalized to 0-1000 scale
- id: unique identifier (e.g., "logo_1", "text_main", "trust_mark_bio")
- type: one of "logo", "text", "trust_mark", "product_image", "illustration", "icon", "badge", "background", "decorative"
- label: brief description of what the element looks like
- content: actual text content if readable (empty string if not text)
- importance: "high", "medium", or "low"

Return a JSON object:
{{
  "elements": [
    {{"box_2d": [ymin, xmin, ymax, xmax], "id": "...", "type": "...", "label": "...", "content": "...", "importance": "..."}}
  ],
  "dominant_colors": ["#hex1", "#hex2", "#hex3"],
  "style": "modern|vintage|minimalist|bold|organic|etc"
}}

IMPORTANT RULES:
- box_2d coordinates MUST be integers between 0 and 1000
- box_2d order is [ymin, xmin, ymax, xmax] (top, left, bottom, right)
- 0,0 is top-left corner, 1000,1000 is bottom-right corner
- Each element MUST have a UNIQUE bounding box - do NOT repeat the same box
- Detect ALL distinct elements: logos, text blocks, images, icons, badges, trust marks, backgrounds

Be thorough - identify every distinct visual element."""


SOURCE_EXTRACTION_PROMPT = """Analyze this product packaging and detect ALL brand elements with their bounding boxes.

BRAND CONTEXT:
{brand_identity}

Focus on elements that define this brand:
- Brand logo (highest priority - must detect accurately)
- Brand name text
- Product name and descriptions
- Trust marks, certifications, badges
- Product images or illustrations
- Brand-specific icons or patterns

For EACH element, return:
- box_2d: bounding box as [ymin, xmin, ymax, xmax] normalized to 0-1000 scale
- id: unique identifier (e.g., "brand_logo", "product_name", "cert_bio")
- type: one of "logo", "text", "trust_mark", "product_image", "illustration", "icon", "badge", "decorative"
- label: brief description
- content: actual text content if readable
- importance: "high", "medium", or "low"

Return a JSON object:
{{
  "brand_name": "detected brand name",
  "product_name": "detected product name",
  "elements": [
    {{"box_2d": [ymin, xmin, ymax, xmax], "id": "...", "type": "...", "label": "...", "content": "...", "importance": "..."}}
  ],
  "brand_colors": ["#hex1", "#hex2"],
  "claims": ["claim1", "claim2"]
}}

IMPORTANT RULES:
- box_2d coordinates MUST be integers between 0 and 1000
- box_2d order is [ymin, xmin, ymax, xmax] (top, left, bottom, right)
- Each element MUST have a UNIQUE bounding box - do NOT repeat the same coordinates
- Focus on brand-defining elements that should be preserved in rebranding"""


# =============================================================================
# Response Parsing Utilities
# =============================================================================

def clean_json_response(text: str) -> str:
    """Remove markdown code fences and clean up JSON response."""
    if not text:
        return ""
    
    text = text.strip()
    
    # Remove markdown code blocks
    if "```json" in text:
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
    if "```" in text:
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    return text


def parse_unified_response(response_text: str) -> Tuple[List[Dict], Dict]:
    """Parse the unified extraction response.
    
    Returns:
        Tuple of (elements_with_bbox, metadata_dict)
    """
    text = clean_json_response(response_text)
    
    print(f"    [DEBUG] Response length: {len(text)}")
    print(f"    [DEBUG] First 500 chars: {text[:500]}")
    
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"    [!] JSON parse error at position {e.pos}: {e.msg}")
        print(f"    [!] Context: ...{text[max(0,e.pos-50):e.pos+50]}...")
        return [], {}
    
    # Extract elements and metadata
    elements = []
    metadata = {}
    
    if isinstance(data, dict):
        elements = data.get('elements', [])
        # Copy metadata fields
        for key in ['dominant_colors', 'brand_colors', 'style', 'brand_name', 'product_name', 'claims']:
            if key in data:
                metadata[key] = data[key]
    elif isinstance(data, list):
        elements = data
    
    # Validate and clean elements
    valid_elements = []
    seen_boxes = set()  # Track duplicate bounding boxes
    
    for i, elem in enumerate(elements):
        if not isinstance(elem, dict):
            print(f"    [!] Skipping non-dict element at index {i}: {type(elem)}")
            continue
        
        # Must have box_2d
        box_2d = elem.get('box_2d', elem.get('bounding_box', elem.get('bbox')))
        
        if not box_2d or not isinstance(box_2d, list) or len(box_2d) < 4:
            print(f"    [!] Element {i} missing valid box_2d, skipping")
            continue
        
        # Parse and validate coordinates
        try:
            ymin = max(0, min(1000, int(float(box_2d[0]))))
            xmin = max(0, min(1000, int(float(box_2d[1]))))
            ymax = max(0, min(1000, int(float(box_2d[2]))))
            xmax = max(0, min(1000, int(float(box_2d[3]))))
            
            # Ensure valid box
            if xmax <= xmin:
                xmax = min(xmin + 50, 1000)
            if ymax <= ymin:
                ymax = min(ymin + 50, 1000)
            
            # Check for duplicates (same or nearly same box)
            box_key = (xmin // 20, ymin // 20, xmax // 20, ymax // 20)  # Quantize to detect near-duplicates
            
            # Check if this is essentially the full image (0,0,1000,1000 or close)
            is_full_image = (xmin < 50 and ymin < 50 and xmax > 950 and ymax > 950)
            
            if box_key in seen_boxes:
                print(f"    [!] Duplicate bbox for element {i}, skipping")
                continue
            
            if is_full_image and len(valid_elements) > 0:
                # Only allow one full-image element (background)
                has_full_bg = any(e.get('_is_full', False) for e in valid_elements)
                if has_full_bg:
                    print(f"    [!] Multiple full-image elements detected, skipping duplicate")
                    continue
            
            seen_boxes.add(box_key)
            
            # Build clean element
            clean_elem = {
                'box_2d': [ymin, xmin, ymax, xmax],
                'xmin': xmin,
                'ymin': ymin,
                'xmax': xmax,
                'ymax': ymax,
                'id': elem.get('id', elem.get('element_id', f'elem_{i}')),
                'type': elem.get('type', elem.get('element_type', 'decorative')),
                'label': elem.get('label', elem.get('description', '')),
                'content': elem.get('content', ''),
                'importance': elem.get('importance', 'medium'),
                '_is_full': is_full_image
            }
            
            valid_elements.append(clean_elem)
            
        except (ValueError, TypeError) as e:
            print(f"    [!] Failed to parse coordinates for element {i}: {e}")
            continue
    
    print(f"    [DEBUG] Parsed {len(valid_elements)} valid elements (filtered from {len(elements)})")
    return valid_elements, metadata


# =============================================================================
# Cropping Utilities
# =============================================================================

def convert_bbox_to_pixels(
    xmin: int, ymin: int, xmax: int, ymax: int,
    image_width: int, image_height: int
) -> Tuple[int, int, int, int]:
    """Convert normalized 0-1000 coordinates to pixel coordinates."""
    x1 = int(xmin / 1000 * image_width)
    y1 = int(ymin / 1000 * image_height)
    x2 = int(xmax / 1000 * image_width)
    y2 = int(ymax / 1000 * image_height)
    
    # Ensure within bounds
    x1 = max(0, min(x1, image_width - 1))
    y1 = max(0, min(y1, image_height - 1))
    x2 = max(x1 + 1, min(x2, image_width))
    y2 = max(y1 + 1, min(y2, image_height))
    
    return (x1, y1, x2, y2)


def crop_element(
    image: Image.Image,
    xmin: int, ymin: int, xmax: int, ymax: int,
    output_path: Path
) -> Optional[Path]:
    """Crop a single element from an image using normalized coordinates."""
    try:
        width, height = image.size
        x1, y1, x2, y2 = convert_bbox_to_pixels(xmin, ymin, xmax, ymax, width, height)
        
        crop_width = x2 - x1
        crop_height = y2 - y1
        
        if crop_width < MIN_CROP_SIZE or crop_height < MIN_CROP_SIZE:
            print(f"      [!] Crop too small: {crop_width}x{crop_height}")
            return None
        
        cropped = image.crop((x1, y1, x2, y2))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(output_path, format='PNG', quality=95)
        
        return output_path
        
    except Exception as e:
        print(f"      [!] Crop failed: {e}")
        return None


# =============================================================================
# Unified Extraction Core Function
# =============================================================================

def call_gemini(
    client: genai.Client,
    model: str,
    image: Image.Image,
    prompt: str,
    label: str
) -> Optional[str]:
    """Make a Gemini API call with retry and logging."""
    print(f"    [LLM] Calling Gemini for: {label}")
    
    try:
        gen_config = types.GenerateContentConfig(
            temperature=0.2,  # Low temperature for consistent output
            response_mime_type="application/json",
        )
        
        response = invoke_with_retry(
            lambda: client.models.generate_content(
                model=model,
                contents=[image, prompt],
                config=gen_config
            ),
            max_retries=3,
            label=label
        )
        
        if not response.text:
            print(f"    [!] Empty response for {label}")
            return None
        
        print(f"    [✓] Got response for {label} ({len(response.text)} chars)")
        return response.text
        
    except Exception as e:
        print(f"    [!] API error for {label}: {e}")
        traceback.print_exc()
        return None


def extract_elements_unified(
    client: genai.Client,
    model: str,
    image: Image.Image,
    prompt: str,
    label: str
) -> Tuple[List[Dict], Dict]:
    """
    Unified extraction: Get both element identification AND bounding boxes in one call.
    
    Returns:
        Tuple of (elements_with_coordinates, metadata_dict)
    """
    print(f"  [Unified Extraction] {label}...")
    
    response = call_gemini(client, model, image, prompt, label)
    
    if not response:
        return [], {}
    
    elements, metadata = parse_unified_response(response)
    print(f"  [✓] Extracted {len(elements)} elements with bounding boxes")
    
    return elements, metadata


def build_extracted_elements(elements: List[Dict]) -> List[ExtractedElement]:
    """Build ExtractedElement objects from parsed elements (already have coordinates)."""
    result = []
    
    for elem in elements:
        # Coordinates already parsed
        xmin = elem.get('xmin', 0)
        ymin = elem.get('ymin', 0)
        xmax = elem.get('xmax', 1000)
        ymax = elem.get('ymax', 1000)
        
        # Determine element type
        elem_type = elem.get('type', 'decorative')
        valid_types = {'logo', 'text', 'trust_mark', 'product_image', 'illustration', 
                       'icon', 'badge', 'background', 'decorative'}
        if elem_type not in valid_types:
            elem_type = 'decorative'
        
        # Infer position from bbox center
        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2
        h_pos = 'left' if cx < 333 else ('right' if cx > 666 else 'center')
        v_pos = 'top' if cy < 333 else ('bottom' if cy > 666 else 'center')
        position = 'center' if (v_pos == 'center' and h_pos == 'center') else f"{v_pos}-{h_pos}"
        
        # Calculate size percentage
        width = xmax - xmin
        height = ymax - ymin
        size_pct = (width * height) / 10000  # as percentage of 1000x1000
        
        # Map importance to hierarchy
        importance = elem.get('importance', 'medium')
        hierarchy = 1 if importance == 'high' else (2 if importance == 'medium' else 3)
        
        extracted = ExtractedElement(
            element_id=elem.get('id', ''),
            element_type=elem_type,
            content=elem.get('content', '') or elem.get('label', ''),
            position=position,
            bounding_box=ElementBoundingBox(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax),
            visual_description=elem.get('label', ''),
            size_percentage=float(size_pct),
            hierarchy_level=hierarchy
        )
        result.append(extracted)
    
    return result


def crop_all_elements(
    image: Image.Image,
    elements: List[ExtractedElement],
    output_dir: Path,
    prefix: str
) -> Dict[str, Path]:
    """Crop all elements and save to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cropped_paths = {}
    
    for elem in elements:
        output_path = output_dir / f"{prefix}_{elem.element_id}.png"
        
        result = crop_element(
            image,
            elem.bounding_box.xmin,
            elem.bounding_box.ymin,
            elem.bounding_box.xmax,
            elem.bounding_box.ymax,
            output_path
        )
        
        if result:
            cropped_paths[elem.element_id] = result
            print(f"    [✓] Cropped {elem.element_id}: {elem.element_type} ({elem.bounding_box.xmin},{elem.bounding_box.ymin})-({elem.bounding_box.xmax},{elem.bounding_box.ymax})")
        else:
            print(f"    [!] Failed to crop {elem.element_id}")
    
    return cropped_paths


# =============================================================================
# Public API: Step 1 - Inspiration Extraction
# =============================================================================

def extract_inspiration_elements(
    image_path: Path,
    output_dir: Path,
    config: Optional[DiscoveryConfig] = None
) -> Tuple[Optional[InspirationExtraction], Dict[str, Path]]:
    """
    Step 1: Extract all visual elements from inspiration image.
    
    Uses unified extraction (identification + coordinates in one call).
    """
    if config is None:
        config = get_config()
    
    print(f"\n{'='*60}")
    print(f"INSPIRATION EXTRACTION (Unified)")
    print(f"{'='*60}")
    
    if not image_path.exists():
        print(f"[!] Image not found: {image_path}")
        return None, {}
    
    print(f"Image: {image_path.name}")
    
    try:
        image = Image.open(image_path)
        width, height = image.size
        print(f"Dimensions: {width}x{height}")
    except Exception as e:
        print(f"[!] Failed to open image: {e}")
        return None, {}
    
    # Initialize Gemini client
    client = genai.Client(api_key=config.gemini_vision.api_key)
    model = config.gemini_vision.model
    
    try:
        # Unified extraction
        elements_raw, metadata = extract_elements_unified(
            client=client,
            model=model,
            image=image,
            prompt=UNIFIED_EXTRACTION_PROMPT,
            label="inspiration elements"
        )
        
        if not elements_raw:
            print("[!] No elements extracted")
            return None, {}
        
        # Build ExtractedElement objects
        elements = build_extracted_elements(elements_raw)
        print(f"[✓] Built {len(elements)} ExtractedElement objects")
        
        # Build composition
        composition = CompositionDescription(
            layout_type=metadata.get('style', 'detected'),
            visual_flow="top-to-bottom",
            balance="symmetric",
            dominant_zone="center",
            whitespace_zones=[],
            overall_style=metadata.get('style', 'packaging')
        )
        
        # Build color palette
        color_palette = []
        for hex_color in metadata.get('dominant_colors', []):
            if hex_color and isinstance(hex_color, str):
                color_palette.append(ColorInfo(
                    hex_code=hex_color,
                    color_name=hex_color,
                    usage="dominant"
                ))
        
        # Build extraction result
        extraction = InspirationExtraction(
            elements=elements,
            composition=composition,
            color_palette=color_palette,
            total_elements=len(elements),
            image_dimensions={'width': width, 'height': height}
        )
        
        # Crop elements
        print("\nCropping elements...")
        crops_dir = output_dir / "inspiration_crops"
        cropped_paths = crop_all_elements(image, elements, crops_dir, "insp")
        print(f"[✓] Cropped {len(cropped_paths)}/{len(elements)} elements")
        
        return extraction, cropped_paths
        
    except Exception as e:
        print(f"[!] Extraction failed: {e}")
        traceback.print_exc()
        return None, {}


# =============================================================================
# Public API: Step 2 - Source Extraction
# =============================================================================

def extract_source_elements(
    image_path: Path,
    brand_identity: str,
    output_dir: Path,
    config: Optional[DiscoveryConfig] = None
) -> Tuple[Optional[SourceExtraction], Dict[str, Path]]:
    """
    Step 2: Extract elements from source image using brand identity.
    
    Uses unified extraction (identification + coordinates in one call).
    """
    if config is None:
        config = get_config()
    
    print(f"\n{'='*60}")
    print(f"SOURCE EXTRACTION (Unified)")
    print(f"{'='*60}")
    
    if not image_path.exists():
        print(f"[!] Image not found: {image_path}")
        return None, {}
    
    print(f"Image: {image_path.name}")
    print(f"Brand Identity: {brand_identity[:100]}...")
    
    try:
        image = Image.open(image_path)
        width, height = image.size
        print(f"Dimensions: {width}x{height}")
    except Exception as e:
        print(f"[!] Failed to open image: {e}")
        return None, {}
    
    # Initialize Gemini client
    client = genai.Client(api_key=config.gemini_vision.api_key)
    model = config.gemini_vision.model
    
    # Format prompt with brand identity
    prompt = SOURCE_EXTRACTION_PROMPT.format(brand_identity=brand_identity)
    
    try:
        # Unified extraction
        elements_raw, metadata = extract_elements_unified(
            client=client,
            model=model,
            image=image,
            prompt=prompt,
            label="source elements"
        )
        
        if not elements_raw:
            print("[!] No elements extracted")
            return None, {}
        
        # Build ExtractedElement objects
        elements = build_extracted_elements(elements_raw)
        print(f"[✓] Built {len(elements)} ExtractedElement objects")
        
        # Extract brand info from metadata
        brand_name = metadata.get('brand_name', 'Unknown')
        product_name = metadata.get('product_name', 'Unknown Product')
        claims = metadata.get('claims', [])
        
        # Build color palette
        color_palette = []
        for hex_color in metadata.get('brand_colors', []):
            if hex_color and isinstance(hex_color, str):
                color_palette.append(ColorInfo(
                    hex_code=hex_color,
                    color_name=hex_color,
                    usage="brand"
                ))
        
        print(f"Brand: {brand_name}")
        print(f"Product: {product_name}")
        print(f"Claims: {len(claims)}")
        
        # Build extraction result
        extraction = SourceExtraction(
            elements=elements,
            brand_name=brand_name,
            product_name=product_name,
            available_claims=claims if isinstance(claims, list) else [],
            color_palette=color_palette,
            total_elements=len(elements)
        )
        
        # Crop elements
        print("\nCropping elements...")
        crops_dir = output_dir / "source_crops"
        cropped_paths = crop_all_elements(image, elements, crops_dir, "src")
        print(f"[✓] Cropped {len(cropped_paths)}/{len(elements)} elements")
        
        return extraction, cropped_paths
        
    except Exception as e:
        print(f"[!] Extraction failed: {e}")
        traceback.print_exc()
        return None, {}
