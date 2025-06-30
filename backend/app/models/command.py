"""
Command model for LMS Core API.

This module contains the Command model and related functionality
for device command management and control.
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from datetime import datetime
from typing import Dict, Any, Optional

from .base import BaseModel
from .event import Event


class Command(Event):
    """
    Command model for device commands.
    
    Maps to the existing events table with event_type = 'device.command'
    and stores command data in the data JSONB column.
    """
    
    def __init__(self, *args, **kwargs):
        # Set default event_type for device commands
        if 'event_type' not in kwargs:
            kwargs['event_type'] = 'device.command'
        super().__init__(*args, **kwargs)
    
    @classmethod
    def get_device_commands(
        cls, 
        db, 
        device_id,
        status: str = None,
        limit: int = 100
    ):
        """
        Get commands for a specific device.
        
        Args:
            db: Database session
            device_id: Device entity ID
            status: Optional status filter
            limit: Maximum number of commands to return
            
        Returns:
            List of command instances
        """
        query = db.query(cls).filter(
            cls.event_type == "device.command",
            cls.entity_id == device_id
        )
        
        if status:
            query = query.filter(cls.data['status'].astext == status)
        
        return query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_pending_commands(cls, db, device_id):
        """
        Get pending commands for a device.
        
        Args:
            db: Database session
            device_id: Device entity ID
            
        Returns:
            List of pending command instances
        """
        return cls.get_device_commands(db, device_id, status="pending")
    
    @classmethod
    def create_command(
        cls, 
        db, 
        device_id, 
        command_type: str, 
        parameters: dict = None,
        priority: str = "normal"
    ):
        """
        Create a new device command.
        
        Args:
            db: Database session
            device_id: Device entity ID
            command_type: Type of command
            parameters: Command parameters
            priority: Command priority
            
        Returns:
            Created command instance
        """
        command = cls(
            entity_id=device_id,
            entity_type="device.esp32",
            event_type="device.command",
            timestamp=datetime.utcnow(),
            data={
                'commandType': command_type,
                'parameters': parameters or {},
                'status': 'pending',
                'priority': priority,
                'createdAt': datetime.utcnow().isoformat(),
                'executedAt': None,
                'result': None,
                'error': None
            }
        )
        
        db.add(command)
        db.commit()
        db.refresh(command)
        
        return command
    
    def get_command_type(self) -> str:
        """
        Get command type from data.
        
        Returns:
            Command type string
        """
        return self.get_data_value('commandType', '')
    
    def get_parameters(self) -> dict:
        """
        Get command parameters from data.
        
        Returns:
            Command parameters dictionary
        """
        return self.get_data_value('parameters', {})
    
    def get_status(self) -> str:
        """
        Get command status from data.
        
        Returns:
            Command status string
        """
        return self.get_data_value('status', 'pending')
    
    def get_priority(self) -> str:
        """
        Get command priority from data.
        
        Returns:
            Command priority string
        """
        return self.get_data_value('priority', 'normal')
    
    def get_result(self) -> dict:
        """
        Get command result from data.
        
        Returns:
            Command result dictionary
        """
        return self.get_data_value('result', {})
    
    def get_error(self) -> str:
        """
        Get command error from data.
        
        Returns:
            Command error string
        """
        return self.get_data_value('error', '')
    
    def is_pending(self) -> bool:
        """
        Check if command is pending.
        
        Returns:
            True if pending, False otherwise
        """
        return self.get_status() == "pending"
    
    def is_executed(self) -> bool:
        """
        Check if command is executed.
        
        Returns:
            True if executed, False otherwise
        """
        return self.get_status() == "executed"
    
    def is_failed(self) -> bool:
        """
        Check if command failed.
        
        Returns:
            True if failed, False otherwise
        """
        return self.get_status() == "failed"
    
    def mark_executed(self, result: dict = None):
        """
        Mark command as executed.
        
        Args:
            result: Command execution result
        """
        self.set_data_value('status', 'executed')
        self.set_data_value('executedAt', datetime.utcnow().isoformat())
        if result:
            self.set_data_value('result', result)
    
    def mark_failed(self, error: str):
        """
        Mark command as failed.
        
        Args:
            error: Error message
        """
        self.set_data_value('status', 'failed')
        self.set_data_value('error', error)
        self.set_data_value('executedAt', datetime.utcnow().isoformat())
    
    def __repr__(self):
        """String representation of the command."""
        return f"<Command(id={self.id}, type={self.get_command_type()}, status={self.get_status()})>" 