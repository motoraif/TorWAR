#!/usr/bin/env python3
"""
Add Performance Monitoring to Existing TorWAR App
Author: Mohamed Toraif

Simple patch to add performance monitoring without breaking existing functionality.
"""

# Add these lines to your existing app.py after the Flask app initialization:

def add_performance_monitoring(app):
    """Add performance monitoring to existing Flask app."""
    
    try:
        from performance_monitor import monitor
        from cache_manager import cache
        from flask import jsonify
        
        # Add monitoring hooks
        app.before_request(monitor.before_request)
        app.after_request(monitor.after_request)
        
        # Add performance endpoints
        @app.route('/api/performance/metrics')
        def perf_metrics():
            return jsonify(monitor.get_metrics())
        
        @app.route('/api/performance/cache/stats')
        def cache_stats():
            return jsonify(cache.get_stats())
        
        print("✅ Performance monitoring added to existing app")
        
    except Exception as e:
        print(f"⚠️ Performance monitoring not available: {e}")

# Usage: Add this to your app.py
# from add_performance_monitoring import add_performance_monitoring
# add_performance_monitoring(app)
