"""Service for reading category and product data from output files.

This service provides methods to:
- List all available categories
- Get category overview (PODs, POPs, insights)
- Get products for a category
- Get detailed product information with visual analysis
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class CategoryService:
    """Service for accessing category and product data from file system."""

    def __init__(self, output_dir: str, api_base_url: str = ""):
        """Initialize with output directory path.

        Args:
            output_dir: Path to output directory (e.g., "/app/output")
            api_base_url: Base URL for API (e.g., "http://localhost:5000") for constructing full image URLs
        """
        self.output_dir = Path(output_dir)
        self.analysis_dir = self.output_dir / "analysis"
        self.api_base_url = api_base_url

    def list_categories(self) -> List[Dict[str, Any]]:
        """List all available categories from output directory.

        Scans the analysis directory for competitive analysis files and
        extracts category metadata.

        Returns:
            List of category metadata dictionaries with structure:
                [
                    {
                        'id': 'lait_davoine_20260120_184854',
                        'name': 'lait d\'avoine',
                        'run_id': '20260120_184854',
                        'product_count': 23,
                        'has_visual_analysis': True,
                        'has_competitive_analysis': True,
                        'analysis_date': '2026-01-20'
                    },
                    ...
                ]
        """
        categories = []

        if not self.analysis_dir.exists():
            return categories

        # Find all competitive analysis files
        for comp_file in self.analysis_dir.glob("*_competitive_analysis_*.json"):
            # Extract category slug and run_id from filename
            # Format: lait_davoine_competitive_analysis_20260120_184854.json
            filename = comp_file.stem
            parts = filename.split('_competitive_analysis_')

            if len(parts) == 2:
                category_slug = parts[0]
                run_id = parts[1]

                # Read file to get metadata
                try:
                    with open(comp_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Check for corresponding visual analysis
                    visual_file = self.analysis_dir / f"{category_slug}_visual_analysis_{run_id}.json"

                    categories.append({
                        'id': f"{category_slug}_{run_id}",
                        'name': data.get('category', category_slug.replace('_', ' ')),
                        'run_id': run_id,
                        'product_count': data.get('product_count', len(data.get('products', []))),
                        'has_visual_analysis': visual_file.exists(),
                        'has_competitive_analysis': True,
                        'analysis_date': data.get('analysis_date', run_id[:8])  # Extract date from run_id
                    })
                except (json.JSONDecodeError, IOError) as e:
                    # Skip files that can't be read
                    continue

        # Sort by run_id (newest first)
        return sorted(categories, key=lambda x: x['run_id'], reverse=True)

    def get_category_overview(self, category_id: str) -> Dict[str, Any]:
        """Get category overview with PODs, POPs, and strategic insights.

        Args:
            category_id: Composite ID format "lait_davoine_20260120_184854"

        Returns:
            Category data dictionary with structure:
                {
                    'id': 'lait_davoine_20260120_184854',
                    'name': 'lait d\'avoine',
                    'summary': '...',
                    'product_count': 23,
                    'points_of_difference': [...],
                    'points_of_parity': [...],
                    'strategic_insights': [...]
                }

        Raises:
            ValueError: If category_id format is invalid
            FileNotFoundError: If category data file doesn't exist
        """
        category_slug, run_id = self._parse_category_id(category_id)

        # Load competitive analysis
        comp_file = self.analysis_dir / f"{category_slug}_competitive_analysis_{run_id}.json"

        if not comp_file.exists():
            raise FileNotFoundError(f"Category not found: {category_id}")

        with open(comp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            'id': category_id,
            'name': data.get('category'),
            'summary': data.get('category_summary'),
            'product_count': data.get('product_count', len(data.get('products', []))),
            'points_of_difference': data.get('points_of_difference', []),
            'points_of_parity': data.get('points_of_parity', []),
            'strategic_insights': data.get('strategic_insights', [])
        }

    def get_category_products(self, category_id: str) -> List[Dict[str, Any]]:
        """Get all products for a category.

        Merges competitive analysis and visual analysis data.

        Args:
            category_id: Composite ID format "lait_davoine_20260120_184854"

        Returns:
            List of product dictionaries

        Raises:
            ValueError: If category_id format is invalid
            FileNotFoundError: If category data file doesn't exist
        """
        category_slug, run_id = self._parse_category_id(category_id)

        # Load competitive analysis
        comp_file = self.analysis_dir / f"{category_slug}_competitive_analysis_{run_id}.json"
        visual_file = self.analysis_dir / f"{category_slug}_visual_analysis_{run_id}.json"

        if not comp_file.exists():
            raise FileNotFoundError(f"Category not found: {category_id}")

        with open(comp_file, 'r', encoding='utf-8') as f:
            comp_data = json.load(f)

        # Load visual analysis if available
        visual_data = []
        if visual_file.exists():
            with open(visual_file, 'r', encoding='utf-8') as f:
                visual_data = json.load(f)

        # Create lookup by image_path
        comp_lookup = {p['image_path']: p for p in comp_data.get('products', [])}
        visual_lookup = {v['image_path']: v for v in visual_data}

        # Build merged products array
        products = []

        # Use visual data as primary source (has all products)
        for visual_entry in visual_data:
            image_path = visual_entry['image_path']
            comp_entry = comp_lookup.get(image_path, {})

            # Transform image paths for API serving
            filename = image_path.split('/')[-1]
            api_image_path = f"{self.api_base_url}/images/{category_slug}_{run_id}/{filename}"

            # Generate heatmap path
            name_part, ext = filename.rsplit('.', 1) if '.' in filename else (filename, 'png')
            heatmap_path = f"{self.api_base_url}/images/{category_slug}_{run_id}/heatmaps/{name_part}_heatmap.{ext}"

            # Generate product ID from brand name
            product_id = visual_entry['brand'].lower().replace(' ', '_').replace('-', '_')

            # Build visual_analysis object from the analysis data
            analysis = visual_entry.get('analysis', {})
            visual_analysis = None

            if analysis:
                visual_analysis = {
                    'visual_anchor': analysis.get('visual_anchor'),
                    'visual_anchor_description': analysis.get('visual_anchor_description'),
                    'elements': analysis.get('elements', []),
                    'eye_tracking': analysis.get('eye_tracking', {}),
                    'hierarchy_clarity_score': analysis.get('hierarchy_clarity_score'),
                    'detailed_analysis': analysis.get('detailed_analysis'),
                    'massing': analysis.get('massing', {}),
                    'chromatic_mapping': {
                        'color_palette': analysis.get('chromatic_mapping', {}).get('color_palette', []),
                        'surface_finish': analysis.get('chromatic_mapping', {}).get('surface_finish', ''),
                        'surface_finish_description': analysis.get('chromatic_mapping', {}).get('surface_finish_description', ''),
                        'color_harmony': analysis.get('chromatic_mapping', {}).get('color_harmony', ''),
                        'color_psychology_notes': analysis.get('chromatic_mapping', {}).get('color_psychology_notes', ''),
                        'primary_branding_colors': analysis.get('chromatic_mapping', {}).get('primary_branding_colors', []),
                        'accent_colors': analysis.get('chromatic_mapping', {}).get('accent_colors', []),
                        'background_colors': analysis.get('chromatic_mapping', {}).get('background_colors', []),
                    },
                    'textual_inventory': {
                        'claims_summary': analysis.get('textual_inventory', {}).get('claims_summary', []),
                        'emphasized_claims': analysis.get('textual_inventory', {}).get('emphasized_claims', []),
                        'typography_consistency': analysis.get('textual_inventory', {}).get('typography_consistency', ''),
                        'readability_assessment': analysis.get('textual_inventory', {}).get('readability_assessment', ''),
                        'all_text_blocks': analysis.get('textual_inventory', {}).get('all_text_blocks', []),
                        'brand_name_typography': analysis.get('textual_inventory', {}).get('brand_name_typography', ''),
                        'product_name_typography': analysis.get('textual_inventory', {}).get('product_name_typography', ''),
                    },
                    'asset_symbolism': {
                        'trust_marks': analysis.get('asset_symbolism', {}).get('trust_marks', []),
                        'photography_vs_illustration_ratio': analysis.get('asset_symbolism', {}).get('photography_vs_illustration_ratio', ''),
                        'visual_storytelling_elements': analysis.get('asset_symbolism', {}).get('visual_storytelling_elements', []),
                        'trust_signal_effectiveness': analysis.get('asset_symbolism', {}).get('trust_signal_effectiveness', ''),
                        'graphical_assets': analysis.get('asset_symbolism', {}).get('graphical_assets', []),
                    }
                }

            products.append({
                'id': product_id,
                'brand': visual_entry['brand'],
                'name': visual_entry['product_name'],
                'image': api_image_path,
                'heatmap': heatmap_path,
                'pod_scores': comp_entry.get('pod_scores', []),
                'pop_status': comp_entry.get('pop_status', []),
                'positioning': comp_entry.get('positioning_summary', ''),
                'key_differentiator': comp_entry.get('key_differentiator', ''),
                'palette': analysis.get('chromatic_mapping', {}).get('color_palette', []),
                'visual_analysis': visual_analysis
            })

        return products

    def get_product_detail(self, category_id: str, product_id: str) -> Dict[str, Any]:
        """Get single product with full visual analysis.

        Args:
            category_id: Composite ID format "lait_davoine_20260120_184854"
            product_id: Product identifier (e.g., "bjorg")

        Returns:
            Product dictionary with full visual analysis

        Raises:
            ValueError: If category_id format is invalid
            FileNotFoundError: If product or category not found
        """
        # Get all products first
        products = self.get_category_products(category_id)

        # Find matching product
        for product in products:
            if product['id'] == product_id:
                # Load full visual analysis
                category_slug, run_id = self._parse_category_id(category_id)
                visual_file = self.analysis_dir / f"{category_slug}_visual_analysis_{run_id}.json"

                if visual_file.exists():
                    with open(visual_file, 'r', encoding='utf-8') as f:
                        visual_data = json.load(f)

                    # Find matching visual entry by brand name
                    for entry in visual_data:
                        entry_id = entry['brand'].lower().replace(' ', '_').replace('-', '_')
                        if entry_id == product_id:
                            product['visual_analysis'] = entry.get('analysis')
                            break

                return product

        raise FileNotFoundError(f"Product not found: {product_id}")

    def _parse_category_id(self, category_id: str) -> tuple[str, str]:
        """Parse category_id into category_slug and run_id.

        Args:
            category_id: Composite ID like "lait_davoine_20260120_184854"

        Returns:
            Tuple of (category_slug, run_id)

        Raises:
            ValueError: If category_id format is invalid

        Example:
            >>> service._parse_category_id("lait_davoine_20260120_184854")
            ("lait_davoine", "20260120_184854")
        """
        # Split by last two underscores to extract run_id (YYYYMMDD_HHMMSS format)
        parts = category_id.rsplit('_', 2)

        if len(parts) >= 3:
            # Reconstruct: everything before last 2 parts is category_slug
            category_slug = '_'.join(parts[:-2])
            # Last 2 parts form run_id
            run_id = '_'.join(parts[-2:])
            return category_slug, run_id
        else:
            raise ValueError(f"Invalid category_id format: {category_id}. Expected format: category_slug_YYYYMMDD_HHMMSS")
