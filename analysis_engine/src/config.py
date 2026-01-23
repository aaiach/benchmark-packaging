"""Configuration for the product scraper.

This module centralizes all configuration settings for the LLM-powered
product discovery pipeline.

Architecture:
- Step 1 (Brand Discovery): Gemini with Google Search grounding
- Step 2 (Product Details): OpenAI with Web Search (Responses API)
- Step 3 (Scraping): Firecrawl (parallel - up to 5 concurrent)
- Step 4 (Image Selection): OpenAI Mini with structured outputs
- Step 5-6 (Visual Analysis): Gemini Vision
- Step 7 (Competitive Analysis): Gemini

Parallelization:
- OpenAI (Tier 5): 30,000 RPM - high concurrency (15)
- Gemini: 60 RPM - 10 concurrent requests (upgraded tier)
- Firecrawl: Up to 5 concurrent requests (upgraded subscription)
"""
from dataclasses import dataclass, field
from typing import Optional
import os

from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# Parallelization Configuration
# =============================================================================

@dataclass
class ParallelConfig:
    """Configuration for parallel execution."""
    max_concurrent: int
    rate_limit_rpm: int
    min_delay_seconds: float = 0.0


@dataclass
class ParallelizationConfig:
    """Parallelization settings for all providers.
    
    Rate limits based on:
    - OpenAI Tier 5: 30,000 RPM (using conservative 1000)
    - Gemini: 15-60 RPM depending on tier (using conservative 30)
    - Firecrawl: No concurrency (sequential only)
    """
    # OpenAI settings (Tier 5: 30,000 RPM available)
    openai: ParallelConfig = field(default_factory=lambda: ParallelConfig(
        max_concurrent=15,
        rate_limit_rpm=1000,  # Conservative: 1000 of 30000
        min_delay_seconds=0.05
    ))
    
    # OpenAI Mini (same tier)
    openai_mini: ParallelConfig = field(default_factory=lambda: ParallelConfig(
        max_concurrent=15,
        rate_limit_rpm=1000,
        min_delay_seconds=0.05
    ))
    
    # Gemini text (upgraded tier - 10 concurrent)
    gemini: ParallelConfig = field(default_factory=lambda: ParallelConfig(
        max_concurrent=10,
        rate_limit_rpm=60,
        min_delay_seconds=0.2
    ))
    
    # Gemini Vision (same limits as text)
    gemini_vision: ParallelConfig = field(default_factory=lambda: ParallelConfig(
        max_concurrent=10,
        rate_limit_rpm=60,
        min_delay_seconds=0.2
    ))
    
    # Firecrawl - up to 5 concurrent (upgraded subscription)
    # Note: Multiple users may hit limits, so retry logic is implemented in scraper
    firecrawl: ParallelConfig = field(default_factory=lambda: ParallelConfig(
        max_concurrent=5,
        rate_limit_rpm=60,  # Conservative estimate
        min_delay_seconds=0.1  # Minimal delay since we scrape different domains
    ))


# =============================================================================
# Model Configuration
# =============================================================================

@dataclass
class GeminiConfig:
    """Configuration for Gemini (Brand Discovery - Step 1)."""
    model: str = "gemini-3-pro-preview"  # Preview suffix required for Gemini 3
    temperature: float = 1.0  # Gemini 3+ requires temperature=1.0 to avoid issues
    # Google Search grounding is enabled via bind_tools
    
    @property
    def api_key(self) -> str:
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable required")
        return key


@dataclass  
class OpenAIConfig:
    """Configuration for OpenAI (Product Details - Step 2)."""
    model: str = "gpt-5"  # Latest model with web search support
    temperature: float = 0.0
    # Web search is enabled via Responses API (use_responses_api=True) with web_search tool
    
    @property
    def api_key(self) -> str:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        return key


@dataclass
class OpenAIMiniConfig:
    """Configuration for OpenAI Mini model (Image Selection - Step 4)."""
    model: str = "gpt-5"  # Using full model for better image selection decisions
    temperature: float = 1.0  # OpenAI models only support temperature=1.0
    
    @property
    def api_key(self) -> str:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        return key


@dataclass
class GeminiVisionConfig:
    """Configuration for Gemini Vision model (Visual Analysis - Step 5)."""
    model: str = "gemini-3-pro-image-preview"  # Gemini 3 Pro with image/vision capabilities
    temperature: float = 1.0  # Recommended for Gemini models
    
    @property
    def api_key(self) -> str:
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable required")
        return key


# =============================================================================
# Pipeline Configuration
# =============================================================================

@dataclass
class DiscoveryConfig:
    """Configuration for the discovery pipeline."""
    # Default values
    default_count: int = 30
    default_country: str = "France"
    
    # LLM configs
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    openai_mini: OpenAIMiniConfig = field(default_factory=OpenAIMiniConfig)
    gemini_vision: GeminiVisionConfig = field(default_factory=GeminiVisionConfig)
    
    # Parallelization settings
    parallel: ParallelizationConfig = field(default_factory=ParallelizationConfig)
    
    # Output settings - use OUTPUT_DIR env var if available (for Docker/API deployment)
    output_dir: str = field(default_factory=lambda: os.getenv('OUTPUT_DIR', 'output'))
    images_subdir: str = "images"
    analysis_subdir: str = "analysis"
    verbose: bool = True


# =============================================================================
# Global Config Instance
# =============================================================================

# Singleton config instance
_config: Optional[DiscoveryConfig] = None


def get_config() -> DiscoveryConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = DiscoveryConfig()
    return _config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None
