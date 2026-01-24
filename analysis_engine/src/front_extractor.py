"""Front extraction module for isolating product packaging front faces.

This module analyzes product images from e-commerce sites and extracts the
front-facing view of the packaging using Gemini Vision for detection and
PIL for lossless cropping.

Key features:
- Detects front-facing product packaging in various image types
- Handles angled shots, multiple products, lifestyle images
- Performs LOSSLESS cropping - no pixel modification
- Falls back to original image on failure

Uses: Gemini 3 Pro Image Preview for vision analysis
"""
import json
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from google import genai
from google.genai import types
from PIL import Image

from .config import get_config, DiscoveryConfig
from .models import FrontExtractionResult, FrontExtractionBoundingBox
from .utils import load_prompt, invoke_with_retry


# =============================================================================
# Constants
# =============================================================================

# Supported image formats for extraction
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# Minimum confidence threshold for extraction
MIN_CONFIDENCE_THRESHOLD = 0.5

# Minimum crop size (percentage of original) to prevent over-cropping
MIN_CROP_PERCENTAGE = 0.15


# =============================================================================
# FrontExtractor Class
# =============================================================================

class FrontExtractor:
    """Extracts front-facing product packaging from e-commerce images.
    
    Uses Gemini Vision to detect bounding box coordinates for the front face,
    then uses PIL to perform lossless cropping. No pixel modification occurs -
    the extraction is a pure crop operation preserving all original image data.
    """
    
    def __init__(self, config: Optional[DiscoveryConfig] = None):
        """Initialize the front extractor.
        
        Args:
            config: Optional configuration. Uses global config if not provided.
        """
        self.config = config or get_config()
        
        # Use the Gemini Vision model for front extraction
        self.model = self.config.front_extraction.model
        
        # Initialize Google GenAI client
        self.client = genai.Client(api_key=self.config.front_extraction.api_key)
        
        # Load prompts
        self.system_prompt = load_prompt("front_extraction_system.txt")
        self.user_prompt_template = load_prompt("front_extraction_user.txt")
        
        print(f"[FrontExtractor] Initialized with {self.model}")
    
    def _convert_coordinates(
        self,
        bbox: FrontExtractionBoundingBox,
        image_width: int,
        image_height: int
    ) -> Tuple[int, int, int, int]:
        """Convert normalized 0-1000 coordinates to actual pixel coordinates.
        
        Args:
            bbox: Bounding box with normalized coordinates
            image_width: Actual image width in pixels
            image_height: Actual image height in pixels
            
        Returns:
            Tuple of (x1, y1, x2, y2) in pixel coordinates for PIL cropping
        """
        # Convert from 0-1000 scale to actual pixels
        # Note: Gemini returns [ymin, xmin, ymax, xmax]
        # PIL expects (left, upper, right, lower) = (x1, y1, x2, y2)
        x1 = int(bbox.xmin / 1000 * image_width)
        y1 = int(bbox.ymin / 1000 * image_height)
        x2 = int(bbox.xmax / 1000 * image_width)
        y2 = int(bbox.ymax / 1000 * image_height)
        
        # Ensure coordinates are within bounds
        x1 = max(0, min(x1, image_width))
        y1 = max(0, min(y1, image_height))
        x2 = max(0, min(x2, image_width))
        y2 = max(0, min(y2, image_height))
        
        # Ensure x2 > x1 and y2 > y1
        if x2 <= x1:
            x2 = x1 + 1
        if y2 <= y1:
            y2 = y1 + 1
        
        return (x1, y1, x2, y2)
    
    def _validate_crop_area(
        self,
        crop_box: Tuple[int, int, int, int],
        image_width: int,
        image_height: int
    ) -> bool:
        """Validate that the crop area is reasonable.
        
        Args:
            crop_box: (x1, y1, x2, y2) pixel coordinates
            image_width: Original image width
            image_height: Original image height
            
        Returns:
            True if crop area is valid and reasonable
        """
        x1, y1, x2, y2 = crop_box
        
        crop_width = x2 - x1
        crop_height = y2 - y1
        
        # Check minimum size
        original_area = image_width * image_height
        crop_area = crop_width * crop_height
        
        if crop_area < original_area * MIN_CROP_PERCENTAGE:
            return False
        
        # Check aspect ratio isn't too extreme (max 5:1 ratio)
        aspect_ratio = max(crop_width, crop_height) / max(min(crop_width, crop_height), 1)
        if aspect_ratio > 5:
            return False
        
        return True
    
    def analyze_image(
        self,
        image_path: Path,
        brand: str = "Unknown",
        product_name: str = "Unknown Product",
        category: str = ""
    ) -> Optional[FrontExtractionResult]:
        """Analyze an image to detect front-facing packaging bounds.
        
        Args:
            image_path: Path to the image file
            brand: Brand name for context
            product_name: Product name for context
            category: Product category for context
            
        Returns:
            FrontExtractionResult with bounding box, or None if analysis failed
        """
        if not image_path.exists():
            print(f"    [!] Image not found: {image_path}")
            return None
        
        if image_path.suffix.lower() not in SUPPORTED_FORMATS:
            print(f"    [!] Unsupported format: {image_path.suffix}")
            return None
        
        # Load image
        try:
            image = Image.open(image_path)
        except Exception as e:
            print(f"    [!] Failed to open image: {e}")
            return None
        
        # Build user prompt
        user_prompt = self.user_prompt_template.format(
            brand=brand,
            product_name=product_name,
            category=category
        )
        
        # Combine system and user prompts
        full_prompt = f"{self.system_prompt}\n\n---\n\n{user_prompt}"
        
        try:
            # Configure for JSON response with structured output
            config = types.GenerateContentConfig(
                temperature=self.config.front_extraction.temperature,
                response_mime_type="application/json",
                response_schema=FrontExtractionResult,
            )
            
            # Call Gemini with image and prompt
            response = invoke_with_retry(
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=[image, full_prompt],
                    config=config
                ),
                max_retries=3,
                label=f"Front extraction ({brand})"
            )
            
            # Parse JSON response
            if not response.text:
                print(f"    [!] Empty response from model")
                return None
            
            result_data = json.loads(response.text)
            
            # Build Pydantic model from response
            bbox = None
            if result_data.get('bounding_box'):
                bbox_data = result_data['bounding_box']
                bbox = FrontExtractionBoundingBox(
                    ymin=bbox_data.get('ymin', 0),
                    xmin=bbox_data.get('xmin', 0),
                    ymax=bbox_data.get('ymax', 1000),
                    xmax=bbox_data.get('xmax', 1000)
                )
            
            return FrontExtractionResult(
                can_extract=result_data.get('can_extract', False),
                bounding_box=bbox,
                confidence=result_data.get('confidence', 0.0),
                image_type=result_data.get('image_type', 'other'),
                reasoning=result_data.get('reasoning', ''),
                extraction_notes=result_data.get('extraction_notes')
            )
            
        except json.JSONDecodeError as e:
            print(f"    [!] JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"    [!] Analysis error: {e}")
            return None
    
    def extract_front(
        self,
        image_path: Path,
        brand: str = "Unknown",
        product_name: str = "Unknown Product",
        category: str = "",
        output_path: Optional[Path] = None
    ) -> Tuple[bool, Path, Optional[Dict[str, Any]]]:
        """Extract front-facing view from an image.
        
        This is the main entry point for front extraction. It:
        1. Analyzes the image with Gemini to detect front face bounds
        2. Crops the image using PIL (lossless operation)
        3. Saves the cropped image (or keeps original on failure)
        
        Args:
            image_path: Path to the original image
            brand: Brand name for context
            product_name: Product name for context
            category: Product category for context
            output_path: Optional custom output path. If None, overwrites original.
            
        Returns:
            Tuple of (success, final_image_path, extraction_metadata)
            - success: True if extraction was performed
            - final_image_path: Path to the result (cropped or original)
            - extraction_metadata: Dict with extraction details (or None)
        """
        if output_path is None:
            output_path = image_path
        
        # Analyze the image
        result = self.analyze_image(
            image_path=image_path,
            brand=brand,
            product_name=product_name,
            category=category
        )
        
        # If analysis failed, keep original
        if result is None:
            print(f"    [i] Analysis failed, keeping original image")
            return False, image_path, None
        
        # Build metadata
        metadata = {
            'can_extract': result.can_extract,
            'confidence': result.confidence,
            'image_type': result.image_type,
            'reasoning': result.reasoning,
            'extraction_notes': result.extraction_notes,
            'extracted': False,
        }
        
        # Check if extraction is possible and confident enough
        if not result.can_extract:
            print(f"    [i] Cannot extract front: {result.reasoning[:60]}...")
            return False, image_path, metadata
        
        if result.confidence < MIN_CONFIDENCE_THRESHOLD:
            print(f"    [i] Confidence too low ({result.confidence:.2f}), keeping original")
            return False, image_path, metadata
        
        if result.bounding_box is None:
            print(f"    [i] No bounding box provided, keeping original")
            return False, image_path, metadata
        
        # Open image for cropping
        try:
            image = Image.open(image_path)
            width, height = image.size
        except Exception as e:
            print(f"    [!] Failed to open image for cropping: {e}")
            return False, image_path, metadata
        
        # Convert coordinates
        crop_box = self._convert_coordinates(
            result.bounding_box,
            width,
            height
        )
        
        # Validate crop area
        if not self._validate_crop_area(crop_box, width, height):
            print(f"    [i] Invalid crop area, keeping original")
            metadata['extraction_notes'] = (metadata.get('extraction_notes') or '') + ' Crop area validation failed.'
            return False, image_path, metadata
        
        # Check if crop is significantly different from original
        x1, y1, x2, y2 = crop_box
        crop_width = x2 - x1
        crop_height = y2 - y1
        
        # If crop is nearly the full image (>95%), skip cropping
        if (crop_width >= width * 0.95) and (crop_height >= height * 0.95):
            print(f"    [i] Image already front-facing, no crop needed")
            metadata['extraction_notes'] = (metadata.get('extraction_notes') or '') + ' Already optimal framing.'
            metadata['extracted'] = False
            return True, image_path, metadata
        
        # Perform the crop
        try:
            cropped_image = image.crop(crop_box)
            
            # Determine output format (preserve original)
            output_format = image.format or 'PNG'
            
            # Save cropped image
            if output_path == image_path:
                # Create temp file, then replace
                temp_path = image_path.with_suffix('.tmp' + image_path.suffix)
                cropped_image.save(temp_path, format=output_format, quality=95)
                
                # Close original image before replacing
                image.close()
                
                # Replace original with cropped
                temp_path.replace(image_path)
                final_path = image_path
            else:
                cropped_image.save(output_path, format=output_format, quality=95)
                final_path = output_path
            
            metadata['extracted'] = True
            metadata['original_size'] = (width, height)
            metadata['cropped_size'] = (crop_width, crop_height)
            metadata['crop_box'] = crop_box
            
            print(f"    [✓] Front extracted: {width}x{height} → {crop_width}x{crop_height}")
            
            return True, final_path, metadata
            
        except Exception as e:
            print(f"    [!] Crop failed: {e}")
            return False, image_path, metadata
    
    def process_images_directory(
        self,
        images_dir: Path,
        products_data: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Process all images in a directory for front extraction.
        
        Args:
            images_dir: Directory containing product images
            products_data: Optional mapping of image filename to product data
            
        Returns:
            Dict mapping image filename to extraction results
        """
        if not images_dir.exists():
            print(f"[!] Directory not found: {images_dir}")
            return {}
        
        # Find all images
        images = []
        for ext in SUPPORTED_FORMATS:
            images.extend(images_dir.glob(f"*{ext}"))
        
        if not images:
            print(f"[!] No images found in {images_dir}")
            return {}
        
        images.sort(key=lambda p: p.name)
        products_data = products_data or {}
        
        print(f"\n[FrontExtractor] Processing {len(images)} images")
        print(f"  Directory: {images_dir}")
        print(f"  Model: {self.model}")
        print("-" * 70)
        
        results = {}
        success_count = 0
        
        for i, image_path in enumerate(images, 1):
            # Get product context
            product = products_data.get(image_path.name, {})
            brand = product.get('brand', 'Unknown')
            product_name = product.get('full_name', 'Unknown Product')
            category = product.get('category', '')
            
            print(f"[{i:2}/{len(images)}] {brand} - {product_name[:40]}")
            print(f"    Image: {image_path.name}")
            
            # Extract front
            success, final_path, metadata = self.extract_front(
                image_path=image_path,
                brand=brand,
                product_name=product_name,
                category=category
            )
            
            results[image_path.name] = {
                'success': success,
                'final_path': str(final_path),
                'metadata': metadata
            }
            
            if success and metadata and metadata.get('extracted'):
                success_count += 1
        
        print("-" * 70)
        print(f"[FrontExtractor] Complete: {success_count}/{len(images)} images extracted")
        
        return results


# =============================================================================
# Convenience Functions
# =============================================================================

def extract_front_from_image(
    image_path: Path,
    brand: str = "Unknown",
    product_name: str = "Unknown Product",
    category: str = "",
    output_path: Optional[Path] = None
) -> Tuple[bool, Path, Optional[Dict[str, Any]]]:
    """Convenience function to extract front from a single image.
    
    Args:
        image_path: Path to the image
        brand: Brand name for context
        product_name: Product name for context  
        category: Product category for context
        output_path: Optional custom output path
        
    Returns:
        Tuple of (success, final_path, metadata)
    """
    extractor = FrontExtractor()
    return extractor.extract_front(
        image_path=image_path,
        brand=brand,
        product_name=product_name,
        category=category,
        output_path=output_path
    )
