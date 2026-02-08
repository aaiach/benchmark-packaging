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
    """Step 2: Product Details using OpenAI + Web Search (PARALLELIZED).
    
    Gets detailed product information for each discovered brand.
    Uses parallel execution for faster processing.
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
    print(f"  Mode: PARALLEL ({config.parallel.openai.max_concurrent} concurrent)")
    print("-" * 70)
    
    # Use parallel execution
    results = discovery.get_product_details_parallel(brands, ctx.category, ctx.country)
    
    products: List[Product] = []
    for brand, details in results:
        if details:
            product = Product.from_product_details(details, ctx.category)
            products.append(product)
    
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
    """Step 3: Web Scraping using Firecrawl (PARALLELIZED).
    
    Scrapes product pages to extract prices, descriptions, images, etc.
    Uses parallel execution for faster processing.
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
    print(f"  Mode: PARALLEL ({config.parallel.firecrawl.max_concurrent} concurrent)")
    
    scraper = ProductScraper(config=config)
    scraped_products = scraper.scrape_products_batch(products, parallel=True)
    
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


def execute_step_8_review_correlation(ctx: PipelineContext, config: Any) -> Optional[Path]:
    """Step 8: Review-Packaging Correlation Analysis (Phase 1.3).
    
    Scrapes customer reviews, analyzes sentiment and packaging topics,
    then correlates packaging design attributes with customer satisfaction.
    
    Outputs:
    - Review analyses with sentiment and topic extraction
    - Correlation analysis between packaging attributes and sentiment
    - Ranked list of packaging attributes by customer impact
    
    Returns:
        Path to the correlation analysis JSON file
    """
    from ..review_scraper import ReviewScraper
    from ..review_analyzer import ReviewAnalyzer
    from ..correlation_engine import CorrelationEngine
    from ..models import Product
    
    print(f"[Step 8] Review-Packaging Correlation Analysis...")
    
    # Load product details from step 2/3
    products_file = ctx.output_dir / f"{ctx.category_slug}_discovered_{ctx.run_id}.json"
    if not products_file.exists():
        print("[!] Product details not found. Run steps 1-2 first.")
        return None
    
    with open(products_file, 'r', encoding='utf-8') as f:
        products_data = json.load(f)
    
    # Convert to Product objects
    products = []
    for p in products_data:
        product = Product(
            brand=p['brand'],
            full_name=p['full_name'],
            category=ctx.category,
            target_audience=p.get('target_audience', ''),
            product_url=p.get('product_url'),
            brand_website=p.get('brand_website')
        )
        products.append(product)
    
    print(f"  Loaded {len(products)} products")
    
    # Load visual analyses from step 5
    visual_analysis_file = ctx.output_dir / "analysis" / f"{ctx.category_slug}_visual_analysis_{ctx.run_id}.json"
    if not visual_analysis_file.exists():
        print("[!] Visual analysis not found. Run step 5 first.")
        return None
    
    with open(visual_analysis_file, 'r', encoding='utf-8') as f:
        visual_data = json.load(f)
    
    # Parse visual analyses
    from ..models import VisualHierarchyAnalysis
    packaging_analyses = {}
    for analysis in visual_data.get('analyses', []):
        brand = analysis['brand']
        product_name = analysis['product_name']
        product_key = f"{brand}_{product_name}"
        
        # Parse into VisualHierarchyAnalysis model
        try:
            packaging_analyses[product_key] = VisualHierarchyAnalysis.model_validate(analysis['analysis'])
        except Exception as e:
            print(f"  [!] Failed to parse visual analysis for {product_key}: {e}")
            continue
    
    print(f"  Loaded {len(packaging_analyses)} visual analyses")
    
    # Step 1: Scrape reviews
    print(f"\n  [1/3] Scraping customer reviews...")
    scraper = ReviewScraper()
    all_reviews = scraper.scrape_all_products(products, max_reviews_per_product=30)
    
    total_reviews = sum(len(reviews) for reviews in all_reviews.values())
    print(f"  ✓ Scraped {total_reviews} reviews across {len(all_reviews)} products")
    
    # Step 2: Analyze reviews
    print(f"\n  [2/3] Analyzing reviews for sentiment and packaging topics...")
    analyzer = ReviewAnalyzer()
    
    review_analyses = {}
    for product in products:
        product_key = f"{product.brand}_{product.full_name}"
        reviews = all_reviews.get(product_key, [])
        
        if not reviews:
            continue
        
        analyses = analyzer.analyze_reviews_batch(
            reviews,
            product.brand,
            product.full_name
        )
        review_analyses[product_key] = analyses
    
    packaging_focused_total = sum(
        sum(1 for a in analyses if a.is_packaging_focused)
        for analyses in review_analyses.values()
    )
    print(f"  ✓ Analyzed {total_reviews} reviews, {packaging_focused_total} are packaging-focused")
    
    # Step 3: Correlate with packaging attributes
    print(f"\n  [3/3] Correlating packaging attributes with customer satisfaction...")
    correlation_engine = CorrelationEngine()
    
    correlation_result = correlation_engine.analyze_correlations(
        review_analyses,
        packaging_analyses,
        ctx.category
    )
    
    print(f"  ✓ Identified {len(correlation_result.attribute_rankings)} correlated attributes")
    
    # Save results
    output_dir = ctx.output_dir / "analysis"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    output_file = output_dir / f"{ctx.category_slug}_review_correlation_{ctx.run_id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(
            correlation_result.model_dump(),
            f,
            indent=2,
            ensure_ascii=False
        )
    
    print(f"\n[✓] Review-packaging correlation analysis complete")
    print(f"    Output: {output_file}")
    
    # Print top 5 findings
    print(f"\n  Top 5 Packaging Attributes by Customer Impact:")
    for ranking in correlation_result.attribute_rankings[:5]:
        attr = ranking.attribute
        impact_emoji = "🔺" if "positive" in attr.impact_category else "🔻" if "negative" in attr.impact_category else "➖"
        print(f"    {ranking.rank}. {impact_emoji} {attr.attribute_value}")
        print(f"       Correlation: {attr.correlation_score:+.2f}, Significance: p={attr.statistical_significance:.3f}")
    
    return output_file


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
        description="Web Scraping (Firecrawl - Parallel)",
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
    8: Step(
        number=8,
        name="review_correlation",
        description="Review-Packaging Correlation Analysis (Phase 1.3)",
        output_pattern="analysis/{category}_review_correlation_{run_id}.json",
        requires=[2, 5],  # Requires product details and visual analysis
        executor=execute_step_8_review_correlation,
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
