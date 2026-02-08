"""Structure validation tests for OCR pipeline (no API calls)."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all OCR modules can be imported."""
    print("[Test] Validating imports...")
    
    try:
        from src import models
        print("  ✓ models imported")
        
        from src import ocr_analyzer
        print("  ✓ ocr_analyzer imported")
        
        from src.pipeline import steps
        print("  ✓ pipeline.steps imported")
        
        # Check OCR models exist
        assert hasattr(models, 'OCRResult'), "OCRResult model not found"
        assert hasattr(models, 'BrandIdentity'), "BrandIdentity model not found"
        assert hasattr(models, 'ProductClaim'), "ProductClaim model not found"
        assert hasattr(models, 'NutritionalInformation'), "NutritionalInformation model not found"
        assert hasattr(models, 'Certification'), "Certification model not found"
        assert hasattr(models, 'RegulatoryMention'), "RegulatoryMention model not found"
        assert hasattr(models, 'VisualCodes'), "VisualCodes model not found"
        print("  ✓ All OCR models present")
        
        # Check OCR analyzer class exists
        assert hasattr(ocr_analyzer, 'OCRAnalyzer'), "OCRAnalyzer class not found"
        assert hasattr(ocr_analyzer, 'analyze_images_for_run'), "analyze_images_for_run function not found"
        assert hasattr(ocr_analyzer, 'analyze_single_image'), "analyze_single_image function not found"
        print("  ✓ OCR analyzer functions present")
        
        # Check Step 8 exists
        assert hasattr(steps, 'execute_step_8_ocr'), "execute_step_8_ocr not found"
        step_8 = steps.get_step(8)
        assert step_8 is not None, "Step 8 not registered"
        assert step_8.name == 'ocr', f"Step 8 name is '{step_8.name}', expected 'ocr'"
        print("  ✓ Step 8 registered in pipeline")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompts():
    """Test that OCR prompts exist and can be loaded."""
    print("\n[Test] Validating prompts...")
    
    try:
        prompts_dir = Path(__file__).parent / "src" / "prompts"
        
        system_prompt = prompts_dir / "ocr_extraction_system.txt"
        user_prompt = prompts_dir / "ocr_extraction_user.txt"
        
        assert system_prompt.exists(), f"System prompt not found: {system_prompt}"
        print(f"  ✓ System prompt exists ({system_prompt.stat().st_size} bytes)")
        
        assert user_prompt.exists(), f"User prompt not found: {user_prompt}"
        print(f"  ✓ User prompt exists ({user_prompt.stat().st_size} bytes)")
        
        # Check system prompt content
        with open(system_prompt, 'r') as f:
            content = f.read()
            assert 'Brand Identity' in content, "Brand Identity section missing"
            assert 'Product Claims' in content, "Product Claims section missing"
            assert 'Nutritional Information' in content, "Nutritional Information section missing"
            assert 'Certifications' in content, "Certifications section missing"
            assert 'Regulatory Mentions' in content, "Regulatory Mentions section missing"
            assert 'Visual Codes' in content, "Visual Codes section missing"
            print("  ✓ System prompt contains all required sections")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Prompt validation failed: {e}")
        return False


def test_model_structure():
    """Test that OCR models have expected fields."""
    print("\n[Test] Validating model structures...")
    
    try:
        from src.models import OCRResult, BrandIdentity, ProductClaim, Certification
        
        # Check OCRResult fields
        ocr_fields = set(OCRResult.model_fields.keys())
        expected_fields = {
            'image_path', 'brand', 'product_name', 'analysis_timestamp',
            'brand_identity', 'product_claims', 'nutritional_info',
            'certifications', 'regulatory_mentions', 'visual_codes',
            'detected_languages', 'all_text_raw', 'extraction_confidence', 'notes'
        }
        assert expected_fields.issubset(ocr_fields), f"Missing fields: {expected_fields - ocr_fields}"
        print("  ✓ OCRResult has all required fields")
        
        # Check BrandIdentity fields
        brand_fields = set(BrandIdentity.model_fields.keys())
        assert 'brand_name' in brand_fields, "BrandIdentity missing brand_name"
        assert 'slogan' in brand_fields, "BrandIdentity missing slogan"
        print("  ✓ BrandIdentity structure valid")
        
        # Check ProductClaim fields
        claim_fields = set(ProductClaim.model_fields.keys())
        assert 'claim_text' in claim_fields, "ProductClaim missing claim_text"
        assert 'claim_type' in claim_fields, "ProductClaim missing claim_type"
        print("  ✓ ProductClaim structure valid")
        
        # Check Certification fields
        cert_fields = set(Certification.model_fields.keys())
        assert 'name' in cert_fields, "Certification missing name"
        assert 'certification_type' in cert_fields, "Certification missing certification_type"
        print("  ✓ Certification structure valid")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Model validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_integration():
    """Test that Step 8 is properly integrated."""
    print("\n[Test] Validating pipeline integration...")
    
    try:
        from src.pipeline.steps import STEPS, list_steps
        
        # Check Step 8 is in STEPS dict
        assert 8 in STEPS, "Step 8 not in STEPS dictionary"
        print("  ✓ Step 8 in STEPS dictionary")
        
        # Check step properties
        step_8 = STEPS[8]
        assert step_8.number == 8, f"Step number is {step_8.number}, expected 8"
        assert step_8.name == 'ocr', f"Step name is '{step_8.name}', expected 'ocr'"
        assert step_8.description, "Step description is empty"
        assert step_8.output_pattern, "Step output_pattern is empty"
        assert step_8.executor is not None, "Step executor is None"
        print("  ✓ Step 8 properties valid")
        
        # Check dependencies
        assert 4 in step_8.requires, "Step 8 should require step 4 (images)"
        print(f"  ✓ Step 8 dependencies: {step_8.requires}")
        
        # Check list_steps includes step 8
        all_steps = list_steps()
        step_8_info = next((s for s in all_steps if s['number'] == 8), None)
        assert step_8_info is not None, "Step 8 not in list_steps() output"
        print("  ✓ Step 8 appears in list_steps()")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Pipeline integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("="*80)
    print("OCR Pipeline Structure Validation")
    print("="*80)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Prompts", test_prompts()))
    results.append(("Models", test_model_structure()))
    results.append(("Pipeline", test_pipeline_integration()))
    
    print("\n" + "="*80)
    print("Test Results Summary")
    print("="*80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("="*80)
    
    if all_passed:
        print("\n✓ All validation tests passed!")
        print("\nNext steps:")
        print("  1. Set up API keys in .env file (see .env.example)")
        print("  2. Run: uv run python test_ocr.py")
        print("  3. Or run on existing pipeline: python main.py --run-id <run_id> --steps 8")
        return 0
    else:
        print("\n✗ Some validation tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
