#!/usr/bin/env python3
"""
TorWAR Modern Frontend Integration
Author: Mohamed Toraif
"""

from flask import Flask, render_template, send_from_directory
import os

def integrate_modern_frontend(app: Flask):
    """Integrate modern Vue.js frontend with Flask backend."""
    
    # Serve Vue.js app
    @app.route('/')
    @app.route('/<path:path>')
    def serve_frontend(path=''):
        """Serve Vue.js frontend for all routes."""
        # Check if it's an API route
        if path.startswith('api/'):
            return {'error': 'API endpoint not found'}, 404
        
        # Serve static files
        if path and '.' in path:
            try:
                return send_from_directory('static/dist', path)
            except:
                pass
        
        # Serve Vue.js app for all other routes
        return render_template('spa.html')
    
    # API endpoints for frontend
    @app.route('/api/frontend/config')
    def frontend_config():
        """Get frontend configuration."""
        return {
            'app_name': 'TorWAR',
            'version': '2.0.0',
            'api_base_url': '/api',
            'features': {
                'ai_dashboard': True,
                'real_time_updates': True,
                'dark_mode': True,
                'mobile_responsive': True
            }
        }
    
    print("✅ Modern frontend integration enabled")

def create_spa_template():
    """Create SPA template for Vue.js app."""
    template_dir = 'templates'
    os.makedirs(template_dir, exist_ok=True)
    
    spa_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="TorWAR - AWS Well-Architected Review Tool">
    <title>TorWAR - Modern Frontend</title>
    
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <!-- Preload critical resources -->
    <link rel="preload" href="/static/dist/assets/index.css" as="style">
    <link rel="preload" href="/static/dist/assets/index.js" as="script">
    
    <!-- Vue.js app styles -->
    <link rel="stylesheet" href="/static/dist/assets/index.css">
</head>
<body>
    <div id="app">
        <!-- Loading fallback -->
        <div style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div style="text-align: center;">
                <div style="width: 50px; height: 50px; border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
                <h2 style="color: #333; margin-bottom: 10px;">Loading TorWAR...</h2>
                <p style="color: #666;">Modern AWS Well-Architected Review Tool</p>
            </div>
        </div>
    </div>
    
    <!-- Vue.js app script -->
    <script type="module" src="/static/dist/assets/index.js"></script>
    
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</body>
</html>'''
    
    with open(os.path.join(template_dir, 'spa.html'), 'w') as f:
        f.write(spa_template)
    
    print("✅ SPA template created")

def enable_modern_frontend():
    """Enable modern frontend in TorWAR."""
    
    try:
        from app import app
        
        print("🎨 Enabling TorWAR modern frontend...")
        
        # Create SPA template
        create_spa_template()
        
        # Integrate frontend routes
        integrate_modern_frontend(app)
        
        print("✅ Modern frontend enabled!")
        print("\n🎨 Frontend features:")
        print("  ✅ Vue.js 3 with Composition API")
        print("  ✅ Modern component architecture")
        print("  ✅ Responsive mobile design")
        print("  ✅ Real-time data updates")
        print("  ✅ Progressive Web App (PWA) ready")
        print("  ✅ Modern build system with Vite")
        
        print("\n🚀 Development workflow:")
        print("  1. cd frontend && npm install")
        print("  2. npm run dev (for development)")
        print("  3. npm run build (for production)")
        
        return app
        
    except Exception as e:
        print(f"❌ Error enabling frontend: {e}")
        return None

if __name__ == "__main__":
    app = enable_modern_frontend()
    if app:
        print("\n🎯 Modern frontend-enabled TorWAR ready!")
        app.run(host='0.0.0.0', port=5000, debug=False)
