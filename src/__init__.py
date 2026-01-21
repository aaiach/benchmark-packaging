"""Product scraper package.

Architecture LLM en plusieurs étapes avec web search:
1. Découverte des marques: Gemini + Google Search
2. Détails par marque: OpenAI + Web Search (Responses API)
3. Scraping via Firecrawl
4. Sélection d'images: OpenAI Mini + téléchargement local
5. Analyse visuelle: Gemini Vision (hiérarchie visuelle, eye-tracking)
6. Génération de heatmaps: Gemini Vision (overlay de chaleur visuelle)

Usage:
    # Run complet
    uv run python main.py "lait d'avoine" --steps 1-6
    
    # Continuer un run existant avec heatmaps
    uv run python main.py --run-id 20260120_184854 --steps 6
"""
from .config import (
    get_config,
    reset_config,
    DiscoveryConfig,
    GeminiConfig,
    OpenAIConfig,
    OpenAIMiniConfig,
    GeminiVisionConfig,
)
from .models import (
    Product, 
    Brand, 
    BrandList, 
    ProductDetails,
    ProductDetailsList,
    ImageSelection,
    ImageSelectionResult,
    VisualElement,
    EyeTrackingPattern,
    MassingAnalysis,
    VisualHierarchyAnalysis,
)
from .product_discovery import ProductDiscovery, discover_products
from .scraper import ProductScraper
from .image_selector import ImageSelector, select_images, list_runs
from .visual_analyzer import VisualAnalyzer, analyze_images, generate_heatmaps, list_runs_with_images
from .pipeline import Pipeline, PipelineContext, STEPS, parse_steps_arg, list_steps

__all__ = [
    # Config
    'get_config',
    'reset_config',
    'DiscoveryConfig',
    'GeminiConfig',
    'OpenAIConfig',
    'OpenAIMiniConfig',
    'GeminiVisionConfig',
    # Models
    'Product',
    'Brand',
    'BrandList', 
    'ProductDetails',
    'ProductDetailsList',
    'ImageSelection',
    'ImageSelectionResult',
    'VisualElement',
    'EyeTrackingPattern',
    'MassingAnalysis',
    'VisualHierarchyAnalysis',
    # Discovery
    'ProductDiscovery',
    'discover_products',
    # Scraper
    'ProductScraper',
    # Image Selection
    'ImageSelector',
    'select_images',
    'list_runs',
    # Visual Analysis
    'VisualAnalyzer',
    'analyze_images',
    'generate_heatmaps',
    'list_runs_with_images',
    # Pipeline
    'Pipeline',
    'PipelineContext',
    'STEPS',
    'parse_steps_arg',
    'list_steps',
]
