#!/usr/bin/env python3
"""
Performance Monitoring Middleware for TorWAR
Author: Mohamed Toraif

Tracks request performance and provides insights into slow operations.
"""

import time
import functools
from flask import request, g
from logging_config import get_logger

# Initialize performance logger
perf_logger = get_logger("performance")

class PerformanceMonitor:
    """Performance monitoring middleware for Flask applications."""
    
    def __init__(self, app=None, slow_request_threshold=2.0):
        self.app = app
        self.slow_request_threshold = slow_request_threshold
        self.request_stats = {}
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the performance monitor with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
    
    def before_request(self):
        """Record request start time."""
        g.start_time = time.time()
        g.request_id = f"{request.method}_{request.endpoint}_{int(time.time() * 1000)}"
    
    def after_request(self, response):
        """Record request completion and log performance."""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Log slow requests
            if duration > self.slow_request_threshold:
                perf_logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s (threshold: {self.slow_request_threshold}s)"
                )
            else:
                perf_logger.debug(
                    f"Request: {request.method} {request.path} "
                    f"completed in {duration:.2f}s"
                )
            
            # Update statistics
            endpoint = request.endpoint or 'unknown'
            if endpoint not in self.request_stats:
                self.request_stats[endpoint] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'slow_requests': 0
                }
            
            stats = self.request_stats[endpoint]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['min_time'] = min(stats['min_time'], duration)
            stats['max_time'] = max(stats['max_time'], duration)
            
            if duration > self.slow_request_threshold:
                stats['slow_requests'] += 1
        
        return response
    
    def teardown_request(self, exception):
        """Clean up request context."""
        if exception:
            perf_logger.error(f"Request failed with exception: {str(exception)}")
    
    def get_stats(self):
        """Get performance statistics."""
        stats = {}
        for endpoint, data in self.request_stats.items():
            if data['count'] > 0:
                stats[endpoint] = {
                    'count': data['count'],
                    'avg_time': data['total_time'] / data['count'],
                    'min_time': data['min_time'],
                    'max_time': data['max_time'],
                    'slow_requests': data['slow_requests'],
                    'slow_percentage': (data['slow_requests'] / data['count']) * 100
                }
        return stats
    
    def reset_stats(self):
        """Reset performance statistics."""
        self.request_stats.clear()
        perf_logger.info("Performance statistics reset")

def monitor_function_performance(threshold=1.0):
    """Decorator to monitor function performance."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if duration > threshold:
                    perf_logger.warning(
                        f"Slow function: {func.__name__} took {duration:.2f}s "
                        f"(threshold: {threshold}s)"
                    )
                else:
                    perf_logger.debug(
                        f"Function: {func.__name__} completed in {duration:.2f}s"
                    )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                perf_logger.error(
                    f"Function: {func.__name__} failed after {duration:.2f}s: {str(e)}"
                )
                raise
        return wrapper
    return decorator

# Global performance monitor instance
performance_monitor = PerformanceMonitor(slow_request_threshold=3.0)

# Convenience functions
def init_performance_monitoring(app, threshold=3.0):
    """Initialize performance monitoring for Flask app."""
    global performance_monitor
    performance_monitor = PerformanceMonitor(app, threshold)
    perf_logger.info(f"Performance monitoring initialized (threshold: {threshold}s)")

def get_performance_stats():
    """Get current performance statistics."""
    return performance_monitor.get_stats()

def reset_performance_stats():
    """Reset performance statistics."""
    performance_monitor.reset_stats()

# AWS operation monitoring
def monitor_aws_operation(operation_name):
    """Decorator specifically for AWS operations."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                perf_logger.info(
                    f"AWS {operation_name}: completed in {duration:.2f}s"
                )
                
                # Log slow AWS operations (threshold: 5 seconds)
                if duration > 5.0:
                    perf_logger.warning(
                        f"Slow AWS operation: {operation_name} took {duration:.2f}s"
                    )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                perf_logger.error(
                    f"AWS {operation_name}: failed after {duration:.2f}s: {str(e)}"
                )
                raise
        return wrapper
    return decorator
