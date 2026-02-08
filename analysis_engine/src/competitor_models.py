"""Data models for competitor packaging scraper.

This module defines Pydantic models for structured competitor packaging data
collected from multiple sources (Amazon, retailers, Google Images).
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


# =============================================================================
# Core Competitor Packaging Models
# =============================================================================

class PackagingImage(BaseModel):
    """A single packaging image with metadata."""
    url: str = Field(description="Image URL")
    view: Literal["front", "back", "side", "top", "bottom", "angle", "lifestyle", "unknown"] = Field(
        default="unknown",
        description="Packaging view/angle"
    )
    resolution: Optional[str] = Field(None, description="Image resolution (e.g., '1200x800')")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    local_path: Optional[str] = Field(None, description="Local storage path after download")
    cloud_url: Optional[str] = Field(None, description="Cloud storage URL")
    source: Literal["amazon", "retailer", "google_images", "brand_website", "other"] = Field(
        description="Image source"
    )
    downloaded_at: Optional[datetime] = Field(None, description="Download timestamp")


class ProductReview(BaseModel):
    """A customer review from Amazon or retailer."""
    rating: float = Field(description="Rating (1-5 stars)", ge=1, le=5)
    title: Optional[str] = Field(None, description="Review title")
    text: str = Field(description="Review text content")
    author: Optional[str] = Field(None, description="Reviewer name")
    verified_purchase: Optional[bool] = Field(None, description="Verified purchase flag")
    helpful_count: Optional[int] = Field(None, description="Number of helpful votes")
    date: Optional[str] = Field(None, description="Review date")
    source: Literal["amazon", "retailer", "other"] = Field(description="Review source")


class ProductClaim(BaseModel):
    """A marketing claim or feature highlighted on packaging or product page."""
    claim_text: str = Field(description="Exact claim text")
    claim_type: Literal[
        "nutritional", "environmental", "origin", "quality", 
        "certification", "taste", "health", "ethical", "other"
    ] = Field(description="Type of claim")
    prominence: Literal["primary", "secondary", "tertiary"] = Field(
        description="Visual prominence on packaging"
    )
    location: Optional[str] = Field(None, description="Location on packaging (e.g., 'front top', 'back panel')")
    has_certification: bool = Field(default=False, description="Whether claim is backed by certification")


class PricePoint(BaseModel):
    """Price information from a specific retailer."""
    price: float = Field(description="Price in local currency")
    currency: str = Field(default="EUR", description="Currency code")
    unit: Optional[str] = Field(None, description="Unit (e.g., 'per liter', 'per package')")
    retailer: str = Field(description="Retailer name")
    url: Optional[str] = Field(None, description="Product page URL")
    date_collected: datetime = Field(default_factory=datetime.utcnow, description="Collection timestamp")
    in_stock: Optional[bool] = Field(None, description="Availability status")
    promotion: Optional[str] = Field(None, description="Any active promotion")


class CompetitorProduct(BaseModel):
    """Complete competitor product packaging data."""
    
    # Basic Info
    brand: str = Field(description="Brand name (e.g., 'Alpro', 'Oatly')")
    product_name: str = Field(description="Full product name")
    category: str = Field(default="plant-based milk", description="Product category")
    variant: Optional[str] = Field(None, description="Product variant (e.g., 'Original', 'Barista')")
    package_size: Optional[str] = Field(None, description="Package size (e.g., '1L', '500ml')")
    
    # Packaging Images
    images: List[PackagingImage] = Field(
        default_factory=list,
        description="High-res packaging images from multiple angles"
    )
    
    # Product Information
    description: Optional[str] = Field(None, description="Product description")
    claims: List[ProductClaim] = Field(
        default_factory=list,
        description="Marketing claims and features"
    )
    
    # Reviews & Ratings
    reviews: List[ProductReview] = Field(
        default_factory=list,
        description="Customer reviews"
    )
    average_rating: Optional[float] = Field(None, description="Average rating (1-5)")
    review_count: Optional[int] = Field(None, description="Total review count")
    
    # Price Points
    prices: List[PricePoint] = Field(
        default_factory=list,
        description="Price points from different retailers"
    )
    
    # Source URLs
    amazon_url: Optional[str] = Field(None, description="Amazon product page URL")
    brand_website_url: Optional[str] = Field(None, description="Official brand website URL")
    retailer_urls: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Retailer URLs (list of {retailer: url})"
    )
    
    # Metadata
    country: str = Field(default="Belgium", description="Target country/market")
    language: str = Field(default="fr", description="Language (fr/nl/en)")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="Scraping timestamp")
    data_sources: List[str] = Field(
        default_factory=list,
        description="Sources used (amazon, retailer names, google_images)"
    )
    
    # Additional Data
    additional_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any additional scraped data"
    )


class CompetitorPackagingDataset(BaseModel):
    """Complete dataset of competitor packaging data."""
    
    # Metadata
    dataset_id: str = Field(description="Unique dataset identifier")
    category: str = Field(description="Product category")
    target_brands: List[str] = Field(description="Target brands list")
    countries: List[str] = Field(description="Target countries")
    
    # Products
    products: List[CompetitorProduct] = Field(
        default_factory=list,
        description="All competitor products collected"
    )
    
    # Collection Stats
    total_products: int = Field(default=0, description="Total products collected")
    total_images: int = Field(default=0, description="Total images collected")
    total_reviews: int = Field(default=0, description="Total reviews collected")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Dataset creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    
    # Output Paths
    output_dir: Optional[str] = Field(None, description="Output directory path")
    metadata_file: Optional[str] = Field(None, description="Metadata JSON file path")
    images_dir: Optional[str] = Field(None, description="Images directory path")


# =============================================================================
# Scraper Configuration Models
# =============================================================================

class ScraperSourceConfig(BaseModel):
    """Configuration for a specific scraper source."""
    enabled: bool = Field(default=True, description="Whether this source is enabled")
    max_products_per_brand: int = Field(default=5, description="Max products to scrape per brand")
    max_images_per_product: int = Field(default=10, description="Max images per product")
    max_reviews_per_product: int = Field(default=50, description="Max reviews per product")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    retry_count: int = Field(default=3, description="Number of retries on failure")


class AmazonScraperConfig(ScraperSourceConfig):
    """Amazon-specific scraper configuration."""
    marketplace: str = Field(default="amazon.fr", description="Amazon marketplace")
    collect_reviews: bool = Field(default=True, description="Collect customer reviews")
    collect_qa: bool = Field(default=False, description="Collect Q&A section")


class RetailerScraperConfig(ScraperSourceConfig):
    """Retailer-specific scraper configuration."""
    retailers: List[str] = Field(
        default=["carrefour.be", "delhaize.be", "colruyt.be"],
        description="Target retailers"
    )


class GoogleImagesConfig(ScraperSourceConfig):
    """Google Images scraper configuration."""
    min_resolution: str = Field(default="800x600", description="Minimum image resolution")
    image_type: Literal["photo", "clipart", "lineart", "any"] = Field(
        default="photo",
        description="Image type filter"
    )


class CompetitorScraperConfig(BaseModel):
    """Complete competitor scraper configuration."""
    
    # Target Configuration
    target_brands: List[str] = Field(
        default=["Alpro", "Oatly", "Bjorg", "Roa Ra", "Hély"],
        description="Target competitor brands"
    )
    category: str = Field(default="plant-based milk", description="Product category")
    countries: List[str] = Field(default=["Belgium", "France"], description="Target countries")
    
    # Source Configurations
    amazon: AmazonScraperConfig = Field(default_factory=AmazonScraperConfig)
    retailers: RetailerScraperConfig = Field(default_factory=RetailerScraperConfig)
    google_images: GoogleImagesConfig = Field(default_factory=GoogleImagesConfig)
    
    # Output Configuration
    output_dir: str = Field(default="output/competitor_packaging", description="Output directory")
    store_images_locally: bool = Field(default=True, description="Download images locally")
    upload_to_cloud: bool = Field(default=False, description="Upload to cloud storage")
    cloud_bucket: Optional[str] = Field(None, description="Cloud storage bucket name")
    
    # Rate Limiting
    rate_limit_delay: float = Field(default=2.0, description="Delay between requests (seconds)")
    max_concurrent_requests: int = Field(default=3, description="Max concurrent requests")


# =============================================================================
# Scraper Result Models
# =============================================================================

class ScraperProgress(BaseModel):
    """Progress tracking for scraper job."""
    current_brand: Optional[str] = Field(None, description="Currently scraping brand")
    current_source: Optional[str] = Field(None, description="Currently scraping source")
    brands_completed: int = Field(default=0, description="Brands completed")
    brands_total: int = Field(default=0, description="Total brands to scrape")
    products_collected: int = Field(default=0, description="Products collected so far")
    images_downloaded: int = Field(default=0, description="Images downloaded")
    reviews_collected: int = Field(default=0, description="Reviews collected")
    progress_percent: int = Field(default=0, description="Overall progress percentage")


class ScraperResult(BaseModel):
    """Result of a competitor scraping job."""
    
    # Job Info
    job_id: str = Field(description="Unique job identifier")
    status: Literal["success", "partial", "failed"] = Field(description="Job status")
    
    # Results
    dataset: CompetitorPackagingDataset = Field(description="Collected dataset")
    
    # Progress
    progress: ScraperProgress = Field(description="Final progress state")
    
    # Errors
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Warnings")
    
    # Timing
    started_at: datetime = Field(description="Job start time")
    completed_at: datetime = Field(description="Job completion time")
    duration_seconds: float = Field(description="Total duration")
    
    # Output Files
    output_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Generated output files (metadata, images dir, etc.)"
    )
