"""Visualization tools for review-packaging correlation results.

Generates visualizations and reports for the correlation analysis,
including charts, tables, and formatted output.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class CorrelationVisualizer:
    """Creates visualizations for correlation analysis results."""
    
    def __init__(self, output_dir: Path):
        """Initialize visualizer.
        
        Args:
            output_dir: Directory to save visualizations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self,
        correlation_data: Dict[str, Any],
        output_filename: str = "correlation_report.md"
    ) -> Path:
        """Generate a markdown report of the correlation analysis.
        
        Args:
            correlation_data: Correlation analysis results
            output_filename: Name of output file
            
        Returns:
            Path to generated report
        """
        report_path = self.output_dir / output_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# Review-Packaging Correlation Analysis\n\n")
            f.write(f"**Category:** {correlation_data.get('category', 'N/A')}\n\n")
            f.write(f"**Analysis Date:** {correlation_data.get('analysis_date', 'N/A')}\n\n")
            f.write(f"**Products Analyzed:** {correlation_data.get('products_analyzed', 0)}\n\n")
            f.write(f"**Total Reviews:** {correlation_data.get('total_reviews', 0)}\n\n")
            f.write(f"**Packaging-Focused Reviews:** {correlation_data.get('packaging_focused_reviews', 0)}\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(f"{correlation_data.get('executive_summary', 'No summary available.')}\n\n")
            
            # Key Findings
            f.write("## Key Findings\n\n")
            findings = correlation_data.get('key_findings', [])
            if findings:
                for i, finding in enumerate(findings, 1):
                    f.write(f"{i}. {finding}\n\n")
            else:
                f.write("No key findings available.\n\n")
            
            # Top Packaging Attributes
            f.write("## Top Packaging Attributes by Customer Impact\n\n")
            f.write("| Rank | Attribute | Category | Correlation | Significance | Impact |\n")
            f.write("|------|-----------|----------|-------------|--------------|--------|\n")
            
            rankings = correlation_data.get('attribute_rankings', [])
            for ranking in rankings[:15]:  # Top 15
                attr = ranking['attribute']
                impact_icon = self._get_impact_icon(attr['impact_category'])
                
                f.write(
                    f"| {ranking['rank']} | {attr['attribute_value']} | "
                    f"{attr['attribute_category']} | {attr['correlation_score']:+.3f} | "
                    f"p={attr['statistical_significance']:.3f} | {impact_icon} |\n"
                )
            
            f.write("\n")
            
            # Topic Correlations
            f.write("## Packaging Topic Mentions vs. Sentiment\n\n")
            f.write("| Topic | Mentions | Avg Sentiment (Mentioned) | Avg Sentiment (Not Mentioned) | Delta |\n")
            f.write("|-------|----------|---------------------------|------------------------------|-------|\n")
            
            topic_correlations = correlation_data.get('topic_correlations', [])
            for topic in topic_correlations:
                delta_icon = "📈" if topic['sentiment_delta'] > 0 else "📉" if topic['sentiment_delta'] < 0 else "➡️"
                
                f.write(
                    f"| {topic['topic'].replace('_', ' ').title()} | "
                    f"{topic['mention_count']} | "
                    f"{topic['average_sentiment_when_mentioned']:+.2f} | "
                    f"{topic['average_sentiment_when_not_mentioned']:+.2f} | "
                    f"{delta_icon} {topic['sentiment_delta']:+.2f} |\n"
                )
            
            f.write("\n")
            
            # Product Insights
            f.write("## Product-Level Insights\n\n")
            f.write("| Rank | Brand | Product | Avg Sentiment | Reviews | Packaging Focus Rate |\n")
            f.write("|------|-------|---------|---------------|---------|---------------------|\n")
            
            product_insights = correlation_data.get('product_insights', [])
            for i, product in enumerate(product_insights[:10], 1):  # Top 10
                sentiment_icon = "😀" if product['average_sentiment'] > 0.5 else "🙂" if product['average_sentiment'] > 0 else "😐" if product['average_sentiment'] > -0.5 else "☹️"
                
                f.write(
                    f"| {i} | {product['brand']} | {product['product_name']} | "
                    f"{sentiment_icon} {product['average_sentiment']:+.2f} | "
                    f"{product['review_count']} | "
                    f"{product['packaging_focus_rate']:.0%} |\n"
                )
            
            f.write("\n")
            
            # Methodology
            f.write("## Methodology\n\n")
            f.write("### Sentiment Analysis\n\n")
            f.write("- **Model:** Transformer-based sentiment classification (DistilBERT)\n")
            f.write("- **Scale:** -1 (very negative) to +1 (very positive)\n")
            f.write("- **Granularity:** Sentence-level analysis aggregated to review level\n\n")
            
            f.write("### Topic Extraction\n\n")
            f.write("- **Method:** Keyword pattern matching with contextual analysis\n")
            f.write("- **Topics:** Design, Readability, Claims Believability, Shelf Appeal, ")
            f.write("Color, Typography, Trust Marks, Overall Appearance\n\n")
            
            f.write("### Correlation Analysis\n\n")
            f.write("- **Statistical Test:** Pearson correlation for numerical attributes, ")
            f.write("t-test for categorical attributes\n")
            f.write("- **Significance Level:** p < 0.05\n")
            f.write("- **Sample Size:** Minimum 3 products per correlation\n\n")
            
            # Appendix: Detailed Attribute Data
            f.write("## Appendix: Detailed Attribute Correlations\n\n")
            
            for ranking in rankings:
                attr = ranking['attribute']
                f.write(f"### {ranking['rank']}. {attr['attribute_value']}\n\n")
                f.write(f"- **Category:** {attr['attribute_category']}\n")
                f.write(f"- **Correlation:** {attr['correlation_score']:+.3f}\n")
                f.write(f"- **P-value:** {attr['statistical_significance']:.4f}\n")
                f.write(f"- **Average Sentiment:** {attr['average_sentiment']:+.2f}\n")
                f.write(f"- **Sample Size:** {attr['sample_size']} products\n")
                f.write(f"- **Impact:** {attr['impact_category'].replace('_', ' ').title()}\n\n")
                
                if ranking.get('supporting_evidence'):
                    f.write("**Supporting Evidence:**\n\n")
                    for evidence in ranking['supporting_evidence']:
                        f.write(f"- {evidence}\n")
                    f.write("\n")
        
        logger.info(f"Generated correlation report: {report_path}")
        return report_path
    
    def _get_impact_icon(self, impact_category: str) -> str:
        """Get an icon for impact category.
        
        Args:
            impact_category: Impact category string
            
        Returns:
            Icon string
        """
        icons = {
            "strong_positive": "🔺🔺",
            "positive": "🔺",
            "neutral": "➖",
            "negative": "🔻",
            "strong_negative": "🔻🔻"
        }
        return icons.get(impact_category, "❓")
    
    def generate_summary_json(
        self,
        correlation_data: Dict[str, Any],
        output_filename: str = "correlation_summary.json"
    ) -> Path:
        """Generate a concise JSON summary for API/frontend consumption.
        
        Args:
            correlation_data: Correlation analysis results
            output_filename: Name of output file
            
        Returns:
            Path to generated summary
        """
        summary = {
            "category": correlation_data.get('category'),
            "analysis_date": correlation_data.get('analysis_date'),
            "stats": {
                "total_reviews": correlation_data.get('total_reviews'),
                "packaging_focused_reviews": correlation_data.get('packaging_focused_reviews'),
                "products_analyzed": correlation_data.get('products_analyzed'),
                "packaging_focus_rate": (
                    correlation_data.get('packaging_focused_reviews', 0) / 
                    max(correlation_data.get('total_reviews', 1), 1)
                )
            },
            "executive_summary": correlation_data.get('executive_summary'),
            "key_findings": correlation_data.get('key_findings', []),
            "top_attributes": [
                {
                    "rank": r['rank'],
                    "attribute": r['attribute']['attribute_value'],
                    "category": r['attribute']['attribute_category'],
                    "correlation": r['attribute']['correlation_score'],
                    "impact": r['attribute']['impact_category']
                }
                for r in correlation_data.get('attribute_rankings', [])[:10]
            ],
            "top_topics": [
                {
                    "topic": t['topic'],
                    "mentions": t['mention_count'],
                    "sentiment_delta": t['sentiment_delta']
                }
                for t in correlation_data.get('topic_correlations', [])[:5]
            ],
            "best_products": [
                {
                    "brand": p['brand'],
                    "product": p['product_name'],
                    "sentiment": p['average_sentiment'],
                    "reviews": p['review_count']
                }
                for p in correlation_data.get('product_insights', [])[:5]
            ]
        }
        
        summary_path = self.output_dir / output_filename
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated correlation summary: {summary_path}")
        return summary_path
    
    def generate_csv_export(
        self,
        correlation_data: Dict[str, Any],
        output_filename: str = "attribute_rankings.csv"
    ) -> Path:
        """Generate CSV export of attribute rankings.
        
        Args:
            correlation_data: Correlation analysis results
            output_filename: Name of output file
            
        Returns:
            Path to generated CSV
        """
        csv_path = self.output_dir / output_filename
        
        with open(csv_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("Rank,Attribute,Category,Correlation,P-Value,Avg Sentiment,Sample Size,Impact\n")
            
            # Data rows
            rankings = correlation_data.get('attribute_rankings', [])
            for ranking in rankings:
                attr = ranking['attribute']
                f.write(
                    f"{ranking['rank']},"
                    f"\"{attr['attribute_value']}\","
                    f"{attr['attribute_category']},"
                    f"{attr['correlation_score']:.4f},"
                    f"{attr['statistical_significance']:.4f},"
                    f"{attr['average_sentiment']:.4f},"
                    f"{attr['sample_size']},"
                    f"{attr['impact_category']}\n"
                )
        
        logger.info(f"Generated CSV export: {csv_path}")
        return csv_path


def visualize_correlation_results(
    correlation_file: Path,
    output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """Generate all visualizations for a correlation analysis result.
    
    Args:
        correlation_file: Path to correlation JSON file
        output_dir: Optional output directory (defaults to same as input)
        
    Returns:
        Dictionary mapping visualization type to output path
    """
    # Load correlation data
    with open(correlation_file, 'r', encoding='utf-8') as f:
        correlation_data = json.load(f)
    
    # Set output directory
    if output_dir is None:
        output_dir = correlation_file.parent
    
    # Create visualizer
    visualizer = CorrelationVisualizer(output_dir)
    
    # Generate all outputs
    outputs = {}
    
    # Markdown report
    outputs['report'] = visualizer.generate_report(correlation_data)
    
    # JSON summary
    outputs['summary'] = visualizer.generate_summary_json(correlation_data)
    
    # CSV export
    outputs['csv'] = visualizer.generate_csv_export(correlation_data)
    
    logger.info(f"Generated {len(outputs)} visualization outputs")
    
    return outputs
