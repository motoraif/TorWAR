#!/usr/bin/env python3
"""
TorWAR Performance Optimization Enabler
Author: Mohamed Toraif

Quick script to enable performance optimizations in existing TorWAR app.
"""

def enable_performance_optimizations():
    """Enable performance optimizations in the main app."""
    
    try:
        # Import the main app
        from app import app
        
        # Initialize performance optimizations
        from performance_integration import (
            init_performance_optimizations,
            optimize_trusted_advisor_helper,
            optimize_aws_helper
        )
        
        print("🚀 Enabling TorWAR performance optimizations...")
        
        # Initialize performance monitoring and caching
        init_performance_optimizations(app)
        
        # Optimize existing helpers
        optimize_trusted_advisor_helper()
        optimize_aws_helper()
        
        print("✅ Performance optimizations enabled!")
        print("\n📊 New endpoints available:")
        print("  - GET  /api/performance/metrics")
        print("  - GET  /api/performance/cache/stats")
        print("  - POST /api/performance/cache/clear")
        print("  - POST /api/tasks/refresh/recommendations")
        print("  - POST /api/tasks/refresh/workloads")
        print("  - GET  /api/tasks/<task_id>/status")
        
        print("\n🔧 Optimizations applied:")
        print("  ✅ Redis caching with memory fallback")
        print("  ✅ Connection pooling for AWS clients")
        print("  ✅ Performance monitoring")
        print("  ✅ Background task queue")
        print("  ✅ Async AWS operations")
        
        return app
        
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("Make sure to install performance dependencies:")
        print("pip install redis aioboto3 psutil")
        return None
    except Exception as e:
        print(f"❌ Error enabling optimizations: {e}")
        return None

if __name__ == "__main__":
    app = enable_performance_optimizations()
    if app:
        print("\n🎯 To start with optimizations:")
        print("python enable_performance.py")
        print("\n🔍 Monitor performance at: http://localhost:5000/api/performance/metrics")
        
        # Start the app
        app.run(host='0.0.0.0', port=5000, debug=False)
