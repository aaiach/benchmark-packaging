"""Test script for review-packaging correlation analysis.

This script demonstrates the review-packaging correlation analysis with sample data.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from src.review_scraper import Review
from src.review_analyzer import ReviewAnalyzer
from src.correlation_engine import CorrelationEngine
from src.models import (
    VisualHierarchyAnalysis,
    VisualElement,
    EyeTrackingPattern,
    MassingAnalysis,
    ChromaticMapping,
    ColorEntry,
    TextualInventory,
    TextBlock,
    AssetSymbolism,
    GraphicalAsset,
    TrustMark,
)
from src.visualization import visualize_correlation_results

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_reviews(brand: str, product_name: str, num_reviews: int = 10) -> List[Review]:
    """Create sample reviews for testing.
    
    Args:
        brand: Brand name
        product_name: Product name
        num_reviews: Number of reviews to create
        
    Returns:
        List of sample Review objects
    """
    sample_texts = [
        # Positive reviews mentioning packaging
        "I love the design of this packaging! The colors are vibrant and eye-catching. Really stands out on the shelf.",
        "Great product and the packaging is beautiful. The matte finish gives it a premium feel. Easy to read all the information.",
        "The organic certification badge is prominently displayed which I appreciate. Trustworthy brand with great design.",
        
        # Mixed reviews mentioning readability
        "Good product but the text on the package is too small. Hard to read the ingredients list.",
        "Nice looking package but some of the claims seem exaggerated. Not sure if I believe all of them.",
        
        # Positive reviews on overall appearance
        "The package looks modern and clean. Minimalist design that appeals to me. Very attractive.",
        "I bought this because it caught my eye on the shelf. The design is elegant and the colors match well.",
        
        # Reviews mentioning trust marks
        "I trust this brand because of all the certifications shown. The organic and fair trade badges give me confidence.",
        
        # Neutral/negative
        "Product is okay. Packaging is nothing special, just a basic design.",
        "The package design is fine but could be better. A bit boring compared to competitors.",
    ]
    
    ratings = [5, 5, 5, 3, 3, 5, 5, 5, 3, 3]
    
    reviews = []
    for i in range(min(num_reviews, len(sample_texts))):
        review = Review(
            review_id=f"{brand}_{i}",
            text=sample_texts[i],
            rating=ratings[i],
            date=datetime.now().isoformat(),
            verified_purchase=True,
            source="sample_data"
        )
        reviews.append(review)
    
    return reviews


def create_sample_packaging_analysis(brand: str, product_name: str, variant: str = "default") -> VisualHierarchyAnalysis:
    """Create sample packaging analysis for testing.
    
    Args:
        brand: Brand name
        product_name: Product name
        variant: Variant type to create different attribute combinations
        
    Returns:
        Sample VisualHierarchyAnalysis object
    """
    # Vary attributes based on variant
    if variant == "premium":
        num_colors = 3
        surface_finish = "matte"
        hierarchy_clarity = 9
        num_trust_marks = 4
    elif variant == "basic":
        num_colors = 2
        surface_finish = "high-gloss"
        hierarchy_clarity = 5
        num_trust_marks = 1
    else:
        num_colors = 4
        surface_finish = "semi-gloss"
        hierarchy_clarity = 7
        num_trust_marks = 2
    
    return VisualHierarchyAnalysis(
        visual_anchor="Brand logo",
        visual_anchor_description="Large brand logo centered at top",
        elements=[
            VisualElement(
                element_type="logo",
                description="Brand logo",
                position="top-center",
                visual_weight=10,
                dominant_color="#2D5A3D",
                size_percentage=15
            ),
            VisualElement(
                element_type="text",
                description="Product name",
                position="center",
                visual_weight=8,
                dominant_color="#000000",
                size_percentage=10
            ),
        ],
        eye_tracking=EyeTrackingPattern(
            pattern_type="Z",
            entry_point="top-center logo",
            fixation_sequence=["logo", "product name", "claims", "trust marks"],
            exit_point="bottom trust marks",
            dwell_zones=["logo", "product name"]
        ),
        massing=MassingAnalysis(
            balance_type="symmetric",
            dense_zones=["top-center", "center"],
            light_zones=["bottom-left", "bottom-right"],
            center_of_gravity="center"
        ),
        hierarchy_clarity_score=hierarchy_clarity,
        detailed_analysis="Sample analysis for testing",
        chromatic_mapping=ChromaticMapping(
            color_palette=[
                ColorEntry(
                    color_name="Forest Green",
                    hex_code="#2D5A3D",
                    usage="background",
                    coverage_percentage=60
                )
                for _ in range(num_colors)
            ],
            background_colors=["#FFFFFF"],
            primary_branding_colors=["#2D5A3D"],
            accent_colors=["#F5A623"],
            surface_finish=surface_finish,
            surface_finish_description=f"The package has a {surface_finish} finish",
            color_harmony="complementary",
            color_psychology_notes="Green evokes natural and organic feelings"
        ),
        textual_inventory=TextualInventory(
            all_text_blocks=[
                TextBlock(
                    text_content="Organic",
                    font_category="Geometric Sans-Serif",
                    font_weight="bold",
                    text_size="large",
                    text_color="#2D5A3D",
                    position="top-right",
                    emphasis_techniques=["bold", "color block background"],
                    is_claim=True,
                    hierarchy_level=2
                ),
                TextBlock(
                    text_content="100% Natural",
                    font_category="Humanist Sans-Serif",
                    font_weight="medium",
                    text_size="medium",
                    text_color="#000000",
                    position="center",
                    emphasis_techniques=["bold"],
                    is_claim=True,
                    hierarchy_level=3
                ),
            ],
            brand_name_typography="Bold geometric sans-serif",
            product_name_typography="Medium humanist sans-serif",
            claims_summary=["Organic", "100% Natural", "Non-GMO"],
            emphasized_claims=["Organic"],
            typography_consistency="Consistent 2-font system",
            readability_assessment="Excellent readability with high contrast"
        ),
        asset_symbolism=AssetSymbolism(
            graphical_assets=[
                GraphicalAsset(
                    asset_type="illustration",
                    description="Leaf illustration",
                    style="Line art",
                    position="bottom-left",
                    size_percentage=10,
                    purpose="Natural/organic signaling"
                )
            ],
            trust_marks=[
                TrustMark(
                    name="EU Organic",
                    mark_type="organic-certification",
                    visual_description="Green leaf symbol",
                    position="bottom-right",
                    prominence="prominent",
                    colors=["#00A651"]
                )
                for _ in range(num_trust_marks)
            ],
            photography_vs_illustration_ratio="30% photography / 70% illustration",
            visual_storytelling_elements=["Natural ingredients imagery"],
            trust_signal_effectiveness="High effectiveness with prominent certifications"
        )
    )


def main():
    """Run the test."""
    logger.info("Starting review-packaging correlation test")
    
    # Create sample data for 3 products with different packaging attributes
    products = [
        ("Brand A", "Oat Milk Premium", "premium"),
        ("Brand B", "Oat Milk Classic", "default"),
        ("Brand C", "Oat Milk Basic", "basic"),
    ]
    
    # Generate sample reviews
    all_reviews = {}
    review_analyses = {}
    
    logger.info("Creating sample reviews...")
    analyzer = ReviewAnalyzer()
    
    for brand, product_name, _ in products:
        product_key = f"{brand}_{product_name}"
        
        # Create sample reviews
        reviews = create_sample_reviews(brand, product_name, num_reviews=10)
        all_reviews[product_key] = reviews
        
        # Analyze reviews
        analyses = analyzer.analyze_reviews_batch(reviews, brand, product_name)
        review_analyses[product_key] = analyses
        
        logger.info(f"  {brand}: {len(reviews)} reviews, {sum(1 for a in analyses if a.is_packaging_focused)} packaging-focused")
    
    # Generate sample packaging analyses
    logger.info("Creating sample packaging analyses...")
    packaging_analyses = {}
    
    for brand, product_name, variant in products:
        product_key = f"{brand}_{product_name}"
        packaging = create_sample_packaging_analysis(brand, product_name, variant)
        packaging_analyses[product_key] = packaging
    
    # Run correlation analysis
    logger.info("Running correlation analysis...")
    correlation_engine = CorrelationEngine()
    
    correlation_result = correlation_engine.analyze_correlations(
        review_analyses,
        packaging_analyses,
        "Oat Milk"
    )
    
    # Save results
    output_dir = Path("output/test_correlation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = output_dir / "correlation_result.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(correlation_result.model_dump(), f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved correlation results to: {result_file}")
    
    # Generate visualizations
    logger.info("Generating visualizations...")
    viz_outputs = visualize_correlation_results(result_file, output_dir)
    
    logger.info("Generated visualizations:")
    for viz_type, path in viz_outputs.items():
        logger.info(f"  {viz_type}: {path}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("REVIEW-PACKAGING CORRELATION ANALYSIS - TEST RESULTS")
    print("=" * 80)
    print(f"\nCategory: {correlation_result.category}")
    print(f"Products Analyzed: {correlation_result.products_analyzed}")
    print(f"Total Reviews: {correlation_result.total_reviews}")
    print(f"Packaging-Focused Reviews: {correlation_result.packaging_focused_reviews}")
    
    print(f"\n{correlation_result.executive_summary}")
    
    print("\nTop 5 Packaging Attributes by Customer Impact:")
    for ranking in correlation_result.attribute_rankings[:5]:
        attr = ranking.attribute
        impact_icon = "🔺" if "positive" in attr.impact_category else "🔻" if "negative" in attr.impact_category else "➖"
        print(f"  {ranking.rank}. {impact_icon} {attr.attribute_value}")
        print(f"     Correlation: {attr.correlation_score:+.2f}, p={attr.statistical_significance:.3f}")
    
    print("\nKey Findings:")
    for i, finding in enumerate(correlation_result.key_findings, 1):
        print(f"  {i}. {finding}")
    
    print("\n" + "=" * 80)
    print(f"✓ Test complete! See full report at: {viz_outputs['report']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
