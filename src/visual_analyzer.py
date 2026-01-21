"""Visual analysis module using Gemini Vision for eye-tracking and hierarchy analysis.

This module analyzes product images using Gemini 3 Pro to understand:
- Visual hierarchy and element ranking
- Eye-tracking simulation (Z, F, circular patterns)
- Massing and balance of visual elements
- Design effectiveness
- Heatmap generation for visual attention

Uses the Google GenAI Python SDK with structured output for reliable parsing.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from google import genai
from google.genai import types
from PIL import Image

from .config import get_config, DiscoveryConfig
from .models import VisualHierarchyAnalysis, VisualElement, EyeTrackingPattern, MassingAnalysis
from .utils import load_prompt


# =============================================================================
# Constants
# =============================================================================

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# MIME type mapping
MIME_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_mime_type(filepath: Path) -> str:
    """Get MIME type from file extension."""
    ext = filepath.suffix.lower()
    return MIME_TYPES.get(ext, 'image/jpeg')


def find_images_for_run(output_dir: Path, run_id: str) -> Tuple[Optional[Path], List[Path]]:
    """Find all images for a given run.
    
    Args:
        output_dir: Base output directory
        run_id: Run identifier (timestamp)
        
    Returns:
        Tuple of (images_directory, list_of_image_paths)
    """
    images_base = output_dir / "images"
    
    # Find the images directory for this run
    pattern = f"*_{run_id}"
    matches = list(images_base.glob(pattern))
    
    if not matches:
        return None, []
    
    images_dir = matches[0]
    
    # Find all images in the directory
    images = []
    for ext in SUPPORTED_FORMATS:
        images.extend(images_dir.glob(f"*{ext}"))
    
    # Sort by filename (which includes index)
    images.sort(key=lambda p: p.name)
    
    return images_dir, images


def load_product_data_for_run(output_dir: Path, run_id: str) -> Dict[str, Dict[str, Any]]:
    """Load product data from the with_images JSON file.
    
    Returns a dict mapping local_image_path to product data.
    """
    # Find the with_images JSON file
    pattern = f"*_with_images_{run_id}.json"
    matches = list(output_dir.glob(pattern))
    
    if not matches:
        return {}
    
    with open(matches[0], 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    # Create mapping from image path to product
    mapping = {}
    for product in products:
        local_path = product.get('local_image_path')
        if local_path:
            # Normalize path for matching
            mapping[local_path] = product
            # Also store by filename only
            mapping[Path(local_path).name] = product
    
    return mapping


# =============================================================================
# Main VisualAnalyzer Class
# =============================================================================

class VisualAnalyzer:
    """Analyzes product images for visual hierarchy using Gemini Vision.
    
    Uses Gemini 2.5 Pro to perform:
    - Eye-tracking simulation
    - Visual element ranking
    - Massing and balance analysis
    - Design effectiveness scoring
    """
    
    def __init__(self, config: Optional[DiscoveryConfig] = None):
        """Initialize the visual analyzer.
        
        Args:
            config: Optional configuration. Uses global config if not provided.
        """
        self.config = config or get_config()
        
        # Initialize Google GenAI client
        self.client = genai.Client(api_key=self.config.gemini_vision.api_key)
        self.model = self.config.gemini_vision.model
        
        # Load prompts
        self.system_prompt = load_prompt("visual_analysis_system.txt")
        self.user_prompt_template = load_prompt("visual_analysis_user.txt")
        
        print(f"[VisualAnalyzer] Initialized with {self.model}")
    
    def analyze_image(
        self,
        image_path: Path,
        brand: str = "Unknown",
        product_name: str = "Unknown Product",
        category: str = ""
    ) -> Optional[VisualHierarchyAnalysis]:
        """Analyze a single image for visual hierarchy.
        
        Args:
            image_path: Path to the local image file
            brand: Brand name for context
            product_name: Product name for context
            category: Product category for context
            
        Returns:
            VisualHierarchyAnalysis result or None if failed
        """
        if not image_path.exists():
            print(f"    [!] Image not found: {image_path}")
            return None
        
        # Check file extension
        if image_path.suffix.lower() not in SUPPORTED_FORMATS:
            print(f"    [!] Unsupported format: {image_path.suffix}")
            return None
        
        # Read image bytes
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        mime_type = get_mime_type(image_path)
        
        # Build user prompt
        user_prompt = self.user_prompt_template.format(
            brand=brand,
            product_name=product_name,
            category=category
        )
        
        # Combine system and user prompts
        full_prompt = f"{self.system_prompt}\n\n---\n\n{user_prompt}"
        
        try:
            # Call Gemini with structured output
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    full_prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
                config=types.GenerateContentConfig(
                    temperature=self.config.gemini_vision.temperature,
                    response_mime_type='application/json',
                    response_schema=VisualHierarchyAnalysis,
                ),
            )
            
            # Parse the response
            if response.parsed:
                return response.parsed
            
            # Fallback: try to parse from text
            if response.text:
                data = json.loads(response.text)
                return VisualHierarchyAnalysis(**data)
            
            print("    [!] Empty response from model")
            return None
            
        except Exception as e:
            print(f"    [!] Analysis error: {e}")
            return None
    
    def analyze_run(
        self,
        run_id: str,
        max_images: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Analyze all images from a previous run.
        
        Args:
            run_id: Run identifier (timestamp)
            max_images: Optional limit on number of images to process
            
        Returns:
            List of analysis results (dict with image info + analysis)
        """
        output_dir = Path(self.config.output_dir)
        
        # Find images
        images_dir, images = find_images_for_run(output_dir, run_id)
        
        if not images:
            print(f"[!] No images found for run_id: {run_id}")
            return []
        
        # Load product data for context
        product_data = load_product_data_for_run(output_dir, run_id)
        
        # Limit images if requested
        if max_images:
            images = images[:max_images]
        
        print(f"\n[VisualAnalyzer] Analyzing {len(images)} images")
        print(f"  Images directory: {images_dir}")
        print(f"  Model: {self.model}")
        print("-" * 70)
        
        results = []
        success_count = 0
        
        for i, image_path in enumerate(images, 1):
            # Get product context
            product = product_data.get(str(image_path)) or product_data.get(image_path.name, {})
            brand = product.get('brand', 'Unknown')
            product_name = product.get('full_name', 'Unknown Product')
            category = product.get('category', '')
            
            print(f"[{i:2}/{len(images)}] {brand} - {product_name[:40]}")
            print(f"    Image: {image_path.name}")
            
            # Analyze the image
            analysis = self.analyze_image(
                image_path=image_path,
                brand=brand,
                product_name=product_name,
                category=category
            )
            
            # Build result entry
            result = {
                'image_path': str(image_path),
                'image_filename': image_path.name,
                'brand': brand,
                'product_name': product_name,
                'category': category,
                'analysis': None,
                'analysis_success': False,
            }
            
            if analysis:
                result['analysis'] = analysis.model_dump()
                result['analysis_success'] = True
                success_count += 1
                
                # Print summary
                print(f"    [✓] Anchor: {analysis.visual_anchor[:50]}...")
                print(f"    [✓] Elements: {len(analysis.elements)}, Pattern: {analysis.eye_tracking.pattern_type}")
                print(f"    [✓] Hierarchy clarity: {analysis.hierarchy_clarity_score}/10")
            else:
                print(f"    [✗] Analysis failed")
            
            results.append(result)
        
        print("-" * 70)
        print(f"[VisualAnalyzer] Complete: {success_count}/{len(images)} images analyzed")
        
        return results
    
    def run(
        self,
        run_id: str,
        max_images: Optional[int] = None
    ) -> Optional[Path]:
        """Run visual analysis and save results to JSON.
        
        Args:
            run_id: Run identifier (timestamp)
            max_images: Optional limit on number of images
            
        Returns:
            Path to the output JSON file or None if failed
        """
        output_dir = Path(self.config.output_dir)
        
        # Find category slug from existing files
        pattern = f"*_with_images_{run_id}.json"
        matches = list(output_dir.glob(pattern))
        
        if not matches:
            print(f"[!] No with_images file found for run_id: {run_id}")
            return None
        
        # Extract category slug
        filename = matches[0].stem
        category_slug = filename.replace(f"_with_images_{run_id}", "")
        
        print("=" * 70)
        print(f"VISUAL ANALYSIS - Run: {run_id}")
        print(f"  Category: {category_slug.replace('_', ' ')}")
        print(f"  Model: {self.model}")
        print("=" * 70)
        
        # Run analysis
        results = self.analyze_run(run_id, max_images)
        
        if not results:
            return None
        
        # Save results
        analysis_dir = output_dir / self.config.analysis_subdir
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = analysis_dir / f"{category_slug}_visual_analysis_{run_id}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n[✓] Analysis saved: {output_file}")
        
        return output_file
    
    # =========================================================================
    # Heatmap Generation Methods
    # =========================================================================
    
    def _format_elements_hierarchy(self, analysis: Dict[str, Any]) -> str:
        """Format visual elements as a ranked hierarchy text.
        
        Args:
            analysis: Analysis dict containing 'elements' list
            
        Returns:
            Formatted string with elements in hierarchy order
        """
        elements = analysis.get('elements', [])
        if not elements:
            return "Aucun élément identifié"
        
        lines = []
        for i, elem in enumerate(elements, 1):
            weight = elem.get('visual_weight', 0)
            elem_type = elem.get('element_type', 'unknown')
            description = elem.get('description', '')
            position = elem.get('position', '')
            color = elem.get('dominant_color', '')
            size = elem.get('size_percentage', '')
            
            size_str = f", ~{size}% de l'image" if size else ""
            
            lines.append(
                f"{i}. [{weight}/10] {elem_type.upper()} - {description}\n"
                f"   Position: {position} | Couleur: {color}{size_str}"
            )
        
        return "\n".join(lines)
    
    def generate_heatmap(
        self,
        image_path: Path,
        analysis: Dict[str, Any],
        output_path: Path,
        brand: str = "Unknown",
        product_name: str = "Unknown Product"
    ) -> Optional[Path]:
        """Generate a heatmap overlay for a single image.
        
        Args:
            image_path: Path to the original image
            analysis: Visual hierarchy analysis dict
            output_path: Path to save the heatmap image
            brand: Brand name for context
            product_name: Product name for context
            
        Returns:
            Path to the generated heatmap or None if failed
        """
        if not image_path.exists():
            print(f"    [!] Image not found: {image_path}")
            return None
        
        # Load prompts
        system_prompt = load_prompt("heatmap_generation_system.txt")
        user_prompt_template = load_prompt("heatmap_generation_user.txt")
        
        # Extract analysis data
        eye_tracking = analysis.get('eye_tracking', {})
        massing = analysis.get('massing', {})
        
        # Format elements hierarchy
        elements_hierarchy = self._format_elements_hierarchy(analysis)
        
        # Build user prompt with analysis context
        user_prompt = user_prompt_template.format(
            brand=brand,
            product_name=product_name,
            visual_anchor=analysis.get('visual_anchor', 'Non identifié'),
            elements_hierarchy=elements_hierarchy,
            eye_pattern=eye_tracking.get('pattern_type', 'unknown'),
            entry_point=eye_tracking.get('entry_point', 'Non identifié'),
            fixation_sequence=" → ".join(eye_tracking.get('fixation_sequence', [])),
            exit_point=eye_tracking.get('exit_point', 'Non identifié'),
            dwell_zones=", ".join(eye_tracking.get('dwell_zones', [])),
            balance_type=massing.get('balance_type', 'unknown'),
            dense_zones=", ".join(massing.get('dense_zones', [])),
            light_zones=", ".join(massing.get('light_zones', [])),
            center_of_gravity=massing.get('center_of_gravity', 'Non identifié')
        )
        
        # Combine prompts
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
        
        # Load the original image
        original_image = Image.open(image_path)
        
        try:
            # Call Gemini to generate the heatmap overlay
            response = self.client.models.generate_content(
                model=self.model,
                contents=[full_prompt, original_image],
                config=types.GenerateContentConfig(
                    temperature=self.config.gemini_vision.temperature,
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            
            # Check if response has parts
            if not response.parts:
                # Try to get any text explanation for why generation failed
                if hasattr(response, 'text') and response.text:
                    print(f"    [!] No image generated. Response: {response.text[:100]}...")
                else:
                    print("    [!] Empty response from model (possible content policy block)")
                return None
            
            # Extract the generated image from response
            for part in response.parts:
                if part.inline_data is not None:
                    generated_image = part.as_image()
                    
                    # Ensure output directory exists
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Save the heatmap
                    generated_image.save(str(output_path))
                    return output_path
            
            # If we got here, parts existed but no image was found
            print("    [!] Response contained no image data")
            # Print any text that was returned
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    print(f"    [i] Model response: {part.text[:150]}...")
                    break
            return None
            
        except Exception as e:
            print(f"    [!] Heatmap generation error: {e}")
            return None
    
    def generate_heatmaps_for_run(
        self,
        run_id: str,
        max_images: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generate heatmaps for all analyzed images in a run.
        
        Args:
            run_id: Run identifier (timestamp)
            max_images: Optional limit on number of images
            
        Returns:
            List of results with heatmap paths
        """
        output_dir = Path(self.config.output_dir)
        
        # Load the visual analysis results
        analysis_dir = output_dir / self.config.analysis_subdir
        pattern = f"*_visual_analysis_{run_id}.json"
        matches = list(analysis_dir.glob(pattern))
        
        if not matches:
            print(f"[!] No visual analysis found for run_id: {run_id}")
            print("    Run step 5 first to generate visual analysis.")
            return []
        
        analysis_file = matches[0]
        
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analyses = json.load(f)
        
        # Filter to only successful analyses
        analyses = [a for a in analyses if a.get('analysis_success')]
        
        if not analyses:
            print("[!] No successful analyses found to generate heatmaps")
            return []
        
        # Limit if requested
        if max_images:
            analyses = analyses[:max_images]
        
        print(f"\n[VisualAnalyzer] Generating heatmaps for {len(analyses)} images")
        print(f"  Model: {self.model}")
        print("-" * 70)
        
        results = []
        success_count = 0
        
        for i, item in enumerate(analyses, 1):
            image_path = Path(item['image_path'])
            brand = item.get('brand', 'Unknown')
            product_name = item.get('product_name', 'Unknown Product')
            analysis = item.get('analysis', {})
            
            print(f"[{i:2}/{len(analyses)}] {brand} - {product_name[:40]}")
            
            # Determine heatmap output path (same dir as image, in heatmaps subdir)
            heatmaps_dir = image_path.parent / "heatmaps"
            heatmap_filename = image_path.stem + "_heatmap" + image_path.suffix
            heatmap_path = heatmaps_dir / heatmap_filename
            
            print(f"    Generating: {heatmap_filename}")
            
            # Generate heatmap
            result_path = self.generate_heatmap(
                image_path=image_path,
                analysis=analysis,
                output_path=heatmap_path,
                brand=brand,
                product_name=product_name
            )
            
            result = {
                'image_path': str(image_path),
                'brand': brand,
                'product_name': product_name,
                'heatmap_path': str(result_path) if result_path else None,
                'heatmap_success': result_path is not None,
            }
            
            if result_path:
                success_count += 1
                print(f"    [✓] Saved: {result_path}")
            else:
                print(f"    [✗] Generation failed")
            
            results.append(result)
        
        print("-" * 70)
        print(f"[VisualAnalyzer] Complete: {success_count}/{len(analyses)} heatmaps generated")
        
        return results
    
    def run_heatmaps(
        self,
        run_id: str,
        max_images: Optional[int] = None
    ) -> Optional[Path]:
        """Run heatmap generation and update the analysis JSON.
        
        Args:
            run_id: Run identifier (timestamp)
            max_images: Optional limit on number of images
            
        Returns:
            Path to the updated analysis JSON or None if failed
        """
        output_dir = Path(self.config.output_dir)
        
        # Find category slug from analysis file
        analysis_dir = output_dir / self.config.analysis_subdir
        pattern = f"*_visual_analysis_{run_id}.json"
        matches = list(analysis_dir.glob(pattern))
        
        if not matches:
            print(f"[!] No visual analysis found for run_id: {run_id}")
            return None
        
        analysis_file = matches[0]
        category_slug = analysis_file.stem.replace(f"_visual_analysis_{run_id}", "")
        
        print("=" * 70)
        print(f"HEATMAP GENERATION - Run: {run_id}")
        print(f"  Category: {category_slug.replace('_', ' ')}")
        print(f"  Model: {self.model}")
        print("=" * 70)
        
        # Generate heatmaps
        heatmap_results = self.generate_heatmaps_for_run(run_id, max_images)
        
        if not heatmap_results:
            return None
        
        # Update the analysis JSON with heatmap paths
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analyses = json.load(f)
        
        # Create a mapping from image_path to heatmap result
        heatmap_map = {r['image_path']: r for r in heatmap_results}
        
        # Update analyses with heatmap info
        for analysis in analyses:
            img_path = analysis.get('image_path')
            if img_path in heatmap_map:
                hm_result = heatmap_map[img_path]
                analysis['heatmap_path'] = hm_result.get('heatmap_path')
                analysis['heatmap_success'] = hm_result.get('heatmap_success', False)
        
        # Save updated analysis
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analyses, f, indent=2, ensure_ascii=False)
        
        print(f"\n[✓] Analysis updated with heatmap paths: {analysis_file}")
        
        return analysis_file


# =============================================================================
# Convenience Functions
# =============================================================================

def analyze_images(
    run_id: str,
    max_images: Optional[int] = None
) -> Optional[Path]:
    """Convenience function to run visual analysis.
    
    Args:
        run_id: Run identifier (timestamp)
        max_images: Optional limit on images to process
        
    Returns:
        Path to output JSON file or None
    """
    analyzer = VisualAnalyzer()
    return analyzer.run(run_id=run_id, max_images=max_images)


def generate_heatmaps(
    run_id: str,
    max_images: Optional[int] = None
) -> Optional[Path]:
    """Convenience function to generate heatmaps for a run.
    
    Args:
        run_id: Run identifier (timestamp)
        max_images: Optional limit on images to process
        
    Returns:
        Path to updated analysis JSON file or None
    """
    analyzer = VisualAnalyzer()
    return analyzer.run_heatmaps(run_id=run_id, max_images=max_images)


def list_runs_with_images() -> List[Dict[str, str]]:
    """List all runs that have downloaded images."""
    config = get_config()
    output_dir = Path(config.output_dir)
    images_dir = output_dir / config.images_subdir
    
    if not images_dir.exists():
        return []
    
    runs = []
    for d in images_dir.iterdir():
        if d.is_dir():
            # Extract run_id from directory name (format: category_runid)
            match = re.search(r'_(\d{8}_\d{6})$', d.name)
            if match:
                run_id = match.group(1)
                category = d.name.replace(f"_{run_id}", "").replace('_', ' ')
                
                # Count images
                image_count = sum(1 for ext in SUPPORTED_FORMATS for _ in d.glob(f"*{ext}"))
                
                runs.append({
                    'run_id': run_id,
                    'category': category,
                    'images_dir': str(d),
                    'image_count': image_count,
                })
    
    # Sort by run_id (most recent first)
    runs.sort(key=lambda x: x['run_id'], reverse=True)
    return runs
