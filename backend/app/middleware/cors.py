"""
CORS middleware configuration for LMS Core API.

This module handles Cross-Origin Resource Sharing (CORS) configuration
for the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import settings


def setup_cors_middleware(app: FastAPI) -> None:
    """
    Setup CORS middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=getattr(settings, 'allow_credentials', True),
        allow_methods=getattr(settings, 'allow_methods', ["*"]),
        allow_headers=getattr(settings, 'allow_headers', ["*"]),
    ) 