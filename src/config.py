"""Configuration for the product scraper.

This module centralizes all configuration settings for the LLM-powered
product discovery pipeline.

Architecture:
- Step 1 (Brand Discovery): Gemini with Google Search grounding
- Step 2 (Product Details): OpenAI with Web Search (Responses API)
- Step 3 (Image Selection): OpenAI Mini with structured outputs
"""
from dataclasses import dataclass, field
from typing import Optional
import os

from dotenv import load_dotenv

load_dotenv()


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
    """Configuration for OpenAI Mini model (Image Selection - Step 3)."""
    model: str = "gpt-5"  # Using full model for better image selection decisions
    temperature: float = 1.0  # OpenAI models only support temperature=1.0
    
    @property
    def api_key(self) -> str:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable required")
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
    
    # Output settings
    output_dir: str = "output"
    images_subdir: str = "images"
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
