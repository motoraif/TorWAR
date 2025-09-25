#!/usr/bin/env python3
"""
TorWAR Performance Integration - Connect optimizations to main app
Author: Mohamed Toraif
"""

from flask import Flask, jsonify, request
from performance_monitor import monitor, performance_cache
from task_queue import task_queue, refresh_trusted_advisor_cache, refresh_workloads_cache
from cache_manager import cache
from aws_helper_optimized import OptimizedAWSHelper

def init_performance_optimizations(app: Flask):
    """Initialize all performance optimizations."""
    
    # Register performance monitoring
    app.before_request(monitor.before_request)
    app.after_request(monitor.after_request)
    
    # Performance routes
    @app.route('/api/performance/metrics')
    def performance_metrics():
        """Get performance metrics."""
        return jsonify(monitor.get_metrics())
    
    @app.route('/api/performance/cache/stats')
    def cache_stats():
        """Get cache statistics."""
        return jsonify(cache.get_stats())
    
    @app.route('/api/performance/cache/clear', methods=['POST'])
    def clear_performance_cache():
        """Clear application cache."""
        pattern = request.json.get('pattern', '*') if request.is_json else '*'
        cache.clear_pattern(pattern)
        OptimizedAWSHelper.clear_cache()
        return jsonify({'success': True, 'message': 'Cache cleared'})
    
    @app.route('/api/tasks/refresh/recommendations', methods=['POST'])
    def refresh_recommendations():
        """Start background task to refresh recommendations."""
        task_id = task_queue.submit(refresh_trusted_advisor_cache)
        return jsonify({'task_id': task_id, 'status': 'queued'})
    
    @app.route('/api/tasks/refresh/workloads', methods=['POST'])
    def refresh_workloads():
        """Start background task to refresh workloads."""
        task_id = task_queue.submit(refresh_workloads_cache)
        return jsonify({'task_id': task_id, 'status': 'queued'})
    
    @app.route('/api/tasks/<task_id>/status')
    def task_status(task_id):
        """Get task status."""
        status = task_queue.get_status(task_id)
        return jsonify(status)
    
    # Cleanup old tasks periodically
    def setup_cleanup():
        import threading
        import time
        
        def cleanup_worker():
            while True:
                time.sleep(3600)  # Run every hour
                task_queue.cleanup_old_results()
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    # Start cleanup on first request
    setup_cleanup()
    
    print("✅ Performance optimizations initialized")

# Optimized route decorators
def cached_route(ttl=300):
    """Decorator for caching route responses."""
    def decorator(func):
        return performance_cache(ttl=ttl)(func)
    return decorator

# Quick optimization functions
def optimize_trusted_advisor_helper():
    """Add caching to trusted advisor without replacing functions."""
    # Skip optimization to avoid circular imports
    pass

def optimize_aws_helper():
    """Add optimizations to AWS helper without replacing functions."""
    # Skip optimization to avoid conflicts with existing code
    pass
