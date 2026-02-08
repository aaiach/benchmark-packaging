#!/usr/bin/env python3
"""Test script for competitor packaging scraper.

This script performs a simple test of the competitor scraper with a limited
number of brands to verify the implementation works correctly.
"""
import sys
from pathlib import Path

# Add analysis_engine to path
sys.path.insert(0, str(Path(__file__).parent / 'analysis_engine' / 'src'))

def test_scraper_basic():
    """Test basic scraper functionality."""
    from competitor_scraper import scrape_competitor_packaging
    
    print("=" * 70)
    print("Testing Competitor Packaging Scraper")
    print("=" * 70)
    print("\nTest Configuration:")
    print("  Brands: Alpro, Oatly")
    print("  Category: plant-based milk")
    print("  Countries: Belgium")
    print("  Sources: Google Images only (for quick testing)")
    print("=" * 70)
    
    # Run scraper with limited scope for testing
    try:
        result = scrape_competitor_packaging(
            target_brands=["Alpro", "Oatly"],
            category="plant-based milk",
            countries=["Belgium"],
            enable_amazon=False,  # Disable for quick test
            enable_retailers=False,  # Disable for quick test
            enable_google_images=True,  # Only test Google Images
            job_id="test_run"
        )
        
        print("\n" + "=" * 70)
        print("Test Results")
        print("=" * 70)
        print(f"Status: {result.status}")
        print(f"Job ID: {result.job_id}")
        print(f"Products collected: {result.dataset.total_products}")
        print(f"Images downloaded: {result.dataset.total_images}")
        print(f"Reviews collected: {result.dataset.total_reviews}")
        print(f"Duration: {result.duration_seconds:.1f}s")
        print(f"\nOutput directory: {result.dataset.output_dir}")
        print(f"Metadata file: {result.dataset.metadata_file}")
        print(f"Images directory: {result.dataset.images_dir}")
        
        if result.errors:
            print(f"\n⚠️  Errors: {len(result.errors)}")
            for error in result.errors:
                print(f"  - {error}")
        
        if result.warnings:
            print(f"\n⚠️  Warnings: {len(result.warnings)}")
            for warning in result.warnings[:3]:
                print(f"  - {warning}")
        
        # Validate output
        print("\n" + "=" * 70)
        print("Validation")
        print("=" * 70)
        
        output_dir = Path(result.dataset.output_dir)
        metadata_file = Path(result.dataset.metadata_file)
        images_dir = Path(result.dataset.images_dir)
        
        checks = [
            ("Output directory exists", output_dir.exists()),
            ("Metadata file exists", metadata_file.exists()),
            ("Images directory exists", images_dir.exists()),
            ("Dataset has products", result.dataset.total_products > 0),
        ]
        
        all_passed = True
        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n✅ All checks passed!")
            return 0
        else:
            print("\n❌ Some checks failed")
            return 1
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def test_models():
    """Test data models."""
    from competitor_models import (
        CompetitorProduct,
        PackagingImage,
        ProductReview,
        ProductClaim,
        PricePoint
    )
    from datetime import datetime
    
    print("=" * 70)
    print("Testing Data Models")
    print("=" * 70)
    
    # Create test product
    product = CompetitorProduct(
        brand="Alpro",
        product_name="Alpro Oat Original",
        category="plant-based milk",
        variant="Original",
        package_size="1L"
    )
    
    # Add image
    image = PackagingImage(
        url="https://example.com/image.jpg",
        view="front",
        resolution="1200x800",
        source="google_images",
        downloaded_at=datetime.utcnow()
    )
    product.images.append(image)
    
    # Add claim
    claim = ProductClaim(
        claim_text="100% Plant-Based",
        claim_type="category",
        prominence="primary"
    )
    product.claims.append(claim)
    
    # Add review
    review = ProductReview(
        rating=4.5,
        title="Great taste",
        text="Really smooth and delicious",
        source="amazon"
    )
    product.reviews.append(review)
    
    # Add price
    price = PricePoint(
        price=2.99,
        currency="EUR",
        retailer="Carrefour"
    )
    product.prices.append(price)
    
    # Validate
    print("✓ Created CompetitorProduct")
    print(f"  - Brand: {product.brand}")
    print(f"  - Images: {len(product.images)}")
    print(f"  - Claims: {len(product.claims)}")
    print(f"  - Reviews: {len(product.reviews)}")
    print(f"  - Prices: {len(product.prices)}")
    
    # Test serialization
    data = product.model_dump()
    print(f"✓ Serialized to dict ({len(data)} keys)")
    
    # Test JSON serialization
    import json
    json_str = product.model_dump_json()
    print(f"✓ Serialized to JSON ({len(json_str)} bytes)")
    
    print("\n✅ Model tests passed!")
    return 0


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Competitor Scraper Test Suite")
    print("=" * 70 + "\n")
    
    # Test 1: Data models
    print("Test 1: Data Models")
    print("-" * 70)
    result1 = test_models()
    
    print("\n" + "=" * 70 + "\n")
    
    # Test 2: Basic scraper
    print("Test 2: Basic Scraper Functionality")
    print("-" * 70)
    result2 = test_scraper_basic()
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Data Models: {'✅ PASSED' if result1 == 0 else '❌ FAILED'}")
    print(f"Basic Scraper: {'✅ PASSED' if result2 == 0 else '❌ FAILED'}")
    print("=" * 70 + "\n")
    
    sys.exit(max(result1, result2))
