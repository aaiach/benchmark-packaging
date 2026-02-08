#!/usr/bin/env python3
"""Standalone CLI tool to generate Golden Rules reports from competitive analysis data.

This is a standalone version that doesn't require the full analysis_engine dependencies.

Usage:
    python3 generate_golden_rules_standalone.py --category lait_davoine --run-id 20260208_120000
    python3 generate_golden_rules_standalone.py --category lait_davoine --run-id 20260208_120000 --format json
"""
import argparse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from golden_rules_generator import GoldenRulesAnalyzer


def list_runs(output_dir="output"):
    """List available runs by scanning for competitive analysis files."""
    from pathlib import Path
    import json
    
    analysis_dir = Path(output_dir) / "analysis"
    if not analysis_dir.exists():
        return []
    
    runs = []
    for comp_file in analysis_dir.glob("*_competitive_analysis_*.json"):
        filename = comp_file.stem
        parts = filename.split('_competitive_analysis_')
        
        if len(parts) == 2:
            category_slug = parts[0]
            run_id = parts[1]
            
            try:
                with open(comp_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                runs.append({
                    'category': data.get('category', category_slug.replace('_', ' ')),
                    'run_id': run_id
                })
            except:
                continue
    
    return runs


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description='Generate Golden Rules report from competitive analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --category lait_davoine --run-id 20260208_120000
  %(prog)s --category lait_davoine --run-id 20260208_120000 --format json --output report.json
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
        help='Run ID (e.g., "20260208_120000")'
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
        default='output',
        help='Output directory (default: output)'
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
        runs = list_runs(args.output_dir)
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
            from pathlib import Path
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
