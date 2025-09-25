#!/usr/bin/env python3
"""
TorWAR Performance Monitor - Request timing and metrics
Author: Mohamed Toraif
"""

import time
import psutil
from flask import g, request, jsonify
from functools import wraps
from cache_manager import cache
from datetime import datetime, timedelta
import threading

class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self):
        self.metrics = {
            'requests': 0,
            'total_time': 0,
            'slow_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self.lock = threading.Lock()
    
    def before_request(self):
        """Start request timing."""
        g.start_time = time.time()
        g.request_id = f"{int(time.time())}-{threading.get_ident()}"
    
    def after_request(self, response):
        """End request timing and collect metrics."""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            with self.lock:
                self.metrics['requests'] += 1
                self.metrics['total_time'] += duration
                
                if duration > 2.0:  # Slow request threshold
                    self.metrics['slow_requests'] += 1
            
            # Log slow requests
            if duration > 5.0:
                print(f"⚠️ Slow request: {request.method} {request.path} - {duration:.2f}s")
            
            # Add performance headers
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
            response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
        
        return response
    
    def get_metrics(self):
        """Get current performance metrics."""
        with self.lock:
            avg_time = (self.metrics['total_time'] / self.metrics['requests'] 
                       if self.metrics['requests'] > 0 else 0)
            
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # Cache stats
            cache_stats = cache.get_stats()
            
            return {
                'requests': {
                    'total': self.metrics['requests'],
                    'slow_requests': self.metrics['slow_requests'],
                    'avg_response_time': f"{avg_time:.3f}s"
                },
                'system': {
                    'cpu_percent': f"{cpu_percent}%",
                    'memory_percent': f"{memory.percent}%",
                    'memory_available': f"{memory.available / 1024**3:.1f}GB"
                },
                'cache': cache_stats,
                'timestamp': datetime.now().isoformat()
            }
    
    def reset_metrics(self):
        """Reset performance metrics."""
        with self.lock:
            self.metrics = {
                'requests': 0,
                'total_time': 0,
                'slow_requests': 0,
                'cache_hits': 0,
                'cache_misses': 0
            }

def performance_cache(ttl=300):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            cache_key = f"func:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator

# Global monitor instance
monitor = PerformanceMonitor()
