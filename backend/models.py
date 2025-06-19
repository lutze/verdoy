from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, ForeignKey, Boolean, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"), nullable=False, unique=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to entity
    entity = relationship("Entity", back_populates="user")

class Entity(Base):
    __tablename__ = "entities"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(100), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    properties = Column(JSONB, nullable=False, default={})
    status = Column(String(50), default="active")
    organization_id = Column(PostgresUUID(as_uuid=True), nullable=True)  # For multi-tenant support
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="entity", uselist=False)
    from_relationships = relationship("Relationship", foreign_keys="Relationship.from_entity", back_populates="from_entity_rel")
    to_relationships = relationship("Relationship", foreign_keys="Relationship.to_entity", back_populates="to_entity_rel")

class Relationship(Base):
    __tablename__ = "relationships"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_entity = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    to_entity = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    properties = Column(JSONB, default={})
    strength = Column(Integer, default=100)  # 0-100 scale
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_to = Column(DateTime)
    created_by = Column(String(100))
    
    # Relationships
    from_entity_rel = relationship("Entity", foreign_keys=[from_entity], back_populates="from_relationships")
    to_entity_rel = relationship("Entity", foreign_keys=[to_entity], back_populates="to_relationships")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_type = Column(String(100), nullable=False)
    entity_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    entity_type = Column(String(100), nullable=False)
    data = Column(JSONB, nullable=False)
    metadata = Column(JSONB, default={})
    source_node = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class Schema(Base):
    __tablename__ = "schemas"
    
    id = Column(String(100), primary_key=True)
    version = Column(Integer, nullable=False)
    entity_type = Column(String(100), nullable=False)
    definition = Column(JSONB, nullable=False)
    description = Column(Text)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_to = Column(DateTime)
    created_by = Column(String(100))

class Process(Base):
    __tablename__ = "processes"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False)
    process_type = Column(String(100), nullable=False)
    definition = Column(JSONB, nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProcessInstance(Base):
    __tablename__ = "process_instances"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    process_id = Column(PostgresUUID(as_uuid=True), ForeignKey("processes.id"), nullable=False)
    batch_id = Column(String(100))
    status = Column(String(50), default="running")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    parameters = Column(JSONB, default={})
    results = Column(JSONB, default={}) 