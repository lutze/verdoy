"""
Billing schemas for LMS Core API.

This module contains Pydantic schemas for billing management,
subscriptions, and payment processing.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

from .base import BaseResponseSchema, PaginationParams


class BillingStatus(str, Enum):
    """Billing status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIAL = "trial"
    EXPIRED = "expired"


class BillingPeriod(str, Enum):
    """Billing period enumeration."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    INVOICE = "invoice"


class BillingCreate(BaseModel):
    """Schema for billing record creation."""
    organization_id: UUID = Field(..., description="Organization ID")
    subscription_id: Optional[UUID] = Field(None, description="Subscription ID")
    amount: float = Field(..., gt=0, description="Billing amount")
    currency: str = Field("USD", description="Currency code")
    billing_period: BillingPeriod = Field(BillingPeriod.MONTHLY, description="Billing period")
    description: str = Field(..., description="Billing description")
    due_date: datetime = Field(..., description="Due date")
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code."""
        valid_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF']
        if v not in valid_currencies:
            raise ValueError(f'Invalid currency: {v}. Must be one of {valid_currencies}')
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate billing amount."""
        if v <= 0:
            raise ValueError('Billing amount must be greater than 0')
        if v > 1000000:  # $1M limit
            raise ValueError('Billing amount cannot exceed $1,000,000')
        return round(v, 2)


class BillingUpdate(BaseModel):
    """Schema for billing record updates."""
    status: Optional[BillingStatus] = Field(None, description="Billing status")
    paid_amount: Optional[float] = Field(None, ge=0, description="Paid amount")
    paid_date: Optional[datetime] = Field(None, description="Payment date")
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    notes: Optional[str] = Field(None, description="Billing notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('paid_amount')
    def validate_paid_amount(cls, v):
        """Validate paid amount."""
        if v is not None and v < 0:
            raise ValueError('Paid amount cannot be negative')
        if v is not None and v > 1000000:  # $1M limit
            raise ValueError('Paid amount cannot exceed $1,000,000')
        return round(v, 2) if v is not None else v


class BillingResponse(BaseResponseSchema):
    """Schema for billing record response."""
    organization_id: UUID = Field(..., description="Organization ID")
    subscription_id: Optional[UUID] = Field(None, description="Subscription ID")
    amount: float = Field(..., description="Billing amount")
    currency: str = Field(..., description="Currency code")
    billing_period: str = Field(..., description="Billing period")
    status: str = Field(..., description="Billing status")
    description: str = Field(..., description="Billing description")
    due_date: datetime = Field(..., description="Due date")
    paid_amount: Optional[float] = Field(None, description="Paid amount")
    paid_date: Optional[datetime] = Field(None, description="Payment date")
    payment_method: Optional[str] = Field(None, description="Payment method")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    notes: Optional[str] = Field(None, description="Billing notes")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    properties: Dict[str, Any] = Field(..., description="Billing properties")


class BillingListResponse(BaseModel):
    """Schema for billing list response."""
    billings: List[BillingResponse] = Field(..., description="List of billing records")
    total: int = Field(..., description="Total number of billing records")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_amount: float = Field(..., description="Total billing amount")
    total_paid: float = Field(..., description="Total paid amount")


class SubscriptionCreate(BaseModel):
    """Schema for subscription creation."""
    organization_id: UUID = Field(..., description="Organization ID")
    plan_name: str = Field(..., description="Subscription plan name")
    billing_period: BillingPeriod = Field(BillingPeriod.MONTHLY, description="Billing period")
    amount: float = Field(..., gt=0, description="Subscription amount")
    currency: str = Field("USD", description="Currency code")
    start_date: datetime = Field(..., description="Subscription start date")
    end_date: Optional[datetime] = Field(None, description="Subscription end date")
    trial_end_date: Optional[datetime] = Field(None, description="Trial end date")
    max_devices: int = Field(..., ge=1, description="Maximum number of devices")
    max_members: int = Field(..., ge=1, description="Maximum number of members")
    features: List[str] = Field(default_factory=list, description="Subscription features")
    auto_renew: bool = Field(True, description="Auto-renewal enabled")
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code."""
        valid_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF']
        if v not in valid_currencies:
            raise ValueError(f'Invalid currency: {v}. Must be one of {valid_currencies}')
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate subscription amount."""
        if v <= 0:
            raise ValueError('Subscription amount must be greater than 0')
        if v > 10000:  # $10K limit
            raise ValueError('Subscription amount cannot exceed $10,000')
        return round(v, 2)
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate end date."""
        if v is not None:
            start_date = values.get('start_date')
            if start_date and v <= start_date:
                raise ValueError('End date must be after start date')
        return v


class SubscriptionUpdate(BaseModel):
    """Schema for subscription updates."""
    plan_name: Optional[str] = Field(None, description="Subscription plan name")
    billing_period: Optional[BillingPeriod] = Field(None, description="Billing period")
    amount: Optional[float] = Field(None, gt=0, description="Subscription amount")
    end_date: Optional[datetime] = Field(None, description="Subscription end date")
    max_devices: Optional[int] = Field(None, ge=1, description="Maximum number of devices")
    max_members: Optional[int] = Field(None, ge=1, description="Maximum number of members")
    features: Optional[List[str]] = Field(None, description="Subscription features")
    auto_renew: Optional[bool] = Field(None, description="Auto-renewal enabled")
    status: Optional[SubscriptionStatus] = Field(None, description="Subscription status")
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate subscription amount."""
        if v is not None and v <= 0:
            raise ValueError('Subscription amount must be greater than 0')
        if v is not None and v > 10000:  # $10K limit
            raise ValueError('Subscription amount cannot exceed $10,000')
        return round(v, 2) if v is not None else v


class SubscriptionResponse(BaseResponseSchema):
    """Schema for subscription response."""
    organization_id: UUID = Field(..., description="Organization ID")
    plan_name: str = Field(..., description="Subscription plan name")
    billing_period: str = Field(..., description="Billing period")
    status: str = Field(..., description="Subscription status")
    amount: float = Field(..., description="Subscription amount")
    currency: str = Field(..., description="Currency code")
    start_date: datetime = Field(..., description="Subscription start date")
    end_date: Optional[datetime] = Field(None, description="Subscription end date")
    trial_end_date: Optional[datetime] = Field(None, description="Trial end date")
    max_devices: int = Field(..., description="Maximum number of devices")
    max_members: int = Field(..., description="Maximum number of members")
    features: List[str] = Field(..., description="Subscription features")
    auto_renew: bool = Field(..., description="Auto-renewal enabled")
    payment_method: Optional[str] = Field(None, description="Payment method")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    properties: Dict[str, Any] = Field(..., description="Subscription properties")
    next_billing_date: Optional[datetime] = Field(None, description="Next billing date")
    current_usage: Dict[str, int] = Field(..., description="Current usage statistics")


class SubscriptionListResponse(BaseModel):
    """Schema for subscription list response."""
    subscriptions: List[SubscriptionResponse] = Field(..., description="List of subscriptions")
    total: int = Field(..., description="Total number of subscriptions")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class BillingQueryParams(PaginationParams):
    """Schema for billing query parameters."""
    organization_id: Optional[UUID] = Field(None, description="Filter by organization")
    subscription_id: Optional[UUID] = Field(None, description="Filter by subscription")
    status: Optional[BillingStatus] = Field(None, description="Filter by status")
    billing_period: Optional[BillingPeriod] = Field(None, description="Filter by billing period")
    payment_method: Optional[PaymentMethod] = Field(None, description="Filter by payment method")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum amount filter")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum amount filter")
    sort_by: Optional[str] = Field("created_at", description="Sort by field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")


class SubscriptionQueryParams(PaginationParams):
    """Schema for subscription query parameters."""
    organization_id: Optional[UUID] = Field(None, description="Filter by organization")
    status: Optional[SubscriptionStatus] = Field(None, description="Filter by status")
    billing_period: Optional[BillingPeriod] = Field(None, description="Filter by billing period")
    plan_name: Optional[str] = Field(None, description="Filter by plan name")
    auto_renew: Optional[bool] = Field(None, description="Filter by auto-renewal")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    sort_by: Optional[str] = Field("created_at", description="Sort by field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")


class BillingStatsResponse(BaseModel):
    """Schema for billing statistics response."""
    organization_id: UUID = Field(..., description="Organization ID")
    total_billings: int = Field(..., description="Total number of billing records")
    total_amount: float = Field(..., description="Total billing amount")
    total_paid: float = Field(..., description="Total paid amount")
    outstanding_amount: float = Field(..., description="Outstanding amount")
    overdue_amount: float = Field(..., description="Overdue amount")
    status_distribution: Dict[str, int] = Field(..., description="Status distribution")
    currency_distribution: Dict[str, float] = Field(..., description="Currency distribution")
    monthly_totals: Dict[str, float] = Field(..., description="Monthly totals")
    time_period: str = Field(..., description="Time period for statistics")


class PaymentMethodCreate(BaseModel):
    """Schema for payment method creation."""
    organization_id: UUID = Field(..., description="Organization ID")
    payment_type: PaymentMethod = Field(..., description="Payment method type")
    card_last4: Optional[str] = Field(None, description="Last 4 digits of card")
    card_brand: Optional[str] = Field(None, description="Card brand")
    card_exp_month: Optional[int] = Field(None, ge=1, le=12, description="Card expiration month")
    card_exp_year: Optional[int] = Field(None, ge=2024, description="Card expiration year")
    bank_name: Optional[str] = Field(None, description="Bank name")
    account_last4: Optional[str] = Field(None, description="Last 4 digits of account")
    is_default: bool = Field(False, description="Set as default payment method")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class PaymentMethodResponse(BaseModel):
    """Schema for payment method response."""
    id: UUID = Field(..., description="Payment method ID")
    organization_id: UUID = Field(..., description="Organization ID")
    payment_type: str = Field(..., description="Payment method type")
    card_last4: Optional[str] = Field(None, description="Last 4 digits of card")
    card_brand: Optional[str] = Field(None, description="Card brand")
    card_exp_month: Optional[int] = Field(None, description="Card expiration month")
    card_exp_year: Optional[int] = Field(None, description="Card expiration year")
    bank_name: Optional[str] = Field(None, description="Bank name")
    account_last4: Optional[str] = Field(None, description="Last 4 digits of account")
    is_default: bool = Field(..., description="Default payment method")
    is_active: bool = Field(..., description="Payment method active")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    
    class Config:
        from_attributes = True 