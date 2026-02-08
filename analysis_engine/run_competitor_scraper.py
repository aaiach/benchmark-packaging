#!/usr/bin/env python3
"""CLI runner for competitor packaging scraper.

Usage:
    python run_competitor_scraper.py --brands "Alpro,Oatly,Bjorg" --category "oat milk"
    python run_competitor_scraper.py --help

Examples:
    # Scrape default competitors (Alpro, Oatly, Bjorg, Roa Ra, Hély)
    python run_competitor_scraper.py
    
    # Scrape specific brands
    python run_competitor_scraper.py --brands "Alpro,Oatly"
    
    # Scrape with custom category
    python run_competitor_scraper.py --category "almond milk"
    
    # Enable only specific sources
    python run_competitor_scraper.py --no-amazon --no-retailers
    
    # Upload to cloud after scraping
    python run_competitor_scraper.py --upload-cloud --bucket my-bucket
"""
import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from competitor_scraper import scrape_competitor_packaging
from cloud_storage import upload_competitor_images_to_cloud


def main():
    parser = argparse.ArgumentParser(
        description='Scrape competitor packaging from Amazon, retailers, and Google Images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Brand and category options
    parser.add_argument(
        '--brands',
        type=str,
        help='Comma-separated list of brands to scrape (default: Alpro,Oatly,Bjorg,Roa Ra,Hély)'
    )
    parser.add_argument(
        '--category',
        type=str,
        default='plant-based milk',
        help='Product category (default: "plant-based milk")'
    )
    parser.add_argument(
        '--countries',
        type=str,
        default='Belgium,France',
        help='Comma-separated list of countries (default: Belgium,France)'
    )
    
    # Source toggles
    parser.add_argument(
        '--no-amazon',
        action='store_true',
        help='Disable Amazon scraping'
    )
    parser.add_argument(
        '--no-retailers',
        action='store_true',
        help='Disable retailer scraping'
    )
    parser.add_argument(
        '--no-google-images',
        action='store_true',
        help='Disable Google Images scraping'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output/competitor_packaging',
        help='Output directory (default: output/competitor_packaging)'
    )
    parser.add_argument(
        '--job-id',
        type=str,
        help='Custom job ID (default: auto-generated)'
    )
    
    # Cloud upload options
    parser.add_argument(
        '--upload-cloud',
        action='store_true',
        help='Upload images to cloud storage after scraping'
    )
    parser.add_argument(
        '--bucket',
        type=str,
        help='Cloud storage bucket name (required with --upload-cloud)'
    )
    parser.add_argument(
        '--provider',
        type=str,
        choices=['s3', 'gcs', 'azure'],
        help='Cloud storage provider (auto-detected if not specified)'
    )
    parser.add_argument(
        '--public',
        action='store_true',
        help='Make uploaded images publicly accessible'
    )
    
    args = parser.parse_args()
    
    # Parse brands
    if args.brands:
        target_brands = [b.strip() for b in args.brands.split(',')]
    else:
        target_brands = None  # Use defaults
    
    # Parse countries
    countries = [c.strip() for c in args.countries.split(',')]
    
    # Validate cloud upload options
    if args.upload_cloud and not args.bucket:
        parser.error('--bucket is required when --upload-cloud is specified')
    
    print("=" * 70)
    print("Competitor Packaging Scraper")
    print("=" * 70)
    
    # Run scraper
    try:
        result = scrape_competitor_packaging(
            target_brands=target_brands,
            category=args.category,
            countries=countries,
            output_dir=args.output_dir,
            enable_amazon=not args.no_amazon,
            enable_retailers=not args.no_retailers,
            enable_google_images=not args.no_google_images,
            job_id=args.job_id
        )
        
        # Print results
        print(f"\nStatus: {result.status.upper()}")
        print(f"Dataset ID: {result.dataset.dataset_id}")
        print(f"Products collected: {result.dataset.total_products}")
        print(f"Images downloaded: {result.dataset.total_images}")
        print(f"Reviews collected: {result.dataset.total_reviews}")
        print(f"Duration: {result.duration_seconds:.1f}s")
        print(f"\nOutput directory: {result.dataset.output_dir}")
        print(f"Metadata file: {result.dataset.metadata_file}")
        print(f"Images directory: {result.dataset.images_dir}")
        
        if result.errors:
            print(f"\n⚠️  Errors encountered: {len(result.errors)}")
            for error in result.errors[:3]:
                print(f"  - {error}")
            if len(result.errors) > 3:
                print(f"  ... and {len(result.errors) - 3} more")
        
        if result.warnings:
            print(f"\n⚠️  Warnings: {len(result.warnings)}")
        
        # Cloud upload
        if args.upload_cloud:
            print(f"\n{'='*70}")
            print("Uploading to Cloud Storage")
            print(f"{'='*70}")
            
            try:
                urls = upload_competitor_images_to_cloud(
                    dataset_dir=result.dataset.output_dir,
                    bucket_name=args.bucket,
                    provider=args.provider,
                    public=args.public
                )
                
                successful = sum(1 for url in urls.values() if url)
                print(f"✓ Uploaded {successful}/{len(urls)} images to {args.bucket}")
                
            except Exception as e:
                print(f"✗ Cloud upload failed: {e}")
                return 1
        
        return 0 if result.status == 'success' else 1
        
    except Exception as e:
        print(f"\n✗ Scraper failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
