#!/usr/bin/env python3
"""
Backup Management System - Application Entry Point
Supports both development (Flask dev server) and production (Waitress) modes

Usage:
    Development (Linux):
        python run.py
        or
        flask run

    Production (Windows/Linux):
        python run.py --production
        or
        FLASK_ENV=production python run.py

Environment Variables:
    FLASK_ENV: 'development', 'production', or 'testing' (default: development)
    FLASK_HOST: Host to bind to (default: 127.0.0.1 for dev, 0.0.0.0 for prod)
    FLASK_PORT: Port to bind to (default: 5000)
"""
import argparse
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from app import create_app


def run_development(app, host, port):
    """
    Run Flask development server

    Args:
        app: Flask application instance
        host: Host to bind to
        port: Port to bind to
    """
    app.logger.info("=" * 60)
    app.logger.info("Starting Flask Development Server")
    app.logger.info(f"Host: {host}")
    app.logger.info(f"Port: {port}")
    app.logger.info(f"Debug Mode: {app.debug}")
    app.logger.info("=" * 60)

    # Run Flask development server
    app.run(host=host, port=port, debug=app.debug, use_reloader=True, threaded=True)


def run_production(app, host, port):
    """
    Run Waitress WSGI server (production)

    Args:
        app: Flask application instance
        host: Host to bind to
        port: Port to bind to
    """
    try:
        from waitress import serve

        app.logger.info("=" * 60)
        app.logger.info("Starting Waitress Production Server")
        app.logger.info(f"Host: {host}")
        app.logger.info(f"Port: {port}")
        app.logger.info(f"Platform: {os.name}")
        app.logger.info("=" * 60)

        # Waitress configuration
        # See: https://docs.pylonsproject.org/projects/waitress/en/stable/
        serve(
            app,
            host=host,
            port=port,
            threads=8,  # Number of threads for handling requests
            channel_timeout=120,  # Timeout for client connections
            cleanup_interval=30,  # Cleanup interval for inactive connections
            url_scheme="http",  # Use 'https' if SSL is configured
            ident="Backup Management System",  # Server identity
        )

    except ImportError:
        app.logger.error("Waitress is not installed. Please install it:")
        app.logger.error("  pip install waitress")
        sys.exit(1)


def run_testing(app):
    """
    Run application in testing mode

    Args:
        app: Flask application instance
    """
    app.logger.info("=" * 60)
    app.logger.info("Application running in TESTING mode")
    app.logger.info("This mode is for automated testing only")
    app.logger.info("=" * 60)


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Backup Management System - 3-2-1-1-0 Rule Compliance")
    parser.add_argument("--production", action="store_true", help="Run in production mode with Waitress WSGI server")
    parser.add_argument(
        "--host", type=str, default=None, help="Host to bind to (default: 127.0.0.1 for dev, 0.0.0.0 for prod)"
    )
    parser.add_argument("--port", type=int, default=None, help="Port to bind to (default: 5000)")
    parser.add_argument(
        "--config",
        type=str,
        choices=["development", "production", "testing"],
        default=None,
        help="Configuration to use (overrides FLASK_ENV)",
    )

    args = parser.parse_args()

    # Determine configuration
    if args.config:
        config_name = args.config
        os.environ["FLASK_ENV"] = config_name
    elif args.production:
        config_name = "production"
        os.environ["FLASK_ENV"] = "production"
    else:
        config_name = os.environ.get("FLASK_ENV", "development")

    # Create Flask application
    app = create_app(config_name)

    # Determine host and port
    if args.host:
        host = args.host
    else:
        if config_name == "production":
            # Production: bind to all interfaces
            host = os.environ.get("FLASK_HOST", "0.0.0.0")
        else:
            # Development: bind to localhost only
            host = os.environ.get("FLASK_HOST", "127.0.0.1")

    port = args.port or int(os.environ.get("FLASK_PORT", 5000))

    # Create database tables if they don't exist
    with app.app_context():
        from app.models import db

        try:
            db.create_all()
            app.logger.info("Database tables created/verified successfully")
        except Exception as e:
            app.logger.error(f"Failed to create database tables: {e}")
            sys.exit(1)

    # Run application
    try:
        if config_name == "testing":
            run_testing(app)
        elif config_name == "production" or args.production:
            run_production(app, host, port)
        else:
            run_development(app, host, port)

    except KeyboardInterrupt:
        app.logger.info("Application shutdown requested")
        sys.exit(0)
    except Exception as e:
        app.logger.error(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
