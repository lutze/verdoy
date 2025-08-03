"""
Bioreactor service for LMS Core API.

This module contains the BioreactorService class and related functionality
for bioreactor business logic, CRUD operations, and safety management.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.bioreactor import Bioreactor
from ..models.event import Event
from ..schemas.bioreactor import (
    BioreactorCreate, 
    BioreactorUpdate, 
    BioreactorResponse,
    BioreactorEnrollmentStep1,
    BioreactorEnrollmentStep2,
    BioreactorEnrollmentStep3,
    BioreactorControlRequest,
    BioreactorStatusResponse
)
from ..exceptions import (
    ValidationException,
    NotFoundException,
    ConflictException,
    SafetyException
)

logger = logging.getLogger(__name__)


class BioreactorService:
    """
    Service class for bioreactor business logic and operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_bioreactor(self, bioreactor_data: BioreactorCreate, user_id: UUID) -> Bioreactor:
        """
        Create a new bioreactor.
        
        Args:
            bioreactor_data: Bioreactor creation data
            user_id: ID of the user creating the bioreactor
            
        Returns:
            Created Bioreactor instance
            
        Raises:
            ValidationException: If validation fails
            ConflictException: If bioreactor with same name exists
        """
        try:
            # Check if bioreactor with same name exists in organization
            existing = Bioreactor.get_by_bioreactor_name(self.db, bioreactor_data.name)
            if existing and existing.organization_id == bioreactor_data.organization_id:
                raise ConflictException(f"Bioreactor with name '{bioreactor_data.name}' already exists")
            
            # Create bioreactor instance
            bioreactor = Bioreactor(
                name=bioreactor_data.name,
                description=bioreactor_data.description,
                location=bioreactor_data.location,
                organization_id=bioreactor_data.organization_id,
                entity_type='device.bioreactor',
                status='offline'
            )
            
            # Set bioreactor-specific properties
            bioreactor.set_bioreactor_type(bioreactor_data.bioreactor_type)
            bioreactor.set_vessel_volume(bioreactor_data.vessel_volume)
            
            # Set working volume - use 70% of vessel volume as default if not provided
            if bioreactor_data.working_volume:
                bioreactor.set_working_volume(bioreactor_data.working_volume)
            else:
                # Default to 70% of vessel volume
                default_working_volume = bioreactor_data.vessel_volume * 0.7
                bioreactor.set_working_volume(default_working_volume)
            
            # Set hardware configuration
            hardware_config = {
                'model': bioreactor_data.hardware_model,
                'macAddress': bioreactor_data.mac_address,
                'sensors': [sensor.dict() for sensor in bioreactor_data.sensors],
                'actuators': [actuator.dict() for actuator in bioreactor_data.actuators]
            }
            bioreactor.set_property('hardware', hardware_config)
            
            # Set firmware configuration
            firmware_config = {
                'version': bioreactor_data.firmware_version,
                'lastUpdate': datetime.utcnow().isoformat()
            }
            bioreactor.set_property('firmware', firmware_config)
            
            # Set safety and operating parameters
            if bioreactor_data.safety_limits:
                bioreactor.set_safety_limits(bioreactor_data.safety_limits.dict())
            
            if bioreactor_data.operating_parameters:
                bioreactor.set_operating_parameters(bioreactor_data.operating_parameters.dict())
            
            if bioreactor_data.maintenance_schedule:
                bioreactor.set_maintenance_schedule(bioreactor_data.maintenance_schedule.dict())
            
            # Set device configuration
            bioreactor.set_config_value('readingInterval', bioreactor_data.reading_interval)
            
            # Generate API key for device authentication
            api_key = f"bioreactor_{bioreactor.id.hex[:8]}"
            bioreactor.set_property('api_key', api_key)
            
            # Save to database
            self.db.add(bioreactor)
            self.db.commit()
            self.db.refresh(bioreactor)
            
            # Log creation event
            self._log_event(bioreactor.id, 'bioreactor.created', {
                'user_id': str(user_id),
                'bioreactor_name': bioreactor.name,
                'organization_id': str(bioreactor.organization_id)
            })
            
            logger.info(f"Created bioreactor '{bioreactor.name}' with ID {bioreactor.id}")
            return bioreactor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create bioreactor: {str(e)}")
            raise
    
    def get_bioreactor(self, bioreactor_id: UUID) -> Bioreactor:
        """
        Get bioreactor by ID.
        
        Args:
            bioreactor_id: Bioreactor ID
            
        Returns:
            Bioreactor instance
            
        Raises:
            NotFoundException: If bioreactor not found
        """
        bioreactor = Bioreactor.get_by_bioreactor_id(self.db, str(bioreactor_id))
        if not bioreactor:
            raise NotFoundException(f"Bioreactor with ID {bioreactor_id} not found")
        return bioreactor
    
    def get_bioreactors_by_organization(self, organization_id: UUID, status: Optional[str] = None) -> List[Bioreactor]:
        """
        Get bioreactors for a specific organization.
        
        Args:
            organization_id: Organization ID
            status: Optional status filter
            
        Returns:
            List of bioreactors
        """
        try:
            query = self.db.query(Bioreactor).filter(
                Bioreactor.organization_id == organization_id,
                Bioreactor.entity_type == 'device.bioreactor'
            )
            
            if status:
                query = query.filter(Bioreactor.status == status)
            
            bioreactors = query.order_by(Bioreactor.created_at.desc()).all()
            return bioreactors
            
        except Exception as e:
            logger.error(f"Error getting bioreactors by organization: {e}")
            return []
    
    def get_organization_bioreactors(
        self, 
        organization_id: UUID, 
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get bioreactors for an organization with pagination.
        
        Args:
            organization_id: Organization ID
            status: Filter by status
            page: Page number
            page_size: Page size
            
        Returns:
            Dictionary with bioreactors and pagination info
        """
        query = self.db.query(Bioreactor).filter(
            Bioreactor.entity_type == "device.bioreactor",
            Bioreactor.organization_id == organization_id,
            Bioreactor.is_active == True
        )
        
        if status:
            query = query.filter(Bioreactor.status == status)
        
        total_count = query.count()
        total_pages = (total_count + page_size - 1) // page_size
        
        bioreactors = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            'bioreactors': bioreactors,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        }
    
    def update_bioreactor(self, bioreactor_id: UUID, update_data: BioreactorUpdate, user_id: UUID) -> Bioreactor:
        """
        Update bioreactor.
        
        Args:
            bioreactor_id: Bioreactor ID
            update_data: Update data
            user_id: ID of the user updating the bioreactor
            
        Returns:
            Updated Bioreactor instance
            
        Raises:
            NotFoundException: If bioreactor not found
            ValidationException: If validation fails
        """
        bioreactor = self.get_bioreactor(bioreactor_id)
        
        try:
            # Update basic properties
            if update_data.name is not None:
                bioreactor.name = update_data.name
            if update_data.description is not None:
                bioreactor.description = update_data.description
            if update_data.location is not None:
                bioreactor.location = update_data.location
            
            # Update bioreactor-specific properties
            if update_data.bioreactor_type is not None:
                bioreactor.set_bioreactor_type(update_data.bioreactor_type)
            if update_data.vessel_volume is not None:
                bioreactor.set_vessel_volume(update_data.vessel_volume)
            if update_data.working_volume is not None:
                bioreactor.set_working_volume(update_data.working_volume)
            
            # Update hardware configuration
            if update_data.sensors is not None or update_data.actuators is not None:
                hardware_config = bioreactor.get_property('hardware', {})
                if update_data.sensors is not None:
                    hardware_config['sensors'] = [sensor.dict() for sensor in update_data.sensors]
                if update_data.actuators is not None:
                    hardware_config['actuators'] = [actuator.dict() for actuator in update_data.actuators]
                bioreactor.set_property('hardware', hardware_config)
            
            # Update safety and operating parameters
            if update_data.safety_limits is not None:
                bioreactor.set_safety_limits(update_data.safety_limits.dict())
            if update_data.operating_parameters is not None:
                bioreactor.set_operating_parameters(update_data.operating_parameters.dict())
            if update_data.maintenance_schedule is not None:
                bioreactor.set_maintenance_schedule(update_data.maintenance_schedule.dict())
            
            # Update device configuration
            if update_data.firmware_version is not None:
                firmware_config = bioreactor.get_property('firmware', {})
                firmware_config['version'] = update_data.firmware_version
                bioreactor.set_property('firmware', firmware_config)
            if update_data.reading_interval is not None:
                bioreactor.set_config_value('readingInterval', update_data.reading_interval)
            
            # Update timestamp
            bioreactor.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(bioreactor)
            
            # Log update event
            self._log_event(bioreactor.id, 'bioreactor.updated', {
                'user_id': str(user_id),
                'bioreactor_name': bioreactor.name
            })
            
            logger.info(f"Updated bioreactor '{bioreactor.name}' with ID {bioreactor.id}")
            return bioreactor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update bioreactor {bioreactor_id}: {str(e)}")
            raise
    
    def archive_bioreactor(self, bioreactor_id: UUID, user_id: UUID) -> Bioreactor:
        """
        Archive bioreactor (soft delete).
        
        Args:
            bioreactor_id: Bioreactor ID
            user_id: ID of the user archiving the bioreactor
            
        Returns:
            Archived Bioreactor instance
            
        Raises:
            NotFoundException: If bioreactor not found
            SafetyException: If bioreactor is running an experiment
        """
        bioreactor = self.get_bioreactor(bioreactor_id)
        
        # Check if bioreactor is running an experiment
        if bioreactor.is_running_experiment():
            raise SafetyException("Cannot archive bioreactor while running an experiment")
        
        try:
            bioreactor.is_active = False
            bioreactor.status = 'archived'
            bioreactor.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(bioreactor)
            
            # Log archive event
            self._log_event(bioreactor.id, 'bioreactor.archived', {
                'user_id': str(user_id),
                'bioreactor_name': bioreactor.name
            })
            
            logger.info(f"Archived bioreactor '{bioreactor.name}' with ID {bioreactor.id}")
            return bioreactor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to archive bioreactor {bioreactor_id}: {str(e)}")
            raise
    
    def get_bioreactor_status(self, bioreactor_id: UUID) -> BioreactorStatusResponse:
        """
        Get current bioreactor status.
        
        Args:
            bioreactor_id: Bioreactor ID
            
        Returns:
            BioreactorStatusResponse with current status
            
        Raises:
            NotFoundException: If bioreactor not found
        """
        bioreactor = self.get_bioreactor(bioreactor_id)
        
        return BioreactorStatusResponse(
            id=bioreactor.id,
            name=bioreactor.name,
            status=bioreactor.get_status(),
            control_mode=bioreactor.get_control_mode(),
            operating_parameters=bioreactor.get_operating_parameters(),
            safety_status=bioreactor.get_safety_status(),
            is_operational=bioreactor.is_operational(),
            is_running_experiment=bioreactor.is_running_experiment(),
            last_seen=bioreactor.get_last_seen(),
            experiment_id=bioreactor.get_experiment_id()
        )
    
    def control_bioreactor(self, bioreactor_id: UUID, control_request: BioreactorControlRequest, user_id: UUID) -> Dict[str, Any]:
        """
        Control bioreactor (setpoints, emergency stop, etc.).
        
        Args:
            bioreactor_id: Bioreactor ID
            control_request: Control request
            user_id: ID of the user controlling the bioreactor
            
        Returns:
            Control response
            
        Raises:
            NotFoundException: If bioreactor not found
            SafetyException: If safety checks fail
            ValidationException: If control request is invalid
        """
        bioreactor = self.get_bioreactor(bioreactor_id)
        
        # Check if bioreactor is operational
        if not bioreactor.is_operational():
            raise SafetyException("Bioreactor is not operational")
        
        try:
            control_id = f"control_{datetime.utcnow().timestamp()}"
            
            if control_request.control_type == 'emergency_stop':
                # Emergency stop
                bioreactor.emergency_stop()
                message = "Emergency stop activated"
                
            elif control_request.control_type == 'setpoint':
                # Set parameter setpoint
                if not control_request.parameter or control_request.value is None:
                    raise ValidationException("Parameter and value required for setpoint control")
                
                # Validate parameter exists in sensors/actuators
                valid_parameters = [s['type'] for s in bioreactor.get_sensors()] + [a['type'] for a in bioreactor.get_actuators()]
                if control_request.parameter not in valid_parameters:
                    raise ValidationException(f"Invalid parameter: {control_request.parameter}")
                
                # Update operating parameters
                operating_params = bioreactor.get_operating_parameters()
                operating_params[control_request.parameter] = control_request.value
                bioreactor.set_operating_parameters(operating_params)
                
                message = f"Set {control_request.parameter} to {control_request.value}"
                
            elif control_request.control_type == 'control_mode':
                # Change control mode
                valid_modes = ['manual', 'automatic', 'experiment']
                if control_request.parameter not in valid_modes:
                    raise ValidationException(f"Invalid control mode: {control_request.parameter}")
                
                bioreactor.set_control_mode(control_request.parameter)
                message = f"Control mode changed to {control_request.parameter}"
                
            else:
                raise ValidationException(f"Unknown control type: {control_request.control_type}")
            
            # Update timestamp
            bioreactor.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log control event
            self._log_event(bioreactor.id, 'bioreactor.controlled', {
                'user_id': str(user_id),
                'control_type': control_request.control_type,
                'parameter': control_request.parameter,
                'value': control_request.value,
                'control_id': control_id
            })
            
            logger.info(f"Bioreactor {bioreactor_id} controlled: {message}")
            
            return {
                'success': True,
                'message': message,
                'control_id': control_id,
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to control bioreactor {bioreactor_id}: {str(e)}")
            raise
    
    def get_bioreactor_statistics(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Get bioreactor statistics for an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Dictionary with bioreactor statistics
        """
        bioreactors = Bioreactor.get_organization_bioreactors(self.db, str(organization_id))
        
        total_count = len(bioreactors)
        online_count = len([b for b in bioreactors if b.is_operational()])
        running_experiments = len([b for b in bioreactors if b.is_running_experiment()])
        
        # Calculate average vessel volume
        total_volume = sum(b.get_vessel_volume() for b in bioreactors)
        avg_volume = total_volume / total_count if total_count > 0 else 0
        
        # Get status distribution
        status_counts = {}
        for bioreactor in bioreactors:
            status = bioreactor.get_status()
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_bioreactors': total_count,
            'online_bioreactors': online_count,
            'offline_bioreactors': total_count - online_count,
            'running_experiments': running_experiments,
            'average_vessel_volume': avg_volume,
            'status_distribution': status_counts
        }
    
    def _log_event(self, bioreactor_id: UUID, event_type: str, data: Dict[str, Any]):
        """
        Log bioreactor event.
        
        Args:
            bioreactor_id: Bioreactor ID
            event_type: Event type
            data: Event data
        """
        try:
            event = Event(
                entity_id=bioreactor_id,
                event_type=event_type,
                data=data,
                timestamp=datetime.utcnow()
            )
            self.db.add(event)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log bioreactor event: {str(e)}")
    
    def validate_bioreactor_data(self, bioreactor_data: BioreactorCreate) -> None:
        """
        Validate bioreactor creation data.
        
        Args:
            bioreactor_data: Bioreactor creation data
            
        Raises:
            ValidationException: If validation fails
        """
        errors = []
        
        # Validate vessel volume
        if bioreactor_data.vessel_volume <= 0:
            errors.append("Vessel volume must be greater than 0")
        
        # Validate working volume
        if bioreactor_data.working_volume is not None:
            if bioreactor_data.working_volume <= 0:
                errors.append("Working volume must be greater than 0")
            if bioreactor_data.working_volume > bioreactor_data.vessel_volume:
                errors.append("Working volume cannot be greater than vessel volume")
        
        # Validate sensors
        if not bioreactor_data.sensors:
            errors.append("At least one sensor must be configured")
        
        # Validate actuators
        if not bioreactor_data.actuators:
            errors.append("At least one actuator must be configured")
        
        # Validate MAC address format
        if not bioreactor_data.mac_address or ':' not in bioreactor_data.mac_address:
            errors.append("Valid MAC address required")
        
        if errors:
            raise ValidationException(f"Bioreactor validation failed: {'; '.join(errors)}") 