#!/usr/bin/env python3
"""CLI tool to generate Golden Rules reports from competitive analysis data.

Usage:
    python generate_golden_rules.py --category lait_davoine --run-id 20260120_184854
    python generate_golden_rules.py --category lait_davoine --run-id 20260120_184854 --format json
    python generate_golden_rules.py --list-runs
"""
import argparse
import sys
from pathlib import Path

from src.golden_rules_generator import GoldenRulesAnalyzer
from src.image_selector import list_runs
from src.config import get_config


def main():
    """Main CLI entry point."""
    config = get_config()
    
    parser = argparse.ArgumentParser(
        description='Generate Golden Rules report from competitive analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --category lait_davoine --run-id 20260120_184854
  %(prog)s --category lait_davoine --run-id 20260120_184854 --format json --output report.json
  %(prog)s --list-runs
        """
    )
    
    # Category and run ID
    parser.add_argument(
        '--category',
        type=str,
        help='Category slug (e.g., "lait_davoine")'
    )
    
    parser.add_argument(
        '--run-id',
        type=str,
        help='Run ID (e.g., "20260120_184854")'
    )
    
    # Output options
    parser.add_argument(
        '--format',
        type=str,
        choices=['markdown', 'json', 'html'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: stdout)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=config.output_dir,
        help=f'Output directory (default: {config.output_dir})'
    )
    
    # Information commands
    parser.add_argument(
        '--list-runs',
        action='store_true',
        help='List all available runs'
    )
    
    args = parser.parse_args()
    
    # Handle --list-runs
    if args.list_runs:
        print("\nAvailable runs:")
        print("-" * 70)
        runs = list_runs()
        if not runs:
            print("  No runs found in the output directory")
        else:
            for run in runs:
                print(f"  Category: {run['category']:<20} Run ID: {run['run_id']}")
        print("-" * 70)
        return 0
    
    # Validate required arguments
    if not args.category or not args.run_id:
        print("[!] Error: --category and --run-id are required")
        print("    Use --list-runs to see available runs")
        return 1
    
    # Print header
    print("=" * 80)
    print(f"GOLDEN RULES REPORT GENERATOR")
    print("=" * 80)
    print(f"Category:     {args.category}")
    print(f"Run ID:       {args.run_id}")
    print(f"Format:       {args.format}")
    print(f"Output:       {args.output or 'stdout'}")
    print("-" * 80)
    
    # Initialize analyzer
    analyzer = GoldenRulesAnalyzer(args.output_dir)
    
    try:
        # Generate report
        print("Generating report...")
        report_content = analyzer.generate_report(
            category_slug=args.category,
            run_id=args.run_id,
            output_format=args.format
        )
        
        # Output report
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"✓ Report saved to: {output_path}")
            print(f"  File size: {len(report_content)} bytes")
        else:
            print("\n" + "=" * 80)
            print(report_content)
        
        print("\n" + "=" * 80)
        print("✓ REPORT GENERATION COMPLETE")
        print("=" * 80)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n[!] Error: {e}")
        print("    Make sure the competitive analysis has been run first")
        print(f"    Expected files in: {args.output_dir}/analysis/")
        return 1
    
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
