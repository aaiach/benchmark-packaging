"""Competitive analysis module using Gemini for POD/POP extraction.

This module analyzes the visual analysis JSON to:
- Extract top 5 Points-of-Difference (PODs) for radar charts
- Extract top 5 Points-of-Parity (POPs) for comparison matrices
- Score each product on each axis
- Generate strategic insights

Output is formatted for frontend React consumption (BCG-style presentation).
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types

from .config import get_config, DiscoveryConfig
from .models import (
    CompetitiveAnalysisResult,
    PointOfDifference,
    PointOfParity,
    ProductCompetitiveProfile,
    ProductPODScore,
    ProductPOPStatus,
    StrategicInsight,
)
from .utils import load_prompt


# =============================================================================
# Helper Functions
# =============================================================================

def format_product_for_prompt(product_data: Dict[str, Any]) -> str:
    """Format a single product's analysis data for the prompt.
    
    Extracts the most relevant information for competitive analysis.
    """
    brand = product_data.get('brand', 'Unknown')
    product_name = product_data.get('product_name', 'Unknown Product')
    analysis = product_data.get('analysis', {})
    
    if not analysis:
        return f"### {brand} - {product_name}\n[Analyse non disponible]\n"
    
    # Extract key data
    visual_anchor = analysis.get('visual_anchor', 'N/A')
    hierarchy_score = analysis.get('hierarchy_clarity_score', 'N/A')
    
    # Eye tracking
    eye_tracking = analysis.get('eye_tracking', {})
    pattern_type = eye_tracking.get('pattern_type', 'N/A')
    
    # Chromatic mapping
    chromatic = analysis.get('chromatic_mapping', {})
    surface_finish = chromatic.get('surface_finish', 'N/A')
    color_harmony = chromatic.get('color_harmony', 'N/A')
    color_psychology = chromatic.get('color_psychology_notes', 'N/A')
    
    # Color palette summary
    colors = chromatic.get('color_palette', [])
    color_summary = ", ".join([c.get('color_name', '') for c in colors[:4]])
    
    # Textual inventory
    textual = analysis.get('textual_inventory', {})
    claims = textual.get('claims_summary', [])
    emphasized = textual.get('emphasized_claims', [])
    typography_consistency = textual.get('typography_consistency', 'N/A')
    
    # Asset symbolism
    assets = analysis.get('asset_symbolism', {})
    trust_marks = assets.get('trust_marks', [])
    trust_names = [tm.get('name', '') for tm in trust_marks]
    storytelling = assets.get('visual_storytelling_elements', [])
    photo_ratio = assets.get('photography_vs_illustration_ratio', 'N/A')
    
    # Format output
    output = f"""### {brand} - {product_name}

**Visual Identity:**
- Anchor visuelle: {visual_anchor}
- Pattern oculaire: {pattern_type}
- Score clarté: {hierarchy_score}/10
- Finition: {surface_finish}
- Harmonie couleurs: {color_harmony}
- Palette: {color_summary}

**Claims & Messages:**
- Claims: {', '.join(claims) if claims else 'Aucun'}
- Claims mis en avant: {', '.join(emphasized) if emphasized else 'Aucun'}
- Cohérence typo: {typography_consistency}

**Confiance & Certification:**
- Certifications: {', '.join(trust_names) if trust_names else 'Aucune'}
- Storytelling: {', '.join(storytelling) if storytelling else 'N/A'}
- Ratio photo/illus: {photo_ratio}

**Psychologie couleur:**
{color_psychology}

---
"""
    return output


def load_visual_analysis(output_dir: Path, run_id: str) -> Optional[List[Dict[str, Any]]]:
    """Load the visual analysis JSON for a run."""
    analysis_dir = output_dir / "analysis"
    pattern = f"*_visual_analysis_{run_id}.json"
    matches = list(analysis_dir.glob(pattern))
    
    if not matches:
        return None
    
    with open(matches[0], 'r', encoding='utf-8') as f:
        return json.load(f)


# =============================================================================
# Main CompetitiveAnalyzer Class
# =============================================================================

class CompetitiveAnalyzer:
    """Analyzes visual analysis data to extract competitive insights.
    
    Uses Gemini to:
    - Identify Points-of-Difference (PODs) for radar charts
    - Identify Points-of-Parity (POPs) for comparison matrices
    - Score products and generate strategic insights
    """
    
    def __init__(self, config: Optional[DiscoveryConfig] = None):
        """Initialize the competitive analyzer.
        
        Args:
            config: Optional configuration. Uses global config if not provided.
        """
        self.config = config or get_config()
        
        # Initialize Google GenAI client (text-only, no vision needed)
        self.client = genai.Client(api_key=self.config.gemini.api_key)
        self.model = self.config.gemini.model
        
        # Load prompts
        self.system_prompt = load_prompt("competitive_analysis_system.txt")
        self.user_prompt_template = load_prompt("competitive_analysis_user.txt")
        
        print(f"[CompetitiveAnalyzer] Initialized with {self.model}")
    
    def analyze(
        self,
        products_analysis: List[Dict[str, Any]],
        category: str
    ) -> Optional[CompetitiveAnalysisResult]:
        """Perform competitive analysis on a set of products.
        
        Args:
            products_analysis: List of product analysis dicts from visual analysis
            category: Product category name
            
        Returns:
            CompetitiveAnalysisResult or None if failed
        """
        # Filter to successful analyses only
        valid_products = [p for p in products_analysis if p.get('analysis_success')]
        
        if len(valid_products) < 2:
            print("[!] Need at least 2 products with successful analysis")
            return None
        
        # Format products data for prompt
        products_text = "\n".join([
            format_product_for_prompt(p) for p in valid_products
        ])
        
        # Build user prompt
        user_prompt = self.user_prompt_template.format(
            product_count=len(valid_products),
            category=category,
            products_data=products_text
        )
        
        # Combine prompts
        full_prompt = f"{self.system_prompt}\n\n---\n\n{user_prompt}"
        
        try:
            # Call Gemini with structured output
            response = self.client.models.generate_content(
                model=self.model,
                contents=[full_prompt],
                config=types.GenerateContentConfig(
                    temperature=self.config.gemini.temperature,
                    response_mime_type='application/json',
                    response_schema=CompetitiveAnalysisResult,
                ),
            )
            
            # Parse the response
            if response.parsed:
                return response.parsed
            
            # Fallback: try to parse from text
            if response.text:
                data = json.loads(response.text)
                return CompetitiveAnalysisResult(**data)
            
            print("    [!] Empty response from model")
            return None
            
        except Exception as e:
            print(f"    [!] Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run(
        self,
        run_id: str
    ) -> Optional[Path]:
        """Run competitive analysis and save results.
        
        Args:
            run_id: Run identifier (timestamp)
            
        Returns:
            Path to the output JSON file or None if failed
        """
        output_dir = Path(self.config.output_dir)
        
        # Load visual analysis data
        products_analysis = load_visual_analysis(output_dir, run_id)
        
        if not products_analysis:
            print(f"[!] No visual analysis found for run_id: {run_id}")
            print("    Run steps 5-6 first to generate visual analysis.")
            return None
        
        # Get category from first product or file name
        category = products_analysis[0].get('category', 'Unknown Category')
        
        # Find category slug
        analysis_dir = output_dir / "analysis"
        pattern = f"*_visual_analysis_{run_id}.json"
        matches = list(analysis_dir.glob(pattern))
        category_slug = matches[0].stem.replace(f"_visual_analysis_{run_id}", "") if matches else "unknown"
        
        print("=" * 70)
        print(f"COMPETITIVE ANALYSIS - Run: {run_id}")
        print(f"  Category: {category}")
        print(f"  Products: {len(products_analysis)}")
        print(f"  Model: {self.model}")
        print("=" * 70)
        
        # Run analysis
        print("\n[CompetitiveAnalyzer] Extracting PODs and POPs...")
        result = self.analyze(products_analysis, category)
        
        if not result:
            print("[!] Competitive analysis failed")
            return None
        
        # Update result with metadata
        result.category = category
        result.analysis_date = datetime.now().isoformat()
        result.product_count = len([p for p in products_analysis if p.get('analysis_success')])
        
        # Add image paths to product profiles
        product_map = {p.get('brand', ''): p for p in products_analysis}
        for profile in result.products:
            if profile.brand in product_map:
                profile.image_path = product_map[profile.brand].get('image_path')
        
        # Save results
        output_file = analysis_dir / f"{category_slug}_competitive_analysis_{run_id}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "-" * 70)
        print("[✓] Analysis complete!")
        print("\n📊 Points-of-Difference (Radar Chart Axes):")
        for i, pod in enumerate(result.points_of_difference, 1):
            print(f"  {i}. {pod.axis_name}: {pod.description[:60]}...")
        
        print("\n✓ Points-of-Parity (Matrix Attributes):")
        for i, pop in enumerate(result.points_of_parity, 1):
            print(f"  {i}. {pop.pop_name} ({pop.pop_type})")
        
        print("\n💡 Strategic Insights:")
        for insight in result.strategic_insights[:3]:
            print(f"  • {insight.title}")
        
        print("\n" + "-" * 70)
        print(f"[✓] Output saved: {output_file}")
        
        return output_file


# =============================================================================
# Convenience Functions
# =============================================================================

def run_competitive_analysis(run_id: str) -> Optional[Path]:
    """Convenience function to run competitive analysis.
    
    Args:
        run_id: Run identifier (timestamp)
        
    Returns:
        Path to output JSON file or None
    """
    analyzer = CompetitiveAnalyzer()
    return analyzer.run(run_id=run_id)
