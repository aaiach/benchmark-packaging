"""OCR analysis module for packaging text extraction and categorization.

This module extracts and categorizes text from product packaging images using 
Gemini Vision for competitive intelligence purposes.

Features:
- Multilingual text extraction (French, Dutch, English)
- Categorization into: brand identity, claims, nutritional info, certifications, regulatory text
- Visual code identification (colors, typography, layout)
- Structured JSON output for market analysis

Uses LangChain's ChatGoogleGenerativeAI with structured output for reliable parsing.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from .config import get_config, DiscoveryConfig
from .models import OCRResult
from .utils import load_prompt, invoke_with_retry
from .visual_analyzer import get_mime_type, find_images_for_run, load_product_data_for_run
from .parallel_executor import (
    ParallelExecutor,
    Provider,
    ProviderLimits,
)


# =============================================================================
# Main OCRAnalyzer Class
# =============================================================================

class OCRAnalyzer:
    """Analyzes product packaging for text extraction and categorization using Gemini Vision.
    
    Extracts and categorizes all text on packaging into:
    - Brand identity (name, slogan)
    - Product claims (health, taste, eco, origin)
    - Nutritional information
    - Certifications and labels
    - Regulatory mentions
    - Visual design codes
    """
    
    def __init__(self, config: Optional[DiscoveryConfig] = None):
        """Initialize the OCR analyzer.
        
        Args:
            config: Optional configuration. Uses global config if not provided.
        """
        self.config = config or get_config()
        
        # Initialize Gemini with structured output for OCR
        self.llm = ChatGoogleGenerativeAI(
            model=self.config.gemini.model,
            temperature=0.0,  # Deterministic for text extraction
            google_api_key=self.config.gemini.api_key,
        )
        
        # Bind the structured output schema
        self.structured_llm = self.llm.with_structured_output(OCRResult)
        
        # Load prompts
        self.system_prompt = load_prompt("ocr_extraction_system")
        self.user_prompt_template = load_prompt("ocr_extraction_user")
        
        print(f"[OCRAnalyzer] Initialized with model: {self.config.gemini.model}")
    
    def analyze_image(
        self, 
        image_path: Path,
        category: str = "unknown",
        brand: str = "unknown",
        product_name: str = "unknown"
    ) -> OCRResult:
        """Analyze a single packaging image for OCR extraction.
        
        Args:
            image_path: Path to the product packaging image
            category: Product category for context
            brand: Expected brand name for context
            product_name: Expected product name for context
            
        Returns:
            OCRResult with categorized text extraction
        """
        print(f"[OCR] Analyzing {image_path.name}...")
        
        # Load image
        mime_type = get_mime_type(image_path)
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Prepare user prompt
        user_prompt = self.user_prompt_template.format(
            category=category,
            brand=brand,
            product_name=product_name
        )
        
        # Create messages with image
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=[
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{self._encode_image(image_data)}"
                    }
                }
            ])
        ]
        
        # Invoke with retry logic
        result = invoke_with_retry(
            llm=self.structured_llm,
            messages=messages,
            operation_name=f"OCR extraction for {image_path.name}"
        )
        
        # Add metadata
        result.image_path = str(image_path)
        result.brand = brand
        result.product_name = product_name
        result.analysis_timestamp = datetime.now().isoformat()
        
        print(f"[OCR] ✓ Extracted {len(result.product_claims)} claims, "
              f"{len(result.certifications)} certifications, "
              f"languages: {', '.join(result.detected_languages)}")
        
        return result
    
    def analyze_multiple_images(
        self,
        image_paths: List[Path],
        products_data: Dict[str, Dict[str, Any]],
        category: str = "unknown"
    ) -> List[OCRResult]:
        """Analyze multiple packaging images in parallel.
        
        Args:
            image_paths: List of image paths to analyze
            products_data: Dict mapping image filenames to product data
            category: Product category
            
        Returns:
            List of OCRResult objects
        """
        print(f"\n[OCR] Analyzing {len(image_paths)} images in parallel...")
        
        # Prepare tasks for parallel execution
        tasks = []
        for image_path in image_paths:
            # Get product data for this image
            product_data = products_data.get(image_path.name, {})
            brand = product_data.get('brand', 'unknown')
            product_name = product_data.get('full_name', 'unknown')
            
            tasks.append({
                'image_path': image_path,
                'category': category,
                'brand': brand,
                'product_name': product_name
            })
        
        # Execute in parallel using ParallelExecutor
        executor = ParallelExecutor(
            provider=Provider.GOOGLE,
            provider_limits=ProviderLimits(
                rpm=14,  # Conservative limit for Gemini
                tpm=800000,  # Token limit
                max_concurrent=10
            )
        )
        
        results = []
        for task in tasks:
            result = executor.submit(
                func=self._analyze_image_task,
                task_data=task
            )
            results.append(result)
        
        # Wait for all results
        completed_results = executor.wait_all()
        
        print(f"[OCR] ✓ Completed {len(completed_results)} OCR extractions")
        
        return completed_results
    
    def _analyze_image_task(self, task_data: Dict[str, Any]) -> OCRResult:
        """Task wrapper for parallel execution.
        
        Args:
            task_data: Dict containing image_path, category, brand, product_name
            
        Returns:
            OCRResult
        """
        return self.analyze_image(
            image_path=task_data['image_path'],
            category=task_data['category'],
            brand=task_data['brand'],
            product_name=task_data['product_name']
        )
    
    def _encode_image(self, image_data: bytes) -> str:
        """Encode image data to base64 string.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Base64 encoded string
        """
        import base64
        return base64.b64encode(image_data).decode('utf-8')


# =============================================================================
# Standalone Functions for Pipeline Integration
# =============================================================================

def analyze_images_for_run(
    output_dir: Path,
    run_id: str,
    category: str,
    config: Optional[DiscoveryConfig] = None
) -> List[OCRResult]:
    """Analyze all images for a given run with OCR extraction.
    
    This is the main entry point for Step 8 of the pipeline.
    
    Args:
        output_dir: Output directory containing run data
        run_id: Run identifier (timestamp)
        category: Product category
        config: Optional configuration
        
    Returns:
        List of OCRResult objects
    """
    print(f"\n{'='*80}")
    print(f"[Step 8] OCR Text Extraction & Categorization")
    print(f"{'='*80}")
    
    # Find images for this run
    images_dir, image_paths = find_images_for_run(output_dir, run_id)
    
    if not image_paths:
        print(f"[!] No images found for run {run_id}")
        return []
    
    print(f"[OCR] Found {len(image_paths)} images in {images_dir}")
    
    # Load product data
    products_data = load_product_data_for_run(output_dir, run_id)
    print(f"[OCR] Loaded product data for {len(products_data)} products")
    
    # Initialize analyzer
    analyzer = OCRAnalyzer(config=config)
    
    # Analyze images in parallel
    results = analyzer.analyze_multiple_images(
        image_paths=image_paths,
        products_data=products_data,
        category=category
    )
    
    # Save results
    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(exist_ok=True)
    
    output_file = analysis_dir / f"{category.replace(' ', '_')}_ocr_{run_id}.json"
    
    # Convert results to dict for JSON serialization
    results_dict = [result.model_dump() for result in results]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OCR] ✓ Results saved to: {output_file}")
    print(f"[OCR] Summary:")
    print(f"  - Total products analyzed: {len(results)}")
    
    # Calculate statistics
    total_claims = sum(len(r.product_claims) for r in results)
    total_certifications = sum(len(r.certifications) for r in results)
    all_languages = set()
    for r in results:
        all_languages.update(r.detected_languages)
    
    print(f"  - Total claims extracted: {total_claims}")
    print(f"  - Total certifications: {total_certifications}")
    print(f"  - Languages detected: {', '.join(sorted(all_languages))}")
    
    return results


def analyze_single_image(
    image_path: Path,
    category: str = "unknown",
    brand: str = "unknown", 
    product_name: str = "unknown",
    output_path: Optional[Path] = None,
    config: Optional[DiscoveryConfig] = None
) -> OCRResult:
    """Analyze a single image with OCR extraction.
    
    Convenience function for analyzing individual images.
    
    Args:
        image_path: Path to packaging image
        category: Product category
        brand: Brand name
        product_name: Product name
        output_path: Optional path to save JSON result
        config: Optional configuration
        
    Returns:
        OCRResult
    """
    analyzer = OCRAnalyzer(config=config)
    result = analyzer.analyze_image(
        image_path=image_path,
        category=category,
        brand=brand,
        product_name=product_name
    )
    
    # Save if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
        print(f"[OCR] ✓ Result saved to: {output_path}")
    
    return result
