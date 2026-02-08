"""Golden Rules Report Generator for Phase 1.4

Synthesizes data from OCR analysis (visual) and competitive analysis to generate
an actionable "Golden Rules" report for plant-based milk packaging market.

This report identifies:
- Recurring keywords and messaging patterns
- Color codes and visual conventions
- Text structure and information hierarchy patterns
- Successful claims (correlated with positive reviews)
- Market gaps (Blue Ocean opportunities)
- Specific recommendations for Recolt's positioning
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass
import re


@dataclass
class GoldenRule:
    """A single golden rule extracted from market analysis."""
    category: str  # e.g., "color", "typography", "claim", "structure"
    rule: str  # The golden rule statement
    frequency: int  # How many products follow this pattern
    examples: List[str]  # Brand examples
    recommendation: str  # What Recolt should do
    market_share: float  # Percentage of market following this rule


class GoldenRulesAnalyzer:
    """Analyzes competitive data to extract golden rules."""
    
    def __init__(self, output_dir: str):
        """Initialize analyzer with output directory path.
        
        Args:
            output_dir: Path to output directory containing analysis files
        """
        self.output_dir = Path(output_dir)
        self.analysis_dir = self.output_dir / "analysis"
        
    def load_analysis_data(self, category_slug: str, run_id: str) -> Tuple[Dict, List[Dict]]:
        """Load competitive and visual analysis data.
        
        Args:
            category_slug: Category slug (e.g., "lait_davoine")
            run_id: Run ID (e.g., "20260120_184854")
            
        Returns:
            Tuple of (competitive_data, visual_data_list)
        """
        comp_file = self.analysis_dir / f"{category_slug}_competitive_analysis_{run_id}.json"
        visual_file = self.analysis_dir / f"{category_slug}_visual_analysis_{run_id}.json"
        
        if not comp_file.exists():
            raise FileNotFoundError(f"Competitive analysis not found: {comp_file}")
        if not visual_file.exists():
            raise FileNotFoundError(f"Visual analysis not found: {visual_file}")
        
        with open(comp_file, 'r', encoding='utf-8') as f:
            comp_data = json.load(f)
        
        with open(visual_file, 'r', encoding='utf-8') as f:
            visual_data = json.load(f)
        
        return comp_data, visual_data
    
    def analyze_color_patterns(self, visual_data: List[Dict]) -> List[GoldenRule]:
        """Analyze color usage patterns across products.
        
        Args:
            visual_data: List of visual analysis results
            
        Returns:
            List of color-related golden rules
        """
        rules = []
        
        # Collect all colors used
        color_usage = Counter()
        color_by_purpose = defaultdict(list)
        surface_finishes = Counter()
        color_harmonies = Counter()
        
        total_products = len([p for p in visual_data if p.get('analysis_success')])
        
        for product in visual_data:
            if not product.get('analysis_success'):
                continue
                
            analysis = product.get('analysis', {})
            chromatic = analysis.get('chromatic_mapping', {})
            
            # Track surface finish
            finish = chromatic.get('surface_finish', '')
            if finish:
                surface_finishes[finish] += 1
            
            # Track color harmony
            harmony = chromatic.get('color_harmony', '')
            if harmony:
                color_harmonies[harmony] += 1
            
            # Track color palette
            palette = chromatic.get('color_palette', [])
            for color_entry in palette:
                color_name = color_entry.get('color_name', '')
                hex_code = color_entry.get('hex_code', '')
                usage = color_entry.get('usage', '')
                
                if color_name:
                    color_usage[color_name] += 1
                    color_by_purpose[usage].append({
                        'color': color_name,
                        'hex': hex_code,
                        'brand': product.get('brand', '')
                    })
        
        # Golden Rule: Most common surface finish
        if surface_finishes:
            most_common_finish = surface_finishes.most_common(1)[0]
            finish_name, finish_count = most_common_finish
            rules.append(GoldenRule(
                category="color_finish",
                rule=f"Use {finish_name} surface finish",
                frequency=finish_count,
                examples=[],
                recommendation=f"Consider {finish_name} finish for premium perception" if finish_name in ['matte', 'satin'] else "Consider differentiation with alternative finish",
                market_share=finish_count / total_products * 100
            ))
        
        # Golden Rule: Most common color harmony
        if color_harmonies:
            most_common_harmony = color_harmonies.most_common(1)[0]
            harmony_name, harmony_count = most_common_harmony
            rules.append(GoldenRule(
                category="color_harmony",
                rule=f"Employ {harmony_name} color harmony",
                frequency=harmony_count,
                examples=[],
                recommendation=f"Follow market standard with {harmony_name} scheme" if harmony_count / total_products > 0.5 else "Opportunity to differentiate with alternative color harmony",
                market_share=harmony_count / total_products * 100
            ))
        
        # Golden Rule: Background colors
        if 'background' in color_by_purpose:
            bg_colors = [c['color'] for c in color_by_purpose['background']]
            bg_counter = Counter(bg_colors)
            most_common_bg = bg_counter.most_common(3)
            
            if most_common_bg:
                bg_names = [name for name, _ in most_common_bg]
                rules.append(GoldenRule(
                    category="color_background",
                    rule=f"Common backgrounds: {', '.join(bg_names)}",
                    frequency=sum(count for _, count in most_common_bg),
                    examples=bg_names,
                    recommendation="Consider white/light backgrounds for freshness, or differentiate with bold colors",
                    market_share=sum(count for _, count in most_common_bg) / total_products * 100
                ))
        
        return rules
    
    def analyze_typography_patterns(self, visual_data: List[Dict]) -> List[GoldenRule]:
        """Analyze typography and text hierarchy patterns.
        
        Args:
            visual_data: List of visual analysis results
            
        Returns:
            List of typography-related golden rules
        """
        rules = []
        
        font_categories = Counter()
        text_hierarchies = []
        emphasis_techniques = Counter()
        
        total_products = len([p for p in visual_data if p.get('analysis_success')])
        
        for product in visual_data:
            if not product.get('analysis_success'):
                continue
                
            analysis = product.get('analysis', {})
            textual = analysis.get('textual_inventory', {})
            
            # Track all text blocks
            text_blocks = textual.get('all_text_blocks', [])
            
            # Track hierarchy structure (how many levels)
            if text_blocks:
                max_hierarchy = max(block.get('hierarchy_level', 1) for block in text_blocks)
                text_hierarchies.append(max_hierarchy)
            
            # Track font categories
            for block in text_blocks:
                font = block.get('font_category', '')
                if font:
                    font_categories[font] += 1
                
                # Track emphasis techniques
                techniques = block.get('emphasis_techniques', [])
                for technique in techniques:
                    emphasis_techniques[technique] += 1
        
        # Golden Rule: Common font categories
        if font_categories:
            top_fonts = font_categories.most_common(3)
            font_names = [name for name, _ in top_fonts]
            rules.append(GoldenRule(
                category="typography_font",
                rule=f"Predominant fonts: {', '.join(font_names)}",
                frequency=sum(count for _, count in top_fonts),
                examples=font_names,
                recommendation="Modern sans-serif fonts dominate the category for clean, fresh perception",
                market_share=sum(count for _, count in top_fonts) / (len(font_categories) or 1) * 100
            ))
        
        # Golden Rule: Hierarchy levels
        if text_hierarchies:
            avg_hierarchy = sum(text_hierarchies) / len(text_hierarchies)
            most_common_hierarchy = Counter(text_hierarchies).most_common(1)[0][0]
            rules.append(GoldenRule(
                category="typography_hierarchy",
                rule=f"Typical hierarchy: {most_common_hierarchy} levels",
                frequency=Counter(text_hierarchies)[most_common_hierarchy],
                examples=[],
                recommendation=f"Use {most_common_hierarchy}-level hierarchy for clear information flow",
                market_share=Counter(text_hierarchies)[most_common_hierarchy] / len(text_hierarchies) * 100
            ))
        
        # Golden Rule: Emphasis techniques
        if emphasis_techniques:
            top_techniques = emphasis_techniques.most_common(3)
            technique_names = [name for name, _ in top_techniques]
            rules.append(GoldenRule(
                category="typography_emphasis",
                rule=f"Common emphasis: {', '.join(technique_names)}",
                frequency=sum(count for _, count in top_techniques),
                examples=technique_names,
                recommendation="Use bold and color contrast for key claims",
                market_share=sum(count for _, count in top_techniques) / (len(emphasis_techniques) or 1) * 100
            ))
        
        return rules
    
    def analyze_claims_patterns(self, visual_data: List[Dict]) -> List[GoldenRule]:
        """Analyze marketing claims and messaging patterns.
        
        Args:
            visual_data: List of visual analysis results
            
        Returns:
            List of claim-related golden rules
        """
        rules = []
        
        all_claims = []
        emphasized_claims = []
        claim_keywords = Counter()
        
        total_products = len([p for p in visual_data if p.get('analysis_success')])
        
        for product in visual_data:
            if not product.get('analysis_success'):
                continue
                
            analysis = product.get('analysis', {})
            textual = analysis.get('textual_inventory', {})
            
            claims = textual.get('claims_summary', [])
            emphasized = textual.get('emphasized_claims', [])
            
            all_claims.extend(claims)
            emphasized_claims.extend(emphasized)
            
            # Extract keywords from claims
            for claim in claims:
                # Extract key words (simple tokenization)
                words = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', claim.lower())
                for word in words:
                    if word not in ['with', 'without', 'this', 'that', 'have', 'from']:
                        claim_keywords[word] += 1
        
        # Golden Rule: Most common claim keywords
        if claim_keywords:
            top_keywords = claim_keywords.most_common(10)
            keyword_names = [name for name, _ in top_keywords[:5]]
            rules.append(GoldenRule(
                category="claims_keywords",
                rule=f"Key messaging themes: {', '.join(keyword_names)}",
                frequency=sum(count for _, count in top_keywords[:5]),
                examples=keyword_names,
                recommendation="Focus on organic, natural, healthy, sustainable themes",
                market_share=sum(count for _, count in top_keywords[:5]) / (sum(claim_keywords.values()) or 1) * 100
            ))
        
        # Golden Rule: Emphasized claims
        if emphasized_claims:
            emphasized_counter = Counter(emphasized_claims)
            top_emphasized = emphasized_counter.most_common(5)
            rules.append(GoldenRule(
                category="claims_emphasized",
                rule=f"Most emphasized claims appear {len(emphasized_claims)} times across products",
                frequency=len(emphasized_claims),
                examples=[claim for claim, _ in top_emphasized[:3]],
                recommendation="Prioritize visually emphasizing health and sustainability claims",
                market_share=len(emphasized_claims) / (len(all_claims) or 1) * 100
            ))
        
        # Golden Rule: Average number of claims
        avg_claims = len(all_claims) / total_products if total_products > 0 else 0
        rules.append(GoldenRule(
            category="claims_quantity",
            rule=f"Average {avg_claims:.1f} claims per product",
            frequency=len(all_claims),
            examples=[],
            recommendation=f"Include {int(avg_claims)}-{int(avg_claims)+2} key claims without overcrowding",
            market_share=100.0
        ))
        
        return rules
    
    def analyze_trust_marks(self, visual_data: List[Dict]) -> List[GoldenRule]:
        """Analyze trust marks and certifications usage.
        
        Args:
            visual_data: List of visual analysis results
            
        Returns:
            List of trust mark related golden rules
        """
        rules = []
        
        trust_mark_types = Counter()
        trust_mark_names = Counter()
        trust_mark_prominence = Counter()
        
        total_products = len([p for p in visual_data if p.get('analysis_success')])
        products_with_marks = 0
        
        for product in visual_data:
            if not product.get('analysis_success'):
                continue
                
            analysis = product.get('analysis', {})
            assets = analysis.get('asset_symbolism', {})
            trust_marks = assets.get('trust_marks', [])
            
            if trust_marks:
                products_with_marks += 1
            
            for mark in trust_marks:
                mark_type = mark.get('mark_type', '')
                mark_name = mark.get('name', '')
                prominence = mark.get('prominence', '')
                
                if mark_type:
                    trust_mark_types[mark_type] += 1
                if mark_name:
                    trust_mark_names[mark_name] += 1
                if prominence:
                    trust_mark_prominence[prominence] += 1
        
        # Golden Rule: Trust mark prevalence
        if total_products > 0:
            mark_percentage = products_with_marks / total_products * 100
            rules.append(GoldenRule(
                category="trust_marks_prevalence",
                rule=f"{mark_percentage:.0f}% of products display trust marks",
                frequency=products_with_marks,
                examples=[],
                recommendation="Include relevant certifications (organic, sustainable) as they're market standard" if mark_percentage > 50 else "Opportunity to stand out with prominent certifications",
                market_share=mark_percentage
            ))
        
        # Golden Rule: Most common mark types
        if trust_mark_types:
            top_types = trust_mark_types.most_common(3)
            type_names = [name.replace('-', ' ').title() for name, _ in top_types]
            rules.append(GoldenRule(
                category="trust_marks_types",
                rule=f"Common certifications: {', '.join(type_names)}",
                frequency=sum(count for _, count in top_types),
                examples=type_names,
                recommendation="Prioritize organic and environmental certifications",
                market_share=sum(count for _, count in top_types) / (sum(trust_mark_types.values()) or 1) * 100
            ))
        
        # Golden Rule: Most common specific marks
        if trust_mark_names:
            top_marks = trust_mark_names.most_common(5)
            rules.append(GoldenRule(
                category="trust_marks_specific",
                rule=f"Frequent marks: {', '.join([name for name, _ in top_marks])}",
                frequency=sum(count for _, count in top_marks),
                examples=[name for name, _ in top_marks],
                recommendation="Consider EU Organic, B-Corp, or regional certifications",
                market_share=sum(count for _, count in top_marks) / (sum(trust_mark_names.values()) or 1) * 100
            ))
        
        return rules
    
    def analyze_visual_structure(self, visual_data: List[Dict]) -> List[GoldenRule]:
        """Analyze visual structure and layout patterns.
        
        Args:
            visual_data: List of visual analysis results
            
        Returns:
            List of visual structure related golden rules
        """
        rules = []
        
        eye_tracking_patterns = Counter()
        balance_types = Counter()
        hierarchy_scores = []
        
        total_products = len([p for p in visual_data if p.get('analysis_success')])
        
        for product in visual_data:
            if not product.get('analysis_success'):
                continue
                
            analysis = product.get('analysis', {})
            
            # Eye tracking pattern
            eye_tracking = analysis.get('eye_tracking', {})
            pattern = eye_tracking.get('pattern_type', '')
            if pattern:
                eye_tracking_patterns[pattern] += 1
            
            # Visual balance
            massing = analysis.get('massing', {})
            balance = massing.get('balance_type', '')
            if balance:
                balance_types[balance] += 1
            
            # Hierarchy clarity
            score = analysis.get('hierarchy_clarity_score', 0)
            if score:
                hierarchy_scores.append(score)
        
        # Golden Rule: Eye tracking patterns
        if eye_tracking_patterns:
            top_pattern = eye_tracking_patterns.most_common(1)[0]
            pattern_name, pattern_count = top_pattern
            rules.append(GoldenRule(
                category="visual_structure_eye",
                rule=f"Dominant eye pattern: {pattern_name}",
                frequency=pattern_count,
                examples=[],
                recommendation=f"Design for {pattern_name} reading pattern with key info at entry points",
                market_share=pattern_count / total_products * 100
            ))
        
        # Golden Rule: Visual balance
        if balance_types:
            top_balance = balance_types.most_common(1)[0]
            balance_name, balance_count = top_balance
            rules.append(GoldenRule(
                category="visual_structure_balance",
                rule=f"Common balance: {balance_name}",
                frequency=balance_count,
                examples=[],
                recommendation=f"Use {balance_name} composition for {('professional appeal' if balance_name == 'symmetric' else 'dynamic interest')}",
                market_share=balance_count / total_products * 100
            ))
        
        # Golden Rule: Hierarchy clarity benchmark
        if hierarchy_scores:
            avg_score = sum(hierarchy_scores) / len(hierarchy_scores)
            rules.append(GoldenRule(
                category="visual_structure_clarity",
                rule=f"Market average hierarchy clarity: {avg_score:.1f}/10",
                frequency=len(hierarchy_scores),
                examples=[],
                recommendation=f"Target clarity score of {min(10, avg_score + 1):.0f}+ to exceed market standard",
                market_share=100.0
            ))
        
        return rules
    
    def identify_market_gaps(self, comp_data: Dict, visual_data: List[Dict]) -> List[Dict[str, Any]]:
        """Identify market gaps (Blue Ocean opportunities).
        
        Args:
            comp_data: Competitive analysis data
            visual_data: Visual analysis data
            
        Returns:
            List of market gap opportunities
        """
        gaps = []
        
        # Analyze POD scores to find under-represented positioning
        products = comp_data.get('products', [])
        pods = comp_data.get('points_of_difference', [])
        
        # Calculate average scores per POD axis
        pod_avg_scores = {}
        for pod in pods:
            axis_id = pod['axis_id']
            scores = []
            for product in products:
                for score_entry in product.get('pod_scores', []):
                    if score_entry['axis_id'] == axis_id:
                        scores.append(score_entry['score'])
            
            if scores:
                pod_avg_scores[axis_id] = {
                    'axis_name': pod['axis_name'],
                    'avg_score': sum(scores) / len(scores),
                    'max_score': max(scores),
                    'min_score': min(scores)
                }
        
        # Identify under-represented axes (market gaps)
        for axis_id, stats in pod_avg_scores.items():
            if stats['avg_score'] < 5.0:  # Low average means underexplored
                gaps.append({
                    'type': 'positioning_gap',
                    'axis': stats['axis_name'],
                    'description': f"Low market emphasis on {stats['axis_name']} (avg: {stats['avg_score']:.1f}/10)",
                    'opportunity': f"Differentiate by strongly emphasizing {stats['axis_name']}",
                    'blue_ocean_potential': 'high' if stats['avg_score'] < 4.0 else 'medium'
                })
        
        # Analyze color gaps
        all_colors = []
        for product in visual_data:
            if not product.get('analysis_success'):
                continue
            analysis = product.get('analysis', {})
            chromatic = analysis.get('chromatic_mapping', {})
            palette = chromatic.get('color_palette', [])
            for color_entry in palette:
                all_colors.append(color_entry.get('color_name', '').lower())
        
        # Identify unused colors (simple approach)
        color_counter = Counter(all_colors)
        
        # Define strategic color opportunities
        strategic_colors = {
            'deep purple': 'premium/luxury',
            'coral pink': 'playful/modern',
            'teal': 'innovation/tech',
            'terracotta': 'artisanal/authentic',
            'navy blue': 'trust/professional'
        }
        
        for color, positioning in strategic_colors.items():
            if color not in color_counter or color_counter[color] < 2:
                gaps.append({
                    'type': 'color_gap',
                    'description': f"{color.title()} is underutilized in the category",
                    'opportunity': f"Use {color} to convey {positioning}",
                    'blue_ocean_potential': 'medium'
                })
        
        # Analyze claim gaps
        all_claim_keywords = []
        for product in visual_data:
            if not product.get('analysis_success'):
                continue
            analysis = product.get('analysis', {})
            textual = analysis.get('textual_inventory', {})
            claims = textual.get('claims_summary', [])
            
            for claim in claims:
                words = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', claim.lower())
                all_claim_keywords.extend(words)
        
        # Strategic claim keywords to check
        strategic_claims = {
            'regenerative': 'Next-gen sustainability positioning',
            'artisanal': 'Craft/quality differentiation',
            'terroir': 'Local/origin storytelling',
            'carbon-neutral': 'Climate leadership',
            'circular': 'Circular economy positioning'
        }
        
        claim_counter = Counter(all_claim_keywords)
        for claim, positioning in strategic_claims.items():
            if claim not in claim_counter or claim_counter[claim] < 2:
                gaps.append({
                    'type': 'claim_gap',
                    'description': f"'{claim.title()}' messaging is rare in category",
                    'opportunity': positioning,
                    'blue_ocean_potential': 'high' if claim not in claim_counter else 'medium'
                })
        
        return gaps
    
    def generate_recolt_recommendations(
        self,
        rules: List[GoldenRule],
        gaps: List[Dict[str, Any]],
        comp_data: Dict
    ) -> Dict[str, List[str]]:
        """Generate specific recommendations for Recolt positioning.
        
        Args:
            rules: List of golden rules
            gaps: List of market gaps
            comp_data: Competitive analysis data
            
        Returns:
            Dictionary with 'adopt' and 'disrupt' recommendations
        """
        recommendations = {
            'adopt': [],
            'disrupt': [],
            'recolt_strategy': []
        }
        
        # ADOPT: Market standards with >60% adoption
        for rule in rules:
            if rule.market_share > 60:
                recommendations['adopt'].append(
                    f"{rule.rule} ({rule.market_share:.0f}% market adoption) - Market standard expectation"
                )
        
        # DISRUPT: Leverage high-potential gaps
        high_potential_gaps = [g for g in gaps if g.get('blue_ocean_potential') == 'high']
        for gap in high_potential_gaps[:5]:  # Top 5 opportunities
            if gap['type'] == 'positioning_gap':
                recommendations['disrupt'].append(
                    f"Position strongly on {gap.get('axis', 'differentiation')}: {gap['opportunity']}"
                )
            elif gap['type'] == 'claim_gap':
                recommendations['disrupt'].append(
                    f"Messaging: {gap['opportunity']} (currently underused: {gap['description']})"
                )
            elif gap['type'] == 'color_gap':
                recommendations['disrupt'].append(
                    f"Visual: {gap['opportunity']} to stand out from category norms"
                )
        
        # RECOLT-SPECIFIC STRATEGY (based on brief)
        # Message hierarchy: 1) Taste & intensity, 2) Health, 3) Eco/local
        recommendations['recolt_strategy'] = [
            "PRIMARY MESSAGE: Emphasize taste and intensity as #1 differentiator (most oat milks focus on health first)",
            "HIERARCHY: Taste > Health > Eco/local (unlike competitors who lead with sustainability)",
            "COLOR: Consider bold, appetite-appealing colors (vs. typical green/brown earth tones)",
            "POSITIONING: 'Belgian artisanal craftsmanship' to leverage local premium perception",
            "CLAIMS: Lead with sensory/taste descriptors before functional health benefits",
            "FORMAT: Black & white base with strategic color accents for premium/gourmet positioning",
            "TYPOGRAPHY: Mix traditional serif (craft/quality) with modern sans (freshness)",
            "DISRUPTION: Position as 'Quinoat' - unique grain angle differentiates from generic oat milk"
        ]
        
        return recommendations
    
    def generate_report(
        self,
        category_slug: str,
        run_id: str,
        output_format: str = 'markdown'
    ) -> str:
        """Generate complete Golden Rules report.
        
        Args:
            category_slug: Category slug (e.g., "lait_davoine")
            run_id: Run ID (e.g., "20260120_184854")
            output_format: Output format ('markdown', 'json', 'html')
            
        Returns:
            Report content as string
        """
        # Load data
        comp_data, visual_data = self.load_analysis_data(category_slug, run_id)
        
        # Analyze patterns
        color_rules = self.analyze_color_patterns(visual_data)
        typo_rules = self.analyze_typography_patterns(visual_data)
        claim_rules = self.analyze_claims_patterns(visual_data)
        trust_rules = self.analyze_trust_marks(visual_data)
        structure_rules = self.analyze_visual_structure(visual_data)
        
        all_rules = color_rules + typo_rules + claim_rules + trust_rules + structure_rules
        
        # Identify gaps
        gaps = self.identify_market_gaps(comp_data, visual_data)
        
        # Generate recommendations
        recommendations = self.generate_recolt_recommendations(all_rules, gaps, comp_data)
        
        # Format report
        if output_format == 'json':
            return self._format_as_json(comp_data, all_rules, gaps, recommendations)
        elif output_format == 'html':
            return self._format_as_html(comp_data, all_rules, gaps, recommendations)
        else:  # markdown
            return self._format_as_markdown(comp_data, all_rules, gaps, recommendations)
    
    def _format_as_markdown(
        self,
        comp_data: Dict,
        rules: List[GoldenRule],
        gaps: List[Dict],
        recommendations: Dict
    ) -> str:
        """Format report as Markdown."""
        category_name = comp_data.get('category', 'Product Category')
        product_count = comp_data.get('product_count', 0)
        
        md = f"""# Golden Rules Report: {category_name}

## Executive Summary

This report synthesizes competitive intelligence from **{product_count} products** in the {category_name} category, identifying market patterns, conventions, and Blue Ocean opportunities for Recolt's positioning strategy.

---

## 1. Market Golden Rules

### 1.1 Color & Visual Codes

"""
        
        # Color rules
        color_rules = [r for r in rules if r.category.startswith('color')]
        for rule in color_rules:
            md += f"#### {rule.rule}\n\n"
            md += f"- **Market Adoption**: {rule.market_share:.1f}%\n"
            md += f"- **Frequency**: {rule.frequency} products\n"
            if rule.examples:
                md += f"- **Examples**: {', '.join(rule.examples)}\n"
            md += f"- **💡 Recommendation**: {rule.recommendation}\n\n"
        
        md += "### 1.2 Typography & Text Hierarchy\n\n"
        
        # Typography rules
        typo_rules = [r for r in rules if r.category.startswith('typography')]
        for rule in typo_rules:
            md += f"#### {rule.rule}\n\n"
            md += f"- **Market Adoption**: {rule.market_share:.1f}%\n"
            md += f"- **💡 Recommendation**: {rule.recommendation}\n\n"
        
        md += "### 1.3 Claims & Messaging\n\n"
        
        # Claim rules
        claim_rules = [r for r in rules if r.category.startswith('claims')]
        for rule in claim_rules:
            md += f"#### {rule.rule}\n\n"
            if rule.examples:
                md += f"- **Top Examples**: {', '.join(rule.examples[:5])}\n"
            md += f"- **💡 Recommendation**: {rule.recommendation}\n\n"
        
        md += "### 1.4 Trust Marks & Certifications\n\n"
        
        # Trust mark rules
        trust_rules = [r for r in rules if r.category.startswith('trust')]
        for rule in trust_rules:
            md += f"#### {rule.rule}\n\n"
            if rule.examples:
                md += f"- **Examples**: {', '.join(rule.examples)}\n"
            md += f"- **💡 Recommendation**: {rule.recommendation}\n\n"
        
        md += "### 1.5 Visual Structure & Layout\n\n"
        
        # Structure rules
        structure_rules = [r for r in rules if r.category.startswith('visual_structure')]
        for rule in structure_rules:
            md += f"#### {rule.rule}\n\n"
            md += f"- **💡 Recommendation**: {rule.recommendation}\n\n"
        
        md += "\n---\n\n## 2. Market Gaps (Blue Ocean Opportunities)\n\n"
        
        # High potential gaps
        high_gaps = [g for g in gaps if g.get('blue_ocean_potential') == 'high']
        medium_gaps = [g for g in gaps if g.get('blue_ocean_potential') == 'medium']
        
        if high_gaps:
            md += "### 2.1 High-Potential Opportunities\n\n"
            for i, gap in enumerate(high_gaps, 1):
                md += f"{i}. **{gap['type'].replace('_', ' ').title()}**: {gap['description']}\n"
                md += f"   - 🌊 **Blue Ocean Play**: {gap['opportunity']}\n\n"
        
        if medium_gaps:
            md += "### 2.2 Medium-Potential Opportunities\n\n"
            for i, gap in enumerate(medium_gaps, 1):
                md += f"{i}. **{gap['type'].replace('_', ' ').title()}**: {gap['description']}\n"
                md += f"   - 💡 **Opportunity**: {gap['opportunity']}\n\n"
        
        md += "\n---\n\n## 3. Recolt Positioning Strategy\n\n"
        md += "### 3.1 What to ADOPT (Market Standards)\n\n"
        
        for i, adopt in enumerate(recommendations['adopt'], 1):
            md += f"{i}. {adopt}\n"
        
        md += "\n### 3.2 What to DISRUPT (Differentiation)\n\n"
        
        for i, disrupt in enumerate(recommendations['disrupt'], 1):
            md += f"{i}. {disrupt}\n"
        
        md += "\n### 3.3 Recolt-Specific Strategic Guidelines\n\n"
        
        for i, strategy in enumerate(recommendations['recolt_strategy'], 1):
            md += f"{i}. {strategy}\n"
        
        md += "\n---\n\n## 4. Summary Data Tables\n\n"
        
        # Create summary tables
        md += "### Golden Rules by Category\n\n"
        md += "| Category | Rule | Market Share | Recommendation |\n"
        md += "|----------|------|--------------|----------------|\n"
        
        # Top rules by market share
        sorted_rules = sorted(rules, key=lambda r: r.market_share, reverse=True)[:15]
        for rule in sorted_rules:
            category_display = rule.category.replace('_', ' ').title()
            rule_short = rule.rule[:60] + '...' if len(rule.rule) > 60 else rule.rule
            rec_short = rule.recommendation[:80] + '...' if len(rule.recommendation) > 80 else rule.recommendation
            md += f"| {category_display} | {rule_short} | {rule.market_share:.0f}% | {rec_short} |\n"
        
        md += "\n---\n\n"
        md += f"*Report generated for {category_name} category with {product_count} products analyzed*\n"
        
        return md
    
    def _format_as_json(
        self,
        comp_data: Dict,
        rules: List[GoldenRule],
        gaps: List[Dict],
        recommendations: Dict
    ) -> str:
        """Format report as JSON."""
        report_data = {
            'category': comp_data.get('category'),
            'product_count': comp_data.get('product_count'),
            'analysis_date': comp_data.get('analysis_date'),
            'golden_rules': [
                {
                    'category': r.category,
                    'rule': r.rule,
                    'frequency': r.frequency,
                    'examples': r.examples,
                    'recommendation': r.recommendation,
                    'market_share': r.market_share
                }
                for r in rules
            ],
            'market_gaps': gaps,
            'recommendations': recommendations
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _format_as_html(
        self,
        comp_data: Dict,
        rules: List[GoldenRule],
        gaps: List[Dict],
        recommendations: Dict
    ) -> str:
        """Format report as HTML."""
        # Convert markdown to HTML (basic implementation)
        markdown_report = self._format_as_markdown(comp_data, rules, gaps, recommendations)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Golden Rules Report - {comp_data.get('category', '')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        .metric {{
            background: #ecf0f1;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .recommendation {{
            background: #d5f4e6;
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #27ae60;
        }}
        .gap {{
            background: #fef5e7;
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #f39c12;
        }}
    </style>
</head>
<body>
    <div class="container">
        <pre>{markdown_report}</pre>
    </div>
</body>
</html>"""
        
        return html
