"""Image selection module using AI to find the best product image.

This module analyzes scraped product data and uses GPT-5 Mini to identify
the highest quality product image from available URLs, then downloads it locally.
"""
import json
import os
import re
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from openai import OpenAI
from pydantic import BaseModel

from .config import get_config, DiscoveryConfig
from .models import ImageSelection, ImageSelectionResult
from .utils import load_prompt


# =============================================================================
# Constants
# =============================================================================

# Image URL patterns to avoid (likely not product images)
SKIP_PATTERNS = [
    r'pixel\.png',
    r'no-picture',
    r'placeholder',
    r'default\.',
    r'logo\.',
    r'icon\.',
    r'favicon',
    r'payment',
    r'visa\.',
    r'mastercard',
    r'paypal',
    r'50x50',
    r'32x32',
    r'16x16',
]

# Valid image extensions
VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif'}

# Content-Type to extension mapping
CONTENT_TYPE_TO_EXT = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/avif': '.avif',
    'image/svg+xml': '.svg',
}


# =============================================================================
# Helper Functions
# =============================================================================

def is_valid_image_url(url: str) -> bool:
    """Check if URL appears to be a valid product image."""
    if not url:
        return False
    
    url_lower = url.lower()
    
    # Skip data URIs
    if url_lower.startswith('data:'):
        return False
    
    # Check for skip patterns
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, url_lower):
            return False
    
    return True


def extract_url_from_proxy(url: str) -> str:
    """Extract original URL from proxy/CDN wrapper URLs.
    
    Handles cases like Netlify image proxy:
    https://example.com/.netlify/images?url=http%3A%2F%2Freal-image.com%2Fimg.png
    """
    # Handle Netlify image proxy
    if '.netlify/images' in url and 'url=' in url:
        try:
            from urllib.parse import urlparse, parse_qs, unquote
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            if 'url' in params:
                original_url = unquote(params['url'][0])
                return original_url
        except Exception:
            pass
    
    return url


def get_file_extension(url: str) -> str:
    """Extract file extension from URL."""
    # Remove query parameters
    path = url.split('?')[0]
    ext = os.path.splitext(path)[1].lower()
    
    if ext in VALID_EXTENSIONS:
        return ext
    
    # Default to .jpg if no valid extension found
    return '.jpg'


def generate_image_filename(brand: str, index: int, url: str) -> str:
    """Generate a clean, consistent filename for the downloaded image.
    
    Format: {index:02d}_{brand_slug}_{hash}.{ext}
    Example: 01_bjorg_8ec5fd.png, 02_alpro_c04a16.jpg
    
    Args:
        brand: Brand name
        index: Product index (1-based) for ordering
        url: Image URL (used for hash and extension)
        
    Returns:
        Clean filename string
    """
    # Normalize brand name: lowercase, remove special chars, replace spaces with hyphens
    import unicodedata
    # Normalize unicode (é -> e, etc.)
    brand_normalized = unicodedata.normalize('NFKD', brand)
    brand_normalized = brand_normalized.encode('ASCII', 'ignore').decode('ASCII')
    # Clean up: lowercase, only alphanumeric and hyphens
    brand_slug = re.sub(r'[^a-z0-9]+', '-', brand_normalized.lower()).strip('-')[:20]
    
    # Short hash for uniqueness (6 chars is enough)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:6]
    
    # Get extension
    ext = get_file_extension(url)
    
    return f"{index:02d}_{brand_slug}_{url_hash}{ext}"


def download_image(url: str, filepath: Path, timeout: int = 30) -> Optional[Path]:
    """Download an image from URL to local filepath.
    
    Args:
        url: Image URL to download
        filepath: Local path to save the image (extension may be corrected based on Content-Type)
        timeout: Download timeout in seconds
        
    Returns:
        Actual filepath where image was saved, or None if failed.
        Note: The returned path may have a different extension than the input filepath
        if the server returned a different image format than expected.
    """
    # Extract original URL if wrapped in a proxy
    original_url = extract_url_from_proxy(url)
    if original_url != url:
        print(f"    [i] Extracted from proxy: {original_url[:60]}...")
        url = original_url
    
    try:
        # Parse URL to get domain for Referer header
        from urllib.parse import urlparse
        parsed = urlparse(url)
        referer = f"{parsed.scheme}://{parsed.netloc}/"
        
        # Create a request with browser-like headers
        # Note: We avoid requesting AVIF format as PIL doesn't support it well
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/png,image/jpeg,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Referer': referer,
        }
        request = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(request, timeout=timeout) as response:
            # Check content type
            content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
            if not content_type.startswith('image/'):
                print(f"    [!] Not an image: {content_type}")
                return None
            
            # Determine correct extension from Content-Type
            actual_ext = CONTENT_TYPE_TO_EXT.get(content_type)
            if actual_ext and filepath.suffix.lower() != actual_ext:
                # Server returned different format than URL suggested
                filepath = filepath.with_suffix(actual_ext)
                print(f"    [i] Format is {content_type}, saving as {actual_ext}")
            
            # Download the image
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(response.read())
            
            return filepath
            
    except urllib.error.HTTPError as e:
        print(f"    [!] HTTP Error {e.code}: {url[:60]}...")
        return None
    except urllib.error.URLError as e:
        print(f"    [!] URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"    [!] Download error: {e}")
        return None


def find_scraped_files(output_dir: Path, run_id: str) -> Tuple[Optional[Path], Optional[str]]:
    """Find scraped JSON file matching a run ID (timestamp).
    
    Args:
        output_dir: Directory containing output files
        run_id: Run identifier (timestamp like 20260121_082959)
        
    Returns:
        Tuple of (scraped_file_path, category_slug) or (None, None) if not found
    """
    pattern = f"*_scraped_{run_id}.json"
    matches = list(output_dir.glob(pattern))
    
    if not matches:
        return None, None
    
    scraped_file = matches[0]
    # Extract category slug from filename
    filename = scraped_file.stem  # e.g., "lait_davoine_scraped_20260121_082959"
    category_slug = filename.replace(f"_scraped_{run_id}", "")
    
    return scraped_file, category_slug


def list_available_runs(output_dir: Path) -> List[Dict[str, str]]:
    """List all available runs in the output directory.
    
    Returns:
        List of dicts with 'run_id', 'category', 'file' keys
    """
    runs = []
    
    for f in output_dir.glob("*_scraped_*.json"):
        # Extract run_id (timestamp) from filename
        match = re.search(r'_scraped_(\d{8}_\d{6})\.json$', f.name)
        if match:
            run_id = match.group(1)
            category = f.stem.replace(f"_scraped_{run_id}", "").replace('_', ' ')
            runs.append({
                'run_id': run_id,
                'category': category,
                'file': str(f),
            })
    
    # Sort by run_id (most recent first)
    runs.sort(key=lambda x: x['run_id'], reverse=True)
    return runs


# =============================================================================
# Main ImageSelector Class
# =============================================================================

class ImageSelector:
    """Selects and downloads the best product images using AI.
    
    Uses GPT-5 Mini to analyze image URLs and select the best product image
    for each scraped product, then downloads it to a local directory.
    """
    
    def __init__(self, config: Optional[DiscoveryConfig] = None):
        """Initialize the image selector.
        
        Args:
            config: Optional configuration. Uses global config if not provided.
        """
        self.config = config or get_config()
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.config.openai_mini.api_key)
        self.model = self.config.openai_mini.model
        
        # Load prompts
        self.system_prompt = load_prompt("image_selection_system.txt")
        self.user_prompt_template = load_prompt("image_selection_user.txt")
        
        print(f"[ImageSelector] Initialized with {self.model}")
    
    def _collect_image_urls(self, product: Dict[str, Any]) -> Tuple[List[str], Optional[str]]:
        """Collect all available image URLs from a product.
        
        Args:
            product: Product dictionary from scraped JSON
            
        Returns:
            Tuple of (list of image URLs, og_image URL or None)
        """
        urls = []
        og_image = None
        
        # Get images from product.images
        if product.get('images'):
            urls.extend(product['images'])
        
        # Check additional_data for metadata
        additional = product.get('additional_data', {})
        metadata = additional.get('metadata', {})
        
        # Get og:image
        if metadata.get('og_image'):
            og_image = metadata['og_image']
            if og_image not in urls:
                urls.insert(0, og_image)  # Prioritize og:image
        
        # Filter out obviously bad URLs
        urls = [url for url in urls if is_valid_image_url(url)]
        
        return urls, og_image
    
    def _select_best_image(
        self,
        brand: str,
        product_name: str,
        category: str,
        image_urls: List[str],
        og_image: Optional[str]
    ) -> Optional[ImageSelection]:
        """Use AI to select the best product image.
        
        Args:
            brand: Brand name
            product_name: Full product name
            category: Product category
            image_urls: List of available image URLs
            og_image: The og:image URL if available
            
        Returns:
            ImageSelection result or None if failed
        """
        if not image_urls:
            return None
        
        # If only one URL, return it directly
        if len(image_urls) == 1:
            return ImageSelection(
                selected_url=image_urls[0],
                confidence=0.6,
                reasoning="Single image available",
                is_product_image=True
            )
        
        # Format URLs for the prompt
        urls_text = "\n".join(f"  {i+1}. {url}" for i, url in enumerate(image_urls))
        
        # Build user prompt
        user_prompt = self.user_prompt_template.format(
            brand=brand,
            product_name=product_name,
            category=category,
            image_urls=urls_text,
            og_image=og_image or "Non disponible"
        )
        
        try:
            # Call OpenAI with structured output
            completion = self.client.chat.completions.parse(
                model=self.model,
                temperature=self.config.openai_mini.temperature,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=ImageSelection
            )
            
            return completion.choices[0].message.parsed
            
        except Exception as e:
            print(f"    [!] AI selection error: {e}")
            # Fallback: return og_image or first URL
            fallback_url = og_image if og_image else image_urls[0]
            return ImageSelection(
                selected_url=fallback_url,
                confidence=0.3,
                reasoning=f"Fallback selection (AI error: {str(e)[:50]})",
                is_product_image=True
            )
    
    def select_image_for_product(
        self,
        product: Dict[str, Any],
        images_dir: Path,
        index: int = 1
    ) -> ImageSelectionResult:
        """Select and download the best image for a single product.
        
        Args:
            product: Product dictionary from scraped JSON
            images_dir: Directory to save downloaded images
            
        Returns:
            ImageSelectionResult with selection details
        """
        brand = product.get('brand', 'Unknown')
        product_name = product.get('full_name', 'Unknown Product')
        category = product.get('category', '')
        
        result = ImageSelectionResult(
            brand=brand,
            product_name=product_name
        )
        
        # Collect available URLs
        image_urls, og_image = self._collect_image_urls(product)
        
        if not image_urls:
            print(f"    [!] No images available")
            return result
        
        # Select best image using AI
        selection = self._select_best_image(
            brand, product_name, category, image_urls, og_image
        )
        
        if not selection or not selection.selected_url:
            return result
        
        result.selected_image_url = selection.selected_url
        result.selection_confidence = selection.confidence
        result.selection_reasoning = selection.reasoning
        
        # Download the image if it's a valid product image
        if selection.is_product_image and selection.confidence >= 0.3:
            filename = generate_image_filename(brand, index, selection.selected_url)
            filepath = images_dir / filename
            
            print(f"    Downloading: {selection.selected_url[:60]}...")
            actual_filepath = download_image(selection.selected_url, filepath)
            if actual_filepath:
                result.local_image_path = str(actual_filepath)
                print(f"    [✓] Saved: {actual_filepath.name}")
            else:
                print(f"    [!] Download failed")
        
        return result
    
    def process_scraped_data(
        self,
        scraped_file: Path,
        run_id: str,
        category_slug: str
    ) -> List[Dict[str, Any]]:
        """Process all products in a scraped JSON file.
        
        Args:
            scraped_file: Path to the scraped JSON file
            run_id: Run identifier (timestamp)
            category_slug: Category slug for directory naming
            
        Returns:
            Updated list of product dictionaries with image paths
        """
        # Load scraped data
        with open(scraped_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        if not products:
            print("[!] No products found in file")
            return []
        
        # Create images directory for this run
        output_dir = Path(self.config.output_dir)
        images_dir = output_dir / self.config.images_subdir / f"{category_slug}_{run_id}"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n[ImageSelector] Processing {len(products)} products")
        print(f"  Images directory: {images_dir}")
        print("-" * 70)
        
        # Process each product
        updated_products = []
        success_count = 0
        
        for i, product in enumerate(products, 1):
            brand = product.get('brand', 'Unknown')
            name = product.get('full_name', 'Unknown')[:40]
            print(f"[{i:2}/{len(products)}] {brand} - {name}")
            
            result = self.select_image_for_product(product, images_dir, index=i)
            
            # Update product with image selection results
            product['selected_image_url'] = result.selected_image_url
            product['local_image_path'] = result.local_image_path
            product['image_selection'] = {
                'confidence': result.selection_confidence,
                'reasoning': result.selection_reasoning,
            }
            
            if result.local_image_path:
                success_count += 1
            
            updated_products.append(product)
        
        print("-" * 70)
        print(f"[ImageSelector] Complete: {success_count}/{len(products)} images downloaded")
        
        return updated_products
    
    def run(
        self,
        run_id: Optional[str] = None,
        scraped_file: Optional[Path] = None
    ) -> Optional[Path]:
        """Run image selection on a previous scrape run or provided file.
        
        Args:
            run_id: Optional run ID (timestamp) to process
            scraped_file: Optional direct path to scraped JSON file
            
        Returns:
            Path to the updated JSON file, or None if failed
        """
        output_dir = Path(self.config.output_dir)
        
        # Determine which file to process
        if scraped_file:
            if not scraped_file.exists():
                print(f"[!] File not found: {scraped_file}")
                return None
            # Extract run_id from filename
            match = re.search(r'_scraped_(\d{8}_\d{6})\.json$', scraped_file.name)
            if match:
                run_id = match.group(1)
                category_slug = scraped_file.stem.replace(f"_scraped_{run_id}", "")
            else:
                print("[!] Cannot extract run_id from filename")
                return None
        elif run_id:
            scraped_file, category_slug = find_scraped_files(output_dir, run_id)
            if not scraped_file:
                print(f"[!] No scraped file found for run_id: {run_id}")
                print("\nAvailable runs:")
                for run in list_available_runs(output_dir):
                    print(f"  - {run['run_id']}: {run['category']}")
                return None
        else:
            # List available runs and ask user to specify
            runs = list_available_runs(output_dir)
            if not runs:
                print("[!] No scraped files found in output directory")
                return None
            
            print("\nAvailable runs:")
            for run in runs:
                print(f"  - {run['run_id']}: {run['category']}")
            print("\nPlease specify a run_id to process")
            return None
        
        print("=" * 70)
        print(f"IMAGE SELECTION - Run: {run_id}")
        print(f"  Category: {category_slug.replace('_', ' ')}")
        print(f"  File: {scraped_file}")
        print("=" * 70)
        
        # Process the file
        updated_products = self.process_scraped_data(scraped_file, run_id, category_slug)
        
        if not updated_products:
            return None
        
        # Save updated JSON
        output_file = output_dir / f"{category_slug}_with_images_{run_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(updated_products, f, indent=2, ensure_ascii=False)
        
        print(f"\n[✓] Updated JSON saved: {output_file}")
        
        return output_file


# =============================================================================
# Convenience Functions
# =============================================================================

def select_images(
    run_id: Optional[str] = None,
    scraped_file: Optional[Path] = None
) -> Optional[Path]:
    """Convenience function to run image selection.
    
    Args:
        run_id: Optional run ID to process
        scraped_file: Optional direct path to scraped file
        
    Returns:
        Path to updated JSON file or None
    """
    selector = ImageSelector()
    return selector.run(run_id=run_id, scraped_file=scraped_file)


def list_runs() -> List[Dict[str, str]]:
    """List all available runs in the output directory."""
    config = get_config()
    output_dir = Path(config.output_dir)
    return list_available_runs(output_dir)
