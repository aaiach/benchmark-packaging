"""Step definitions and executors for the product discovery pipeline.

Each step is defined with:
- Number and name for identification
- Output file pattern for checkpointing
- Dependencies on previous steps
- Executor function that performs the work

Current steps:
1. Brand Discovery - Find brands using Gemini + Google Search
2. Product Details - Get details for each brand using OpenAI + Web Search  
3. Web Scraping - Scrape product pages using Firecrawl
4. Image Selection - Select and download best product images using AI
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Step, PipelineContext


# =============================================================================
# Step Executors
# =============================================================================

def execute_step_1_discovery(ctx: PipelineContext, config: Any) -> List[Any]:
    """Step 1: Brand Discovery using Gemini + Google Search.
    
    Discovers brands in the specified category and country.
    Saves discovered brands to JSON file.
    
    Returns:
        List of Brand objects
    """
    from ..product_discovery import ProductDiscovery
    from ..models import Product
    
    print(f"[Step 1] Discovering brands for '{ctx.category}' in {ctx.country}...")
    print(f"  Model: {config.gemini.model} + Google Search grounding")
    
    discovery = ProductDiscovery(config=config)
    brands = discovery.discover_brands(
        category=ctx.category,
        count=ctx.count,
        country=ctx.country
    )
    
    if not brands:
        print("[!] No brands discovered")
        return []
    
    # Save discovered brands
    output_file = ctx.output_dir / f"{ctx.category_slug}_discovered_{ctx.run_id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(
            [{"name": b.name, "country_of_origin": b.country_of_origin} for b in brands],
            f,
            indent=2,
            ensure_ascii=False
        )
    
    print(f"[✓] {len(brands)} brands discovered")
    
    # Store in context for next step
    ctx.data['brands'] = brands
    ctx.data['discovery'] = discovery
    
    return brands


def execute_step_2_details(ctx: PipelineContext, config: Any) -> List[Any]:
    """Step 2: Product Details using OpenAI + Web Search.
    
    Gets detailed product information for each discovered brand.
    Updates the discovered JSON file with full product details.
    
    Returns:
        List of Product objects
    """
    from ..product_discovery import ProductDiscovery
    from ..models import Product, Brand
    
    # Load brands from step 1 if not in context
    if 'brands' not in ctx.data:
        discovered_file = ctx.output_dir / f"{ctx.category_slug}_discovered_{ctx.run_id}.json"
        with open(discovered_file, 'r', encoding='utf-8') as f:
            brands_data = json.load(f)
        brands = [Brand(name=b['name'], country_of_origin=b.get('country_of_origin')) for b in brands_data]
        ctx.data['brands'] = brands
    else:
        brands = ctx.data['brands']
    
    # Get or create discovery instance
    if 'discovery' not in ctx.data:
        discovery = ProductDiscovery(config=config)
        ctx.data['discovery'] = discovery
    else:
        discovery = ctx.data['discovery']
    
    print(f"[Step 2] Getting details for {len(brands)} brands...")
    print(f"  Model: {config.openai.model} + Web Search")
    print("-" * 70)
    
    products: List[Product] = []
    
    for i, brand in enumerate(brands, 1):
        print(f"  [{i:2}/{len(brands)}] {brand.name}...", end=" ", flush=True)
        
        details = discovery.get_product_details(brand, ctx.category, ctx.country)
        
        if details:
            product = Product.from_product_details(details, ctx.category)
            products.append(product)
            site = details.brand_website or "—"
            print(f"✓ {details.full_name[:40]} | {site}")
        else:
            print("✗ Failed")
    
    print("-" * 70)
    print(f"[✓] {len(products)}/{len(brands)} products with details")
    
    # Save products (overwrites discovered file with enriched data)
    output_file = ctx.output_dir / f"{ctx.category_slug}_discovered_{ctx.run_id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(
            [p.to_dict() for p in products],
            f,
            indent=2,
            ensure_ascii=False
        )
    
    # Store in context
    ctx.data['products'] = products
    
    return products


def execute_step_3_scraping(ctx: PipelineContext, config: Any) -> List[Any]:
    """Step 3: Web Scraping using Firecrawl.
    
    Scrapes product pages to extract prices, descriptions, images, etc.
    Saves scraped data to JSON file.
    
    Returns:
        List of scraped Product objects
    """
    from ..scraper import ProductScraper
    from ..models import Product
    
    # Load products from step 2 if not in context
    if 'products' not in ctx.data:
        discovered_file = ctx.output_dir / f"{ctx.category_slug}_discovered_{ctx.run_id}.json"
        with open(discovered_file, 'r', encoding='utf-8') as f:
            products_data = json.load(f)
        products = [
            Product(
                brand=p['brand'],
                full_name=p['full_name'],
                category=p['category'],
                target_audience=p['target_audience'],
                brand_website=p.get('brand_website'),
                product_url=p.get('product_url'),
                additional_data=p.get('additional_data', {})
            )
            for p in products_data
        ]
    else:
        products = ctx.data['products']
    
    print(f"[Step 3] Scraping {len(products)} products with Firecrawl...")
    
    scraper = ProductScraper()
    scraped_products = scraper.scrape_products_batch(products)
    
    # Save scraped data
    output_file = ctx.output_dir / f"{ctx.category_slug}_scraped_{ctx.run_id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(
            [p.to_dict() for p in scraped_products],
            f,
            indent=2,
            ensure_ascii=False
        )
    
    print(f"[✓] Scraped data saved")
    
    # Also create CSV for convenience
    try:
        import pandas as pd
        csv_file = ctx.output_dir / f"{ctx.category_slug}_results_{ctx.run_id}.csv"
        df_data = []
        for p in scraped_products:
            df_data.append({
                'Marque': p.brand,
                'Nom Produit': p.full_name,
                'Catégorie': p.category,
                'Public Cible': p.target_audience,
                'Site Marque': p.brand_website or '',
                'URL Produit': p.product_url or '',
                'Prix': p.price or '',
                'Disponibilité': p.availability or '',
                'Description': (p.description or '')[:200],
                'Nb Images': len(p.images) if p.images else 0,
            })
        df = pd.DataFrame(df_data)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"[✓] CSV saved: {csv_file}")
    except ImportError:
        print("[i] pandas not available, skipping CSV export")
    
    # Store in context
    ctx.data['scraped_products'] = scraped_products
    
    return scraped_products


def execute_step_4_images(ctx: PipelineContext, config: Any) -> Optional[Path]:
    """Step 4: Image Selection using OpenAI.
    
    Analyzes image URLs and selects the best product image for each product.
    Downloads selected images locally.
    
    Returns:
        Path to the output JSON file with image data
    """
    from ..image_selector import ImageSelector
    
    print(f"[Step 4] Selecting images with {config.openai_mini.model}...")
    
    selector = ImageSelector(config=config)
    
    # Find the scraped file
    scraped_file = ctx.output_dir / f"{ctx.category_slug}_scraped_{ctx.run_id}.json"
    
    if not scraped_file.exists():
        print(f"[!] Scraped file not found: {scraped_file}")
        return None
    
    # Process images
    result_file = selector.run(
        run_id=ctx.run_id,
        scraped_file=scraped_file
    )
    
    return result_file


def execute_step_5_visual_analysis(ctx: PipelineContext, config: Any) -> Optional[Path]:
    """Step 5: Visual Analysis using Gemini Vision.
    
    Analyzes each downloaded product image for:
    - Visual hierarchy and element ranking
    - Eye-tracking simulation (Z, F patterns)
    - Massing and visual balance
    - Design effectiveness scoring
    
    Returns:
        Path to the output JSON file with analysis data
    """
    from ..visual_analyzer import VisualAnalyzer
    
    print(f"[Step 5] Visual analysis with {config.gemini_vision.model}...")
    
    analyzer = VisualAnalyzer(config=config)
    
    # Run analysis on all images from this run
    result_file = analyzer.run(run_id=ctx.run_id)
    
    return result_file


def execute_step_6_heatmaps(ctx: PipelineContext, config: Any) -> Optional[Path]:
    """Step 6: Heatmap Generation using Gemini Vision.
    
    Generates eye-tracking heatmap overlays for each product image based on
    the visual hierarchy analysis from Step 5.
    
    Heatmaps are saved in a 'heatmaps' subdirectory alongside the original images.
    
    Returns:
        Path to the updated analysis JSON file with heatmap paths
    """
    from ..visual_analyzer import VisualAnalyzer
    
    print(f"[Step 6] Heatmap generation with {config.gemini_vision.model}...")
    
    analyzer = VisualAnalyzer(config=config)
    
    # Generate heatmaps for all analyzed images
    result_file = analyzer.run_heatmaps(run_id=ctx.run_id)
    
    return result_file


def execute_step_7_competitive(ctx: PipelineContext, config: Any) -> Optional[Path]:
    """Step 7: Competitive Analysis using Gemini.
    
    Analyzes the visual analysis data to extract:
    - Top 5 Points-of-Difference (PODs) for radar chart comparison
    - Top 5 Points-of-Parity (POPs) for attribute matrix
    - Product scores on each POD axis
    - Strategic insights for BCG-style presentation
    
    Output is structured JSON ready for frontend React consumption.
    
    Returns:
        Path to the competitive analysis JSON file
    """
    from ..competitive_analyzer import CompetitiveAnalyzer
    
    print(f"[Step 7] Competitive analysis with {config.gemini.model}...")
    
    analyzer = CompetitiveAnalyzer(config=config)
    
    # Run competitive analysis
    result_file = analyzer.run(run_id=ctx.run_id)
    
    return result_file


# =============================================================================
# Step Registry
# =============================================================================

# Define all pipeline steps
# Note: Steps 1 and 2 share the same output file (discovered_*.json)
# because step 2 enriches step 1's output

STEPS: Dict[int, Step] = {
    1: Step(
        number=1,
        name="discovery",
        description="Brand Discovery (Gemini + Google Search)",
        output_pattern="{category}_discovered_{run_id}.json",
        requires=[],
        executor=execute_step_1_discovery,
    ),
    2: Step(
        number=2,
        name="details",
        description="Product Details (OpenAI + Web Search)",
        output_pattern="{category}_discovered_{run_id}.json",  # Same file, enriched
        requires=[1],
        executor=execute_step_2_details,
    ),
    3: Step(
        number=3,
        name="scraping",
        description="Web Scraping (Firecrawl)",
        output_pattern="{category}_scraped_{run_id}.json",
        requires=[1, 2],
        executor=execute_step_3_scraping,
    ),
    4: Step(
        number=4,
        name="images",
        description="Image Selection (OpenAI)",
        output_pattern="{category}_with_images_{run_id}.json",
        requires=[3],
        executor=execute_step_4_images,
    ),
    5: Step(
        number=5,
        name="analysis",
        description="Visual Analysis (Gemini Vision)",
        output_pattern="analysis/{category}_visual_analysis_{run_id}.json",
        requires=[4],
        executor=execute_step_5_visual_analysis,
    ),
    6: Step(
        number=6,
        name="heatmaps",
        description="Heatmap Generation (Gemini Vision)",
        output_pattern="analysis/{category}_visual_analysis_{run_id}.json",  # Updates same file
        requires=[5],
        executor=execute_step_6_heatmaps,
    ),
    7: Step(
        number=7,
        name="competitive",
        description="Competitive Analysis (PODs/POPs extraction)",
        output_pattern="analysis/{category}_competitive_analysis_{run_id}.json",
        requires=[5],  # Only requires visual analysis, not heatmaps
        executor=execute_step_7_competitive,
    ),
}


def get_step(step_num: int) -> Optional[Step]:
    """Get a step by number."""
    return STEPS.get(step_num)


def list_steps() -> List[Dict[str, Any]]:
    """List all available steps with their info."""
    return [
        {
            "number": step.number,
            "name": step.name,
            "description": step.description,
            "requires": step.requires,
        }
        for step in sorted(STEPS.values(), key=lambda s: s.number)
    ]
