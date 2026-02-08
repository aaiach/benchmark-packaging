# Competitor Packaging Scraper

## Overview

A comprehensive competitor packaging scraper built for Phase 1.1 of the Recolt Custom Packaging Test project. This scraper collects competitor packaging data from multiple sources to support competitive audit and market analysis.

## Features

### Multi-Source Scraping
- **Amazon**: Product pages with reviews, ratings, and packaging images
- **Belgian/French Retailers**: Carrefour, Delhaize, Colruyt, and other retailers
- **Google Images**: High-resolution packaging images (front, back, side views)

### Data Collection
- High-res packaging images (multiple angles)
- Product descriptions and marketing claims
- Customer reviews and ratings
- Price points from multiple retailers
- Structured metadata in queryable JSON format

### Technical Capabilities
- Rate limiting and anti-bot measures
- Async execution via Celery
- Cloud storage integration (AWS S3, GCS, Azure)
- Progress tracking and real-time updates
- RESTful API for job management

## Target Brands

Default competitors for Recolt (plant-based milk category):
- Alpro
- Oatly
- Bjorg
- Roa Ra
- Hély

## Installation

### Prerequisites

```bash
# Python dependencies
cd analysis_engine
pip install -r requirements.txt

# Additional dependencies for competitor scraper
pip install requests Pillow

# Optional: Cloud storage libraries
pip install boto3                    # For AWS S3
pip install google-cloud-storage     # For Google Cloud Storage
pip install azure-storage-blob       # For Azure Blob Storage
```

### API Keys

Create a `.env` file in `analysis_engine/`:

```env
# Required for Google Images scraping
SERPAPI_API_KEY=your_serpapi_key

# Optional: Cloud storage (choose one)
# AWS S3
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=eu-west-1

# Google Cloud Storage
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_ACCOUNT_KEY=your_account_key
```

**Important**: Without `SERPAPI_API_KEY`, Google Images scraping will be skipped. Get a free API key at https://serpapi.com/

## Usage

### 1. Command Line Interface

#### Basic Usage

```bash
# Scrape default competitors
cd analysis_engine
python run_competitor_scraper.py

# Scrape specific brands
python run_competitor_scraper.py --brands "Alpro,Oatly,Bjorg"

# Custom category
python run_competitor_scraper.py --category "almond milk"

# Specific countries
python run_competitor_scraper.py --countries "Belgium,Netherlands"
```

#### Source Selection

```bash
# Amazon only
python run_competitor_scraper.py --no-retailers --no-google-images

# Google Images only
python run_competitor_scraper.py --no-amazon --no-retailers

# Retailers only
python run_competitor_scraper.py --no-amazon --no-google-images
```

#### Cloud Upload

```bash
# Upload to AWS S3
python run_competitor_scraper.py --upload-cloud --bucket recolt-packaging

# Upload to GCS
python run_competitor_scraper.py --upload-cloud --bucket recolt-packaging --provider gcs

# Make images public
python run_competitor_scraper.py --upload-cloud --bucket recolt-packaging --public
```

### 2. Python API

```python
from analysis_engine.src.competitor_scraper import scrape_competitor_packaging

# Simple usage
result = scrape_competitor_packaging(
    target_brands=["Alpro", "Oatly", "Bjorg"],
    category="oat milk"
)

print(f"Collected {result.dataset.total_products} products")
print(f"Downloaded {result.dataset.total_images} images")

# With progress tracking
def progress_callback(progress):
    print(f"Progress: {progress.progress_percent}% - {progress.current_brand}")

result = scrape_competitor_packaging(
    target_brands=["Alpro", "Oatly"],
    category="plant-based milk",
    countries=["Belgium", "France"],
    enable_amazon=True,
    enable_retailers=True,
    enable_google_images=True,
    progress_callback=progress_callback
)

# Upload to cloud
from analysis_engine.src.cloud_storage import upload_competitor_images_to_cloud

urls = upload_competitor_images_to_cloud(
    dataset_dir=result.dataset.output_dir,
    bucket_name="recolt-competitor-packaging",
    public=False
)

print(f"Uploaded {len(urls)} images")
```

### 3. REST API

#### Start a Scraper Job

```bash
# Direct start
curl -X POST http://localhost:5000/api/competitor-scraper/run \
  -H "Content-Type: application/json" \
  -d '{
    "target_brands": ["Alpro", "Oatly", "Bjorg"],
    "category": "oat milk",
    "countries": ["Belgium", "France"],
    "enable_amazon": true,
    "enable_retailers": true,
    "enable_google_images": true
  }'

# Response:
# {
#   "job_id": "abc-123-def-456",
#   "status": "pending",
#   "message": "Job queued successfully"
# }
```

#### Check Job Status

```bash
curl http://localhost:5000/api/competitor-scraper/status/abc-123-def-456

# Response:
# {
#   "job_id": "abc-123-def-456",
#   "state": "PROGRESS",
#   "status": "Scraping Alpro...",
#   "progress": {
#     "current_brand": "Alpro",
#     "brands_completed": 1,
#     "brands_total": 3,
#     "products_collected": 5,
#     "images_downloaded": 42,
#     "progress_percent": 33
#   }
# }
```

#### List All Datasets

```bash
curl http://localhost:5000/api/competitor-scraper/datasets

# Response:
# {
#   "datasets": [
#     {
#       "dataset_id": "competitor_scrape_20260208_120000",
#       "category": "plant-based milk",
#       "target_brands": ["Alpro", "Oatly", "Bjorg"],
#       "total_products": 15,
#       "total_images": 127,
#       "total_reviews": 348,
#       "created_at": "2026-02-08T12:00:00"
#     }
#   ]
# }
```

#### Get Dataset Details

```bash
curl http://localhost:5000/api/competitor-scraper/dataset/competitor_scrape_20260208_120000
```

## Output Structure

```
output/competitor_packaging/
└── competitor_scrape_20260208_120000/
    ├── competitor_scrape_20260208_120000_metadata.json  # Complete dataset metadata
    └── images/
        ├── alpro/
        │   ├── alpro_google_0_a1b2c3d4.jpg
        │   ├── alpro_google_1_e5f6g7h8.jpg
        │   └── ...
        ├── oatly/
        │   ├── oatly_google_0_i9j0k1l2.png
        │   └── ...
        └── bjorg/
            └── ...
```

### Metadata JSON Structure

```json
{
  "dataset_id": "competitor_scrape_20260208_120000",
  "category": "plant-based milk",
  "target_brands": ["Alpro", "Oatly", "Bjorg"],
  "countries": ["Belgium", "France"],
  "products": [
    {
      "brand": "Alpro",
      "product_name": "Alpro Oat Original",
      "category": "plant-based milk",
      "variant": "Original",
      "package_size": "1L",
      "images": [
        {
          "url": "https://...",
          "view": "front",
          "resolution": "1200x800",
          "local_path": "output/.../alpro/alpro_google_0_a1b2c3d4.jpg",
          "source": "google_images",
          "downloaded_at": "2026-02-08T12:05:30"
        }
      ],
      "description": "Oat drink with calcium and vitamins",
      "claims": [
        {
          "claim_text": "Plant-based",
          "claim_type": "category",
          "prominence": "primary"
        }
      ],
      "reviews": [
        {
          "rating": 4.5,
          "title": "Great taste",
          "text": "Really smooth...",
          "source": "amazon"
        }
      ],
      "average_rating": 4.5,
      "review_count": 127,
      "prices": [
        {
          "price": 2.99,
          "currency": "EUR",
          "retailer": "Carrefour",
          "in_stock": true
        }
      ],
      "scraped_at": "2026-02-08T12:05:30"
    }
  ],
  "total_products": 15,
  "total_images": 127,
  "total_reviews": 348
}
```

## Architecture

### Components

```
analysis_engine/src/
├── competitor_models.py        # Pydantic data models
├── competitor_scraper.py       # Core scraper logic
└── cloud_storage.py           # Cloud upload utilities

api/src/
├── routes/
│   └── competitor_scraper.py  # REST API endpoints
└── tasks/
    └── competitor_scraper_tasks.py  # Celery async tasks
```

### Scraping Flow

```
1. Initialize Scraper
   ├── Configure sources (Amazon, retailers, Google Images)
   └── Set rate limits and retry policies

2. For Each Brand:
   ├── [Source 1] Amazon
   │   ├── Search for products
   │   ├── Extract product pages
   │   ├── Collect reviews & ratings
   │   └── Download images
   │
   ├── [Source 2] Retailers
   │   ├── Search on Carrefour.be
   │   ├── Search on Delhaize.be
   │   ├── Extract prices & availability
   │   └── Download images
   │
   └── [Source 3] Google Images
       ├── Search "{brand} {category} packaging front back"
       ├── Filter by resolution (min 800x600)
       └── Download high-res images

3. Save Results
   ├── Organize images by brand
   ├── Generate metadata JSON
   └── Optional: Upload to cloud storage
```

## Rate Limiting & Anti-Bot Measures

The scraper implements several strategies to avoid detection:

1. **Realistic Headers**: Browser-like User-Agent and Accept headers
2. **Random Delays**: 1-3 second delays between requests
3. **Rate Limiting**: Configurable delays and concurrent request limits
4. **Retry Logic**: Exponential backoff on rate limit errors
5. **Session Management**: Maintains cookies and session state

### Recommended Settings

```python
config = CompetitorScraperConfig(
    rate_limit_delay=2.0,  # 2 seconds between requests
    max_concurrent_requests=3,  # Max 3 parallel requests
    amazon=AmazonScraperConfig(
        timeout_seconds=30,
        retry_count=3,
        max_products_per_brand=5
    )
)
```

## Cloud Storage Integration

### Supported Providers

- **AWS S3**: Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- **Google Cloud Storage**: Set `GOOGLE_APPLICATION_CREDENTIALS`
- **Azure Blob Storage**: Set `AZURE_STORAGE_CONNECTION_STRING`

### Upload Example

```python
from analysis_engine.src.cloud_storage import CloudStorageUploader

uploader = CloudStorageUploader(
    bucket_name="recolt-competitor-packaging",
    provider="s3"  # or "gcs", "azure", or None for auto-detect
)

# Upload single image
url = uploader.upload_image(
    local_path="output/.../alpro/image.jpg",
    remote_path="alpro/front_image.jpg",
    metadata={"brand": "Alpro", "view": "front"},
    public=False
)

print(f"Uploaded to: {url}")

# Generate signed URL for temporary access
signed_url = uploader.generate_signed_url(
    "alpro/front_image.jpg",
    expiration_hours=24
)
```

## API Endpoints Reference

### POST `/api/competitor-scraper/run`
Start a new scraper job.

**Request:**
```json
{
  "target_brands": ["Alpro", "Oatly"],
  "category": "oat milk",
  "countries": ["Belgium"],
  "enable_amazon": true,
  "enable_retailers": true,
  "enable_google_images": true
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "message": "Job queued successfully"
}
```

### GET `/api/competitor-scraper/status/<job_id>`
Check job progress.

**Response:**
```json
{
  "job_id": "uuid",
  "state": "PROGRESS",
  "status": "Scraping Alpro...",
  "progress": {
    "current_brand": "Alpro",
    "brands_completed": 1,
    "brands_total": 2,
    "products_collected": 5,
    "images_downloaded": 42,
    "progress_percent": 50
  }
}
```

### GET `/api/competitor-scraper/datasets`
List all scraped datasets.

**Response:**
```json
{
  "datasets": [
    {
      "dataset_id": "competitor_scrape_20260208_120000",
      "category": "plant-based milk",
      "total_products": 15,
      "total_images": 127,
      "created_at": "2026-02-08T12:00:00"
    }
  ]
}
```

### GET `/api/competitor-scraper/dataset/<dataset_id>`
Get complete dataset metadata.

### GET `/images/competitor_packaging/<dataset_id>/images/<brand>/<filename>`
Serve packaging images via HTTP.

## Troubleshooting

### Issue: No images from Google Images

**Cause**: Missing `SERPAPI_API_KEY`

**Solution**: 
1. Sign up at https://serpapi.com/
2. Get your API key
3. Add to `.env`: `SERPAPI_API_KEY=your_key`

### Issue: Amazon scraping fails

**Cause**: Amazon has strong anti-bot measures

**Solution**:
1. Increase `rate_limit_delay` to 3-5 seconds
2. Reduce `max_products_per_brand`
3. Consider using a proxy service
4. Use Amazon Product Advertising API (requires approval)

### Issue: Cloud upload fails

**Cause**: Missing cloud credentials

**Solution**: Configure the appropriate environment variables:
- AWS: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- GCS: `GOOGLE_APPLICATION_CREDENTIALS`
- Azure: `AZURE_STORAGE_CONNECTION_STRING`

## Limitations & Future Improvements

### Current Limitations

1. **Amazon**: Placeholder implementation (requires Product Advertising API or robust HTML parsing)
2. **Retailers**: Requires custom parsers per retailer
3. **Google Images**: Limited to 20 images per search (SerpAPI free tier)
4. **No JS Rendering**: Static page scraping only (no Selenium/Playwright yet)

### Planned Improvements

1. **Amazon Product Advertising API Integration**: Official API for product data
2. **Firecrawl Integration**: Use existing Firecrawl setup for retailer scraping
3. **Selenium/Playwright**: For JavaScript-heavy sites
4. **Image Classification**: Auto-detect front/back/side views using AI
5. **Duplicate Detection**: Perceptual hashing to avoid duplicate images
6. **Proxy Rotation**: For large-scale scraping
7. **Database Storage**: PostgreSQL for queryable metadata

## License

Proprietary - Recolt Custom Packaging Test Project

## Support

For issues or questions, contact the development team or create an issue in the project repository.
