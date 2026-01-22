"""Category and product data API routes.

Endpoints for retrieving category overview, products, and detailed product information.
"""
from flask import Blueprint, jsonify, current_app, request
from api.src.services.category_service import CategoryService

categories_bp = Blueprint('categories', __name__)


def get_api_base_url():
    """Get the API base URL from the request."""
    # Use the request's host to construct the base URL
    scheme = request.scheme  # http or https
    host = request.host  # e.g., localhost:5000
    return f"{scheme}://{host}"


@categories_bp.route('', methods=['GET'])
def list_categories():
    """List all available categories.

    Returns:
        JSON response:
            {
                "categories": [
                    {
                        "id": "lait_davoine_20260120_184854",
                        "name": "lait d'avoine",
                        "run_id": "20260120_184854",
                        "product_count": 23,
                        "has_visual_analysis": true,
                        "has_competitive_analysis": true,
                        "analysis_date": "20260120"
                    },
                    ...
                ]
            }

    Status codes:
        200: Success
        500: Server error
    """
    try:
        output_dir = current_app.config['OUTPUT_DIR']
        api_base_url = get_api_base_url()
        service = CategoryService(output_dir, api_base_url)
        categories = service.list_categories()

        return jsonify({'categories': categories}), 200

    except Exception as e:
        current_app.logger.error(f'Failed to list categories: {e}')
        return jsonify({'error': 'Failed to retrieve categories'}), 500


@categories_bp.route('/<category_id>', methods=['GET'])
def get_category(category_id):
    """Get category overview with PODs, POPs, and insights.

    Args:
        category_id: Composite ID format "lait_davoine_20260120_184854"

    Returns:
        JSON response:
            {
                "id": "lait_davoine_20260120_184854",
                "name": "lait d'avoine",
                "summary": "...",
                "product_count": 23,
                "points_of_difference": [...],
                "points_of_parity": [...],
                "strategic_insights": [...]
            }

    Status codes:
        200: Success
        400: Invalid category ID format
        404: Category not found
        500: Server error
    """
    try:
        output_dir = current_app.config['OUTPUT_DIR']
        api_base_url = get_api_base_url()
        service = CategoryService(output_dir, api_base_url)
        category_data = service.get_category_overview(category_id)

        return jsonify(category_data), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404

    except Exception as e:
        current_app.logger.error(f'Failed to get category {category_id}: {e}')
        return jsonify({'error': 'Failed to retrieve category'}), 500


@categories_bp.route('/<category_id>/products', methods=['GET'])
def get_category_products(category_id):
    """Get all products for a category.

    Args:
        category_id: Composite ID format "lait_davoine_20260120_184854"

    Returns:
        JSON response:
            {
                "products": [
                    {
                        "id": "bjorg",
                        "brand": "Bjorg",
                        "name": "Boisson Avoine Calcium",
                        "image": "/images/lait_davoine_20260120_184854/01_bjorg.png",
                        "heatmap": "/images/lait_davoine_20260120_184854/heatmaps/01_bjorg_heatmap.png",
                        "pod_scores": [...],
                        "pop_status": [...],
                        "positioning": "...",
                        "key_differentiator": "...",
                        "palette": [...]
                    },
                    ...
                ]
            }

    Status codes:
        200: Success
        400: Invalid category ID format
        404: Category not found
        500: Server error
    """
    try:
        output_dir = current_app.config['OUTPUT_DIR']
        api_base_url = get_api_base_url()
        service = CategoryService(output_dir, api_base_url)
        products = service.get_category_products(category_id)

        return jsonify({'products': products}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404

    except Exception as e:
        current_app.logger.error(f'Failed to get products for {category_id}: {e}')
        return jsonify({'error': 'Failed to retrieve products'}), 500


@categories_bp.route('/<category_id>/products/<product_id>', methods=['GET'])
def get_product(category_id, product_id):
    """Get single product with full visual analysis.

    Args:
        category_id: Composite ID format "lait_davoine_20260120_184854"
        product_id: Product identifier (e.g., "bjorg")

    Returns:
        JSON response:
            {
                "id": "bjorg",
                "brand": "Bjorg",
                "name": "Boisson Avoine Calcium",
                "image": "/images/lait_davoine_20260120_184854/01_bjorg.png",
                "heatmap": "/images/lait_davoine_20260120_184854/heatmaps/01_bjorg_heatmap.png",
                "pod_scores": [...],
                "pop_status": [...],
                "positioning": "...",
                "key_differentiator": "...",
                "palette": [...],
                "visual_analysis": {
                    "visual_anchor": "...",
                    "elements": [...],
                    "eye_tracking": {...},
                    "hierarchy_clarity_score": 8,
                    "chromatic_mapping": {...},
                    "textual_inventory": {...},
                    "asset_symbolism": {...}
                }
            }

    Status codes:
        200: Success
        400: Invalid category ID format
        404: Product or category not found
        500: Server error
    """
    try:
        output_dir = current_app.config['OUTPUT_DIR']
        api_base_url = get_api_base_url()
        service = CategoryService(output_dir, api_base_url)
        product = service.get_product_detail(category_id, product_id)

        return jsonify(product), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404

    except Exception as e:
        current_app.logger.error(f'Failed to get product {product_id} for {category_id}: {e}')
        return jsonify({'error': 'Failed to retrieve product'}), 500
