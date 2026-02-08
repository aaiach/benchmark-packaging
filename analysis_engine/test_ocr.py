"""Test script for OCR pipeline with existing images."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ocr_analyzer import analyze_single_image
from config import get_config

def test_ocr_on_sample_images():
    """Test OCR extraction on sample oat milk packaging images."""
    
    # Path to sample images
    images_dir = Path("/workspace/frontend/public/images/lait_davoine")
    
    if not images_dir.exists():
        print(f"[!] Images directory not found: {images_dir}")
        return
    
    # Get a few sample images
    image_files = sorted(images_dir.glob("*.png"))[:3]  # Test on first 3 images
    image_files.extend(sorted(images_dir.glob("*.jpg"))[:2])  # Add 2 jpg files
    
    if not image_files:
        print(f"[!] No images found in {images_dir}")
        return
    
    print(f"[Test] Found {len(image_files)} sample images")
    print(f"[Test] Testing OCR extraction on {len(image_files)} images...")
    print(f"{'='*80}\n")
    
    # Create output directory
    output_dir = Path("/workspace/analysis_engine/output/test_ocr")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get config
    config = get_config()
    
    # Test each image
    for i, image_path in enumerate(image_files, 1):
        print(f"\n[Test {i}/{len(image_files)}] Processing: {image_path.name}")
        print("-" * 80)
        
        # Extract brand name from filename (e.g., "01_bjorg_8ec5db.png" -> "Bjorg")
        parts = image_path.stem.split('_')
        brand_name = parts[1].title() if len(parts) > 1 else "Unknown"
        
        # Run OCR analysis
        try:
            result = analyze_single_image(
                image_path=image_path,
                category="lait d'avoine",
                brand=brand_name,
                product_name=f"{brand_name} Oat Milk",
                output_path=output_dir / f"{image_path.stem}_ocr.json",
                config=config
            )
            
            # Print summary
            print(f"\n[Results for {brand_name}]")
            print(f"  Brand: {result.brand_identity.brand_name}")
            if result.brand_identity.slogan:
                print(f"  Slogan: {result.brand_identity.slogan}")
            print(f"  Claims: {len(result.product_claims)}")
            for claim in result.product_claims[:3]:  # Show first 3 claims
                print(f"    - [{claim.claim_type}] {claim.claim_text}")
            print(f"  Certifications: {len(result.certifications)}")
            for cert in result.certifications:
                print(f"    - {cert.name} ({cert.certification_type})")
            print(f"  Languages: {', '.join(result.detected_languages)}")
            print(f"  Dominant colors: {', '.join(result.visual_codes.dominant_colors[:3])}")
            print(f"  Typography: {result.visual_codes.typography_style}")
            print(f"  Confidence: {result.extraction_confidence:.2f}")
            
        except Exception as e:
            print(f"[ERROR] Failed to process {image_path.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print(f"[Test] Complete! Results saved to: {output_dir}")
    print(f"[Test] Check JSON files for full structured output")

if __name__ == "__main__":
    test_ocr_on_sample_images()
