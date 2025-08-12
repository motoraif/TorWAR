#!/usr/bin/env python3
"""
Trusted Advisor Caching System
Provides fast loading with background updates and intelligent cache management.
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from trusted_advisor_helper import get_all_trusted_advisor_recommendations, get_trusted_advisor_summary

class TrustedAdvisorCache:
    """
    Multi-layered caching system for Trusted Advisor data.
    
    Features:
    - File-based persistent cache
    - In-memory cache for ultra-fast access
    - Background refresh mechanism
    - Configurable cache TTL
    - Graceful fallback to live API calls
    """
    
    def __init__(self, cache_dir: str = "data/cache", cache_ttl_minutes: int = 30, startup_refresh: bool = True):
        self.cache_dir = cache_dir
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.startup_refresh = startup_refresh
        self.recommendations_file = os.path.join(cache_dir, "trusted_advisor_recommendations.json")
        self.summary_file = os.path.join(cache_dir, "trusted_advisor_summary.json")
        self.metadata_file = os.path.join(cache_dir, "cache_metadata.json")
        self.startup_flag_file = os.path.join(cache_dir, "startup_complete.flag")
        
        # In-memory cache
        self._memory_cache = {
            'recommendations': None,
            'summary': None,
            'last_updated': None
        }
        
        # Background refresh control
        self._refresh_in_progress = False
        self._refresh_thread = None
        self._startup_complete = False
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Check if this is first startup
        self._is_first_startup = not os.path.exists(self.startup_flag_file)
        
        # Load existing cache on initialization
        self._load_from_disk()
        
        # If startup refresh is enabled and this is first startup, start background refresh
        if self.startup_refresh and self._is_first_startup:
            print("🚀 First application startup detected - initiating fresh cache fetch...")
            self._start_startup_refresh()
        else:
            self._startup_complete = True
    
    def get_recommendations(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get Trusted Advisor recommendations with intelligent caching.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            Dict containing recommendations data
        """
        print("🔍 TrustedAdvisorCache: Getting recommendations...")
        
        # If startup refresh is in progress, wait for it or return loading state
        if not self._startup_complete and self._refresh_in_progress:
            print("🚀 Startup refresh in progress...")
            return {
                'loading': True,
                'message': 'Loading fresh data on first startup...',
                'recommendations': [],
                'startup_refresh': True
            }
        
        # Check if we should use cache
        if not force_refresh and self._is_cache_valid():
            print("✅ Using cached recommendations (fast path)")
            return self._memory_cache['recommendations']
        
        # Check if background refresh is already in progress
        if self._refresh_in_progress:
            print("🔄 Background refresh in progress, using existing cache if available")
            if self._memory_cache['recommendations']:
                return self._memory_cache['recommendations']
        
        # Start background refresh if cache is stale but not empty
        if self._memory_cache['recommendations'] and not self._refresh_in_progress:
            print("🚀 Starting background refresh...")
            self._start_background_refresh()
            return self._memory_cache['recommendations']
        
        # Cache is empty or force refresh - fetch synchronously
        print("📡 Fetching fresh recommendations (cache miss or force refresh)...")
        return self._fetch_and_cache_recommendations()
    
    def get_summary(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get Trusted Advisor summary with caching.
        Summary is lighter weight, so we can be more aggressive with refresh.
        """
        print("🔍 TrustedAdvisorCache: Getting summary...")
        
        if not force_refresh and self._is_cache_valid() and self._memory_cache['summary']:
            print("✅ Using cached summary")
            return self._memory_cache['summary']
        
        print("📡 Fetching fresh summary...")
        return self._fetch_and_cache_summary()
    
    def _is_cache_valid(self) -> bool:
        """Check if the current cache is still valid based on TTL."""
        if not self._memory_cache['last_updated']:
            return False
        
        cache_age = datetime.now() - self._memory_cache['last_updated']
        is_valid = cache_age < self.cache_ttl
        
        if is_valid:
            print(f"✅ Cache is valid (age: {cache_age.total_seconds():.0f}s, TTL: {self.cache_ttl.total_seconds():.0f}s)")
        else:
            print(f"⏰ Cache is stale (age: {cache_age.total_seconds():.0f}s, TTL: {self.cache_ttl.total_seconds():.0f}s)")
        
        return is_valid
    
    def _fetch_and_cache_recommendations(self) -> Dict[str, Any]:
        """Fetch recommendations from AWS API and update cache."""
        try:
            start_time = time.time()
            print("📡 Calling AWS Trusted Advisor API...")
            
            # Fetch from AWS
            recommendations_data = get_all_trusted_advisor_recommendations()
            
            fetch_time = time.time() - start_time
            print(f"⏱️  AWS API call completed in {fetch_time:.2f} seconds")
            
            if 'error' not in recommendations_data:
                # Update cache
                self._update_cache('recommendations', recommendations_data)
                print(f"💾 Cached {len(recommendations_data.get('recommendations', []))} recommendations")
            
            return recommendations_data
            
        except Exception as e:
            print(f"❌ Error fetching recommendations: {e}")
            # Return cached data if available, otherwise return error
            if self._memory_cache['recommendations']:
                print("🔄 Returning stale cache due to API error")
                return self._memory_cache['recommendations']
            else:
                return {'error': f'Failed to fetch recommendations: {str(e)}', 'recommendations': []}
    
    def _fetch_and_cache_summary(self) -> Dict[str, Any]:
        """Fetch summary from AWS API and update cache."""
        try:
            start_time = time.time()
            summary_data = get_trusted_advisor_summary()
            fetch_time = time.time() - start_time
            print(f"⏱️  Summary API call completed in {fetch_time:.2f} seconds")
            
            if 'error' not in summary_data:
                self._update_cache('summary', summary_data)
            
            return summary_data
            
        except Exception as e:
            print(f"❌ Error fetching summary: {e}")
            if self._memory_cache['summary']:
                return self._memory_cache['summary']
            else:
                return {'available': False, 'error': str(e)}
    
    def _update_cache(self, cache_type: str, data: Dict[str, Any]):
        """Update both memory and disk cache."""
        # Update memory cache
        self._memory_cache[cache_type] = data
        self._memory_cache['last_updated'] = datetime.now()
        
        # Update disk cache
        try:
            if cache_type == 'recommendations':
                with open(self.recommendations_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            elif cache_type == 'summary':
                with open(self.summary_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            
            # Update metadata
            metadata = {
                'last_updated': self._memory_cache['last_updated'].isoformat(),
                'cache_ttl_minutes': self.cache_ttl.total_seconds() / 60,
                'recommendations_count': len(data.get('recommendations', [])) if cache_type == 'recommendations' else None
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            print(f"💾 Updated {cache_type} cache on disk")
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to update disk cache: {e}")
    
    def _load_from_disk(self):
        """Load existing cache from disk on startup."""
        try:
            # Load metadata first
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                    last_updated_str = metadata.get('last_updated')
                    if last_updated_str:
                        self._memory_cache['last_updated'] = datetime.fromisoformat(last_updated_str)
            
            # Load recommendations
            if os.path.exists(self.recommendations_file):
                with open(self.recommendations_file, 'r') as f:
                    self._memory_cache['recommendations'] = json.load(f)
                    print(f"📂 Loaded {len(self._memory_cache['recommendations'].get('recommendations', []))} recommendations from disk cache")
            
            # Load summary
            if os.path.exists(self.summary_file):
                with open(self.summary_file, 'r') as f:
                    self._memory_cache['summary'] = json.load(f)
                    print("📂 Loaded summary from disk cache")
            
            # Check if loaded cache is still valid
            if self._is_cache_valid():
                print("✅ Loaded cache is still valid")
            else:
                print("⏰ Loaded cache is stale, will refresh on next request")
                
        except Exception as e:
            print(f"⚠️  Warning: Failed to load cache from disk: {e}")
    
    def _start_startup_refresh(self):
        """Start background thread to refresh cache on startup."""
        if self._refresh_in_progress:
            return
        
        def startup_refresh():
            self._refresh_in_progress = True
            try:
                print("🚀 Startup refresh started - fetching fresh data...")
                self._fetch_and_cache_recommendations()
                self._fetch_and_cache_summary()
                
                # Mark startup as complete
                with open(self.startup_flag_file, 'w') as f:
                    f.write(f"startup_complete_{datetime.now().isoformat()}")
                
                self._startup_complete = True
                print("✅ Startup refresh completed - application ready!")
            except Exception as e:
                print(f"❌ Startup refresh failed: {e}")
                # Still mark as complete to avoid blocking the app
                self._startup_complete = True
            finally:
                self._refresh_in_progress = False
        
        self._refresh_thread = threading.Thread(target=startup_refresh, daemon=True)
        self._refresh_thread.start()
    
    def _start_background_refresh(self):
        """Start background thread to refresh cache."""
        if self._refresh_in_progress:
            return
        
        def background_refresh():
            self._refresh_in_progress = True
            try:
                print("🔄 Background refresh started...")
                self._fetch_and_cache_recommendations()
                self._fetch_and_cache_summary()
                print("✅ Background refresh completed")
            except Exception as e:
                print(f"❌ Background refresh failed: {e}")
            finally:
                self._refresh_in_progress = False
        
        self._refresh_thread = threading.Thread(target=background_refresh, daemon=True)
        self._refresh_thread.start()
    
    def is_startup_complete(self) -> bool:
        """Check if startup refresh is complete."""
        return self._startup_complete
    
    def is_loading(self) -> bool:
        """Check if cache is currently loading (startup or refresh)."""
        return self._refresh_in_progress and not self._startup_complete
    
    def clear_cache(self):
        """Clear all cache data."""
        self._memory_cache = {'recommendations': None, 'summary': None, 'last_updated': None}
        
        for file_path in [self.recommendations_file, self.summary_file, self.metadata_file]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"⚠️  Warning: Failed to remove {file_path}: {e}")
        
        print("🗑️  Cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        return {
            'cache_valid': self._is_cache_valid(),
            'last_updated': self._memory_cache['last_updated'].isoformat() if self._memory_cache['last_updated'] else None,
            'recommendations_cached': self._memory_cache['recommendations'] is not None,
            'summary_cached': self._memory_cache['summary'] is not None,
            'refresh_in_progress': self._refresh_in_progress,
            'startup_complete': self._startup_complete,
            'is_first_startup': self._is_first_startup,
            'is_loading': self.is_loading(),
            'cache_ttl_minutes': self.cache_ttl.total_seconds() / 60,
            'recommendations_count': len(self._memory_cache['recommendations'].get('recommendations', [])) if self._memory_cache['recommendations'] else 0
        }

# Global cache instance
_cache_instance = None

def get_cache_instance() -> TrustedAdvisorCache:
    """Get or create the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = TrustedAdvisorCache()
    return _cache_instance

# Convenience functions for easy integration
def get_cached_recommendations(force_refresh: bool = False) -> Dict[str, Any]:
    """Get cached Trusted Advisor recommendations."""
    return get_cache_instance().get_recommendations(force_refresh)

def get_cached_summary(force_refresh: bool = False) -> Dict[str, Any]:
    """Get cached Trusted Advisor summary."""
    return get_cache_instance().get_summary(force_refresh)

def clear_trusted_advisor_cache():
    """Clear the Trusted Advisor cache."""
    get_cache_instance().clear_cache()

def get_cache_status() -> Dict[str, Any]:
    """Get cache status information."""
    return get_cache_instance().get_cache_info()

def is_cache_loading() -> bool:
    """Check if cache is currently loading."""
    return get_cache_instance().is_loading()

def is_startup_complete() -> bool:
    """Check if startup refresh is complete."""
    return get_cache_instance().is_startup_complete()
