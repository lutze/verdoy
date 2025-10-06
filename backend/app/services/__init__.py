"""
Service layer package for the VerdoyLab API.

This package contains all business logic services organized by domain:
- auth: Authentication and user management business logic
- device: Device management and IoT operations business logic
- reading: Sensor data processing and analytics business logic
- command: Device command and control business logic
- analytics: Data analysis and reporting business logic
- alert: Alert management and notification business logic
- organization: Multi-tenant organization management business logic
- billing: Subscription and billing business logic
- cache: Caching layer for performance optimization
- notification: Multi-channel notification delivery business logic
- background: Background task processing
- websocket: WebSocket connection management for real-time features

The service layer follows clean architecture principles:
- Separation of concerns
- Dependency inversion
- Single responsibility
- Testability
- Maintainability
"""

from .base import BaseService
from .auth_service import AuthService
from .device_service import DeviceService
from .reading_service import ReadingService
from .command_service import CommandService
from .analytics_service import AnalyticsService
from .alert_service import AlertService
from .organization_service import OrganizationService
from .organization_member_service import OrganizationMemberService
from .organization_invitation_service import OrganizationInvitationService
from .membership_removal_service import MembershipRemovalService
from .project_service import ProjectService
from .billing_service import BillingService
from .cache_service import CacheService
from .notification_service import NotificationService
from .background_service import BackgroundService
from .websocket_service import WebSocketService

__all__ = [
    "BaseService",
    "AuthService",
    "DeviceService", 
    "ReadingService",
    "CommandService",
    "AnalyticsService",
    "AlertService",
    "OrganizationService",
    "OrganizationMemberService",
    "OrganizationInvitationService",
    "MembershipRemovalService",
    "ProjectService",
    "BillingService",
    "CacheService",
    "NotificationService",
    "BackgroundService",
    "WebSocketService",
] 