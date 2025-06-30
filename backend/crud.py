"""
Legacy CRUD Operations with Service Layer Migration

This module provides backward compatibility for existing code while delegating
to the new service layer. All CRUD operations now use the service layer under
the hood, ensuring consistent business logic and proper error handling.

Migration Status: Phase 6 - Service Layer Integration
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import uuid
import json
import logging

# Import new service layer
try:
    from app.services import (
        AuthService,
        DeviceService,
        ReadingService,
        CommandService,
        AnalyticsService,
        AlertService,
        OrganizationService,
        BillingService
    )
    from app.schemas import (
        DeviceCreate,
        DeviceUpdate,
        UserCreate,
        OrganizationCreate
    )
    SERVICE_LAYER_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Service layer integration enabled - delegating to new services")
except ImportError as e:
    SERVICE_LAYER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Service layer not available: {e}. Using legacy CRUD operations.")

# Legacy imports for fallback
from models import Entity, User, Relationship, Event, Schema
from schemas import DeviceCreate, DeviceUpdate, UserCreate, OrganizationCreate

# Migration Layer - Service Layer Delegation

class CRUDMigrationLayer:
    """
    Migration layer that delegates CRUD operations to the new service layer.
    This ensures backward compatibility while using the new architecture.
    """
    
    @staticmethod
    def _get_device_service(db: Session) -> DeviceService:
        """Get device service instance."""
        if not SERVICE_LAYER_AVAILABLE:
            raise ImportError("Service layer not available")
        return DeviceService(db)
    
    @staticmethod
    def _get_auth_service(db: Session) -> AuthService:
        """Get auth service instance."""
        if not SERVICE_LAYER_AVAILABLE:
            raise ImportError("Service layer not available")
        return AuthService(db)
    
    @staticmethod
    def _get_reading_service(db: Session) -> ReadingService:
        """Get reading service instance."""
        if not SERVICE_LAYER_AVAILABLE:
            raise ImportError("Service layer not available")
        return ReadingService(db)
    
    @staticmethod
    def _get_organization_service(db: Session) -> OrganizationService:
        """Get organization service instance."""
        if not SERVICE_LAYER_AVAILABLE:
            raise ImportError("Service layer not available")
        return OrganizationService(db)

# Device CRUD Operations
class DeviceCRUD:
    @staticmethod
    def create_device(
        db: Session, 
        device_data: DeviceCreate, 
        organization_id: Optional[UUID] = None,
        created_by: str = "system"
    ) -> Entity:
        """Create a new device entity."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                device_service = CRUDMigrationLayer._get_device_service(db)
                device = device_service.create_device(
                    device_data=device_data,
                    organization_id=organization_id,
                    created_by=created_by
                )
                logger.info(f"Device created via service layer: {device.id}")
                return device
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy device creation")
        return DeviceCRUD._legacy_create_device(db, device_data, organization_id, created_by)
    
    @staticmethod
    def get_device(db: Session, device_id: UUID) -> Optional[Entity]:
        """Get a device by ID."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                device_service = CRUDMigrationLayer._get_device_service(db)
                device = device_service.get_device_by_id(device_id)
                if device:
                    logger.info(f"Device retrieved via service layer: {device_id}")
                    return device
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy device retrieval")
        return DeviceCRUD._legacy_get_device(db, device_id)
    
    @staticmethod
    def get_devices(
        db: Session, 
        organization_id: Optional[UUID] = None,
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        entity_type: Optional[str] = None
    ) -> List[Entity]:
        """Get devices with optional filtering."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                device_service = CRUDMigrationLayer._get_device_service(db)
                devices = device_service.get_devices(
                    organization_id=organization_id,
                    skip=skip,
                    limit=limit,
                    status=status,
                    entity_type=entity_type
                )
                logger.info(f"Devices retrieved via service layer: {len(devices)} devices")
                return devices
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy device listing")
        return DeviceCRUD._legacy_get_devices(db, organization_id, skip, limit, status, entity_type)
    
    @staticmethod
    def update_device(
        db: Session, 
        device_id: UUID, 
        device_data: DeviceUpdate
    ) -> Optional[Entity]:
        """Update a device."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                device_service = CRUDMigrationLayer._get_device_service(db)
                device = device_service.update_device(device_id, device_data)
                if device:
                    logger.info(f"Device updated via service layer: {device_id}")
                    return device
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy device update")
        return DeviceCRUD._legacy_update_device(db, device_id, device_data)
    
    @staticmethod
    def delete_device(db: Session, device_id: UUID) -> bool:
        """Delete a device."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                device_service = CRUDMigrationLayer._get_device_service(db)
                success = device_service.delete_device(device_id)
                if success:
                    logger.info(f"Device deleted via service layer: {device_id}")
                    return True
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy device deletion")
        return DeviceCRUD._legacy_delete_device(db, device_id)
    
    @staticmethod
    def update_device_status(
        db: Session, 
        device_id: UUID, 
        status: str,
        battery_level: Optional[float] = None,
        wifi_signal: Optional[int] = None
    ) -> Optional[Entity]:
        """Update device status and health metrics."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                device_service = CRUDMigrationLayer._get_device_service(db)
                device = device_service.update_device_status(
                    device_id, status, battery_level, wifi_signal
                )
                if device:
                    logger.info(f"Device status updated via service layer: {device_id}")
                    return device
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy device status update")
        return DeviceCRUD._legacy_update_device_status(db, device_id, status, battery_level, wifi_signal)

    # Legacy implementation methods (original code)
    @staticmethod
    def _legacy_create_device(
        db: Session, 
        device_data: DeviceCreate, 
        organization_id: Optional[UUID] = None,
        created_by: str = "system"
    ) -> Entity:
        """Legacy device creation implementation."""
        # Build device properties from the create request
        properties = {
            "name": device_data.name,
            "location": device_data.location,
            "status": "offline",  # Default status
            "firmware": {
                "version": device_data.firmware_version,
                "lastUpdate": datetime.utcnow().isoformat()
            },
            "hardware": {
                "model": device_data.hardware_model,
                "macAddress": device_data.mac_address,
                "sensors": device_data.sensors
            },
            "config": {
                "readingInterval": device_data.reading_interval,
                "alertThresholds": device_data.alert_thresholds or {}
            },
            "lastSeen": None,
            "batteryLevel": None,
            "metadata": {}
        }
        
        # Generate API key for device
        api_key = f"device_{uuid.uuid4().hex[:16]}"
        properties["api_key"] = api_key
        
        # Create entity
        device = Entity(
            entity_type=device_data.entity_type.value,
            name=device_data.name,
            description=device_data.description,
            properties=properties,
            organization_id=organization_id,
            status="active"
        )
        
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Create event for device creation
        event = Event(
            event_type="device.created",
            entity_id=device.id,
            entity_type=device.entity_type,
            data={
                "name": device_data.name,
                "created_by": created_by,
                "organization_id": str(organization_id) if organization_id else None
            }
        )
        db.add(event)
        db.commit()
        
        return device
    
    @staticmethod
    def _legacy_get_device(db: Session, device_id: UUID) -> Optional[Entity]:
        """Legacy device retrieval implementation."""
        return db.query(Entity).filter(
            Entity.id == device_id,
            Entity.entity_type == "device.esp32"
        ).first()
    
    @staticmethod
    def _legacy_get_devices(
        db: Session, 
        organization_id: Optional[UUID] = None,
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        entity_type: Optional[str] = None
    ) -> List[Entity]:
        """Legacy device listing implementation."""
        query = db.query(Entity).filter(Entity.entity_type == "device.esp32")
        
        if organization_id:
            query = query.filter(Entity.organization_id == organization_id)
        
        if status:
            query = query.filter(Entity.properties['status'].astext == status)
        
        if entity_type:
            query = query.filter(Entity.entity_type == entity_type)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def _legacy_update_device(
        db: Session, 
        device_id: UUID, 
        device_data: DeviceUpdate
    ) -> Optional[Entity]:
        """Legacy device update implementation."""
        device = DeviceCRUD._legacy_get_device(db, device_id)
        if not device:
            return None
        
        # Update basic fields
        if device_data.name is not None:
            device.name = device_data.name
        if device_data.description is not None:
            device.description = device_data.description
        
        # Update properties
        properties = device.properties or {}
        
        if device_data.name is not None:
            properties["name"] = device_data.name
        if device_data.location is not None:
            properties["location"] = device_data.location
        if device_data.status is not None:
            properties["status"] = device_data.status.value
        if device_data.reading_interval is not None:
            properties["config"]["readingInterval"] = device_data.reading_interval
        if device_data.alert_thresholds is not None:
            properties["config"]["alertThresholds"] = device_data.alert_thresholds
        if device_data.metadata is not None:
            properties["metadata"] = {**properties.get("metadata", {}), **device_data.metadata}
        
        device.properties = properties
        device.last_updated = datetime.utcnow()
        
        db.commit()
        db.refresh(device)
        
        # Create update event
        event = Event(
            event_type="device.updated",
            entity_id=device.id,
            entity_type=device.entity_type,
            data={
                "updated_fields": list(device_data.dict(exclude_unset=True).keys())
            }
        )
        db.add(event)
        db.commit()
        
        return device
    
    @staticmethod
    def _legacy_delete_device(db: Session, device_id: UUID) -> bool:
        """Legacy device deletion implementation."""
        device = DeviceCRUD._legacy_get_device(db, device_id)
        if not device:
            return False
        
        # Create deletion event
        event = Event(
            event_type="device.deleted",
            entity_id=device.id,
            entity_type=device.entity_type,
            data={
                "name": device.name,
                "deleted_at": datetime.utcnow().isoformat()
            }
        )
        db.add(event)
        
        # Delete the device
        db.delete(device)
        db.commit()
        
        return True
    
    @staticmethod
    def _legacy_update_device_status(
        db: Session, 
        device_id: UUID, 
        status: str,
        battery_level: Optional[float] = None,
        wifi_signal: Optional[int] = None
    ) -> Optional[Entity]:
        """Legacy device status update implementation."""
        device = DeviceCRUD._legacy_get_device(db, device_id)
        if not device:
            return None
        
        properties = device.properties or {}
        properties["status"] = status
        properties["lastSeen"] = datetime.utcnow().isoformat()
        
        if battery_level is not None:
            properties["batteryLevel"] = battery_level
        
        if wifi_signal is not None:
            properties["config"]["wifi"]["signalStrength"] = wifi_signal
        
        device.properties = properties
        device.last_updated = datetime.utcnow()
        
        db.commit()
        db.refresh(device)
        
        return device

# User CRUD Operations
class UserCRUD:
    @staticmethod
    def create_user(
        db: Session, 
        user_data: UserCreate,
        created_by: str = "system"
    ) -> User:
        """Create a new user with associated entity."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                auth_service = CRUDMigrationLayer._get_auth_service(db)
                user = auth_service.create_user(user_data, created_by)
                logger.info(f"User created via service layer: {user.id}")
                return user
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy user creation")
        return UserCRUD._legacy_create_user(db, user_data, created_by)
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                auth_service = CRUDMigrationLayer._get_auth_service(db)
                user = auth_service.get_user_by_email(email)
                if user:
                    logger.info(f"User retrieved via service layer: {email}")
                    return user
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy user retrieval")
        return UserCRUD._legacy_get_user_by_email(db, email)
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                auth_service = CRUDMigrationLayer._get_auth_service(db)
                user = auth_service.get_user_by_id(user_id)
                if user:
                    logger.info(f"User retrieved via service layer: {user_id}")
                    return user
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy user retrieval")
        return UserCRUD._legacy_get_user_by_id(db, user_id)
    
    @staticmethod
    def get_users(
        db: Session, 
        organization_id: Optional[UUID] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Get users with optional organization filtering."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                auth_service = CRUDMigrationLayer._get_auth_service(db)
                users = auth_service.get_users(organization_id, skip, limit)
                logger.info(f"Users retrieved via service layer: {len(users)} users")
                return users
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy user listing")
        return UserCRUD._legacy_get_users(db, organization_id, skip, limit)

    # Legacy implementation methods
    @staticmethod
    def _legacy_create_user(
        db: Session, 
        user_data: UserCreate,
        created_by: str = "system"
    ) -> User:
        """Legacy user creation implementation."""
        # Create user entity first
        user_entity = Entity(
            entity_type="user",
            name=user_data.name,
            description=f"User: {user_data.email}",
            properties={
                "email": user_data.email,
                "name": user_data.name,
                "organization_id": str(user_data.organization_id) if user_data.organization_id else None
            },
            organization_id=user_data.organization_id,
            status="active"
        )
        
        db.add(user_entity)
        db.flush()  # Get the ID without committing
        
        # Create user record
        from auth import get_password_hash
        user = User(
            entity_id=user_entity.id,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
            is_superuser=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create event
        event = Event(
            event_type="user.created",
            entity_id=user_entity.id,
            entity_type="user",
            data={
                "email": user_data.email,
                "name": user_data.name,
                "created_by": created_by
            }
        )
        db.add(event)
        db.commit()
        
        return user
    
    @staticmethod
    def _legacy_get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Legacy user retrieval by email implementation."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def _legacy_get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """Legacy user retrieval by ID implementation."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def _legacy_get_users(
        db: Session, 
        organization_id: Optional[UUID] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Legacy user listing implementation."""
        query = db.query(User).join(Entity, User.entity_id == Entity.id)
        
        if organization_id:
            query = query.filter(Entity.organization_id == organization_id)
        
        return query.offset(skip).limit(limit).all()

# Organization CRUD Operations
class OrganizationCRUD:
    @staticmethod
    def create_organization(
        db: Session, 
        org_data: OrganizationCreate,
        created_by: str = "system"
    ) -> Entity:
        """Create a new organization entity."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                org_service = CRUDMigrationLayer._get_organization_service(db)
                org = org_service.create_organization(org_data, created_by)
                logger.info(f"Organization created via service layer: {org.id}")
                return org
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy organization creation")
        return OrganizationCRUD._legacy_create_organization(db, org_data, created_by)
    
    @staticmethod
    def get_organization(db: Session, org_id: UUID) -> Optional[Entity]:
        """Get organization by ID."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                org_service = CRUDMigrationLayer._get_organization_service(db)
                org = org_service.get_organization_by_id(org_id)
                if org:
                    logger.info(f"Organization retrieved via service layer: {org_id}")
                    return org
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy organization retrieval")
        return OrganizationCRUD._legacy_get_organization(db, org_id)
    
    @staticmethod
    def get_organizations(
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Entity]:
        """Get all organizations."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                org_service = CRUDMigrationLayer._get_organization_service(db)
                orgs = org_service.get_organizations(skip, limit)
                logger.info(f"Organizations retrieved via service layer: {len(orgs)} orgs")
                return orgs
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy organization listing")
        return OrganizationCRUD._legacy_get_organizations(db, skip, limit)

    # Legacy implementation methods
    @staticmethod
    def _legacy_create_organization(
        db: Session, 
        org_data: OrganizationCreate,
        created_by: str = "system"
    ) -> Entity:
        """Legacy organization creation implementation."""
        org = Entity(
            entity_type="organization",
            name=org_data.name,
            description=org_data.description,
            properties={
                "name": org_data.name,
                "description": org_data.description,
                "member_count": 0
            },
            status="active"
        )
        
        db.add(org)
        db.commit()
        db.refresh(org)
        
        # Create event
        event = Event(
            event_type="organization.created",
            entity_id=org.id,
            entity_type="organization",
            data={
                "name": org_data.name,
                "created_by": created_by
            }
        )
        db.add(event)
        db.commit()
        
        return org
    
    @staticmethod
    def _legacy_get_organization(db: Session, org_id: UUID) -> Optional[Entity]:
        """Legacy organization retrieval implementation."""
        return db.query(Entity).filter(
            Entity.id == org_id,
            Entity.entity_type == "organization"
        ).first()
    
    @staticmethod
    def _legacy_get_organizations(
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Entity]:
        """Legacy organization listing implementation."""
        return db.query(Entity).filter(
            Entity.entity_type == "organization"
        ).offset(skip).limit(limit).all()

# Reading CRUD Operations
class ReadingCRUD:
    @staticmethod
    def store_readings(
        db: Session, 
        device_id: UUID, 
        readings: List[Dict[str, Any]]
    ) -> List[Event]:
        """Store sensor readings as events."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                reading_service = CRUDMigrationLayer._get_reading_service(db)
                events = reading_service.store_readings(device_id, readings)
                logger.info(f"Readings stored via service layer: {len(events)} events")
                return events
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy reading storage")
        return ReadingCRUD._legacy_store_readings(db, device_id, readings)
    
    @staticmethod
    def get_readings(
        db: Session,
        device_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sensor_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """Get sensor readings for a device."""
        # Try to use service layer first
        if SERVICE_LAYER_AVAILABLE:
            try:
                reading_service = CRUDMigrationLayer._get_reading_service(db)
                readings = reading_service.get_readings(
                    device_id, start_time, end_time, sensor_type, skip, limit
                )
                logger.info(f"Readings retrieved via service layer: {len(readings)} readings")
                return readings
            except Exception as e:
                logger.warning(f"Service layer failed, falling back to legacy: {e}")
        
        # Fallback to legacy implementation
        logger.info("Using legacy reading retrieval")
        return ReadingCRUD._legacy_get_readings(db, device_id, start_time, end_time, sensor_type, skip, limit)

    # Legacy implementation methods
    @staticmethod
    def _legacy_store_readings(
        db: Session, 
        device_id: UUID, 
        readings: List[Dict[str, Any]]
    ) -> List[Event]:
        """Legacy reading storage implementation."""
        events = []
        
        for reading in readings:
            event = Event(
                event_type="sensor.reading",
                entity_id=device_id,
                entity_type="device.esp32",
                data=reading,
                event_metadata={
                    "sensor_type": reading.get("sensor_type"),
                    "quality": reading.get("quality", "good")
                }
            )
            events.append(event)
        
        db.add_all(events)
        db.commit()
        
        return events
    
    @staticmethod
    def _legacy_get_readings(
        db: Session,
        device_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sensor_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """Legacy reading retrieval implementation."""
        query = db.query(Event).filter(
            Event.entity_id == device_id,
            Event.event_type == "sensor.reading"
        )
        
        if start_time:
            query = query.filter(Event.timestamp >= start_time)
        if end_time:
            query = query.filter(Event.timestamp <= end_time)
        if sensor_type:
            query = query.filter(Event.event_metadata['sensor_type'].astext == sensor_type)
        
        return query.order_by(desc(Event.timestamp)).offset(skip).limit(limit).all() 