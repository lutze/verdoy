"""
Alert model for VerdoyLab API.

This module contains the Alert and AlertRule models and related functionality
for managing alerts and alert rules.
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime
from typing import Dict, Any, Optional

from .base import BaseModel
from .event import Event
from .entity import Entity
from ..database import JSONType


class Alert(Event):
    """
    Alert model for alert events.
    
    Maps to the existing events table with event_type = 'alert.triggered'
    and stores alert data in the data JSON column.
    """
    
    def __init__(self, *args, **kwargs):
        # Set default event_type for alerts
        if 'event_type' not in kwargs:
            kwargs['event_type'] = 'alert.triggered'
        super().__init__(*args, **kwargs)
    
    @classmethod
    def get_device_alerts(
        cls, 
        db, 
        device_id,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ):
        """
        Get alerts for a specific device.
        
        Args:
            db: Database session
            device_id: Device entity ID
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of alerts to return
            
        Returns:
            List of alert instances
        """
        query = db.query(cls).filter(
            cls.event_type == "alert.triggered",
            cls.entity_id == device_id
        )
        
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
        
        return query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_active_alerts(cls, db, device_id=None):
        """
        Get active (unacknowledged) alerts.
        
        Args:
            db: Database session
            device_id: Optional device entity ID filter
            
        Returns:
            List of active alert instances
        """
        query = db.query(cls).filter(
            cls.event_type == "alert.triggered",
            cls.data['acknowledged'].astext == 'false'
        )
        
        if device_id:
            query = query.filter(cls.entity_id == device_id)
        
        return query.order_by(cls.timestamp.desc()).all()
    
    def get_alert_type(self) -> str:
        """
        Get alert type from data.
        
        Returns:
            Alert type string
        """
        return self.get_data_value('alertType', '')
    
    def get_severity(self) -> str:
        """
        Get alert severity from data.
        
        Returns:
            Alert severity string
        """
        return self.get_data_value('severity', 'medium')
    
    def get_message(self) -> str:
        """
        Get alert message from data.
        
        Returns:
            Alert message string
        """
        return self.get_data_value('message', '')
    
    def get_sensor_type(self) -> str:
        """
        Get sensor type from data.
        
        Returns:
            Sensor type string
        """
        return self.get_data_value('sensorType', '')
    
    def get_value(self) -> float:
        """
        Get sensor value that triggered the alert.
        
        Returns:
            Sensor value as float
        """
        value = self.get_data_value('value')
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_threshold(self) -> float:
        """
        Get threshold value that was exceeded.
        
        Returns:
            Threshold value as float
        """
        value = self.get_data_value('threshold')
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def is_acknowledged(self) -> bool:
        """
        Check if alert is acknowledged.
        
        Returns:
            True if acknowledged, False otherwise
        """
        return self.get_data_value('acknowledged', False)
    
    def acknowledge(self, acknowledged_by: str = None):
        """
        Mark alert as acknowledged.
        
        Args:
            acknowledged_by: User who acknowledged the alert
        """
        self.set_data_value('acknowledged', True)
        self.set_data_value('acknowledgedAt', datetime.utcnow().isoformat())
        if acknowledged_by:
            self.set_data_value('acknowledgedBy', acknowledged_by)
    
    def __repr__(self):
        """String representation of the alert."""
        return f"<Alert(id={self.id}, type={self.get_alert_type()}, severity={self.get_severity()})>"


class AlertRule(Entity):
    """
    Alert rule model for defining alert conditions.
    
    Maps to the existing entities table with entity_type = 'alert.rule'
    and stores rule configuration in the properties JSON column.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'alert.rule',
    }
    
    def __init__(self, *args, **kwargs):
        # Set default entity_type for alert rules
        if 'entity_type' not in kwargs:
            kwargs['entity_type'] = 'alert.rule'
        super().__init__(*args, **kwargs)
    
    @classmethod
    def get_device_rules(cls, db, device_id):
        """
        Get alert rules for a specific device.
        
        Args:
            db: Database session
            device_id: Device entity ID
            
        Returns:
            List of alert rule instances
        """
        # Get all alert rules and filter in Python to avoid JSONB operator issues
        rules = db.query(cls).filter(cls.entity_type == "alert.rule").all()
        return [rule for rule in rules if rule.get_property('deviceId') == str(device_id)]
    
    @classmethod
    def get_active_rules(cls, db):
        """
        Get all active alert rules.
        
        Args:
            db: Database session
            
        Returns:
            List of active alert rule instances
        """
        # Get all alert rules and filter in Python to avoid JSONB operator issues
        rules = db.query(cls).filter(cls.entity_type == "alert.rule").all()
        return [rule for rule in rules if rule.get_property('enabled') == True]
    
    def get_device_id(self) -> str:
        """
        Get device ID from properties.
        
        Returns:
            Device ID string
        """
        return self.get_property('deviceId', '')
    
    def get_sensor_type(self) -> str:
        """
        Get sensor type from properties.
        
        Returns:
            Sensor type string
        """
        return self.get_property('sensorType', '')
    
    def get_condition(self) -> str:
        """
        Get alert condition from properties.
        
        Returns:
            Alert condition string
        """
        return self.get_property('condition', '')
    
    def get_threshold(self) -> float:
        """
        Get threshold value from properties.
        
        Returns:
            Threshold value as float
        """
        value = self.get_property('threshold')
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_severity(self) -> str:
        """
        Get alert severity from properties.
        
        Returns:
            Alert severity string
        """
        return self.get_property('severity', 'medium')
    
    def get_message_template(self) -> str:
        """
        Get message template from properties.
        
        Returns:
            Message template string
        """
        return self.get_property('messageTemplate', '')
    
    def is_enabled(self) -> bool:
        """
        Check if rule is enabled.
        
        Returns:
            True if enabled, False otherwise
        """
        return self.get_property('enabled', False)
    
    def enable(self):
        """Enable the alert rule."""
        self.set_property('enabled', True)
    
    def disable(self):
        """Disable the alert rule."""
        self.set_property('enabled', False)
    
    def check_condition(self, value: float) -> bool:
        """
        Check if a value meets the alert condition.
        
        Args:
            value: Value to check
            
        Returns:
            True if condition is met, False otherwise
        """
        threshold = self.get_threshold()
        condition = self.get_condition()
        
        if condition == "greater_than":
            return value > threshold
        elif condition == "less_than":
            return value < threshold
        elif condition == "equals":
            return value == threshold
        elif condition == "not_equals":
            return value != threshold
        else:
            return False
    
    def __repr__(self):
        """String representation of the alert rule."""
        return f"<AlertRule(id={self.id}, sensor_type={self.get_sensor_type()}, condition={self.get_condition()})>" 