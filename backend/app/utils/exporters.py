"""
Data export utilities for LMS Core API.

This module provides functions for exporting data in various formats
including CSV, JSON, and Excel.
"""

import csv
import json
import io
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

# Optional pandas import for Excel export functionality
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from .helpers import format_timestamp, sanitize_filename


def export_to_csv(data: List[Dict[str, Any]], filename: str = None) -> tuple:
    """
    Export data to CSV format.
    
    Args:
        data: List of dictionaries to export
        filename: Optional filename for the export
        
    Returns:
        Tuple of (file_content, filename, content_type)
    """
    if not data:
        return "", "empty.csv", "text/csv"
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.csv"
    
    # Sanitize filename
    filename = sanitize_filename(filename)
    
    # Create CSV content
    output = io.StringIO()
    if data:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    return output.getvalue(), filename, "text/csv"


def export_to_json(data: List[Dict[str, Any]], filename: str = None, pretty: bool = True) -> tuple:
    """
    Export data to JSON format.
    
    Args:
        data: List of dictionaries to export
        filename: Optional filename for the export
        pretty: Whether to format JSON with indentation
        
    Returns:
        Tuple of (file_content, filename, content_type)
    """
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.json"
    
    # Sanitize filename
    filename = sanitize_filename(filename)
    
    # Convert datetime objects to strings
    def datetime_converter(obj):
        if isinstance(obj, datetime):
            return format_timestamp(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    # Create JSON content
    if pretty:
        content = json.dumps(data, indent=2, default=datetime_converter, ensure_ascii=False)
    else:
        content = json.dumps(data, default=datetime_converter, ensure_ascii=False)
    
    return content, filename, "application/json"


def export_to_excel(data: List[Dict[str, Any]], filename: str = None, sheet_name: str = "Data") -> tuple:
    """
    Export data to Excel format.
    
    Args:
        data: List of dictionaries to export
        filename: Optional filename for the export
        sheet_name: Name of the Excel sheet
        
    Returns:
        Tuple of (file_content, filename, content_type)
        
    Raises:
        ImportError: If pandas is not available
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for Excel export functionality. Install with: pip install pandas openpyxl")
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.xlsx"
    
    # Sanitize filename
    filename = sanitize_filename(filename)
    
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel content
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output.getvalue(), filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def export_readings_to_csv(readings: List[Dict[str, Any]], device_id: str = None) -> tuple:
    """
    Export sensor readings to CSV format with specific formatting.
    
    Args:
        readings: List of sensor reading dictionaries
        device_id: Optional device ID for filename
        
    Returns:
        Tuple of (file_content, filename, content_type)
    """
    if not readings:
        return "", "readings_empty.csv", "text/csv"
    
    # Format readings for export
    formatted_readings = []
    for reading in readings:
        formatted_reading = {
            'timestamp': format_timestamp(reading.get('timestamp')),
            'device_id': reading.get('device_id', ''),
            'sensor_type': reading.get('sensor_type', ''),
            'value': reading.get('value', ''),
            'unit': reading.get('unit', ''),
            'location': reading.get('location', '')
        }
        formatted_readings.append(formatted_reading)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if device_id:
        filename = f"readings_{device_id}_{timestamp}.csv"
    else:
        filename = f"readings_{timestamp}.csv"
    
    return export_to_csv(formatted_readings, filename)


def export_devices_to_csv(devices: List[Dict[str, Any]]) -> tuple:
    """
    Export device data to CSV format.
    
    Args:
        devices: List of device dictionaries
        
    Returns:
        Tuple of (file_content, filename, content_type)
    """
    if not devices:
        return "", "devices_empty.csv", "text/csv"
    
    # Format devices for export
    formatted_devices = []
    for device in devices:
        formatted_device = {
            'device_id': device.get('device_id', ''),
            'name': device.get('name', ''),
            'location': device.get('location', ''),
            'status': device.get('status', ''),
            'last_seen': format_timestamp(device.get('last_seen')),
            'created_at': format_timestamp(device.get('created_at')),
            'firmware_version': device.get('firmware_version', ''),
            'ip_address': device.get('ip_address', '')
        }
        formatted_devices.append(formatted_device)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"devices_{timestamp}.csv"
    
    return export_to_csv(formatted_devices, filename)


def export_alerts_to_csv(alerts: List[Dict[str, Any]]) -> tuple:
    """
    Export alert data to CSV format.
    
    Args:
        alerts: List of alert dictionaries
        
    Returns:
        Tuple of (file_content, filename, content_type)
    """
    if not alerts:
        return "", "alerts_empty.csv", "text/csv"
    
    # Format alerts for export
    formatted_alerts = []
    for alert in alerts:
        formatted_alert = {
            'alert_id': alert.get('alert_id', ''),
            'device_id': alert.get('device_id', ''),
            'alert_type': alert.get('alert_type', ''),
            'severity': alert.get('severity', ''),
            'message': alert.get('message', ''),
            'created_at': format_timestamp(alert.get('created_at')),
            'acknowledged_at': format_timestamp(alert.get('acknowledged_at')),
            'status': alert.get('status', '')
        }
        formatted_alerts.append(formatted_alert)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"alerts_{timestamp}.csv"
    
    return export_to_csv(formatted_alerts, filename)


def create_summary_report(data: Dict[str, Any], format_type: str = "json") -> tuple:
    """
    Create a summary report in the specified format.
    
    Args:
        data: Summary data dictionary
        format_type: Export format ("json", "csv", "excel")
        
    Returns:
        Tuple of (file_content, filename, content_type)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format_type.lower() == "csv":
        # Convert summary to list format for CSV
        summary_list = []
        for key, value in data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    summary_list.append({
                        'category': key,
                        'metric': sub_key,
                        'value': sub_value
                    })
            else:
                summary_list.append({
                    'category': 'general',
                    'metric': key,
                    'value': value
                })
        return export_to_csv(summary_list, f"summary_{timestamp}.csv")
    
    elif format_type.lower() == "excel":
        # Convert summary to list format for Excel
        summary_list = []
        for key, value in data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    summary_list.append({
                        'category': key,
                        'metric': sub_key,
                        'value': sub_value
                    })
            else:
                summary_list.append({
                    'category': 'general',
                    'metric': key,
                    'value': value
                })
        return export_to_excel(summary_list, f"summary_{timestamp}.xlsx")
    
    else:  # JSON
        return export_to_json(data, f"summary_{timestamp}.json") 