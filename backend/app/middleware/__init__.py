"""
Middleware package for LMS Core API.

This package contains custom middleware for CORS, logging,
WebSocket handling, and other cross-cutting concerns.
"""

from .cors import setup_cors_middleware
from .logging import setup_logging_middleware
from .websocket import setup_websocket_middleware

__all__ = [
    "setup_cors_middleware",
    "setup_logging_middleware", 
    "setup_websocket_middleware"
] 