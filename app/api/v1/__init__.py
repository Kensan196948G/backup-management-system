"""
API v1 Module
RESTful API endpoints version 1 for Backup Management System

Endpoints:
- /api/v1/auth - Authentication (login, token refresh)
- /api/v1/backups - Backup job management
- /api/v1/storage - Storage provider management
- /api/v1/verify - Verification management
- /api/v1/compliance - Compliance status
"""
from flask import Blueprint

from app.api import api_bp

# Import v1 route modules
from app.api.v1 import backup_api, storage_api, verification_api

# All routes are registered on the parent api_bp with /api/v1 prefix
