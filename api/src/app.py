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
    from .routes.competitor_scraper import competitor_scraper_bp
    from .routes.categories import categories_bp
    from .routes.email import email_bp
    from .routes.image_analysis import image_analysis_bp
    from .routes.rebrand import rebrand_bp
    from .routes.rebrand_session import rebrand_session_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(scraper_bp, url_prefix='/api/scraper')
    app.register_blueprint(competitor_scraper_bp, url_prefix='/api/competitor-scraper')
    app.register_blueprint(categories_bp, url_prefix='/api/categories')
    app.register_blueprint(email_bp, url_prefix='/api/email')
    app.register_blueprint(image_analysis_bp, url_prefix='/api/image-analysis')
    app.register_blueprint(rebrand_bp, url_prefix='/api/rebrand')
    app.register_blueprint(rebrand_session_bp, url_prefix='/api')

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

    # Static file serving for single image analysis uploads
    @app.route('/images/single_analysis/<path:filename>')
    def serve_single_analysis_image(filename):
        """Serve images from single analysis directory.

        Args:
            filename: Path to image file (e.g., "images/abc123.png")

        Returns:
            Image file or 404 error
        """
        single_analysis_dir = os.path.join(app.config['OUTPUT_DIR'], 'single_analysis')
        return send_from_directory(single_analysis_dir, filename)

    # Static file serving for rebrand images (source, inspiration, crops, final)
    # Cache for 1 year since these are immutable (unique job_id in path)
    @app.route('/images/rebrand/<path:filename>')
    def serve_rebrand_image(filename):
        """Serve images from rebrand output directory.

        Args:
            filename: Path to image file (e.g., "job_id/final_rebrand.png")

        Returns:
            Image file or 404 error with long-term caching (immutable content)
        """
        rebrand_dir = os.path.join(app.config['OUTPUT_DIR'], 'rebrand')
        # max_age=31536000 (1 year) since job_id makes these immutable
        return send_from_directory(rebrand_dir, filename, max_age=31536000)

    # Static file serving for rebrand session images
    # Cache for 1 year since these are immutable (unique session_id in path)
    @app.route('/images/rebrand_sessions/<path:filename>')
    def serve_rebrand_session_image(filename):
        """Serve images from rebrand sessions directory.

        Args:
            filename: Path to image file (e.g., "session_id/source.png")

        Returns:
            Image file or 404 error with long-term caching (immutable content)
        """
        sessions_dir = os.path.join(app.config['OUTPUT_DIR'], 'rebrand_sessions')
        # max_age=31536000 (1 year) since session_id makes these immutable
        return send_from_directory(sessions_dir, filename, max_age=31536000)

    # Static file serving for competitor packaging images
    # Cache for 1 hour since these are scraped data
    @app.route('/images/competitor_packaging/<path:filename>')
    def serve_competitor_packaging_image(filename):
        """Serve images from competitor packaging directory.

        Args:
            filename: Path to image file (e.g., "dataset_id/images/alpro/image.jpg")

        Returns:
            Image file or 404 error with caching
        """
        competitor_dir = os.path.join(app.config['OUTPUT_DIR'], 'competitor_packaging')
        # max_age=3600 (1 hour) for cached competitor images
        return send_from_directory(competitor_dir, filename, max_age=3600)

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
