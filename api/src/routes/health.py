"""Health check endpoint for API monitoring."""
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint.

    Returns:
        JSON response with status
    """
    return jsonify({
        'status': 'healthy',
        'service': 'leadgen-api',
        'version': '1.0.0'
    })
