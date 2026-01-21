"""Product scraper package.

Architecture LLM en plusieurs étapes avec web search:
1. Découverte des marques: Gemini + Google Search
2. Détails par marque: OpenAI + Web Search (Responses API)
3. Scraping via Firecrawl
4. Sélection d'images: OpenAI Mini + téléchargement local

Usage:
    # Run complet
    uv run python main.py "lait d'avoine" --steps 1-4
    
    # Continuer un run existant
    uv run python main.py --run-id 20260120_184854 --steps 4
"""
from .config import (
    get_config,
    reset_config,
    DiscoveryConfig,
    GeminiConfig,
    OpenAIConfig,
    OpenAIMiniConfig,
)
from .models import (
    Product, 
    Brand, 
    BrandList, 
    ProductDetails,
    ProductDetailsList,
    ImageSelection,
    ImageSelectionResult,
)
from .product_discovery import ProductDiscovery, discover_products
from .scraper import ProductScraper
from .image_selector import ImageSelector, select_images, list_runs
from .pipeline import Pipeline, PipelineContext, STEPS, parse_steps_arg, list_steps

__all__ = [
    # Config
    'get_config',
    'reset_config',
    'DiscoveryConfig',
    'GeminiConfig',
    'OpenAIConfig',
    'OpenAIMiniConfig',
    # Models
    'Product',
    'Brand',
    'BrandList', 
    'ProductDetails',
    'ProductDetailsList',
    'ImageSelection',
    'ImageSelectionResult',
    # Discovery
    'ProductDiscovery',
    'discover_products',
    # Scraper
    'ProductScraper',
    # Image Selection
    'ImageSelector',
    'select_images',
    'list_runs',
    # Pipeline
    'Pipeline',
    'PipelineContext',
    'STEPS',
    'parse_steps_arg',
    'list_steps',
]
