"""
Helper functions for VerdoyLab API.

This module contains common utility functions used across the application
for data processing, formatting, and general operations.
"""

import re
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from statistics import mean, median, stdev
from fastapi import Request


def generate_device_id() -> str:
    """
    Generate a unique device ID.
    
    Returns:
        Unique device ID string
    """
    return f"ESP32_{uuid.uuid4().hex[:8].upper()}"


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def format_timestamp(timestamp: Union[datetime, str], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp to string.
    
    Args:
        timestamp: Timestamp to format
        format_str: Format string
        
    Returns:
        Formatted timestamp string
    """
    if isinstance(timestamp, str):
        # Try to parse string timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return timestamp
    
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    return timestamp.strftime(format_str)


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate basic statistics for a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Dictionary with statistics (min, max, mean, median, std_dev, count)
    """
    if not values:
        return {
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "std_dev": 0.0,
            "count": 0
        }
    
    return {
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
        "median": median(values),
        "std_dev": stdev(values) if len(values) > 1 else 0.0,
        "count": len(values)
    }


def generate_hash(data: str) -> str:
    """
    Generate SHA-256 hash of data.
    
    Args:
        data: Data to hash
        
    Returns:
        SHA-256 hash string
    """
    return hashlib.sha256(data.encode()).hexdigest()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + ('.' + ext if ext else '')
    
    return filename


def parse_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate query parameters.
    
    Args:
        params: Raw query parameters
        
    Returns:
        Parsed and validated parameters
    """
    parsed = {}
    
    # Handle pagination
    if 'page' in params:
        try:
            parsed['page'] = max(1, int(params['page']))
        except (ValueError, TypeError):
            parsed['page'] = 1
    
    if 'size' in params:
        try:
            parsed['size'] = max(1, min(100, int(params['size'])))
        except (ValueError, TypeError):
            parsed['size'] = 20
    
    # Handle date ranges
    for date_field in ['start_date', 'end_date', 'created_after', 'created_before']:
        if date_field in params:
            try:
                parsed[date_field] = datetime.fromisoformat(params[date_field])
            except (ValueError, TypeError):
                continue
    
    # Handle boolean fields
    for bool_field in ['active', 'enabled', 'is_online']:
        if bool_field in params:
            parsed[bool_field] = params[bool_field].lower() in ('true', '1', 'yes')
    
    return parsed


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        Secure API key string
    """
    return f"lms_{uuid.uuid4().hex}"


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Check if string is a valid UUID.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def accepts_json(request: Request) -> bool:
    """
    Check if the request accepts JSON response.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if request accepts JSON, False otherwise
    """
    accept_header = request.headers.get("accept", "")
    return "application/json" in accept_header.lower() or "*/*" in accept_header.lower() 