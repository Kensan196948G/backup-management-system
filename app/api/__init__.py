"""
REST API Blueprint
Provides RESTful API endpoints for external integrations
API Version: v1
"""
from flask import Blueprint

# Create API blueprint with /api prefix
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Import routes after blueprint creation to avoid circular imports
# Import v1 API routes
from app.api import alerts, backup, dashboard, jobs, media, reports, v1, verification

# Register error handlers
from app.api.errors import register_error_handlers

register_error_handlers(api_bp)
