"""Review analyzer with NLP for sentiment and packaging topic extraction.

Uses transformer-based models for sentiment analysis and keyword/phrase extraction
to identify packaging-related topics in customer reviews.
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import hashlib

import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

from .models import (
    ReviewAnalysis,
    ReviewSentiment,
    PackagingTopic,
)
from .review_scraper import Review

logger = logging.getLogger(__name__)


# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


class ReviewAnalyzer:
    """Analyzes customer reviews for sentiment and packaging-related topics."""
    
    # Packaging topic keywords and phrases
    TOPIC_KEYWORDS = {
        "design": [
            r'\bdesign', r'\blook', r'\bappearance', r'\baesthetic', r'\bvisual',
            r'\bstyle', r'\bmodern', r'\belegant', r'\battractive', r'\bbeautiful',
            r'\bpretty', r'\bpackaging design', r'\bpackage look'
        ],
        "readability": [
            r'\bread', r'\blegible', r'\bclear', r'\btext', r'\bfont', r'\blabel',
            r'\bhard to read', r'\beasy to read', r'\bcan\'t read', r'\breadable',
            r'\bwriting', r'\bprint', r'\binstructions'
        ],
        "claims_believability": [
            r'\bclaim', r'\bbelieve', r'\btrust', r'\bhonest', r'\bauthentic',
            r'\bgenuine', r'\bmisleading', r'\bdeceptive', r'\bexaggerat',
            r'\btruthful', r'\bcredible', r'\bpromise', r'\bguarantee'
        ],
        "shelf_appeal": [
            r'\bshelf', r'\bstand out', r'\bcatch.*eye', r'\bnotice', r'\bgrab.*attention',
            r'\bvisible', r'\bsee on shelf', r'\bstore display', r'\bpops out'
        ],
        "color": [
            r'\bcolor', r'\bcolour', r'\bblue', r'\bgreen', r'\bred', r'\byellow',
            r'\bwhite', r'\bblack', r'\bbright', r'\bdark', r'\bvibrant', r'\bpastel',
            r'\bcolorful'
        ],
        "typography": [
            r'\bfont', r'\btypeface', r'\btext size', r'\bbold', r'\bitalic',
            r'\blettering', r'\bwriting style', r'\bcapital', r'\buppercase'
        ],
        "trust_marks": [
            r'\bcertified', r'\borganic', r'\bcertification', r'\bseal', r'\bbadge',
            r'\blogo', r'\blabel.*organic', r'\bnon-gmo', r'\bfair trade', r'\beco',
            r'\btrust.*mark'
        ],
        "overall_appearance": [
            r'\bpackage', r'\bpackaging', r'\bbox', r'\bcontainer', r'\bwrapper',
            r'\blooks like', r'\bappears', r'\bpresentation', r'\boverall look'
        ]
    }
    
    def __init__(self, use_gpu: bool = False):
        """Initialize the review analyzer.
        
        Args:
            use_gpu: Whether to use GPU for inference (if available)
        """
        self.device = 0 if use_gpu and torch.cuda.is_available() else -1
        
        logger.info("Loading sentiment analysis model...")
        # Use a robust sentiment analysis model
        try:
            # Try to use a good sentiment model
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=self.device,
                truncation=True,
                max_length=512
            )
        except Exception as e:
            logger.warning(f"Failed to load preferred model, using default: {e}")
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                device=self.device,
                truncation=True,
                max_length=512
            )
        
        logger.info("Sentiment analysis model loaded successfully")
        
        # Stop words for filtering
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            self.stop_words = set()
    
    def analyze_review(
        self,
        review: Review,
        brand: str,
        product_name: str
    ) -> ReviewAnalysis:
        """Analyze a single review for sentiment and packaging topics.
        
        Args:
            review: Review to analyze
            brand: Product brand
            product_name: Product name
            
        Returns:
            ReviewAnalysis with sentiment and topic extraction
        """
        # Overall sentiment
        sentiment = self._analyze_sentiment(review.text)
        
        # Extract packaging topics
        packaging_topics = self._extract_packaging_topics(review.text, sentiment)
        
        # Determine if review is packaging-focused
        is_packaging_focused = len(packaging_topics) > 0 and any(
            topic.relevance_score > 0.3 for topic in packaging_topics
        )
        
        return ReviewAnalysis(
            review_id=review.review_id,
            brand=brand,
            product_name=product_name,
            review_text=review.text,
            rating=review.rating,
            sentiment=sentiment,
            packaging_topics=packaging_topics,
            is_packaging_focused=is_packaging_focused,
            review_date=review.date,
            verified_purchase=review.verified_purchase
        )
    
    def analyze_reviews_batch(
        self,
        reviews: List[Review],
        brand: str,
        product_name: str,
        batch_size: int = 16
    ) -> List[ReviewAnalysis]:
        """Analyze multiple reviews in batches for efficiency.
        
        Args:
            reviews: List of reviews to analyze
            brand: Product brand
            product_name: Product name
            batch_size: Batch size for processing
            
        Returns:
            List of ReviewAnalysis objects
        """
        logger.info(f"Analyzing {len(reviews)} reviews for {brand}")
        
        analyses = []
        for review in reviews:
            try:
                analysis = self.analyze_review(review, brand, product_name)
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing review {review.review_id}: {e}")
                continue
        
        logger.info(f"Successfully analyzed {len(analyses)}/{len(reviews)} reviews")
        return analyses
    
    def _analyze_sentiment(self, text: str) -> ReviewSentiment:
        """Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            ReviewSentiment object
        """
        try:
            # Split into sentences if text is long
            sentences = sent_tokenize(text)
            
            # Analyze each sentence
            sentiments = []
            for sentence in sentences:
                if len(sentence.strip()) < 10:  # Skip very short sentences
                    continue
                
                result = self.sentiment_pipeline(sentence)[0]
                
                # Convert to -1 to 1 scale
                score = result['score'] if result['label'] == 'POSITIVE' else -result['score']
                sentiments.append(score)
            
            # Average sentiment
            if not sentiments:
                sentiments = [0.0]
            
            avg_sentiment = sum(sentiments) / len(sentiments)
            confidence = sum(abs(s) for s in sentiments) / len(sentiments)
            
            # Determine label
            if avg_sentiment > 0.6:
                label = "very_positive"
            elif avg_sentiment > 0.2:
                label = "positive"
            elif avg_sentiment > -0.2:
                label = "neutral"
            elif avg_sentiment > -0.6:
                label = "negative"
            else:
                label = "very_negative"
            
            return ReviewSentiment(
                overall_score=avg_sentiment,
                confidence=confidence,
                sentiment_label=label
            )
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return ReviewSentiment(
                overall_score=0.0,
                confidence=0.0,
                sentiment_label="neutral"
            )
    
    def _extract_packaging_topics(
        self,
        text: str,
        sentiment: ReviewSentiment
    ) -> List[PackagingTopic]:
        """Extract packaging-related topics from review text.
        
        Args:
            text: Review text
            sentiment: Overall review sentiment
            
        Returns:
            List of PackagingTopic objects
        """
        text_lower = text.lower()
        topics = []
        
        for topic_name, patterns in self.TOPIC_KEYWORDS.items():
            # Find all matches for this topic
            mentions = []
            mention_contexts = []
            
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    mentions.append(match.group(0))
                    
                    # Extract context (sentence containing the match)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()
                    mention_contexts.append(context)
            
            if mentions:
                # Calculate topic sentiment (context-specific)
                topic_sentiment = self._analyze_topic_sentiment(
                    mention_contexts,
                    sentiment.overall_score
                )
                
                # Relevance based on number of mentions and context
                relevance = min(1.0, len(mentions) * 0.2)
                
                topics.append(PackagingTopic(
                    topic=topic_name,
                    sentiment=topic_sentiment,
                    relevance_score=relevance,
                    mentioned_phrases=mention_contexts[:3]  # Top 3 contexts
                ))
        
        return topics
    
    def _analyze_topic_sentiment(
        self,
        contexts: List[str],
        overall_sentiment: float
    ) -> float:
        """Analyze sentiment specifically for a topic's mentions.
        
        Args:
            contexts: List of context strings mentioning the topic
            overall_sentiment: Overall review sentiment as fallback
            
        Returns:
            Sentiment score for this specific topic
        """
        if not contexts:
            return overall_sentiment
        
        try:
            sentiments = []
            for context in contexts[:5]:  # Analyze up to 5 contexts
                result = self.sentiment_pipeline(context)[0]
                score = result['score'] if result['label'] == 'POSITIVE' else -result['score']
                sentiments.append(score)
            
            return sum(sentiments) / len(sentiments)
        except:
            return overall_sentiment
    
    def aggregate_product_insights(
        self,
        analyses: List[ReviewAnalysis]
    ) -> Dict[str, Any]:
        """Aggregate insights from multiple reviews for a product.
        
        Args:
            analyses: List of review analyses for a product
            
        Returns:
            Dictionary with aggregated insights
        """
        if not analyses:
            return {}
        
        total_reviews = len(analyses)
        packaging_focused = sum(1 for a in analyses if a.is_packaging_focused)
        
        # Average sentiment
        avg_sentiment = sum(a.sentiment.overall_score for a in analyses) / total_reviews
        
        # Topic frequency and sentiment
        topic_stats = defaultdict(lambda: {"count": 0, "sentiment_sum": 0.0})
        
        for analysis in analyses:
            for topic in analysis.packaging_topics:
                topic_stats[topic.topic]["count"] += 1
                topic_stats[topic.topic]["sentiment_sum"] += topic.sentiment
        
        topic_insights = {}
        for topic_name, stats in topic_stats.items():
            topic_insights[topic_name] = {
                "mention_rate": stats["count"] / total_reviews,
                "average_sentiment": stats["sentiment_sum"] / stats["count"] if stats["count"] > 0 else 0.0,
                "mentions": stats["count"]
            }
        
        return {
            "total_reviews": total_reviews,
            "packaging_focused_reviews": packaging_focused,
            "packaging_focus_rate": packaging_focused / total_reviews,
            "average_sentiment": avg_sentiment,
            "topic_insights": topic_insights
        }
