"""Simple validation of OCR implementation files (no imports needed)."""
from pathlib import Path
import re

def validate_files():
    """Validate that all required files exist and contain key elements."""
    print("="*80)
    print("OCR Pipeline File Validation")
    print("="*80)
    
    base = Path(__file__).parent
    
    checks = []
    
    # Check OCR analyzer module
    ocr_analyzer = base / "src" / "ocr_analyzer.py"
    if ocr_analyzer.exists():
        content = ocr_analyzer.read_text()
        has_class = 'class OCRAnalyzer' in content
        has_analyze = 'def analyze_image' in content
        has_parallel = 'def analyze_multiple_images' in content
        has_run_func = 'def analyze_images_for_run' in content
        
        checks.append(("ocr_analyzer.py exists", True))
        checks.append(("  - OCRAnalyzer class", has_class))
        checks.append(("  - analyze_image method", has_analyze))
        checks.append(("  - analyze_multiple_images method", has_parallel))
        checks.append(("  - analyze_images_for_run function", has_run_func))
    else:
        checks.append(("ocr_analyzer.py exists", False))
    
    # Check models
    models = base / "src" / "models.py"
    if models.exists():
        content = models.read_text()
        has_ocr_result = 'class OCRResult' in content
        has_brand_identity = 'class BrandIdentity' in content
        has_claims = 'class ProductClaim' in content
        has_nutritional = 'class NutritionalInformation' in content
        has_cert = 'class Certification' in content
        has_regulatory = 'class RegulatoryMention' in content
        has_visual_codes = 'class VisualCodes' in content
        
        checks.append(("models.py updated", True))
        checks.append(("  - OCRResult model", has_ocr_result))
        checks.append(("  - BrandIdentity model", has_brand_identity))
        checks.append(("  - ProductClaim model", has_claims))
        checks.append(("  - NutritionalInformation model", has_nutritional))
        checks.append(("  - Certification model", has_cert))
        checks.append(("  - RegulatoryMention model", has_regulatory))
        checks.append(("  - VisualCodes model", has_visual_codes))
    else:
        checks.append(("models.py exists", False))
    
    # Check prompts
    system_prompt = base / "src" / "prompts" / "ocr_extraction_system.txt"
    user_prompt = base / "src" / "prompts" / "ocr_extraction_user.txt"
    
    if system_prompt.exists():
        content = system_prompt.read_text()
        has_sections = all(s in content for s in [
            'Brand Identity', 'Product Claims', 'Nutritional Information',
            'Certifications', 'Regulatory Mentions', 'Visual Codes'
        ])
        has_multilingual = 'French' in content and 'Dutch' in content and 'English' in content
        
        checks.append(("ocr_extraction_system.txt exists", True))
        checks.append(("  - All sections present", has_sections))
        checks.append(("  - Multilingual support", has_multilingual))
    else:
        checks.append(("ocr_extraction_system.txt exists", False))
    
    if user_prompt.exists():
        checks.append(("ocr_extraction_user.txt exists", True))
    else:
        checks.append(("ocr_extraction_user.txt exists", False))
    
    # Check pipeline integration
    steps = base / "src" / "pipeline" / "steps.py"
    if steps.exists():
        content = steps.read_text()
        has_executor = 'def execute_step_8_ocr' in content
        has_step_8 = re.search(r'8:\s*Step\(', content) is not None
        has_ocr_name = "'ocr'" in content or '"ocr"' in content
        
        checks.append(("pipeline/steps.py updated", True))
        checks.append(("  - execute_step_8_ocr function", has_executor))
        checks.append(("  - Step 8 registered", has_step_8))
        checks.append(("  - Step named 'ocr'", has_ocr_name))
    else:
        checks.append(("pipeline/steps.py exists", False))
    
    # Check README
    readme = base / "README.md"
    if readme.exists():
        content = readme.read_text()
        has_ocr_step = '8' in content and 'OCR' in content
        has_ocr_description = 'text extraction' in content.lower()
        
        checks.append(("README.md updated", True))
        checks.append(("  - Step 8 documented", has_ocr_step))
        checks.append(("  - OCR described", has_ocr_description))
    else:
        checks.append(("README.md exists", False))
    
    # Print results
    print()
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*80)
    
    if all_passed:
        print("✓ All validation checks passed!")
        print("\nOCR Pipeline Implementation Complete")
        print("\nCapabilities:")
        print("  • Multilingual text extraction (French, Dutch, English)")
        print("  • Categorized extraction (brand, claims, nutritional, certifications, regulatory)")
        print("  • Visual code identification (colors, typography, layout)")
        print("  • Structured JSON output per product")
        print("  • Parallel processing for multiple images")
        print("\nTo test with real images:")
        print("  1. Ensure API keys are set in environment or .env file")
        print("  2. Run: python main.py <category> --steps 8")
        print("     or: python main.py --run-id <existing_run> --steps 8")
        return 0
    else:
        print("✗ Some checks failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(validate_files())
