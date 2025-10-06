"""
Billing model for VerdoyLab API.

This module contains the Billing and Subscription models and related functionality
for billing and subscription management.
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from .base import BaseModel
from .entity import Entity
from ..database import JSONType


class Billing(Entity):
    """
    Billing model for billing accounts.
    
    Maps to the existing entities table with entity_type = 'billing.account'
    and stores billing configuration in the properties JSON column.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'billing.account',
    }
    
    def __init__(self, *args, **kwargs):
        # Set default entity_type for billing accounts
        if 'entity_type' not in kwargs:
            kwargs['entity_type'] = 'billing.account'
        super().__init__(*args, **kwargs)
    
    @classmethod
    def get_organization_billing(cls, db, organization_id):
        """
        Get billing records for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            List of billing instances
        """
        return db.query(cls).filter(
            cls.entity_type == "billing.record",
            cls.organization_id == organization_id
        ).order_by(cls.created_at.desc()).all()
    
    def get_amount(self) -> float:
        """
        Get billing amount from properties.
        
        Returns:
            Billing amount as float
        """
        value = self.get_property('amount')
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_currency(self) -> str:
        """
        Get currency from properties.
        
        Returns:
            Currency string
        """
        return self.get_property('currency', 'USD')
    
    def get_status(self) -> str:
        """
        Get billing status from properties.
        
        Returns:
            Billing status string
        """
        return self.get_property('status', 'pending')
    
    def get_invoice_number(self) -> str:
        """
        Get invoice number from properties.
        
        Returns:
            Invoice number string
        """
        return self.get_property('invoiceNumber', '')
    
    def __repr__(self):
        """String representation of the billing record."""
        return f"<Billing(id={self.id}, amount={self.get_amount()}, status={self.get_status()})>"


class Subscription(Entity):
    """
    Subscription model for subscription management.
    
    Maps to the existing entities table with entity_type = 'subscription'
    and stores subscription data in the properties JSON column.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'subscription',
    }
    
    def __init__(self, *args, **kwargs):
        # Set default entity_type for subscriptions
        if 'entity_type' not in kwargs:
            kwargs['entity_type'] = 'subscription'
        super().__init__(*args, **kwargs)
    
    @classmethod
    def get_organization_subscription(cls, db, organization_id):
        """
        Get subscription for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            Subscription instance or None
        """
        return db.query(cls).filter(
            cls.entity_type == "subscription",
            cls.organization_id == organization_id
        ).first()
    
    def get_plan_name(self) -> str:
        """
        Get plan name from properties.
        
        Returns:
            Plan name string
        """
        return self.get_property('planName', 'free')
    
    def get_plan_features(self) -> list:
        """
        Get plan features from properties.
        
        Returns:
            List of plan features
        """
        return self.get_property('planFeatures', [])
    
    def get_monthly_price(self) -> float:
        """
        Get monthly price from properties.
        
        Returns:
            Monthly price as float
        """
        value = self.get_property('monthlyPrice')
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_device_limit(self) -> int:
        """
        Get device limit from properties.
        
        Returns:
            Device limit as integer
        """
        return self.get_property('deviceLimit', 1)
    
    def get_data_retention_days(self) -> int:
        """
        Get data retention period from properties.
        
        Returns:
            Data retention days as integer
        """
        return self.get_property('dataRetentionDays', 30)
    
    def is_active(self) -> bool:
        """
        Check if subscription is active.
        
        Returns:
            True if active, False otherwise
        """
        return self.status == "active"
    
    def __repr__(self):
        """String representation of the subscription."""
        return f"<Subscription(id={self.id}, plan={self.get_plan_name()})>"


 