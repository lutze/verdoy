from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import uuid
import json

from models import Entity, User, Relationship, Event, Schema
from schemas import DeviceCreate, DeviceUpdate, UserCreate, OrganizationCreate

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
    def get_device(db: Session, device_id: UUID) -> Optional[Entity]:
        """Get a device by ID."""
        return db.query(Entity).filter(
            Entity.id == device_id,
            Entity.entity_type == "device.esp32"
        ).first()
    
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
        query = db.query(Entity).filter(Entity.entity_type == "device.esp32")
        
        if organization_id:
            query = query.filter(Entity.organization_id == organization_id)
        
        if status:
            query = query.filter(Entity.properties['status'].astext == status)
        
        if entity_type:
            query = query.filter(Entity.entity_type == entity_type)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_device(
        db: Session, 
        device_id: UUID, 
        device_data: DeviceUpdate
    ) -> Optional[Entity]:
        """Update a device."""
        device = DeviceCRUD.get_device(db, device_id)
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
    def delete_device(db: Session, device_id: UUID) -> bool:
        """Delete a device."""
        device = DeviceCRUD.get_device(db, device_id)
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
    def update_device_status(
        db: Session, 
        device_id: UUID, 
        status: str,
        battery_level: Optional[float] = None,
        wifi_signal: Optional[int] = None
    ) -> Optional[Entity]:
        """Update device status and health metrics."""
        device = DeviceCRUD.get_device(db, device_id)
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
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_users(
        db: Session, 
        organization_id: Optional[UUID] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Get users with optional organization filtering."""
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
    def get_organization(db: Session, org_id: UUID) -> Optional[Entity]:
        """Get organization by ID."""
        return db.query(Entity).filter(
            Entity.id == org_id,
            Entity.entity_type == "organization"
        ).first()
    
    @staticmethod
    def get_organizations(
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Entity]:
        """Get all organizations."""
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
        events = []
        
        for reading in readings:
            event = Event(
                event_type="sensor.reading",
                entity_id=device_id,
                entity_type="device.esp32",
                data=reading,
                metadata={
                    "sensor_type": reading.get("sensor_type"),
                    "quality": reading.get("quality", "good")
                }
            )
            events.append(event)
        
        db.add_all(events)
        db.commit()
        
        return events
    
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
        query = db.query(Event).filter(
            Event.entity_id == device_id,
            Event.event_type == "sensor.reading"
        )
        
        if start_time:
            query = query.filter(Event.timestamp >= start_time)
        if end_time:
            query = query.filter(Event.timestamp <= end_time)
        if sensor_type:
            query = query.filter(Event.metadata['sensor_type'].astext == sensor_type)
        
        return query.order_by(desc(Event.timestamp)).offset(skip).limit(limit).all() 