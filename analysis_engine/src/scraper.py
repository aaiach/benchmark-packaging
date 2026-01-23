"""Web scraper for product pages using Firecrawl.

Supports parallel scraping with up to 5 concurrent requests.
Uses ParallelExecutor for rate limiting and retry logic.
"""
import os
import time
import random
from typing import Optional, Dict, Any, List

from firecrawl import FirecrawlApp
from dotenv import load_dotenv

from .models import Product
from .config import get_config, DiscoveryConfig
from .parallel_executor import (
    ParallelExecutor,
    Provider,
    ProviderLimits,
)

load_dotenv()


# Rate limit error indicators (Firecrawl may return these)
RATE_LIMIT_INDICATORS = [
    "rate limit",
    "too many requests",
    "429",
    "quota exceeded",
    "concurrent",
    "limit exceeded",
]


def is_rate_limit_error(error: Exception) -> bool:
    """Check if an exception is a rate limit error."""
    error_str = str(error).lower()
    return any(indicator in error_str for indicator in RATE_LIMIT_INDICATORS)


class ProductScraper:
    """Scrapes product information from web pages using Firecrawl.
    
    Supports parallel scraping with configurable concurrency.
    Implements retry logic with exponential backoff for rate limit errors.
    """

    def __init__(
        self, 
        api_key: str = None, 
        config: Optional[DiscoveryConfig] = None,
        max_retries: int = 3,
        base_retry_delay: float = 5.0
    ):
        """Initialize the product scraper.

        Args:
            api_key: Firecrawl API key. If None, will use FIRECRAWL_API_KEY from environment.
            config: Optional configuration. Uses global config if not provided.
            max_retries: Maximum retries on rate limit errors (default: 3).
            base_retry_delay: Base delay for exponential backoff in seconds (default: 5.0).
        """
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("Firecrawl API key not found in environment or arguments")

        self.app = FirecrawlApp(api_key=self.api_key)
        self.config = config or get_config()
        self.max_retries = max_retries
        self.base_retry_delay = base_retry_delay

    def scrape_product(self, product: Product, verbose: bool = True) -> Product:
        """Scrape les informations détaillées d'un produit.

        Includes retry logic with exponential backoff for rate limit errors.

        Args:
            product: Objet Product avec au moins une URL
            verbose: Whether to print progress (default: True)

        Returns:
            Objet Product mis à jour avec les données scrapées
        """
        # Utilise product_url (site officiel) en priorité, sinon url
        url = product.product_url or product.url
        if not url:
            if verbose:
                print(f"    [!] No URL for {product.brand} - {product.full_name}")
            return product

        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Scrape la page avec Firecrawl
                result = self.app.scrape(
                    url=url,
                    formats=['markdown', 'html'],
                    only_main_content=True,
                )

                # Extract information from the scraped data
                result_dict = self._to_dict(result)
                extracted_data = self._extract_product_info(result_dict)

                # Update product with scraped data
                product.price = extracted_data.get('price') or product.price
                product.description = extracted_data.get('description') or product.description
                product.images = extracted_data.get('images') or product.images
                product.availability = extracted_data.get('availability') or product.availability

                # Merge additional data
                if product.additional_data is None:
                    product.additional_data = {}
                product.additional_data.update(extracted_data.get('additional_data', {}))

                return product

            except Exception as e:
                last_error = e
                
                # Check if it's a rate limit error
                if is_rate_limit_error(e) and attempt < self.max_retries:
                    # Exponential backoff with jitter
                    delay = self.base_retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    if verbose:
                        print(f"    [!] Rate limit hit for {product.brand}, waiting {delay:.1f}s (attempt {attempt + 1}/{self.max_retries + 1})")
                    time.sleep(delay)
                    continue
                
                # Non-rate-limit error or max retries reached
                if verbose:
                    print(f"    [!] Error scraping {product.brand}: {e}")
                return product
        
        # All retries exhausted
        if verbose:
            print(f"    [!] Max retries exceeded for {product.brand}: {last_error}")
        return product

    @staticmethod
    def _to_dict(obj) -> Dict[str, Any]:
        """Convert object to dict recursively."""
        if isinstance(obj, dict):
            return {k: ProductScraper._to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ProductScraper._to_dict(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return ProductScraper._to_dict(obj.__dict__)
        else:
            return obj

    def scrape_products_batch(
        self, 
        products: List[Product], 
        parallel: bool = True
    ) -> List[Product]:
        """Scrape multiple products with parallel execution.

        Uses ParallelExecutor for concurrent scraping with rate limiting
        and retry logic for rate limit errors.

        Args:
            products: List of Product objects
            parallel: Use parallel execution (default: True)

        Returns:
            List of updated Product objects (in original order)
        """
        if not products:
            return []
        
        total = len(products)
        
        if parallel and total > 1:
            # PARALLEL EXECUTION using ParallelExecutor
            limits = ProviderLimits(
                max_concurrent=self.config.parallel.firecrawl.max_concurrent,
                rate_limit_rpm=self.config.parallel.firecrawl.rate_limit_rpm,
                min_delay_seconds=self.config.parallel.firecrawl.min_delay_seconds
            )
            
            print(f"  Mode: PARALLEL ({limits.max_concurrent} concurrent)")
            print("-" * 70)
            
            executor = ParallelExecutor(
                provider=Provider.FIRECRAWL, 
                limits=limits,
                max_retries=self.max_retries,
                retry_delay_seconds=self.base_retry_delay
            )
            
            # Create indexed items for tracking order
            indexed_products = list(enumerate(products))
            
            # Async wrapper for scrape_product
            async def scrape_async(item: tuple) -> tuple:
                import asyncio
                idx, product = item
                loop = asyncio.get_event_loop()
                
                def do_scrape():
                    # Use verbose=False since we're in parallel and will report via callback
                    return (idx, self.scrape_product(product, verbose=False))
                
                return await loop.run_in_executor(None, do_scrape)
            
            # Progress callback
            success_count = [0]
            def on_progress(completed: int, total: int, status: str, item_id: Optional[str]):
                print(f"  [{completed:2}/{total}] {item_id or 'Scraping'}... {status}", flush=True)
            
            # Execute in parallel
            batch_result = executor.execute_sync(
                items=indexed_products,
                process_func=scrape_async,
                get_item_id=lambda x: x[1].brand,
                progress_callback=on_progress
            )
            
            # Reconstruct results in original order
            results_by_index = {}
            for exec_result in batch_result.results:
                if exec_result.success and exec_result.result:
                    idx, scraped_product = exec_result.result
                    results_by_index[idx] = scraped_product
                else:
                    # Failed - use original product
                    idx = exec_result.index
                    results_by_index[idx] = indexed_products[idx][1]
            
            # Build ordered result list
            scraped_products = [results_by_index[i] for i in range(total)]
            
            print("-" * 70)
            print(f"[✓] Scraped {batch_result.successful_count}/{total} products "
                  f"in {batch_result.total_duration_seconds:.1f}s")
            
        else:
            # SEQUENTIAL EXECUTION (fallback)
            print("  Mode: SEQUENTIAL")
            print("-" * 70)
            
            scraped_products = []
            
            for i, product in enumerate(products, 1):
                brand = product.brand
                name = (product.full_name or '')[:40]
                print(f"[{i:2}/{total}] {brand} - {name}...", end=" ", flush=True)
                
                scraped = self.scrape_product(product, verbose=False)
                scraped_products.append(scraped)
                
                # Check if scrape was successful (has images or description)
                if scraped.images or scraped.description:
                    print("✓")
                else:
                    print("✗")
            
            print("-" * 70)
            print(f"[✓] Scraped {total} products")

        return scraped_products

    def _extract_product_info(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured product information from scraped data.

        Args:
            scraped_data: Raw scraped data from Firecrawl

        Returns:
            Dictionary with extracted product information
        """
        extracted = {
            'price': None,
            'description': None,
            'images': [],
            'availability': None,
            'additional_data': {}
        }

        # Get markdown content
        markdown = scraped_data.get('markdown', '')
        html = scraped_data.get('html', '')
        metadata = scraped_data.get('metadata', {})

        # Extract price - common patterns
        price_patterns = ['€', 'EUR', 'prix', 'price']
        for line in markdown.split('\n'):
            line_lower = line.lower()
            if any(pattern.lower() in line_lower for pattern in price_patterns):
                # Try to find price-like patterns
                import re
                price_match = re.search(r'(\d+[.,]\d{2})\s*€', line)
                if price_match:
                    extracted['price'] = price_match.group(0)
                    break

        # Extract description - usually in meta description or first paragraph
        if metadata.get('description'):
            extracted['description'] = metadata['description']
        else:
            # Try to get first meaningful paragraph from markdown
            lines = [l.strip() for l in markdown.split('\n') if l.strip() and not l.startswith('#')]
            if lines:
                extracted['description'] = lines[0][:500]  # Limit to 500 chars

        # Extract images
        if metadata.get('ogImage'):
            extracted['images'].append(metadata['ogImage'])

        # Try to extract images from markdown
        import re
        image_pattern = r'!\[.*?\]\((.*?)\)'
        images_from_md = re.findall(image_pattern, markdown)
        extracted['images'].extend(images_from_md[:5])  # Limit to first 5 images

        # Remove duplicates
        extracted['images'] = list(dict.fromkeys(extracted['images']))

        # Extract availability
        availability_keywords = ['en stock', 'disponible', 'in stock', 'available', 'rupture', 'out of stock']
        for line in markdown.lower().split('\n'):
            if any(keyword in line for keyword in availability_keywords):
                extracted['availability'] = line.strip()
                break

        # Store raw markdown for reference
        extracted['additional_data']['markdown_preview'] = markdown[:1000]
        extracted['additional_data']['metadata'] = metadata

        return extracted
