"""
Cache service for performance optimization and caching.

This service handles:
- Caching frequently accessed data
- Managing cache invalidation
- Integrating with Redis or other cache backends
- Entity-aware caching patterns
"""

from .base import BaseService
from typing import Optional, Any, Dict, List
from uuid import UUID
import logging
import json
import hashlib

logger = logging.getLogger(__name__)

class CacheService(BaseService):
    """
    Cache service for performance optimization and caching.
    
    Provides entity-aware caching with proper key patterns and invalidation.
    """
    
    @property
    def model_class(self):
        # No model class for cache service
        return None
    
    def __init__(self, db):
        super().__init__(db)
        # In-memory cache for now (can be replaced with Redis)
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            if key in self._cache:
                entry = self._cache[key]
                # Check if expired
                if entry.get('expires_at') and entry['expires_at'] < self._now():
                    del self._cache[key]
                    return None
                return entry.get('value')
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        try:
            expires_at = self._now() + ttl if ttl > 0 else None
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': self._now()
            }
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")

    def invalidate(self, key: str):
        """
        Invalidate a cache key.
        
        Args:
            key: Cache key to invalidate
        """
        try:
            if key in self._cache:
                del self._cache[key]
        except Exception as e:
            logger.error(f"Error invalidating cache key {key}: {e}")
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all cache keys matching a pattern.
        
        Args:
            pattern: Pattern to match (supports * wildcard)
        """
        try:
            keys_to_remove = []
            for key in self._cache.keys():
                if self._match_pattern(key, pattern):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
                
        except Exception as e:
            logger.error(f"Error invalidating cache pattern {pattern}: {e}")
    
    # Entity-aware caching methods
    
    def get_entity(self, entity_id: UUID, entity_type: str) -> Optional[Dict[str, Any]]:
        """
        Get cached entity data.
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
            
        Returns:
            Cached entity data or None
        """
        key = self._entity_key(entity_id, entity_type)
        return self.get(key)
    
    def set_entity(self, entity_id: UUID, entity_type: str, entity_data: Dict[str, Any], ttl: int = 3600):
        """
        Cache entity data.
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
            entity_data: Entity data to cache
            ttl: Time to live in seconds
        """
        key = self._entity_key(entity_id, entity_type)
        self.set(key, entity_data, ttl)
    
    def invalidate_entity(self, entity_id: UUID, entity_type: str):
        """
        Invalidate cached entity data.
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
        """
        key = self._entity_key(entity_id, entity_type)
        self.invalidate(key)
        
        # Also invalidate related caches
        self.invalidate_pattern(f"entity:{entity_type}:{entity_id}:*")
    
    def get_entity_list(self, entity_type: str, organization_id: Optional[UUID] = None, 
                       filters: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached entity list.
        
        Args:
            entity_type: Entity type
            organization_id: Optional organization ID
            filters: Optional filters
            
        Returns:
            Cached entity list or None
        """
        key = self._entity_list_key(entity_type, organization_id, filters)
        return self.get(key)
    
    def set_entity_list(self, entity_type: str, entity_list: List[Dict[str, Any]], 
                       organization_id: Optional[UUID] = None, filters: Optional[Dict[str, Any]] = None, 
                       ttl: int = 1800):
        """
        Cache entity list.
        
        Args:
            entity_type: Entity type
            entity_list: List of entities to cache
            organization_id: Optional organization ID
            filters: Optional filters
            ttl: Time to live in seconds
        """
        key = self._entity_list_key(entity_type, organization_id, filters)
        self.set(key, entity_list, ttl)
    
    def invalidate_entity_list(self, entity_type: str, organization_id: Optional[UUID] = None):
        """
        Invalidate cached entity lists for a type and organization.
        
        Args:
            entity_type: Entity type
            organization_id: Optional organization ID
        """
        if organization_id:
            pattern = f"entity_list:{entity_type}:{organization_id}:*"
        else:
            pattern = f"entity_list:{entity_type}:*"
        self.invalidate_pattern(pattern)
    
    def invalidate_organization_entities(self, organization_id: UUID):
        """
        Invalidate all entity caches for an organization.
        
        Args:
            organization_id: Organization ID
        """
        patterns = [
            f"entity:*:{organization_id}:*",
            f"entity_list:*:{organization_id}:*"
        ]
        for pattern in patterns:
            self.invalidate_pattern(pattern)
    
    # Helper methods
    
    def _entity_key(self, entity_id: UUID, entity_type: str) -> str:
        """Generate entity cache key."""
        return f"entity:{entity_type}:{entity_id}"
    
    def _entity_list_key(self, entity_type: str, organization_id: Optional[UUID] = None, 
                        filters: Optional[Dict[str, Any]] = None) -> str:
        """Generate entity list cache key."""
        key_parts = ["entity_list", entity_type]
        
        if organization_id:
            key_parts.append(str(organization_id))
        
        if filters:
            # Create a hash of filters for consistent key generation
            filter_str = json.dumps(filters, sort_keys=True)
            filter_hash = hashlib.md5(filter_str.encode()).hexdigest()[:8]
            key_parts.append(filter_hash)
        
        return ":".join(key_parts)
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for cache invalidation."""
        if '*' not in pattern:
            return key == pattern
        
        # Convert pattern to regex-like matching
        import re
        regex_pattern = pattern.replace('*', '.*')
        return bool(re.match(regex_pattern, key))
    
    def _now(self) -> int:
        """Get current timestamp."""
        import time
        return int(time.time())
    
    def clear_all(self):
        """Clear all cached data."""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_keys = len(self._cache)
        expired_keys = 0
        current_time = self._now()
        
        for entry in self._cache.values():
            if entry.get('expires_at') and entry['expires_at'] < current_time:
                expired_keys += 1
        
        return {
            'total_keys': total_keys,
            'expired_keys': expired_keys,
            'active_keys': total_keys - expired_keys
        } 