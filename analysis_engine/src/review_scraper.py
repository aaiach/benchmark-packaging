"""Review scraper for fetching customer reviews from various sources.

Supports scraping reviews from:
- Amazon
- Google Shopping
- Retailer websites via Firecrawl
"""
import json
import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from firecrawl import FirecrawlApp
from openai import OpenAI

from .config import get_config
from .models import Product

logger = logging.getLogger(__name__)


@dataclass
class Review:
    """A single customer review."""
    review_id: str
    text: str
    rating: Optional[float] = None
    date: Optional[str] = None
    verified_purchase: Optional[bool] = None
    source: Optional[str] = None
    author: Optional[str] = None


class ReviewScraper:
    """Scrapes customer reviews for products."""
    
    def __init__(self):
        self.config = get_config()
        self.firecrawl = FirecrawlApp(api_key=self.config.firecrawl.api_key) if self.config.firecrawl.api_key else None
        self.openai_client = OpenAI(api_key=self.config.openai.api_key) if self.config.openai.api_key else None
    
    def scrape_product_reviews(
        self,
        product: Product,
        max_reviews: int = 50,
        min_length: int = 50
    ) -> List[Review]:
        """Scrape reviews for a product.
        
        Args:
            product: Product to scrape reviews for
            max_reviews: Maximum number of reviews to fetch
            min_length: Minimum review text length in characters
            
        Returns:
            List of Review objects
        """
        logger.info(f"Scraping reviews for {product.brand} - {product.full_name}")
        
        reviews = []
        
        # Try product URL first
        if product.product_url:
            reviews.extend(self._scrape_url_reviews(product.product_url, max_reviews))
        
        # If not enough reviews, try searching
        if len(reviews) < max_reviews and self.openai_client:
            search_reviews = self._search_and_scrape_reviews(
                product,
                max_reviews - len(reviews)
            )
            reviews.extend(search_reviews)
        
        # Filter by minimum length
        reviews = [r for r in reviews if len(r.text) >= min_length]
        
        logger.info(f"Found {len(reviews)} reviews for {product.brand}")
        return reviews[:max_reviews]
    
    def _scrape_url_reviews(self, url: str, max_reviews: int) -> List[Review]:
        """Scrape reviews from a specific URL using Firecrawl."""
        if not self.firecrawl:
            logger.warning("Firecrawl not configured, skipping URL scraping")
            return []
        
        try:
            logger.info(f"Scraping reviews from: {url}")
            
            # Scrape the page
            result = self.firecrawl.scrape_url(
                url,
                params={
                    'formats': ['markdown', 'html'],
                    'onlyMainContent': True
                }
            )
            
            if not result or 'markdown' not in result:
                logger.warning(f"No content scraped from {url}")
                return []
            
            # Extract reviews using LLM
            reviews = self._extract_reviews_with_llm(
                result['markdown'],
                url,
                max_reviews
            )
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            return []
    
    def _search_and_scrape_reviews(
        self,
        product: Product,
        max_reviews: int
    ) -> List[Review]:
        """Search for product reviews and scrape them."""
        if not self.openai_client:
            logger.warning("OpenAI not configured, skipping search")
            return []
        
        try:
            # Use OpenAI with web search to find review pages
            search_query = f"{product.brand} {product.full_name} customer reviews"
            
            logger.info(f"Searching for reviews: {search_query}")
            
            response = self.openai_client.chat.completions.create(
                model=self.config.openai.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that finds customer reviews for products."
                    },
                    {
                        "role": "user",
                        "content": f"Find and extract {max_reviews} customer reviews for: {search_query}\n\nReturn as JSON array with fields: text, rating (1-5), date, verified_purchase (bool)"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            reviews = []
            for i, review_data in enumerate(result.get('reviews', [])[:max_reviews]):
                review = Review(
                    review_id=f"search_{product.brand}_{i}",
                    text=review_data.get('text', ''),
                    rating=review_data.get('rating'),
                    date=review_data.get('date'),
                    verified_purchase=review_data.get('verified_purchase'),
                    source="web_search"
                )
                reviews.append(review)
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error searching for reviews: {e}")
            return []
    
    def _extract_reviews_with_llm(
        self,
        content: str,
        source_url: str,
        max_reviews: int
    ) -> List[Review]:
        """Extract reviews from scraped content using LLM."""
        if not self.openai_client:
            return []
        
        try:
            # Truncate content if too long
            max_content_length = 8000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "...[truncated]"
            
            response = self.openai_client.chat.completions.create(
                model=self.config.openai_mini.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Extract customer reviews from the provided content. Return as JSON array."
                    },
                    {
                        "role": "user",
                        "content": f"Extract up to {max_reviews} customer reviews from this content:\n\n{content}\n\nReturn JSON with array 'reviews', each having: text, rating (1-5 if available), date (if available), verified_purchase (bool if available)"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            reviews = []
            for i, review_data in enumerate(result.get('reviews', [])[:max_reviews]):
                review = Review(
                    review_id=f"{source_url}_{i}",
                    text=review_data.get('text', ''),
                    rating=review_data.get('rating'),
                    date=review_data.get('date'),
                    verified_purchase=review_data.get('verified_purchase'),
                    source=source_url
                )
                reviews.append(review)
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error extracting reviews with LLM: {e}")
            return []
    
    def scrape_all_products(
        self,
        products: List[Product],
        max_reviews_per_product: int = 50
    ) -> Dict[str, List[Review]]:
        """Scrape reviews for multiple products.
        
        Args:
            products: List of products to scrape
            max_reviews_per_product: Max reviews per product
            
        Returns:
            Dictionary mapping product key to list of reviews
        """
        all_reviews = {}
        
        for product in products:
            product_key = f"{product.brand}_{product.full_name}"
            reviews = self.scrape_product_reviews(
                product,
                max_reviews=max_reviews_per_product
            )
            all_reviews[product_key] = reviews
            
            # Rate limiting
            time.sleep(1)
        
        total_reviews = sum(len(r) for r in all_reviews.values())
        logger.info(f"Scraped {total_reviews} total reviews for {len(products)} products")
        
        return all_reviews
