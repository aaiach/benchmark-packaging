"""Celery tasks for competitor scraper execution.

This module wraps the competitor scraper with Celery task management,
providing progress tracking and asynchronous execution.
"""
import sys
import os

# Add analysis_engine to Python path for imports
sys.path.insert(0, '/app/analysis_engine')

from api.celery_app import celery_app


@celery_app.task(bind=True, name='competitor_scraper.run')
def run_competitor_scraper_task(
    self,
    target_brands: list = None,
    category: str = 'plant-based milk',
    countries: list = None,
    enable_amazon: bool = True,
    enable_retailers: bool = True,
    enable_google_images: bool = True,
    job_id: str = None
):
    """Execute competitor packaging scraper as Celery task.
    
    This task wraps the competitor scraper and adds Celery progress
    tracking for real-time job monitoring.
    
    Args:
        self: Celery task instance (bound)
        target_brands: List of brands to scrape. Defaults to Recolt competitors.
        category: Product category (default: "plant-based milk")
        countries: Target countries. Defaults to Belgium and France.
        enable_amazon: Enable Amazon scraping (default: True)
        enable_retailers: Enable retailer scraping (default: True)
        enable_google_images: Enable Google Images scraping (default: True)
        job_id: Optional job identifier
    
    Returns:
        dict: Result with status, dataset info, and output files
    
    Example:
        >>> task = run_competitor_scraper_task.apply_async(
        ...     kwargs={'target_brands': ['Alpro', 'Oatly']}
        ... )
        >>> result = task.get()
        >>> print(result['dataset']['total_products'])
    """
    from analysis_engine.src.competitor_scraper import scrape_competitor_packaging
    from analysis_engine.src.competitor_models import ScraperProgress
    
    # Set defaults
    if target_brands is None:
        target_brands = ["Alpro", "Oatly", "Bjorg", "Roa Ra", "Hély"]
    
    if countries is None:
        countries = ["Belgium", "France"]
    
    # Get output directory from environment
    output_dir = os.path.join(
        os.getenv('OUTPUT_DIR', '/app/output'),
        'competitor_packaging'
    )
    
    # Update initial state
    self.update_state(
        state='STARTED',
        meta={
            'status': 'Initializing competitor scraper',
            'progress_percent': 0,
            'target_brands': target_brands,
            'category': category
        }
    )
    
    # Define progress callback
    def progress_callback(progress: ScraperProgress):
        """Called by scraper to report progress."""
        meta = {
            'status': f'Scraping {progress.current_brand or "competitors"}...',
            'progress': {
                'current_brand': progress.current_brand,
                'current_source': progress.current_source,
                'brands_completed': progress.brands_completed,
                'brands_total': progress.brands_total,
                'products_collected': progress.products_collected,
                'images_downloaded': progress.images_downloaded,
                'reviews_collected': progress.reviews_collected,
                'progress_percent': progress.progress_percent
            },
            'progress_percent': progress.progress_percent
        }
        
        self.update_state(state='PROGRESS', meta=meta)
    
    # Execute scraper with progress tracking
    try:
        result = scrape_competitor_packaging(
            target_brands=target_brands,
            category=category,
            countries=countries,
            output_dir=output_dir,
            enable_amazon=enable_amazon,
            enable_retailers=enable_retailers,
            enable_google_images=enable_google_images,
            job_id=job_id,
            progress_callback=progress_callback
        )
        
        # Update final state
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Scraping completed successfully',
                'progress_percent': 100,
                'dataset': {
                    'dataset_id': result.dataset.dataset_id,
                    'total_products': result.dataset.total_products,
                    'total_images': result.dataset.total_images,
                    'total_reviews': result.dataset.total_reviews
                }
            }
        )
        
        # Return success result
        return {
            'status': result.status,
            'job_id': result.job_id,
            'dataset': {
                'dataset_id': result.dataset.dataset_id,
                'category': result.dataset.category,
                'target_brands': result.dataset.target_brands,
                'total_products': result.dataset.total_products,
                'total_images': result.dataset.total_images,
                'total_reviews': result.dataset.total_reviews,
                'output_dir': result.dataset.output_dir,
                'metadata_file': result.dataset.metadata_file,
                'images_dir': result.dataset.images_dir
            },
            'output_files': result.output_files,
            'duration_seconds': result.duration_seconds,
            'errors': result.errors,
            'warnings': result.warnings
        }
    
    except Exception as e:
        # Log error and return failure result
        error_msg = f'Competitor scraper execution failed: {str(e)}'
        
        return {
            'status': 'error',
            'errors': [error_msg],
            'target_brands': target_brands,
            'category': category
        }


@celery_app.task(name='competitor_scraper.upload_to_cloud')
def upload_competitor_dataset_to_cloud(
    dataset_dir: str,
    bucket_name: str,
    provider: str = None,
    public: bool = False
):
    """Upload a competitor dataset to cloud storage.
    
    Args:
        dataset_dir: Path to dataset directory
        bucket_name: Cloud storage bucket name
        provider: Storage provider (s3/gcs/azure). Auto-detected if not specified.
        public: Whether to make images publicly accessible
    
    Returns:
        dict: Upload results with URLs
    """
    from analysis_engine.src.cloud_storage import upload_competitor_images_to_cloud
    
    try:
        results = upload_competitor_images_to_cloud(
            dataset_dir=dataset_dir,
            bucket_name=bucket_name,
            provider=provider,
            public=public
        )
        
        successful_uploads = sum(1 for url in results.values() if url)
        
        return {
            'status': 'success',
            'uploaded_count': successful_uploads,
            'total_count': len(results),
            'urls': results
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }
