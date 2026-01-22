"""Competitive analysis module using Gemini for POD/POP extraction.

This module analyzes the visual analysis JSON to:
- Extract top 5 Points-of-Difference (PODs) for radar charts
- Extract top 5 Points-of-Parity (POPs) for comparison matrices
- Score each product on each axis (individually for quality)
- Generate strategic insights

Output is formatted for frontend React consumption (BCG-style presentation).

Architecture (3-phase approach for quality):
- Phase 1 (1 call): Identify PODs and POPs for the category
- Phase 2 (N calls): Score each product individually on established axes
- Phase 3 (1 call): Generate strategic insights from complete data

Uses LangChain's ChatGoogleGenerativeAI with structured output for reliable parsing.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from .config import get_config, DiscoveryConfig
from .models import (
    CompetitiveAnalysisResult,
    PointOfDifference,
    PointOfParity,
    ProductCompetitiveProfile,
    ProductPODScore,
    ProductPOPStatus,
    StrategicInsight,
    # Intermediate models
    CategoryAxesResult,
    SingleProductProfile,
    StrategicInsightsResult,
)
from .utils import load_prompt
from .parallel_executor import (
    ParallelExecutor,
    Provider,
    ProviderLimits,
)


# =============================================================================
# Helper Functions
# =============================================================================

def format_product_summary(product_data: Dict[str, Any]) -> str:
    """Format a concise product summary for Phase 1 (axis identification).
    
    Provides enough context to identify differentiating axes without overwhelming detail.
    """
    brand = product_data.get('brand', 'Unknown')
    product_name = product_data.get('product_name', 'Unknown Product')
    analysis = product_data.get('analysis', {})
    
    if not analysis:
        return f"### {brand} - {product_name}\n[Analyse non disponible]\n"
    
    # Key visual identity
    visual_anchor = analysis.get('visual_anchor', 'N/A')
    hierarchy_score = analysis.get('hierarchy_clarity_score', 'N/A')
    
    # Eye tracking
    eye_tracking = analysis.get('eye_tracking', {})
    pattern_type = eye_tracking.get('pattern_type', 'N/A')
    
    # Chromatic mapping
    chromatic = analysis.get('chromatic_mapping', {})
    surface_finish = chromatic.get('surface_finish', 'N/A')
    color_harmony = chromatic.get('color_harmony', 'N/A')
    colors = chromatic.get('color_palette', [])
    color_summary = ", ".join([c.get('color_name', '') for c in colors[:3]])
    
    # Textual inventory
    textual = analysis.get('textual_inventory', {})
    claims = textual.get('claims_summary', [])
    
    # Asset symbolism
    assets = analysis.get('asset_symbolism', {})
    trust_marks = assets.get('trust_marks', [])
    trust_names = [tm.get('name', '') for tm in trust_marks]
    photo_ratio = assets.get('photography_vs_illustration_ratio', 'N/A')
    
    return f"""### {brand} - {product_name}
- Anchor: {visual_anchor}
- Pattern: {pattern_type} | Clarté: {hierarchy_score}/10
- Finition: {surface_finish} | Harmonie: {color_harmony}
- Couleurs: {color_summary}
- Claims: {', '.join(claims[:3]) if claims else 'Aucun'}
- Certifications: {', '.join(trust_names) if trust_names else 'Aucune'}
- Photo/Illus: {photo_ratio}
---
"""


def format_product_full_analysis(product_data: Dict[str, Any]) -> str:
    """Format a detailed product analysis for Phase 2 (individual scoring).
    
    Provides comprehensive detail for accurate scoring.
    """
    brand = product_data.get('brand', 'Unknown')
    product_name = product_data.get('product_name', 'Unknown Product')
    analysis = product_data.get('analysis', {})
    
    if not analysis:
        return f"### {brand} - {product_name}\n[Analyse non disponible]\n"
    
    # Extract key data
    visual_anchor = analysis.get('visual_anchor', 'N/A')
    visual_anchor_desc = analysis.get('visual_anchor_description', 'N/A')
    hierarchy_score = analysis.get('hierarchy_clarity_score', 'N/A')
    detailed_analysis = analysis.get('detailed_analysis', 'N/A')
    
    # Eye tracking
    eye_tracking = analysis.get('eye_tracking', {})
    pattern_type = eye_tracking.get('pattern_type', 'N/A')
    entry_point = eye_tracking.get('entry_point', 'N/A')
    fixation_sequence = eye_tracking.get('fixation_sequence', [])
    dwell_zones = eye_tracking.get('dwell_zones', [])
    
    # Massing
    massing = analysis.get('massing', {})
    balance_type = massing.get('balance_type', 'N/A')
    dense_zones = massing.get('dense_zones', [])
    
    # Chromatic mapping
    chromatic = analysis.get('chromatic_mapping', {})
    surface_finish = chromatic.get('surface_finish', 'N/A')
    surface_finish_desc = chromatic.get('surface_finish_description', 'N/A')
    color_harmony = chromatic.get('color_harmony', 'N/A')
    color_psychology = chromatic.get('color_psychology_notes', 'N/A')
    colors = chromatic.get('color_palette', [])
    
    # Textual inventory
    textual = analysis.get('textual_inventory', {})
    claims = textual.get('claims_summary', [])
    emphasized = textual.get('emphasized_claims', [])
    typography_consistency = textual.get('typography_consistency', 'N/A')
    readability = textual.get('readability_assessment', 'N/A')
    brand_typo = textual.get('brand_name_typography', 'N/A')
    
    # Asset symbolism
    assets = analysis.get('asset_symbolism', {})
    trust_marks = assets.get('trust_marks', [])
    graphical_assets = assets.get('graphical_assets', [])
    storytelling = assets.get('visual_storytelling_elements', [])
    photo_ratio = assets.get('photography_vs_illustration_ratio', 'N/A')
    trust_effectiveness = assets.get('trust_signal_effectiveness', 'N/A')

    # Format colors
    colors_text = "\n".join([
        f"  - {c.get('color_name', 'N/A')} ({c.get('hex_code', 'N/A')}): {c.get('usage', 'N/A')}"
        for c in colors[:5]
    ])
    
    # Format trust marks
    trust_text = "\n".join([
        f"  - {tm.get('name', 'N/A')} ({tm.get('mark_type', 'N/A')}): {tm.get('prominence', 'N/A')}"
        for tm in trust_marks
    ]) if trust_marks else "  Aucune certification visible"
    
    return f"""## {brand} - {product_name}

### SECTION 1: Hiérarchie Visuelle
- **Ancre visuelle**: {visual_anchor}
- **Justification ancre**: {visual_anchor_desc}
- **Score clarté hiérarchie**: {hierarchy_score}/10
- **Pattern oculaire**: {pattern_type}
- **Point d'entrée**: {entry_point}
- **Séquence de fixation**: {' → '.join(fixation_sequence) if fixation_sequence else 'N/A'}
- **Zones de pause**: {', '.join(dwell_zones) if dwell_zones else 'N/A'}
- **Type de balance**: {balance_type}
- **Zones denses**: {', '.join(dense_zones) if dense_zones else 'N/A'}

### SECTION 2: Mapping Chromatique
- **Finition de surface**: {surface_finish}
- **Description finition**: {surface_finish_desc}
- **Harmonie couleurs**: {color_harmony}
- **Psychologie couleurs**: {color_psychology}
- **Palette**:
{colors_text}

### SECTION 3: Inventaire Textuel
- **Typographie marque**: {brand_typo}
- **Cohérence typo**: {typography_consistency}
- **Lisibilité**: {readability}
- **Claims marketing**: {', '.join(claims) if claims else 'Aucun'}
- **Claims mis en avant**: {', '.join(emphasized) if emphasized else 'Aucun'}

### SECTION 4: Symbolisme & Confiance
- **Ratio photo/illustration**: {photo_ratio}
- **Éléments storytelling**: {', '.join(storytelling) if storytelling else 'N/A'}
- **Efficacité signaux de confiance**: {trust_effectiveness}
- **Certifications et badges**:
{trust_text}

### Analyse détaillée
{detailed_analysis[:500] if detailed_analysis else 'N/A'}...
"""


def format_pods_for_scoring(pods: List[PointOfDifference]) -> str:
    """Format PODs for the Phase 2 scoring prompt."""
    lines = []
    for pod in pods:
        indicators = ", ".join(pod.high_score_indicators[:3])
        lines.append(f"""
**{pod.axis_id}** - {pod.axis_name}
  Description: {pod.description}
  Score élevé si: {indicators}
""")
    return "\n".join(lines)


def format_pops_for_checking(pops: List[PointOfParity]) -> str:
    """Format POPs for the Phase 2 checking prompt."""
    lines = []
    for pop in pops:
        lines.append(f"""
**{pop.pop_id}** - {pop.pop_name}
  Type: {pop.pop_type}
  Description: {pop.description}
""")
    return "\n".join(lines)


def format_pods_summary(pods: List[PointOfDifference]) -> str:
    """Format PODs summary for Phase 3."""
    lines = []
    for i, pod in enumerate(pods, 1):
        lines.append(f"{i}. **{pod.axis_name}** ({pod.axis_id}): {pod.description}")
    return "\n".join(lines)


def format_pops_summary(pops: List[PointOfParity]) -> str:
    """Format POPs summary for Phase 3."""
    lines = []
    for i, pop in enumerate(pops, 1):
        lines.append(f"{i}. **{pop.pop_name}** ({pop.pop_type}): {pop.description}")
    return "\n".join(lines)


def format_products_scores(products: List[ProductCompetitiveProfile], pods: List[PointOfDifference]) -> str:
    """Format all products scores for Phase 3 insights."""
    lines = []
    for product in products:
        lines.append(f"\n### {product.brand} - {product.product_name}")
        lines.append(f"Positionnement: {product.positioning_summary}")
        lines.append(f"Différenciateur clé: {product.key_differentiator}")
        lines.append("Scores POD:")
        for score in product.pod_scores:
            # Find axis name
            axis_name = next((p.axis_name for p in pods if p.axis_id == score.axis_id), score.axis_id)
            lines.append(f"  - {axis_name}: {score.score}/10 ({score.reasoning[:50]}...)")
        lines.append("POPs présents:")
        present_pops = [s.pop_id for s in product.pop_status if s.has_attribute]
        lines.append(f"  {', '.join(present_pops) if present_pops else 'Aucun'}")
    return "\n".join(lines)


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
    
    Uses a 3-phase approach for high-quality per-product analysis:
    - Phase 1: Identify PODs and POPs for the category (1 call)
    - Phase 2: Score each product individually (N calls)
    - Phase 3: Generate strategic insights (1 call)
    
    Total: N+2 LLM calls for N products.
    """
    
    def __init__(self, config: Optional[DiscoveryConfig] = None):
        """Initialize the competitive analyzer.
        
        Args:
            config: Optional configuration. Uses global config if not provided.
        """
        self.config = config or get_config()
        self.model = self.config.gemini.model
        
        # Initialize base LLM
        self._llm = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=self.config.gemini.api_key,
            temperature=self.config.gemini.temperature,
        )
        
        # Create structured output chains for each phase
        self._phase1_llm = self._llm.with_structured_output(CategoryAxesResult)
        self._phase2_llm = self._llm.with_structured_output(SingleProductProfile)
        self._phase3_llm = self._llm.with_structured_output(StrategicInsightsResult)
        
        # Load prompts for all phases
        self._phase1_system = load_prompt("competitive_phase1_system.txt")
        self._phase1_user = load_prompt("competitive_phase1_user.txt")
        self._phase2_system = load_prompt("competitive_phase2_system.txt")
        self._phase2_user = load_prompt("competitive_phase2_user.txt")
        self._phase3_system = load_prompt("competitive_phase3_system.txt")
        self._phase3_user = load_prompt("competitive_phase3_user.txt")
        
        print(f"[CompetitiveAnalyzer] Initialized with {self.model}")
        print(f"  Architecture: 3-phase (N+2 calls for quality)")
    
    def _phase1_identify_axes(
        self,
        products_analysis: List[Dict[str, Any]],
        category: str
    ) -> Optional[CategoryAxesResult]:
        """Phase 1: Identify PODs and POPs for the category.
        
        Analyzes all products together to identify differentiating axes.
        
        Args:
            products_analysis: List of product analysis dicts
            category: Product category name
            
        Returns:
            CategoryAxesResult with PODs and POPs, or None if failed
        """
        print(f"  [Phase 1] Identifying PODs and POPs for {len(products_analysis)} products...")
        
        # Format concise summaries for axis identification
        products_summary = "\n".join([
            format_product_summary(p) for p in products_analysis
        ])
        
        user_prompt = self._phase1_user.format(
            product_count=len(products_analysis),
            category=category,
            products_summary=products_summary
        )
        
        try:
            messages = [
                SystemMessage(content=self._phase1_system),
                HumanMessage(content=user_prompt)
            ]
            
            result = self._phase1_llm.invoke(messages)
            
            print(f"    [✓] Identified {len(result.points_of_difference)} PODs and {len(result.points_of_parity)} POPs")
            return result
            
        except Exception as e:
            print(f"    [!] Phase 1 error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _phase2_score_product(
        self,
        product_data: Dict[str, Any],
        pods: List[PointOfDifference],
        pops: List[PointOfParity],
        category: str
    ) -> Optional[SingleProductProfile]:
        """Phase 2: Score a single product on established axes.
        
        Provides focused analysis for quality scoring.
        
        Args:
            product_data: Single product analysis dict
            pods: List of established PODs
            pops: List of established POPs
            category: Product category name
            
        Returns:
            SingleProductProfile with scores, or None if failed
        """
        brand = product_data.get('brand', 'Unknown')
        product_name = product_data.get('product_name', 'Unknown Product')
        
        # Format detailed analysis for this product
        product_analysis = format_product_full_analysis(product_data)
        pods_description = format_pods_for_scoring(pods)
        pops_description = format_pops_for_checking(pops)
        
        user_prompt = self._phase2_user.format(
            brand=brand,
            product_name=product_name,
            category=category,
            product_analysis=product_analysis,
            pods_description=pods_description,
            pops_description=pops_description
        )
        
        try:
            messages = [
                SystemMessage(content=self._phase2_system),
                HumanMessage(content=user_prompt)
            ]
            
            result = self._phase2_llm.invoke(messages)
            return result
            
        except Exception as e:
            print(f"      [!] Scoring error: {e}")
            return None
    
    def _phase3_generate_insights(
        self,
        products: List[ProductCompetitiveProfile],
        pods: List[PointOfDifference],
        pops: List[PointOfParity],
        category: str
    ) -> Optional[StrategicInsightsResult]:
        """Phase 3: Generate strategic insights from complete analysis.
        
        Args:
            products: List of scored product profiles
            pods: List of PODs
            pops: List of POPs
            category: Product category name
            
        Returns:
            StrategicInsightsResult or None if failed
        """
        print(f"  [Phase 3] Generating strategic insights...")
        
        pods_summary = format_pods_summary(pods)
        pops_summary = format_pops_summary(pops)
        products_scores = format_products_scores(products, pods)
        
        user_prompt = self._phase3_user.format(
            category=category,
            product_count=len(products),
            pods_summary=pods_summary,
            pops_summary=pops_summary,
            products_scores_summary=products_scores
        )
        
        try:
            messages = [
                SystemMessage(content=self._phase3_system),
                HumanMessage(content=user_prompt)
            ]
            
            result = self._phase3_llm.invoke(messages)
            
            print(f"    [✓] Generated {len(result.strategic_insights)} insights")
            return result
            
        except Exception as e:
            print(f"    [!] Phase 3 error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def analyze(
        self,
        products_analysis: List[Dict[str, Any]],
        category: str,
        parallel: bool = True
    ) -> Optional[CompetitiveAnalysisResult]:
        """Perform competitive analysis using 3-phase approach (PARALLELIZED).
        
        Phase 1: Identify axes (1 call)
        Phase 2: Score each product (N calls - PARALLEL)
        Phase 3: Generate insights (1 call)
        
        Args:
            products_analysis: List of product analysis dicts from visual analysis
            category: Product category name
            parallel: Use parallel execution for Phase 2 (default: True)
            
        Returns:
            CompetitiveAnalysisResult or None if failed
        """
        # Filter to successful analyses only
        valid_products = [p for p in products_analysis if p.get('analysis_success')]
        
        if len(valid_products) < 2:
            print("[!] Need at least 2 products with successful analysis")
            return None
        
        total_calls = len(valid_products) + 2
        print(f"\n[CompetitiveAnalyzer] Starting 3-phase analysis ({total_calls} LLM calls)")
        
        # =====================================================================
        # PHASE 1: Identify PODs and POPs
        # =====================================================================
        
        axes_result = self._phase1_identify_axes(valid_products, category)
        
        if not axes_result:
            print("[!] Phase 1 failed - cannot continue")
            return None
        
        pods = axes_result.points_of_difference
        pops = axes_result.points_of_parity
        
        # =====================================================================
        # PHASE 2: Score each product individually (PARALLELIZED)
        # =====================================================================
        
        if parallel and len(valid_products) > 1:
            # PARALLEL EXECUTION
            print(f"  [Phase 2] Scoring {len(valid_products)} products (PARALLEL, "
                  f"{self.config.parallel.gemini.max_concurrent} concurrent)...")
            
            # Prepare items for parallel processing
            items_to_process = []
            for i, product_data in enumerate(valid_products):
                items_to_process.append({
                    'index': i,
                    'product_data': product_data,
                    'pods': pods,
                    'pops': pops,
                    'category': category,
                })
            
            # Create executor with Gemini limits
            limits = ProviderLimits(
                max_concurrent=self.config.parallel.gemini.max_concurrent,
                rate_limit_rpm=self.config.parallel.gemini.rate_limit_rpm,
                min_delay_seconds=self.config.parallel.gemini.min_delay_seconds
            )
            executor = ParallelExecutor(provider=Provider.GEMINI, limits=limits)
            
            # Async wrapper for scoring
            async def score_product_async(item: Dict[str, Any]) -> Dict[str, Any]:
                import asyncio
                loop = asyncio.get_event_loop()
                
                def do_scoring():
                    profile = self._phase2_score_product(
                        item['product_data'], 
                        item['pods'], 
                        item['pops'], 
                        item['category']
                    )
                    return {
                        'index': item['index'],
                        'product_data': item['product_data'],
                        'profile': profile,
                    }
                
                return await loop.run_in_executor(None, do_scoring)
            
            def on_progress(completed: int, total: int, status: str, item_id: Optional[str]):
                print(f"    [{completed:2}/{total}] {item_id or 'Scoring'}... {status}", flush=True)
            
            batch_result = executor.execute_sync(
                items=items_to_process,
                process_func=score_product_async,
                get_item_id=lambda x: x['product_data'].get('brand', 'Unknown'),
                progress_callback=on_progress
            )
            
            # Collect results in order
            scored_products: List[ProductCompetitiveProfile] = []
            results_by_index = {}
            
            for exec_result in batch_result.results:
                if exec_result.success and exec_result.result:
                    result_data = exec_result.result
                    results_by_index[result_data['index']] = result_data
            
            # Build scored products in original order
            for i in range(len(valid_products)):
                if i in results_by_index:
                    result_data = results_by_index[i]
                    profile = result_data['profile']
                    product_data = result_data['product_data']
                    
                    if profile:
                        full_profile = ProductCompetitiveProfile(
                            brand=profile.brand,
                            product_name=profile.product_name,
                            image_path=product_data.get('image_path'),
                            pod_scores=profile.pod_scores,
                            pop_status=profile.pop_status,
                            positioning_summary=profile.positioning_summary,
                            key_differentiator=profile.key_differentiator
                        )
                        scored_products.append(full_profile)
            
            print(f"    [✓] {len(scored_products)}/{len(valid_products)} products scored "
                  f"in {batch_result.total_duration_seconds:.1f}s")
            
        else:
            # SEQUENTIAL EXECUTION (fallback)
            print(f"  [Phase 2] Scoring {len(valid_products)} products (SEQUENTIAL)...")
            
            scored_products: List[ProductCompetitiveProfile] = []
            
            for i, product_data in enumerate(valid_products, 1):
                brand = product_data.get('brand', 'Unknown')
                product_name = product_data.get('product_name', 'Unknown')[:40]
                print(f"    [{i:2}/{len(valid_products)}] {brand} - {product_name}...", end=" ", flush=True)
                
                profile = self._phase2_score_product(product_data, pods, pops, category)
                
                if profile:
                    # Convert to ProductCompetitiveProfile and add image path
                    full_profile = ProductCompetitiveProfile(
                        brand=profile.brand,
                        product_name=profile.product_name,
                        image_path=product_data.get('image_path'),
                        pod_scores=profile.pod_scores,
                        pop_status=profile.pop_status,
                        positioning_summary=profile.positioning_summary,
                        key_differentiator=profile.key_differentiator
                    )
                    scored_products.append(full_profile)
                    print("✓")
                else:
                    print("✗")
            
            print(f"    [✓] {len(scored_products)}/{len(valid_products)} products scored")
        
        if not scored_products:
            print("[!] No products scored successfully")
            return None
        
        # =====================================================================
        # PHASE 3: Generate strategic insights
        # =====================================================================
        
        insights_result = self._phase3_generate_insights(scored_products, pods, pops, category)
        
        if not insights_result:
            # Use empty insights if Phase 3 fails (non-critical)
            print("    [!] Using empty insights (Phase 3 failed)")
            insights_result = StrategicInsightsResult(
                strategic_insights=[],
                category_summary=f"Analyse concurrentielle de {len(scored_products)} produits dans la catégorie {category}."
            )
        
        # =====================================================================
        # Assemble final result
        # =====================================================================
        
        return CompetitiveAnalysisResult(
            category=category,
            analysis_date=datetime.now().isoformat(),
            product_count=len(scored_products),
            points_of_difference=pods,
            points_of_parity=pops,
            products=scored_products,
            strategic_insights=insights_result.strategic_insights,
            category_summary=insights_result.category_summary
        )
    
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
        
        valid_count = len([p for p in products_analysis if p.get('analysis_success')])
        
        print("=" * 70)
        print(f"COMPETITIVE ANALYSIS - Run: {run_id}")
        print(f"  Category: {category}")
        print(f"  Products: {valid_count} (with successful visual analysis)")
        print(f"  Model: {self.model}")
        print(f"  Architecture: 3-phase ({valid_count + 2} LLM calls)")
        print("=" * 70)
        
        # Run analysis
        result = self.analyze(products_analysis, category)
        
        if not result:
            print("[!] Competitive analysis failed")
            return None
        
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
        
        print("\n📦 Product Scores:")
        for product in result.products:
            avg_score = sum(s.score for s in product.pod_scores) / len(product.pod_scores) if product.pod_scores else 0
            print(f"  • {product.brand}: avg {avg_score:.1f}/10 - {product.key_differentiator}")
        
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
