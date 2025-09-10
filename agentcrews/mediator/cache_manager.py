"""
Simple in-memory cache for API responses with TTL support
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache manager
        
        Args:
            default_ttl: Default time-to-live in seconds (1 hour default)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._last_cleanup = time.time()
        self.cleanup_interval = 300  # Cleanup every 5 minutes
    
    def _get_cache_key(self, prefix: str, data: Any) -> str:
        """Generate a cache key from prefix and data"""
        # Create a stable hash from the data
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{data_hash}"
    
    def get(self, prefix: str, data: Any) -> Optional[Any]:
        """
        Get cached value if it exists and is not expired
        
        Args:
            prefix: Cache key prefix (e.g., 'workflow', 'domain')
            data: Data to use for cache key generation
            
        Returns:
            Cached value or None if not found/expired
        """
        self._cleanup_if_needed()
        
        key = self._get_cache_key(prefix, data)
        
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry['expires_at']:
                logger.debug(f"Cache hit for {key}")
                return entry['value']
            else:
                # Expired, remove it
                del self.cache[key]
                logger.debug(f"Cache expired for {key}")
        
        return None
    
    def set(self, prefix: str, data: Any, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a cache entry
        
        Args:
            prefix: Cache key prefix
            data: Data to use for cache key generation
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        key = self._get_cache_key(prefix, data)
        ttl = ttl or self.default_ttl
        
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        
        logger.debug(f"Cache set for {key} with TTL {ttl}s")
    
    def invalidate(self, prefix: Optional[str] = None) -> None:
        """
        Invalidate cache entries
        
        Args:
            prefix: If specified, only invalidate entries with this prefix.
                   If None, clear entire cache.
        """
        if prefix is None:
            self.cache.clear()
            logger.info("Entire cache cleared")
        else:
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"{prefix}:")]
            for key in keys_to_remove:
                del self.cache[key]
            logger.info(f"Cleared {len(keys_to_remove)} cache entries with prefix '{prefix}'")
    
    def _cleanup_if_needed(self) -> None:
        """Remove expired entries periodically"""
        current_time = time.time()
        
        if current_time - self._last_cleanup > self.cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = current_time
    
    def _cleanup_expired(self) -> None:
        """Remove all expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry['expires_at'] < current_time
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        valid_entries = sum(
            1 for entry in self.cache.values()
            if entry['expires_at'] > current_time
        )
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.cache) - valid_entries,
            'cache_size_bytes': sum(
                len(json.dumps(entry).encode()) 
                for entry in self.cache.values()
            )
        }

# Global cache instance
cache = CacheManager()