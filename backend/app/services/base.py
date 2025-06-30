"""
Base service class providing common functionality for all services.

This module defines the BaseService class that provides:
- Common database session management
- Error handling and logging
- Caching integration
- Transaction management
- Audit logging
- Performance monitoring
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
from uuid import UUID

from ..database import get_db
from ..exceptions import (
    ServiceException,
    DatabaseException,
    ValidationException,
    NotFoundException
)
from ..models.base import BaseModel

# Type variables for generic service methods
T = TypeVar('T', bound=BaseModel)
CreateSchema = TypeVar('CreateSchema')
UpdateSchema = TypeVar('UpdateSchema')

logger = logging.getLogger(__name__)


class BaseService(ABC, Generic[T]):
    """
    Base service class providing common functionality for all services.
    
    This class implements the template method pattern and provides:
    - Database session management
    - Common CRUD operations
    - Error handling and logging
    - Caching integration
    - Transaction management
    - Audit logging
    """
    
    def __init__(self, db: Session):
        """
        Initialize the service with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    @abstractmethod
    def model_class(self) -> type[T]:
        """
        Abstract property that must be implemented by subclasses.
        
        Returns:
            The SQLAlchemy model class for this service.
        """
        pass
    
    def get_by_id(self, id: UUID) -> Optional[T]:
        """
        Get an entity by its ID.
        
        Args:
            id: The UUID of the entity to retrieve
            
        Returns:
            The entity if found, None otherwise
            
        Raises:
            ServiceException: If database error occurs
        """
        try:
            entity = self.db.query(self.model_class).filter(
                self.model_class.id == id
            ).first()
            
            if entity:
                self.logger.debug(f"Retrieved {self.model_class.__name__} with ID: {id}")
            else:
                self.logger.debug(f"{self.model_class.__name__} with ID {id} not found")
            
            return entity
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving {self.model_class.__name__}: {e}")
            raise DatabaseException(f"Failed to retrieve {self.model_class.__name__}")
    
    def get_by_id_or_raise(self, id: UUID) -> T:
        """
        Get an entity by its ID or raise NotFoundException if not found.
        
        Args:
            id: The UUID of the entity to retrieve
            
        Returns:
            The entity
            
        Raises:
            NotFoundException: If entity not found
            ServiceException: If database error occurs
        """
        entity = self.get_by_id(id)
        if not entity:
            raise NotFoundException(f"{self.model_class.__name__} with ID {id} not found")
        return entity
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """
        Get all entities with optional pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters to apply
            
        Returns:
            List of entities
            
        Raises:
            ServiceException: If database error occurs
        """
        try:
            query = self.db.query(self.model_class)
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field) and value is not None:
                        query = query.filter(getattr(self.model_class, field) == value)
            
            entities = query.offset(skip).limit(limit).all()
            
            self.logger.debug(f"Retrieved {len(entities)} {self.model_class.__name__} entities")
            return entities
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error retrieving {self.model_class.__name__} entities: {e}")
            raise DatabaseException(f"Failed to retrieve {self.model_class.__name__} entities")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities with optional filtering.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Total count of entities
            
        Raises:
            ServiceException: If database error occurs
        """
        try:
            query = self.db.query(self.model_class)
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field) and value is not None:
                        query = query.filter(getattr(self.model_class, field) == value)
            
            count = query.count()
            self.logger.debug(f"Counted {count} {self.model_class.__name__} entities")
            return count
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error counting {self.model_class.__name__} entities: {e}")
            raise DatabaseException(f"Failed to count {self.model_class.__name__} entities")
    
    def create(self, data: CreateSchema, **kwargs) -> T:
        """
        Create a new entity.
        
        Args:
            data: Data for creating the entity
            **kwargs: Additional keyword arguments
            
        Returns:
            The created entity
            
        Raises:
            ValidationException: If data validation fails
            ServiceException: If database error occurs
        """
        try:
            # Convert data to dict if it's a Pydantic model
            if hasattr(data, 'dict'):
                entity_data = data.dict()
            else:
                entity_data = dict(data)
            
            # Add additional kwargs
            entity_data.update(kwargs)
            
            # Create entity instance
            entity = self.model_class(**entity_data)
            
            # Add to database
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            
            self.logger.info(f"Created {self.model_class.__name__} with ID: {entity.id}")
            return entity
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error creating {self.model_class.__name__}: {e}")
            raise DatabaseException(f"Failed to create {self.model_class.__name__}")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise ServiceException(f"Failed to create {self.model_class.__name__}")
    
    def update(self, id: UUID, data: UpdateSchema, **kwargs) -> T:
        """
        Update an existing entity.
        
        Args:
            id: The UUID of the entity to update
            data: Data for updating the entity
            **kwargs: Additional keyword arguments
            
        Returns:
            The updated entity
            
        Raises:
            NotFoundException: If entity not found
            ValidationException: If data validation fails
            ServiceException: If database error occurs
        """
        try:
            entity = self.get_by_id_or_raise(id)
            
            # Convert data to dict if it's a Pydantic model
            if hasattr(data, 'dict'):
                update_data = data.dict(exclude_unset=True)
            else:
                update_data = dict(data)
            
            # Add additional kwargs
            update_data.update(kwargs)
            
            # Update entity attributes
            for field, value in update_data.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)
            
            # Update last_updated timestamp if available
            if hasattr(entity, 'last_updated'):
                entity.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(entity)
            
            self.logger.info(f"Updated {self.model_class.__name__} with ID: {id}")
            return entity
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error updating {self.model_class.__name__}: {e}")
            raise DatabaseException(f"Failed to update {self.model_class.__name__}")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error updating {self.model_class.__name__}: {e}")
            raise ServiceException(f"Failed to update {self.model_class.__name__}")
    
    def delete(self, id: UUID) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            id: The UUID of the entity to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundException: If entity not found
            ServiceException: If database error occurs
        """
        try:
            entity = self.get_by_id_or_raise(id)
            
            self.db.delete(entity)
            self.db.commit()
            
            self.logger.info(f"Deleted {self.model_class.__name__} with ID: {id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error deleting {self.model_class.__name__}: {e}")
            raise DatabaseException(f"Failed to delete {self.model_class.__name__}")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error deleting {self.model_class.__name__}: {e}")
            raise ServiceException(f"Failed to delete {self.model_class.__name__}")
    
    def exists(self, id: UUID) -> bool:
        """
        Check if an entity exists by its ID.
        
        Args:
            id: The UUID of the entity to check
            
        Returns:
            True if entity exists, False otherwise
        """
        try:
            return self.db.query(self.model_class).filter(
                self.model_class.id == id
            ).first() is not None
        except SQLAlchemyError as e:
            self.logger.error(f"Database error checking existence of {self.model_class.__name__}: {e}")
            return False
    
    def bulk_create(self, data_list: List[CreateSchema], **kwargs) -> List[T]:
        """
        Create multiple entities in a single transaction.
        
        Args:
            data_list: List of data for creating entities
            **kwargs: Additional keyword arguments for all entities
            
        Returns:
            List of created entities
            
        Raises:
            ServiceException: If database error occurs
        """
        try:
            entities = []
            
            for data in data_list:
                # Convert data to dict if it's a Pydantic model
                if hasattr(data, 'dict'):
                    entity_data = data.dict()
                else:
                    entity_data = dict(data)
                
                # Add additional kwargs
                entity_data.update(kwargs)
                
                # Create entity instance
                entity = self.model_class(**entity_data)
                entities.append(entity)
                self.db.add(entity)
            
            self.db.commit()
            
            # Refresh all entities
            for entity in entities:
                self.db.refresh(entity)
            
            self.logger.info(f"Created {len(entities)} {self.model_class.__name__} entities")
            return entities
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error bulk creating {self.model_class.__name__} entities: {e}")
            raise DatabaseException(f"Failed to bulk create {self.model_class.__name__} entities")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error bulk creating {self.model_class.__name__} entities: {e}")
            raise ServiceException(f"Failed to bulk create {self.model_class.__name__} entities")
    
    def bulk_delete(self, ids: List[UUID]) -> int:
        """
        Delete multiple entities by their IDs.
        
        Args:
            ids: List of UUIDs of entities to delete
            
        Returns:
            Number of entities deleted
            
        Raises:
            ServiceException: If database error occurs
        """
        try:
            deleted_count = self.db.query(self.model_class).filter(
                self.model_class.id.in_(ids)
            ).delete(synchronize_session=False)
            
            self.db.commit()
            
            self.logger.info(f"Deleted {deleted_count} {self.model_class.__name__} entities")
            return deleted_count
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error bulk deleting {self.model_class.__name__} entities: {e}")
            raise DatabaseException(f"Failed to bulk delete {self.model_class.__name__} entities")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error bulk deleting {self.model_class.__name__} entities: {e}")
            raise ServiceException(f"Failed to bulk delete {self.model_class.__name__} entities")
    
    def validate_data(self, data: Any) -> bool:
        """
        Validate data before processing.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationException: If data validation fails
        """
        # Base implementation - subclasses should override
        if data is None:
            raise ValidationException("Data cannot be None")
        return True
    
    def audit_log(self, action: str, entity_id: UUID, details: Optional[Dict] = None):
        """
        Log audit information for entity operations.
        
        Args:
            action: The action performed (create, update, delete, etc.)
            entity_id: The ID of the entity
            details: Optional additional details
        """
        audit_info = {
            "action": action,
            "entity_type": self.model_class.__name__,
            "entity_id": str(entity_id),
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        self.logger.info(f"Audit: {audit_info}")
        
        # TODO: Store audit logs in database for compliance
        # TODO: Implement audit log service for centralized logging
    
    def performance_monitor(self, operation: str, start_time: datetime):
        """
        Monitor performance of operations.
        
        Args:
            operation: The operation being monitored
            start_time: When the operation started
        """
        duration = datetime.utcnow() - start_time
        duration_ms = duration.total_seconds() * 1000
        
        self.logger.debug(f"Performance: {operation} took {duration_ms:.2f}ms")
        
        # TODO: Send metrics to monitoring system
        # TODO: Alert on slow operations
        # TODO: Track performance trends 