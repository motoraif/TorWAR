#!/usr/bin/env python3
"""
TorWAR Cache Manager - Redis-based caching for performance optimization
Author: Mohamed Toraif
"""

import redis
import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional
import os

class CacheManager:
    """High-performance Redis cache manager with fallback to memory cache."""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection with fallback."""
        try:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            # Test connection
            self.redis_client.ping()
            print("✅ Redis cache initialized")
        except Exception as e:
            print(f"⚠️ Redis unavailable, using memory cache: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if self.redis_client:
                data = self.redis_client.get(f"torwar:{key}")
                if data:
                    self.cache_stats['hits'] += 1
                    return pickle.loads(data)
            else:
                # Memory cache fallback
                if key in self.memory_cache:
                    item = self.memory_cache[key]
                    if item['expires'] > datetime.now():
                        self.cache_stats['hits'] += 1
                        return item['data']
                    else:
                        del self.memory_cache[key]
            
            self.cache_stats['misses'] += 1
            return None
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL."""
        try:
            if self.redis_client:
                self.redis_client.setex(f"torwar:{key}", ttl, pickle.dumps(value))
            else:
                # Memory cache fallback
                self.memory_cache[key] = {
                    'data': value,
                    'expires': datetime.now() + timedelta(seconds=ttl)
                }
        except Exception:
            pass
    
    def delete(self, key: str):
        """Delete key from cache."""
        try:
            if self.redis_client:
                self.redis_client.delete(f"torwar:{key}")
            else:
                self.memory_cache.pop(key, None)
        except Exception:
            pass
    
    def clear_pattern(self, pattern: str):
        """Clear keys matching pattern."""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(f"torwar:{pattern}")
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Memory cache pattern matching
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self.memory_cache[key]
        except Exception:
            pass
    
    def clear_all(self):
        """Clear all TorWAR cache entries."""
        try:
            if self.redis_client:
                # Clear only TorWAR keys to avoid affecting other applications
                keys = self.redis_client.keys("torwar:*")
                if keys:
                    self.redis_client.delete(*keys)
                    print(f"🗑️ Cleared {len(keys)} TorWAR Redis cache entries")
            else:
                self.memory_cache.clear()
                print("🗑️ Cleared all memory cache entries")
        except Exception as e:
            print(f"⚠️ Error clearing cache: {e}")
            pass
    
    def get_stats(self):
        """Get cache statistics."""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total * 100) if total > 0 else 0
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': f"{hit_rate:.1f}%",
            'backend': 'redis' if self.redis_client else 'memory'
        }

# Global cache instance
cache = CacheManager()
