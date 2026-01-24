"""Product scraper package.

Architecture LLM en plusieurs étapes avec web search:
1. Découverte des marques: Gemini + Google Search
2. Détails par marque: OpenAI + Web Search (Responses API)
3. Scraping via Firecrawl
4. Sélection d'images: OpenAI Mini + téléchargement local + extraction front
5. Analyse visuelle: Gemini Vision (hiérarchie visuelle, eye-tracking)
6. Génération de heatmaps: Gemini Vision (overlay de chaleur visuelle)
7. Analyse concurrentielle: PODs/POPs extraction pour présentation BCG-style

The image selection step (4) now includes front extraction:
- Detects and crops the front-facing view of product packaging
- Uses Gemini Vision for bounding box detection
- Performs lossless cropping with PIL (no pixel modification)
- Falls back to original image if extraction fails

Usage:
    # Run complet
    uv run python main.py "lait d'avoine" --steps 1-7
    
    # Continuer un run existant avec analyse concurrentielle
    uv run python main.py --run-id 20260120_184854 --steps 7
"""
from .config import (
    get_config,
    reset_config,
    DiscoveryConfig,
    GeminiConfig,
    OpenAIConfig,
    OpenAIMiniConfig,
    GeminiVisionConfig,
    FrontExtractionConfig,
    ParallelizationConfig,
    ParallelConfig,
)
from .models import (
    Product, 
    Brand, 
    BrandList, 
    ProductDetails,
    ProductDetailsList,
    ImageSelection,
    ImageSelectionResult,
    FrontExtractionResult,
    FrontExtractionBoundingBox,
    VisualElement,
    EyeTrackingPattern,
    MassingAnalysis,
    VisualHierarchyAnalysis,
    # Competitive Analysis models
    CompetitiveAnalysisResult,
    PointOfDifference,
    PointOfParity,
    ProductCompetitiveProfile,
    StrategicInsight,
)
from .product_discovery import ProductDiscovery, discover_products
from .scraper import ProductScraper
from .image_selector import ImageSelector, select_images, list_runs
from .front_extractor import FrontExtractor, extract_front_from_image
from .visual_analyzer import VisualAnalyzer, analyze_images, generate_heatmaps, list_runs_with_images
from .competitive_analyzer import CompetitiveAnalyzer, run_competitive_analysis
from .parallel_executor import ParallelExecutor, Provider, ProviderLimits, run_parallel
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
    'FrontExtractionConfig',
    'ParallelizationConfig',
    'ParallelConfig',
    # Models
    'Product',
    'Brand',
    'BrandList', 
    'ProductDetails',
    'ProductDetailsList',
    'ImageSelection',
    'ImageSelectionResult',
    'FrontExtractionResult',
    'FrontExtractionBoundingBox',
    'VisualElement',
    'EyeTrackingPattern',
    'MassingAnalysis',
    'VisualHierarchyAnalysis',
    # Competitive Analysis Models
    'CompetitiveAnalysisResult',
    'PointOfDifference',
    'PointOfParity',
    'ProductCompetitiveProfile',
    'StrategicInsight',
    # Discovery
    'ProductDiscovery',
    'discover_products',
    # Scraper
    'ProductScraper',
    # Image Selection
    'ImageSelector',
    'select_images',
    'list_runs',
    # Front Extraction
    'FrontExtractor',
    'extract_front_from_image',
    # Visual Analysis
    'VisualAnalyzer',
    'analyze_images',
    'generate_heatmaps',
    'list_runs_with_images',
    # Competitive Analysis
    'CompetitiveAnalyzer',
    'run_competitive_analysis',
    # Parallel Execution
    'ParallelExecutor',
    'Provider',
    'ProviderLimits',
    'run_parallel',
    # Pipeline
    'Pipeline',
    'PipelineContext',
    'STEPS',
    'parse_steps_arg',
    'list_steps',
]
