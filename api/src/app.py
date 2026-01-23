"""Flask application factory and configuration.

This module creates and configures the Flask application with:
- CORS support for frontend communication
- API route blueprints
- Static file serving for images
- Error handling
"""
import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS


def create_app() -> Flask:
    """Create and configure Flask application.

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Configuration
    app.config['OUTPUT_DIR'] = os.getenv('OUTPUT_DIR', '/app/output')
    app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max request size

    # CORS configuration
    # In production, set CORS_ORIGINS to your domain (e.g., "https://packaging-benchmark.tryiceberg.ai")
    # Multiple origins can be comma-separated
    cors_origins = os.getenv('CORS_ORIGINS', '*')
    if cors_origins != '*':
        cors_origins = [origin.strip() for origin in cors_origins.split(',')]
    
    # Enable CORS for API and images endpoints
    CORS(app, resources={
        r"/api/*": {"origins": cors_origins},
        r"/images/*": {"origins": cors_origins}
    })

    # Register blueprints
    from .routes.health import health_bp
    from .routes.scraper import scraper_bp
    from .routes.categories import categories_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(scraper_bp, url_prefix='/api/scraper')
    app.register_blueprint(categories_bp, url_prefix='/api/categories')

    # Static file serving for images and heatmaps
    @app.route('/images/<path:filename>')
    def serve_image(filename):
        """Serve images from output directory.

        Args:
            filename: Path to image file (e.g., "lait_davoine_20260120_184854/01_bjorg.png")

        Returns:
            Image file or 404 error
        """
        images_dir = os.path.join(app.config['OUTPUT_DIR'], 'images')
        return send_from_directory(images_dir, filename)

    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all uncaught exceptions."""
        app.logger.error(f'Unhandled exception: {error}')
        return jsonify({'error': 'An unexpected error occurred'}), 500

    return app
