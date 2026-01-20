"""Product scraper package.

Architecture LLM en deux étapes avec web search:
1. Découverte des marques: Gemini + Google Search
2. Détails par marque: OpenAI + Web Search (Responses API)
"""
from .config import (
    get_config,
    reset_config,
    DiscoveryConfig,
    GeminiConfig,
    OpenAIConfig,
)
from .models import (
    Product, 
    Brand, 
    BrandList, 
    ProductDetails,
    ProductDetailsList,
)
from .product_discovery import ProductDiscovery, discover_products
from .scraper import ProductScraper

__all__ = [
    # Config
    'get_config',
    'reset_config',
    'DiscoveryConfig',
    'GeminiConfig',
    'OpenAIConfig',
    # Models
    'Product',
    'Brand',
    'BrandList', 
    'ProductDetails',
    'ProductDetailsList',
    # Discovery
    'ProductDiscovery',
    'discover_products',
    # Scraper
    'ProductScraper',
]
