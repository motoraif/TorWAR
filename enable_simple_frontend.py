#!/usr/bin/env python3
"""
TorWAR Simple Modern Frontend Enabler
Author: Mohamed Toraif

Works without Node.js build tools - uses CDN Vue.js
"""

import os
import shutil

def enable_simple_frontend():
    """Enable simple modern frontend without build tools."""
    
    try:
        from app import app
        from flask import send_from_directory, render_template_string
        
        print("🎨 Enabling TorWAR simple modern frontend...")
        
        # Copy simple frontend to static directory
        static_dir = 'static'
        os.makedirs(static_dir, exist_ok=True)
        
        # Copy simple.html to static directory as index.html
        if os.path.exists('frontend/simple.html'):
            shutil.copy('frontend/simple.html', os.path.join(static_dir, 'modern.html'))
            print("✅ Modern frontend copied to static/modern.html")
        
        # Add route to serve modern frontend
        @app.route('/modern')
        def modern_frontend():
            """Serve modern Vue.js frontend."""
            return send_from_directory('static', 'modern.html')
        
        @app.route('/api/frontend/demo-stats')
        def demo_stats():
            """Demo stats for frontend testing."""
            return {
                'workloads': 5,
                'reports': 12,
                'recommendations': 23,
                'high_priority': 3,
                'status': 'demo'
            }
        
        print("✅ Simple modern frontend enabled!")
        print("\n🎨 Frontend access:")
        print("  - Modern UI: http://localhost:5000/modern")
        print("  - Original UI: http://localhost:5000/")
        print("  - Demo API: http://localhost:5000/api/frontend/demo-stats")
        
        print("\n🚀 Features available:")
        print("  ✅ Vue.js 3 from CDN")
        print("  ✅ Modern responsive design")
        print("  ✅ Interactive dashboard")
        print("  ✅ Real-time data integration")
        print("  ✅ No build tools required")
        
        return app
        
    except Exception as e:
        print(f"❌ Error enabling simple frontend: {e}")
        return None

if __name__ == "__main__":
    app = enable_simple_frontend()
    if app:
        print("\n🎯 Simple modern frontend ready!")
        print("🌐 Visit: http://localhost:5000/modern")
        app.run(host='0.0.0.0', port=5000, debug=False)
