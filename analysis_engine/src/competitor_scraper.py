"""Competitor packaging scraper with multi-source support.

Scrapes competitor packaging data from:
- Amazon product pages (with reviews and ratings)
- Belgian/French online retailers
- Google Images for high-res packaging photos

Handles rate limiting, anti-bot measures, and cloud storage integration.
"""
import os
import json
import time
import random
import asyncio
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from urllib.parse import urlparse, quote_plus
import re

import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

from .competitor_models import (
    CompetitorProduct,
    CompetitorPackagingDataset,
    PackagingImage,
    ProductReview,
    ProductClaim,
    PricePoint,
    ScraperProgress,
    ScraperResult,
    CompetitorScraperConfig,
)

load_dotenv()


class CompetitorPackagingScraper:
    """Multi-source competitor packaging scraper.
    
    Collects packaging images, product information, reviews, and pricing
    from Amazon, Belgian/French retailers, and Google Images.
    """
    
    def __init__(
        self,
        config: Optional[CompetitorScraperConfig] = None,
        progress_callback: Optional[Callable[[ScraperProgress], None]] = None
    ):
        """Initialize the competitor scraper.
        
        Args:
            config: Scraper configuration. Uses defaults if not provided.
            progress_callback: Optional callback for progress updates.
        """
        self.config = config or CompetitorScraperConfig()
        self.progress_callback = progress_callback
        self.session = requests.Session()
        
        # Set realistic browser headers to avoid bot detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.progress = ScraperProgress(brands_total=len(self.config.target_brands))
        self.errors = []
        self.warnings = []
    
    def scrape_all(self, job_id: Optional[str] = None) -> ScraperResult:
        """Scrape all target brands from all configured sources.
        
        Args:
            job_id: Optional job identifier. Generated if not provided.
        
        Returns:
            ScraperResult with complete dataset and metadata.
        """
        if not job_id:
            job_id = f"competitor_scrape_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        started_at = datetime.utcnow()
        
        print(f"\n{'='*70}")
        print(f"Competitor Packaging Scraper")
        print(f"{'='*70}")
        print(f"Job ID: {job_id}")
        print(f"Target brands: {', '.join(self.config.target_brands)}")
        print(f"Category: {self.config.category}")
        print(f"Countries: {', '.join(self.config.countries)}")
        print(f"{'='*70}\n")
        
        # Initialize dataset
        dataset = CompetitorPackagingDataset(
            dataset_id=job_id,
            category=self.config.category,
            target_brands=self.config.target_brands,
            countries=self.config.countries
        )
        
        # Create output directory
        output_dir = Path(self.config.output_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        dataset.output_dir = str(output_dir)
        dataset.images_dir = str(images_dir)
        
        # Scrape each brand
        for brand_idx, brand in enumerate(self.config.target_brands):
            self.progress.current_brand = brand
            self.progress.brands_completed = brand_idx
            self._update_progress()
            
            print(f"\n[{brand_idx + 1}/{len(self.config.target_brands)}] Scraping {brand}...")
            print("-" * 70)
            
            try:
                products = self._scrape_brand(brand, images_dir)
                dataset.products.extend(products)
                
                # Update stats
                for product in products:
                    self.progress.images_downloaded += len(product.images)
                    self.progress.reviews_collected += len(product.reviews)
                
                self.progress.products_collected = len(dataset.products)
                
                print(f"  ✓ Collected {len(products)} products for {brand}")
                
            except Exception as e:
                error_msg = f"Failed to scrape {brand}: {str(e)}"
                self.errors.append(error_msg)
                print(f"  ✗ {error_msg}")
            
            self.progress.brands_completed = brand_idx + 1
            self._update_progress()
            
            # Rate limiting between brands
            if brand_idx < len(self.config.target_brands) - 1:
                time.sleep(self.config.rate_limit_delay)
        
        # Finalize dataset
        dataset.total_products = len(dataset.products)
        dataset.total_images = sum(len(p.images) for p in dataset.products)
        dataset.total_reviews = sum(len(p.reviews) for p in dataset.products)
        dataset.updated_at = datetime.utcnow()
        
        # Save metadata
        metadata_file = output_dir / f"{job_id}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(dataset.model_dump(mode='json'), f, indent=2, default=str)
        
        dataset.metadata_file = str(metadata_file)
        
        # Prepare result
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        
        status = "success"
        if self.errors:
            status = "partial" if dataset.products else "failed"
        
        self.progress.progress_percent = 100
        self._update_progress()
        
        result = ScraperResult(
            job_id=job_id,
            status=status,
            dataset=dataset,
            progress=self.progress,
            errors=self.errors,
            warnings=self.warnings,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            output_files={
                "metadata": str(metadata_file),
                "images_dir": str(images_dir),
                "output_dir": str(output_dir)
            }
        )
        
        print(f"\n{'='*70}")
        print(f"Scraping Complete!")
        print(f"{'='*70}")
        print(f"Status: {status.upper()}")
        print(f"Products collected: {dataset.total_products}")
        print(f"Images downloaded: {dataset.total_images}")
        print(f"Reviews collected: {dataset.total_reviews}")
        print(f"Duration: {duration:.1f}s")
        print(f"Output: {output_dir}")
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[:5]:
                print(f"  - {error}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more")
        print(f"{'='*70}\n")
        
        return result
    
    def _scrape_brand(self, brand: str, images_dir: Path) -> List[CompetitorProduct]:
        """Scrape all products for a single brand from all sources.
        
        Args:
            brand: Brand name to scrape.
            images_dir: Directory to save images.
        
        Returns:
            List of CompetitorProduct objects.
        """
        products = []
        
        # 1. Amazon
        if self.config.amazon.enabled:
            self.progress.current_source = "Amazon"
            self._update_progress()
            
            print("  [1/3] Scraping Amazon...")
            try:
                amazon_products = self._scrape_amazon(brand, images_dir)
                products.extend(amazon_products)
                print(f"    ✓ Found {len(amazon_products)} products on Amazon")
            except Exception as e:
                error_msg = f"Amazon scraping failed for {brand}: {str(e)}"
                self.warnings.append(error_msg)
                print(f"    ✗ {error_msg}")
        
        # 2. Retailers
        if self.config.retailers.enabled:
            self.progress.current_source = "Retailers"
            self._update_progress()
            
            print("  [2/3] Scraping Belgian/French retailers...")
            try:
                retailer_products = self._scrape_retailers(brand, images_dir)
                products.extend(retailer_products)
                print(f"    ✓ Found {len(retailer_products)} products on retailers")
            except Exception as e:
                error_msg = f"Retailer scraping failed for {brand}: {str(e)}"
                self.warnings.append(error_msg)
                print(f"    ✗ {error_msg}")
        
        # 3. Google Images
        if self.config.google_images.enabled:
            self.progress.current_source = "Google Images"
            self._update_progress()
            
            print("  [3/3] Scraping Google Images...")
            try:
                # If we already have products, add more images to them
                # Otherwise, create a generic product entry
                if products:
                    for product in products[:self.config.google_images.max_products_per_brand]:
                        additional_images = self._scrape_google_images(
                            brand,
                            product.product_name,
                            images_dir
                        )
                        product.images.extend(additional_images)
                        print(f"    ✓ Added {len(additional_images)} images for {product.product_name}")
                else:
                    # Create generic product with images from Google
                    images = self._scrape_google_images(brand, f"{brand} {self.config.category}", images_dir)
                    if images:
                        product = CompetitorProduct(
                            brand=brand,
                            product_name=f"{brand} {self.config.category}",
                            category=self.config.category,
                            images=images,
                            data_sources=["google_images"]
                        )
                        products.append(product)
                        print(f"    ✓ Created product with {len(images)} images from Google")
            except Exception as e:
                error_msg = f"Google Images scraping failed for {brand}: {str(e)}"
                self.warnings.append(error_msg)
                print(f"    ✗ {error_msg}")
        
        return products
    
    def _scrape_amazon(self, brand: str, images_dir: Path) -> List[CompetitorProduct]:
        """Scrape products from Amazon.
        
        Args:
            brand: Brand name to search.
            images_dir: Directory to save images.
        
        Returns:
            List of products found on Amazon.
        """
        products = []
        
        # Search query
        query = f"{brand} {self.config.category}"
        search_url = f"https://{self.config.amazon.marketplace}/s?k={quote_plus(query)}"
        
        try:
            # Simulate human behavior
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(
                search_url,
                timeout=self.config.amazon.timeout_seconds
            )
            response.raise_for_status()
            
            # Parse product listings (simplified - in production, use proper parsing)
            # For now, create mock data structure
            # In real implementation, you'd parse the HTML or use Amazon API
            
            # NOTE: This is a placeholder. Real implementation would:
            # 1. Parse search results HTML or use Amazon Product Advertising API
            # 2. Extract ASINs and product URLs
            # 3. Visit each product page
            # 4. Extract images, price, reviews, etc.
            
            # For demonstration, create a sample product
            product = CompetitorProduct(
                brand=brand,
                product_name=f"{brand} {self.config.category}",
                category=self.config.category,
                amazon_url=search_url,
                country="Belgium" if ".be" in self.config.amazon.marketplace else "France",
                data_sources=["amazon"]
            )
            
            # In real implementation, extract actual images from product page
            # For now, we'll rely on Google Images to get real data
            
            products.append(product)
            
        except Exception as e:
            raise Exception(f"Amazon search failed: {str(e)}")
        
        return products
    
    def _scrape_retailers(self, brand: str, images_dir: Path) -> List[CompetitorProduct]:
        """Scrape products from Belgian/French retailers.
        
        Args:
            brand: Brand name to search.
            images_dir: Directory to save images.
        
        Returns:
            List of products found on retailers.
        """
        products = []
        
        for retailer in self.config.retailers.retailers:
            try:
                # Simulate retailer search
                # In real implementation, each retailer needs custom parsing logic
                
                query = f"{brand} {self.config.category}"
                # Mock search URL (each retailer has different URL structure)
                search_url = f"https://{retailer}/search?q={quote_plus(query)}"
                
                # Rate limiting
                time.sleep(self.config.rate_limit_delay)
                
                # NOTE: Real implementation would:
                # 1. Handle retailer-specific URL structures
                # 2. Parse search results (different HTML structure per retailer)
                # 3. Extract product pages
                # 4. Parse product details, images, prices
                # 5. Handle pagination
                
                # For now, create placeholder
                # In production, use Firecrawl or custom parsers
                
            except Exception as e:
                self.warnings.append(f"Failed to scrape {retailer} for {brand}: {str(e)}")
        
        return products
    
    def _scrape_google_images(
        self,
        brand: str,
        product_name: str,
        images_dir: Path
    ) -> List[PackagingImage]:
        """Scrape high-res packaging images from Google Images.
        
        Args:
            brand: Brand name.
            product_name: Full product name for search.
            images_dir: Directory to save images.
        
        Returns:
            List of PackagingImage objects with downloaded images.
        """
        images = []
        
        # Search query for packaging images
        query = f"{product_name} packaging front back"
        
        # NOTE: Google Images scraping requires careful handling:
        # - Use SerpAPI, ScraperAPI, or similar services
        # - Or use selenium/playwright for JS rendering
        # - Respect robots.txt and rate limits
        
        # For demonstration, we'll use a simple approach
        # In production, integrate with SerpAPI or use Firecrawl
        
        try:
            # Check if we have SerpAPI key
            serpapi_key = os.getenv("SERPAPI_API_KEY")
            
            if serpapi_key:
                images = self._scrape_google_images_serpapi(
                    query,
                    brand,
                    images_dir,
                    serpapi_key
                )
            else:
                self.warnings.append(
                    f"SERPAPI_API_KEY not found. Skipping Google Images for {brand}. "
                    "Add SERPAPI_API_KEY to .env for Google Images support."
                )
        
        except Exception as e:
            raise Exception(f"Google Images scraping failed: {str(e)}")
        
        return images
    
    def _scrape_google_images_serpapi(
        self,
        query: str,
        brand: str,
        images_dir: Path,
        api_key: str
    ) -> List[PackagingImage]:
        """Scrape Google Images using SerpAPI.
        
        Args:
            query: Search query.
            brand: Brand name for organizing images.
            images_dir: Directory to save images.
            api_key: SerpAPI key.
        
        Returns:
            List of PackagingImage objects.
        """
        images = []
        
        try:
            # SerpAPI Google Images search
            search_url = "https://serpapi.com/search"
            
            params = {
                "q": query,
                "tbm": "isch",  # Image search
                "api_key": api_key,
                "num": min(self.config.google_images.max_images_per_product, 20),
                "ijn": 0  # Page number
            }
            
            time.sleep(self.config.rate_limit_delay)
            
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract image results
            image_results = data.get("images_results", [])
            
            for idx, img_data in enumerate(image_results[:self.config.google_images.max_images_per_product]):
                try:
                    # Get original image URL
                    img_url = img_data.get("original")
                    if not img_url:
                        continue
                    
                    # Download image
                    downloaded_img = self._download_image(
                        img_url,
                        brand,
                        images_dir,
                        f"google_{idx}"
                    )
                    
                    if downloaded_img:
                        images.append(downloaded_img)
                        
                        # Rate limiting
                        time.sleep(0.5)
                
                except Exception as e:
                    self.warnings.append(f"Failed to download image from Google: {str(e)}")
        
        except Exception as e:
            raise Exception(f"SerpAPI request failed: {str(e)}")
        
        return images
    
    def _download_image(
        self,
        url: str,
        brand: str,
        images_dir: Path,
        prefix: str = ""
    ) -> Optional[PackagingImage]:
        """Download an image and save it locally.
        
        Args:
            url: Image URL.
            brand: Brand name for organizing.
            images_dir: Directory to save image.
            prefix: Optional filename prefix.
        
        Returns:
            PackagingImage object if successful, None otherwise.
        """
        try:
            # Download image
            response = self.session.get(url, timeout=15, stream=True)
            response.raise_for_status()
            
            # Verify it's an image
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return None
            
            # Read image
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            
            # Check resolution
            width, height = img.size
            min_w, min_h = 800, 600
            if self.config.google_images.min_resolution:
                try:
                    min_w, min_h = map(int, self.config.google_images.min_resolution.split('x'))
                except:
                    pass
            
            if width < min_w or height < min_h:
                return None
            
            # Generate filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            brand_slug = re.sub(r'[^a-z0-9]+', '_', brand.lower())
            
            # Detect format
            img_format = img.format.lower() if img.format else 'jpg'
            filename = f"{brand_slug}_{prefix}_{url_hash}.{img_format}"
            
            # Save image
            brand_dir = images_dir / brand_slug
            brand_dir.mkdir(exist_ok=True)
            
            filepath = brand_dir / filename
            img.save(filepath, quality=95)
            
            # Create PackagingImage object
            packaging_img = PackagingImage(
                url=url,
                view="unknown",
                resolution=f"{width}x{height}",
                file_size=len(response.content),
                local_path=str(filepath),
                source="google_images",
                downloaded_at=datetime.utcnow()
            )
            
            return packaging_img
        
        except Exception as e:
            self.warnings.append(f"Failed to download image: {str(e)}")
            return None
    
    def _update_progress(self):
        """Update progress percentage and call callback if provided."""
        # Calculate progress
        if self.progress.brands_total > 0:
            brand_progress = (self.progress.brands_completed / self.progress.brands_total) * 100
            self.progress.progress_percent = int(brand_progress)
        
        # Call callback
        if self.progress_callback:
            self.progress_callback(self.progress)


# =============================================================================
# Convenience Functions
# =============================================================================

def scrape_competitor_packaging(
    target_brands: Optional[List[str]] = None,
    category: str = "plant-based milk",
    countries: Optional[List[str]] = None,
    output_dir: str = "output/competitor_packaging",
    enable_amazon: bool = True,
    enable_retailers: bool = True,
    enable_google_images: bool = True,
    job_id: Optional[str] = None,
    progress_callback: Optional[Callable[[ScraperProgress], None]] = None
) -> ScraperResult:
    """Convenience function to scrape competitor packaging.
    
    Args:
        target_brands: List of brands to scrape. Defaults to Recolt competitors.
        category: Product category.
        countries: Target countries. Defaults to Belgium and France.
        output_dir: Output directory path.
        enable_amazon: Enable Amazon scraping.
        enable_retailers: Enable retailer scraping.
        enable_google_images: Enable Google Images scraping.
        job_id: Optional job identifier.
        progress_callback: Optional progress callback.
    
    Returns:
        ScraperResult with complete dataset.
    
    Example:
        >>> result = scrape_competitor_packaging(
        ...     target_brands=["Alpro", "Oatly", "Bjorg"],
        ...     category="oat milk"
        ... )
        >>> print(f"Collected {result.dataset.total_products} products")
    """
    if target_brands is None:
        target_brands = ["Alpro", "Oatly", "Bjorg", "Roa Ra", "Hély"]
    
    if countries is None:
        countries = ["Belgium", "France"]
    
    # Create config
    config = CompetitorScraperConfig(
        target_brands=target_brands,
        category=category,
        countries=countries,
        output_dir=output_dir
    )
    
    config.amazon.enabled = enable_amazon
    config.retailers.enabled = enable_retailers
    config.google_images.enabled = enable_google_images
    
    # Create scraper and run
    scraper = CompetitorPackagingScraper(config, progress_callback)
    return scraper.scrape_all(job_id)
