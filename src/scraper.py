"""Web scraper for product pages using Firecrawl."""
import os
import time
from typing import Optional, Dict, Any, List
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from .models import Product

load_dotenv()

# Default delay between API calls to prevent rate limiting
DEFAULT_RATE_LIMIT_DELAY = 3.0  # seconds


class ProductScraper:
    """Scrapes product information from web pages using Firecrawl."""

    def __init__(self, api_key: str = None, rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY):
        """Initialize the product scraper.

        Args:
            api_key: Firecrawl API key. If None, will use FIRECRAWL_API_KEY from environment.
            rate_limit_delay: Delay in seconds between API calls (default: 3.0)
        """
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("Firecrawl API key not found in environment or arguments")

        self.app = FirecrawlApp(api_key=self.api_key)
        self.rate_limit_delay = rate_limit_delay

    def scrape_product(self, product: Product) -> Product:
        """Scrape les informations détaillées d'un produit.

        Args:
            product: Objet Product avec au moins une URL

        Returns:
            Objet Product mis à jour avec les données scrapées
        """
        # Utilise product_url (site officiel) en priorité, sinon url
        url = product.product_url or product.url
        if not url:
            print(f"Attention: Pas d'URL pour {product.brand} - {product.full_name}")
            return product

        print(f"Scraping: {product.brand} - {product.full_name}")
        print(f"URL: {url}")

        try:
            # Scrape la page avec Firecrawl
            result = self.app.scrape(
                url=url,
                formats=['markdown', 'html'],
                only_main_content=True,
            )

            # Extract information from the scraped data
            # Convert Document object to dict recursively
            def to_dict(obj):
                """Convert object to dict recursively."""
                if isinstance(obj, dict):
                    return {k: to_dict(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [to_dict(item) for item in obj]
                elif hasattr(obj, '__dict__'):
                    return to_dict(obj.__dict__)
                else:
                    return obj

            result_dict = to_dict(result)
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

            print(f"Successfully scraped {product.brand}")
            return product

        except Exception as e:
            print(f"Error scraping {product.brand}: {e}")
            return product

    def scrape_products_batch(self, products: List[Product]) -> List[Product]:
        """Scrape multiple products with rate limiting.

        Waits between API calls to prevent rate limiting.

        Args:
            products: List of Product objects

        Returns:
            List of updated Product objects
        """
        scraped_products = []
        total = len(products)

        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{total}] ", end="")
            scraped = self.scrape_product(product)
            scraped_products.append(scraped)

            # Wait between calls to prevent rate limiting (skip after last item)
            if i < total and self.rate_limit_delay > 0:
                print(f"Waiting {self.rate_limit_delay}s before next request...")
                time.sleep(self.rate_limit_delay)

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
