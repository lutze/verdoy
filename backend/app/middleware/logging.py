"""
Logging middleware for LMS Core API.

This module provides middleware for logging HTTP requests and responses,
including performance metrics and error tracking.
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        logger.info(
            f"Request started - ID: {request_id}, "
            f"Method: {request.method}, "
            f"URL: {request.url}, "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed - ID: {request_id}, "
                f"Status: {response.status_code}, "
                f"Duration: {process_time:.4f}s"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed - ID: {request_id}, "
                f"Error: {str(e)}, "
                f"Duration: {process_time:.4f}s"
            )
            raise


def setup_logging_middleware(app: ASGIApp) -> None:
    """
    Setup logging middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(LoggingMiddleware) 