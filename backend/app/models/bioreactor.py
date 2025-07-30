"""
Bioreactor model for LMS Core API.

This module contains the Bioreactor model and related functionality
for bioreactor management and control.
"""

from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

from .base import BaseModel
from .device import Device
from ..database import JSONType


class Bioreactor(Device):
    """
    Bioreactor model for laboratory bioreactor management.
    
    Extends the Device model with bioreactor-specific properties and functionality.
    Maps to the existing entities table with entity_type = 'device.bioreactor'
    and stores bioreactor configuration in the properties JSON column.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'device.bioreactor',
    }
    
    def __init__(self, *args, **kwargs):
        # Set default entity_type for bioreactors
        if 'entity_type' not in kwargs:
            kwargs['entity_type'] = 'device.bioreactor'
        super().__init__(*args, **kwargs)
    
    @classmethod
    def get_by_bioreactor_name(cls, db, name: str):
        """
        Get bioreactor by name.
        
        Args:
            db: Database session
            name: Bioreactor name
            
        Returns:
            Bioreactor instance or None
        """
        return db.query(cls).filter(
            cls.entity_type == "device.bioreactor",
            cls.name == name
        ).first()
    
    @classmethod
    def get_by_bioreactor_id(cls, db, bioreactor_id: str):
        """
        Get bioreactor by ID.
        
        Args:
            db: Database session
            bioreactor_id: Bioreactor ID
            
        Returns:
            Bioreactor instance or None
        """
        return db.query(cls).filter(
            cls.entity_type == "device.bioreactor",
            cls.id == bioreactor_id
        ).first()
    
    @classmethod
    def get_organization_bioreactors(cls, db, organization_id: str):
        """
        Get all bioreactors for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            List of Bioreactor instances
        """
        return db.query(cls).filter(
            cls.entity_type == "device.bioreactor",
            cls.organization_id == organization_id,
            cls.is_active == True
        ).all()
    
    # Bioreactor-specific property getters
    
    def get_bioreactor_type(self) -> str:
        """
        Get bioreactor type from properties.
        
        Returns:
            Bioreactor type string
        """
        return self.get_property('bioreactor_type', 'standard')
    
    def get_vessel_volume(self) -> float:
        """
        Get vessel volume in liters.
        
        Returns:
            Vessel volume in liters
        """
        return self.get_property('vessel_volume', 0.0)
    
    def get_working_volume(self) -> float:
        """
        Get working volume in liters.
        
        Returns:
            Working volume in liters
        """
        return self.get_property('working_volume', 0.0)
    
    def get_operating_parameters(self) -> dict:
        """
        Get operating parameters (temperature, pH, DO, etc.).
        
        Returns:
            Dictionary of operating parameters
        """
        return self.get_property('operating_parameters', {})
    
    def get_safety_limits(self) -> dict:
        """
        Get safety limits for the bioreactor.
        
        Returns:
            Dictionary of safety limits
        """
        return self.get_property('safety_limits', {})
    
    def get_actuators(self) -> List[dict]:
        """
        Get actuator configurations.
        
        Returns:
            List of actuator configurations
        """
        hardware = self.get_property('hardware', {})
        return hardware.get('actuators', []) if isinstance(hardware, dict) else []
    
    def get_sensors(self) -> List[dict]:
        """
        Get sensor configurations (extends Device.get_sensors).
        
        Returns:
            List of sensor configurations
        """
        return super().get_sensors()
    
    def get_control_mode(self) -> str:
        """
        Get current control mode.
        
        Returns:
            Control mode string (manual, automatic, experiment)
        """
        return self.get_property('control_mode', 'manual')
    
    def get_experiment_id(self) -> Optional[str]:
        """
        Get associated experiment ID if running.
        
        Returns:
            Experiment ID or None
        """
        return self.get_property('experiment_id')
    
    def get_last_calibration(self) -> Optional[datetime]:
        """
        Get last calibration date.
        
        Returns:
            Last calibration datetime or None
        """
        calibration_date = self.get_property('last_calibration')
        if calibration_date:
            return datetime.fromisoformat(calibration_date)
        return None
    
    def get_maintenance_schedule(self) -> dict:
        """
        Get maintenance schedule.
        
        Returns:
            Maintenance schedule dictionary
        """
        return self.get_property('maintenance_schedule', {})
    
    # Bioreactor-specific property setters
    
    def set_bioreactor_type(self, bioreactor_type: str):
        """
        Set bioreactor type.
        
        Args:
            bioreactor_type: Bioreactor type string
        """
        self.set_property('bioreactor_type', bioreactor_type)
    
    def set_vessel_volume(self, volume: float):
        """
        Set vessel volume.
        
        Args:
            volume: Vessel volume in liters
        """
        self.set_property('vessel_volume', volume)
    
    def set_working_volume(self, volume: float):
        """
        Set working volume.
        
        Args:
            volume: Working volume in liters
        """
        self.set_property('working_volume', volume)
    
    def set_operating_parameters(self, parameters: dict):
        """
        Set operating parameters.
        
        Args:
            parameters: Dictionary of operating parameters
        """
        self.set_property('operating_parameters', parameters)
    
    def set_safety_limits(self, limits: dict):
        """
        Set safety limits.
        
        Args:
            limits: Dictionary of safety limits
        """
        self.set_property('safety_limits', limits)
    
    def set_control_mode(self, mode: str):
        """
        Set control mode.
        
        Args:
            mode: Control mode string
        """
        self.set_property('control_mode', mode)
    
    def set_experiment_id(self, experiment_id: Optional[str]):
        """
        Set associated experiment ID.
        
        Args:
            experiment_id: Experiment ID or None
        """
        self.set_property('experiment_id', experiment_id)
    
    def set_last_calibration(self, calibration_date: datetime):
        """
        Set last calibration date.
        
        Args:
            calibration_date: Calibration datetime
        """
        self.set_property('last_calibration', calibration_date.isoformat())
    
    def set_maintenance_schedule(self, schedule: dict):
        """
        Set maintenance schedule.
        
        Args:
            schedule: Maintenance schedule dictionary
        """
        self.set_property('maintenance_schedule', schedule)
    
    # Bioreactor-specific methods
    
    def is_operational(self) -> bool:
        """
        Check if bioreactor is operational.
        
        Returns:
            True if operational, False otherwise
        """
        status = self.get_status()
        return status in ['online', 'running', 'idle']
    
    def is_running_experiment(self) -> bool:
        """
        Check if bioreactor is running an experiment.
        
        Returns:
            True if running experiment, False otherwise
        """
        return self.get_experiment_id() is not None and self.get_control_mode() == 'experiment'
    
    def can_start_experiment(self) -> bool:
        """
        Check if bioreactor can start an experiment.
        
        Returns:
            True if can start experiment, False otherwise
        """
        return (self.is_operational() and 
                not self.is_running_experiment() and
                self.get_control_mode() in ['manual', 'automatic'])
    
    def get_safety_status(self) -> dict:
        """
        Get safety status of the bioreactor.
        
        Returns:
            Dictionary with safety status information
        """
        safety_limits = self.get_safety_limits()
        current_params = self.get_operating_parameters()
        
        safety_status = {
            'overall_status': 'safe',
            'warnings': [],
            'alarms': []
        }
        
        # Check temperature limits
        if 'temperature' in safety_limits and 'temperature' in current_params:
            temp_limit = safety_limits['temperature']
            current_temp = current_params['temperature']
            
            if current_temp > temp_limit.get('max', float('inf')):
                safety_status['alarms'].append('Temperature too high')
                safety_status['overall_status'] = 'alarm'
            elif current_temp > temp_limit.get('warning_max', float('inf')):
                safety_status['warnings'].append('Temperature approaching limit')
        
        # Check pH limits
        if 'pH' in safety_limits and 'pH' in current_params:
            ph_limit = safety_limits['pH']
            current_ph = current_params['pH']
            
            if current_ph < ph_limit.get('min', 0) or current_ph > ph_limit.get('max', 14):
                safety_status['alarms'].append('pH out of range')
                safety_status['overall_status'] = 'alarm'
        
        # Check DO limits
        if 'dissolved_oxygen' in safety_limits and 'dissolved_oxygen' in current_params:
            do_limit = safety_limits['dissolved_oxygen']
            current_do = current_params['dissolved_oxygen']
            
            if current_do < do_limit.get('min', 0):
                safety_status['alarms'].append('Dissolved oxygen too low')
                safety_status['overall_status'] = 'alarm'
        
        return safety_status
    
    def emergency_stop(self):
        """
        Perform emergency stop of the bioreactor.
        """
        # Set control mode to manual
        self.set_control_mode('manual')
        
        # Clear experiment association
        self.set_experiment_id(None)
        
        # Set status to emergency_stop
        self.status = 'emergency_stop'
        
        # Log the emergency stop
        # TODO: Add event logging for emergency stop 