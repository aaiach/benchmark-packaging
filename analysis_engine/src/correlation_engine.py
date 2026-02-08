"""Correlation engine for linking packaging attributes with customer satisfaction.

Performs statistical analysis to identify which packaging design elements
correlate with higher customer sentiment and satisfaction scores.
"""
import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import json

import numpy as np
from scipy import stats
import pandas as pd

from .models import (
    ReviewAnalysis,
    PackagingAttributeCorrelation,
    AttributeRanking,
    TopicCorrelation,
    ReviewPackagingCorrelationResult,
    VisualHierarchyAnalysis,
)

logger = logging.getLogger(__name__)


class CorrelationEngine:
    """Analyzes correlations between packaging attributes and customer satisfaction."""
    
    def __init__(self):
        """Initialize the correlation engine."""
        pass
    
    def analyze_correlations(
        self,
        review_analyses: Dict[str, List[ReviewAnalysis]],
        packaging_analyses: Dict[str, VisualHierarchyAnalysis],
        category: str
    ) -> ReviewPackagingCorrelationResult:
        """Analyze correlations between packaging attributes and review sentiment.
        
        Args:
            review_analyses: Dict mapping product key to list of review analyses
            packaging_analyses: Dict mapping product key to packaging visual analysis
            category: Product category name
            
        Returns:
            ReviewPackagingCorrelationResult with ranked attributes and insights
        """
        from datetime import datetime
        
        logger.info(f"Analyzing correlations for {len(review_analyses)} products")
        
        # Prepare data for correlation analysis
        correlation_data = self._prepare_correlation_data(
            review_analyses,
            packaging_analyses
        )
        
        # Calculate attribute correlations
        attribute_correlations = self._calculate_attribute_correlations(
            correlation_data
        )
        
        # Rank attributes by impact
        attribute_rankings = self._rank_attributes(attribute_correlations)
        
        # Calculate topic correlations
        topic_correlations = self._calculate_topic_correlations(review_analyses)
        
        # Generate product-specific insights
        product_insights = self._generate_product_insights(
            review_analyses,
            packaging_analyses
        )
        
        # Generate key findings
        key_findings = self._generate_key_findings(
            attribute_rankings,
            topic_correlations,
            product_insights
        )
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            attribute_rankings,
            topic_correlations,
            len(review_analyses)
        )
        
        # Count total reviews
        total_reviews = sum(len(reviews) for reviews in review_analyses.values())
        packaging_focused = sum(
            sum(1 for r in reviews if r.is_packaging_focused)
            for reviews in review_analyses.values()
        )
        
        return ReviewPackagingCorrelationResult(
            category=category,
            analysis_date=datetime.now().isoformat(),
            total_reviews=total_reviews,
            packaging_focused_reviews=packaging_focused,
            products_analyzed=len(review_analyses),
            attribute_rankings=attribute_rankings,
            topic_correlations=topic_correlations,
            product_insights=product_insights,
            key_findings=key_findings,
            executive_summary=executive_summary
        )
    
    def _prepare_correlation_data(
        self,
        review_analyses: Dict[str, List[ReviewAnalysis]],
        packaging_analyses: Dict[str, VisualHierarchyAnalysis]
    ) -> pd.DataFrame:
        """Prepare data for correlation analysis.
        
        Creates a DataFrame where each row is a product with:
        - Packaging attributes (colors, claims, layout features)
        - Average review sentiment
        - Topic-specific sentiments
        """
        data_rows = []
        
        for product_key, reviews in review_analyses.items():
            if not reviews:
                continue
            
            # Get packaging analysis
            packaging = packaging_analyses.get(product_key)
            if not packaging:
                continue
            
            # Calculate average sentiment
            avg_sentiment = np.mean([r.sentiment.overall_score for r in reviews])
            
            # Extract packaging attributes
            row = {
                'product_key': product_key,
                'avg_sentiment': avg_sentiment,
                'review_count': len(reviews)
            }
            
            # Color attributes
            if packaging.chromatic_mapping:
                row['num_colors'] = len(packaging.chromatic_mapping.color_palette)
                row['background_color'] = packaging.chromatic_mapping.background_colors[0] if packaging.chromatic_mapping.background_colors else None
                row['surface_finish'] = packaging.chromatic_mapping.surface_finish
                row['color_harmony'] = packaging.chromatic_mapping.color_harmony
            
            # Typography/text attributes
            if packaging.textual_inventory:
                row['num_text_blocks'] = len(packaging.textual_inventory.all_text_blocks)
                row['num_claims'] = len(packaging.textual_inventory.claims_summary)
                row['num_emphasized_claims'] = len(packaging.textual_inventory.emphasized_claims)
                row['readability'] = packaging.textual_inventory.readability_assessment
            
            # Trust marks
            if packaging.asset_symbolism:
                row['num_trust_marks'] = len(packaging.asset_symbolism.trust_marks)
                row['num_graphical_assets'] = len(packaging.asset_symbolism.graphical_assets)
            
            # Visual hierarchy
            row['hierarchy_clarity'] = packaging.hierarchy_clarity_score
            row['visual_balance'] = packaging.massing.balance_type
            
            # Topic-specific sentiments
            topic_sentiments = defaultdict(list)
            for review in reviews:
                for topic in review.packaging_topics:
                    topic_sentiments[topic.topic].append(topic.sentiment)
            
            for topic, sentiments in topic_sentiments.items():
                row[f'sentiment_{topic}'] = np.mean(sentiments)
            
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        logger.info(f"Prepared correlation data with {len(df)} products and {len(df.columns)} features")
        
        return df
    
    def _calculate_attribute_correlations(
        self,
        data: pd.DataFrame
    ) -> List[PackagingAttributeCorrelation]:
        """Calculate correlations between packaging attributes and sentiment.
        
        Args:
            data: DataFrame with packaging attributes and sentiment scores
            
        Returns:
            List of PackagingAttributeCorrelation objects
        """
        correlations = []
        
        if len(data) < 3:
            logger.warning("Not enough products for correlation analysis")
            return correlations
        
        # Numerical attribute correlations
        numerical_attrs = {
            'num_colors': 'color',
            'num_text_blocks': 'typography',
            'num_claims': 'claim',
            'num_emphasized_claims': 'claim',
            'num_trust_marks': 'trust_mark',
            'num_graphical_assets': 'layout',
            'hierarchy_clarity': 'layout'
        }
        
        for attr, category in numerical_attrs.items():
            if attr not in data.columns:
                continue
            
            # Remove NaN values
            clean_data = data[[attr, 'avg_sentiment']].dropna()
            
            if len(clean_data) < 3:
                continue
            
            # Calculate Pearson correlation
            try:
                corr, p_value = stats.pearsonr(
                    clean_data[attr],
                    clean_data['avg_sentiment']
                )
                
                # Calculate average sentiment for products with this attribute
                avg_sentiment = clean_data['avg_sentiment'].mean()
                
                # Determine impact category
                impact = self._categorize_impact(corr, p_value)
                
                correlations.append(PackagingAttributeCorrelation(
                    attribute_category=category,
                    attribute_value=attr.replace('_', ' '),
                    correlation_score=float(corr),
                    statistical_significance=float(p_value),
                    average_sentiment=float(avg_sentiment),
                    sample_size=len(clean_data),
                    impact_category=impact
                ))
            except Exception as e:
                logger.error(f"Error calculating correlation for {attr}: {e}")
                continue
        
        # Categorical attribute correlations
        categorical_attrs = {
            'surface_finish': 'surface_finish',
            'color_harmony': 'color',
            'visual_balance': 'layout'
        }
        
        for attr, category in categorical_attrs.items():
            if attr not in data.columns:
                continue
            
            # Calculate average sentiment for each value
            grouped = data.groupby(attr)['avg_sentiment'].agg(['mean', 'count']).reset_index()
            
            for _, row in grouped.iterrows():
                if row['count'] < 2:
                    continue
                
                # Compare this value to others
                this_sentiment = row['mean']
                other_sentiment = data[data[attr] != row[attr]]['avg_sentiment'].mean()
                
                # Calculate effect size (Cohen's d)
                corr_score = (this_sentiment - other_sentiment) / data['avg_sentiment'].std()
                corr_score = np.clip(corr_score, -1, 1)  # Clip to [-1, 1]
                
                # Statistical significance via t-test
                try:
                    _, p_value = stats.ttest_ind(
                        data[data[attr] == row[attr]]['avg_sentiment'],
                        data[data[attr] != row[attr]]['avg_sentiment']
                    )
                except:
                    p_value = 1.0
                
                impact = self._categorize_impact(corr_score, p_value)
                
                correlations.append(PackagingAttributeCorrelation(
                    attribute_category=category,
                    attribute_value=f"{attr}: {row[attr]}",
                    correlation_score=float(corr_score),
                    statistical_significance=float(p_value),
                    average_sentiment=float(this_sentiment),
                    sample_size=int(row['count']),
                    impact_category=impact
                ))
        
        logger.info(f"Calculated {len(correlations)} attribute correlations")
        return correlations
    
    def _categorize_impact(
        self,
        correlation: float,
        p_value: float
    ) -> str:
        """Categorize the impact of a correlation.
        
        Args:
            correlation: Correlation coefficient
            p_value: Statistical significance
            
        Returns:
            Impact category string
        """
        # Consider both strength and significance
        is_significant = p_value < 0.05
        
        if not is_significant:
            return "neutral"
        
        if correlation > 0.5:
            return "strong_positive"
        elif correlation > 0.2:
            return "positive"
        elif correlation < -0.5:
            return "strong_negative"
        elif correlation < -0.2:
            return "negative"
        else:
            return "neutral"
    
    def _rank_attributes(
        self,
        correlations: List[PackagingAttributeCorrelation]
    ) -> List[AttributeRanking]:
        """Rank attributes by customer impact.
        
        Args:
            correlations: List of correlations
            
        Returns:
            Ranked list of attributes
        """
        # Sort by absolute correlation (impact strength) and significance
        def sort_key(corr):
            # Penalize non-significant correlations
            significance_penalty = 1.0 if corr.statistical_significance < 0.05 else 0.5
            return abs(corr.correlation_score) * significance_penalty
        
        sorted_correlations = sorted(
            correlations,
            key=sort_key,
            reverse=True
        )
        
        # Create rankings
        rankings = []
        for rank, corr in enumerate(sorted_correlations[:20], 1):  # Top 20
            # Extract supporting evidence (placeholder - would need review text)
            evidence = [
                f"Correlation: {corr.correlation_score:.2f} (p={corr.statistical_significance:.3f})",
                f"Average sentiment: {corr.average_sentiment:.2f}",
                f"Based on {corr.sample_size} products"
            ]
            
            rankings.append(AttributeRanking(
                rank=rank,
                attribute=corr,
                supporting_evidence=evidence
            ))
        
        logger.info(f"Ranked {len(rankings)} attributes")
        return rankings
    
    def _calculate_topic_correlations(
        self,
        review_analyses: Dict[str, List[ReviewAnalysis]]
    ) -> List[TopicCorrelation]:
        """Calculate correlations between topic mentions and sentiment.
        
        Args:
            review_analyses: Review analyses by product
            
        Returns:
            List of topic correlations
        """
        # Collect all reviews
        all_reviews = []
        for reviews in review_analyses.values():
            all_reviews.extend(reviews)
        
        if not all_reviews:
            return []
        
        # Analyze each topic
        topics = [
            "design", "readability", "claims_believability", "shelf_appeal",
            "color", "typography", "trust_marks", "overall_appearance"
        ]
        
        topic_correlations = []
        
        for topic in topics:
            # Reviews mentioning this topic
            with_topic = [
                r for r in all_reviews
                if any(t.topic == topic for t in r.packaging_topics)
            ]
            
            # Reviews not mentioning this topic
            without_topic = [
                r for r in all_reviews
                if not any(t.topic == topic for t in r.packaging_topics)
            ]
            
            if not with_topic:
                continue
            
            # Calculate average sentiments
            avg_with = np.mean([r.sentiment.overall_score for r in with_topic])
            avg_without = np.mean([r.sentiment.overall_score for r in without_topic]) if without_topic else 0.0
            
            topic_correlations.append(TopicCorrelation(
                topic=topic,
                mention_count=len(with_topic),
                average_sentiment_when_mentioned=float(avg_with),
                average_sentiment_when_not_mentioned=float(avg_without),
                sentiment_delta=float(avg_with - avg_without)
            ))
        
        # Sort by sentiment delta (highest positive impact first)
        topic_correlations.sort(key=lambda x: x.sentiment_delta, reverse=True)
        
        logger.info(f"Calculated {len(topic_correlations)} topic correlations")
        return topic_correlations
    
    def _generate_product_insights(
        self,
        review_analyses: Dict[str, List[ReviewAnalysis]],
        packaging_analyses: Dict[str, VisualHierarchyAnalysis]
    ) -> List[Dict[str, Any]]:
        """Generate per-product insights.
        
        Args:
            review_analyses: Review analyses by product
            packaging_analyses: Packaging analyses by product
            
        Returns:
            List of product insight dictionaries
        """
        insights = []
        
        for product_key, reviews in review_analyses.items():
            if not reviews:
                continue
            
            packaging = packaging_analyses.get(product_key)
            
            # Extract brand and product name
            brand = reviews[0].brand
            product_name = reviews[0].product_name
            
            # Calculate metrics
            avg_sentiment = np.mean([r.sentiment.overall_score for r in reviews])
            packaging_focus_rate = sum(1 for r in reviews if r.is_packaging_focused) / len(reviews)
            
            # Top packaging topics
            topic_counts = defaultdict(int)
            for review in reviews:
                for topic in review.packaging_topics:
                    topic_counts[topic.topic] += 1
            
            top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            insight = {
                "product_key": product_key,
                "brand": brand,
                "product_name": product_name,
                "review_count": len(reviews),
                "average_sentiment": float(avg_sentiment),
                "packaging_focus_rate": float(packaging_focus_rate),
                "top_packaging_topics": [t[0] for t in top_topics],
                "packaging_attributes": {}
            }
            
            # Add packaging attributes if available
            if packaging:
                insight["packaging_attributes"] = {
                    "hierarchy_clarity": packaging.hierarchy_clarity_score,
                    "num_colors": len(packaging.chromatic_mapping.color_palette) if packaging.chromatic_mapping else 0,
                    "num_claims": len(packaging.textual_inventory.claims_summary) if packaging.textual_inventory else 0,
                    "num_trust_marks": len(packaging.asset_symbolism.trust_marks) if packaging.asset_symbolism else 0,
                }
            
            insights.append(insight)
        
        # Sort by sentiment (highest first)
        insights.sort(key=lambda x: x['average_sentiment'], reverse=True)
        
        return insights
    
    def _generate_key_findings(
        self,
        attribute_rankings: List[AttributeRanking],
        topic_correlations: List[TopicCorrelation],
        product_insights: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate key strategic findings.
        
        Args:
            attribute_rankings: Ranked attributes
            topic_correlations: Topic correlations
            product_insights: Product-specific insights
            
        Returns:
            List of key finding strings
        """
        findings = []
        
        # Top attribute finding
        if attribute_rankings:
            top_attr = attribute_rankings[0].attribute
            findings.append(
                f"Strongest correlation: {top_attr.attribute_value} shows {top_attr.impact_category.replace('_', ' ')} "
                f"impact with {top_attr.correlation_score:.2f} correlation coefficient."
            )
        
        # Topic finding
        if topic_correlations:
            top_topic = topic_correlations[0]
            findings.append(
                f"Reviews mentioning '{top_topic.topic}' show {abs(top_topic.sentiment_delta):.2f} "
                f"{'higher' if top_topic.sentiment_delta > 0 else 'lower'} sentiment on average."
            )
        
        # Best performing product
        if product_insights:
            best_product = product_insights[0]
            findings.append(
                f"{best_product['brand']} achieves highest satisfaction ({best_product['average_sentiment']:.2f}) "
                f"with {best_product['packaging_focus_rate']:.0%} of reviews mentioning packaging."
            )
        
        # Packaging impact finding
        if product_insights:
            high_focus = [p for p in product_insights if p['packaging_focus_rate'] > 0.3]
            if high_focus:
                avg_sentiment_high = np.mean([p['average_sentiment'] for p in high_focus])
                findings.append(
                    f"Products with high packaging mention rate (>30%) average {avg_sentiment_high:.2f} sentiment score."
                )
        
        return findings[:5]  # Top 5 findings
    
    def _generate_executive_summary(
        self,
        attribute_rankings: List[AttributeRanking],
        topic_correlations: List[TopicCorrelation],
        num_products: int
    ) -> str:
        """Generate executive summary.
        
        Args:
            attribute_rankings: Ranked attributes
            topic_correlations: Topic correlations
            num_products: Number of products analyzed
            
        Returns:
            Executive summary string
        """
        summary_parts = []
        
        summary_parts.append(
            f"Analysis of {num_products} products reveals significant correlations between "
            f"packaging design elements and customer satisfaction."
        )
        
        if attribute_rankings:
            top_3 = [r.attribute.attribute_value for r in attribute_rankings[:3]]
            summary_parts.append(
                f"Key drivers of satisfaction include: {', '.join(top_3)}."
            )
        
        if topic_correlations:
            positive_topics = [t for t in topic_correlations if t.sentiment_delta > 0]
            if positive_topics:
                summary_parts.append(
                    f"Customer reviews focusing on {positive_topics[0].topic} show "
                    f"consistently higher satisfaction scores."
                )
        
        return " ".join(summary_parts)
