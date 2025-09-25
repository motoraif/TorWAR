#!/usr/bin/env python3
"""
TorWAR Safe Performance Optimization Enabler
Author: Mohamed Toraif
"""

def enable_safe_performance():
    """Enable safe performance optimizations without replacing existing functions."""
    
    try:
        from app import app
        from performance_integration import init_performance_optimizations
        
        print("🚀 Enabling TorWAR performance optimizations (safe mode)...")
        
        # Only initialize monitoring and new endpoints
        init_performance_optimizations(app)
        
        print("✅ Safe performance optimizations enabled!")
        print("\n📊 New endpoints available:")
        print("  - GET  /api/performance/metrics")
        print("  - GET  /api/performance/cache/stats") 
        print("  - POST /api/performance/cache/clear")
        print("  - POST /api/tasks/refresh/recommendations")
        print("  - GET  /api/tasks/<task_id>/status")
        
        print("\n🔧 Optimizations applied:")
        print("  ✅ Memory caching (Redis fallback)")
        print("  ✅ Performance monitoring")
        print("  ✅ Background task queue")
        print("  ✅ New API endpoints")
        
        return app
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    app = enable_safe_performance()
    if app:
        print("\n🎯 Starting TorWAR with performance monitoring...")
        app.run(host='0.0.0.0', port=5000, debug=False)
