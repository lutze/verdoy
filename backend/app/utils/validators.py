"""
Custom validators for VerdoyLab API.

This module contains custom validation functions for various data types
used throughout the application.
"""

import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from pydantic import validator

from .helpers import is_valid_uuid, validate_email


def validate_device_id(device_id: str) -> bool:
    """
    Validate device ID format.
    
    Args:
        device_id: Device ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Device ID should be in format ESP32_XXXXXXXX
    pattern = r'^ESP32_[A-F0-9]{8}$'
    return bool(re.match(pattern, device_id))


def validate_sensor_reading(reading: Dict[str, Any]) -> bool:
    """
    Validate sensor reading data.
    
    Args:
        reading: Sensor reading dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['sensor_type', 'value', 'timestamp']
    
    # Check required fields
    for field in required_fields:
        if field not in reading:
            return False
    
    # Validate sensor type
    valid_sensor_types = ['temperature', 'humidity', 'pressure', 'light', 'motion', 'voltage']
    if reading['sensor_type'] not in valid_sensor_types:
        return False
    
    # Validate value is numeric
    try:
        float(reading['value'])
    except (ValueError, TypeError):
        return False
    
    # Validate timestamp
    try:
        if isinstance(reading['timestamp'], str):
            datetime.fromisoformat(reading['timestamp'].replace('Z', '+00:00'))
        elif isinstance(reading['timestamp'], datetime):
            pass  # Already a datetime object
        else:
            return False
    except ValueError:
        return False
    
    return True


def validate_alert_rule(rule: Dict[str, Any]) -> bool:
    """
    Validate alert rule configuration.
    
    Args:
        rule: Alert rule dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['name', 'sensor_type', 'condition', 'threshold', 'enabled']
    
    # Check required fields
    for field in required_fields:
        if field not in rule:
            return False
    
    # Validate condition
    valid_conditions = ['greater_than', 'less_than', 'equals', 'not_equals']
    if rule['condition'] not in valid_conditions:
        return False
    
    # Validate threshold is numeric
    try:
        float(rule['threshold'])
    except (ValueError, TypeError):
        return False
    
    # Validate enabled is boolean
    if not isinstance(rule['enabled'], bool):
        return False
    
    return True


def validate_password_strength(password: str) -> Dict[str, bool]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with validation results
    """
    return {
        'length': len(password) >= 8,
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'lowercase': bool(re.search(r'[a-z]', password)),
        'digit': bool(re.search(r'\d', password)),
        'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    }


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (7-15 digits)
    return 7 <= len(digits_only) <= 15


def validate_ip_address(ip: str) -> bool:
    """
    Validate IP address format.
    
    Args:
        ip: IP address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(pattern, ip))


def validate_mac_address(mac: str) -> bool:
    """
    Validate MAC address format.
    
    Args:
        mac: MAC address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(pattern, mac))


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate geographic coordinates.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        True if valid, False otherwise
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180


def validate_time_range(start_time: datetime, end_time: datetime) -> bool:
    """
    Validate time range (start time should be before end time).
    
    Args:
        start_time: Start time
        end_time: End time
        
    Returns:
        True if valid, False otherwise
    """
    return start_time < end_time


def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Validate file size.
    
    Args:
        file_size: File size in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        True if valid, False otherwise
    """
    return 0 <= file_size <= max_size


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate file extension.
    
    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions
        
    Returns:
        True if valid, False otherwise
    """
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in [ext.lower() for ext in allowed_extensions]


# Pydantic validators for use in schemas
def validate_device_id_field(v: str) -> str:
    """Pydantic validator for device ID field."""
    if not validate_device_id(v):
        raise ValueError('Invalid device ID format')
    return v


def validate_email_field(v: str) -> str:
    """Pydantic validator for email field."""
    if not validate_email(v):
        raise ValueError('Invalid email format')
    return v


def validate_uuid_field(v: str) -> str:
    """Pydantic validator for UUID field."""
    if not is_valid_uuid(v):
        raise ValueError('Invalid UUID format')
    return v


def validate_positive_number(v: Union[int, float]) -> Union[int, float]:
    """Pydantic validator for positive numbers."""
    if v <= 0:
        raise ValueError('Value must be positive')
    return v


def validate_percentage(v: Union[int, float]) -> Union[int, float]:
    """Pydantic validator for percentage values (0-100)."""
    if not 0 <= v <= 100:
        raise ValueError('Percentage must be between 0 and 100')
    return v 