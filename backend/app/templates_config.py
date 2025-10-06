"""
Shared templates configuration for the VerdoyLab API.

This module provides a centralized Jinja2Templates instance with custom filters
that can be imported and used consistently across all routers.
"""

from fastapi.templating import Jinja2Templates


def get_templates():
    """
    Get configured Jinja2Templates instance with custom filters.
    
    This ensures all routers use the same template configuration
    with consistent custom filters and settings.
    """
    templates = Jinja2Templates(directory="app/templates")
    
    def number_format(value):
        """Format numbers with commas for better readability."""
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return value
    
    # Add custom filters
    templates.env.filters["number_format"] = number_format
    
    return templates


# Global templates instance - import this in routers
templates = get_templates() 