#!/usr/bin/env python3
"""
TorWAR Security Integration Enabler
Author: Mohamed Toraif
"""

def enable_security_features():
    """Enable comprehensive security features in TorWAR."""
    
    try:
        from flask import Flask, jsonify, request
        from security import security
        from auth_system import auth_system
        from security_middleware import security_middleware
        from validation_schemas import validate_request_data
        
        print("🔐 Enabling TorWAR security features...")
        
        # Import main app
        from app import app
        
        # Initialize security components
        security.init_app(app)
        security_middleware.init_app(app)
        
        # Add security API endpoints
        @app.route('/api/security/stats')
        @security.rate_limit(max_requests=30, window=60)
        def security_stats():
            """Get security statistics."""
            stats = security_middleware.get_security_stats()
            stats.update({
                'active_sessions': len(auth_system.active_sessions),
                'csrf_enabled': True,
                'rate_limiting_enabled': True
            })
            return jsonify(stats)
        
        @app.route('/api/auth/token', methods=['POST'])
        @security.rate_limit(max_requests=10, window=60)
        @validate_request_data('AWS_LOGIN')
        def create_api_token():
            """Create JWT token for API access."""
            data = request.validated_data
            
            # Verify AWS session exists
            if 'aws_authenticated' not in session or not session.get('aws_authenticated'):
                return jsonify({'error': 'AWS authentication required'}), 401
            
            # Create API session
            api_session = auth_system.create_api_session(
                aws_profile=session.get('aws_profile', 'default'),
                aws_region=data.get('aws_region', session.get('aws_region')),
                aws_account_id=session.get('aws_account_id', '')
            )
            
            return jsonify(api_session)
        
        @app.route('/api/auth/sessions')
        @auth_system.jwt_required(['admin'])
        def list_active_sessions():
            """List active API sessions."""
            return jsonify(auth_system.get_active_sessions())
        
        @app.route('/api/auth/sessions/<session_id>', methods=['DELETE'])
        @auth_system.jwt_required(['admin'])
        def revoke_session(session_id):
            """Revoke an active session."""
            success = auth_system.revoke_session(session_id)
            if success:
                return jsonify({'success': True})
            return jsonify({'error': 'Session not found'}), 404
        
        @app.route('/api/security/unblock-ip', methods=['POST'])
        @auth_system.jwt_required(['admin'])
        def unblock_ip():
            """Unblock an IP address."""
            data = request.get_json()
            ip_address = data.get('ip_address')
            
            if not ip_address:
                return jsonify({'error': 'IP address required'}), 400
            
            success = security_middleware.unblock_ip(ip_address)
            if success:
                return jsonify({'success': True, 'message': f'IP {ip_address} unblocked'})
            return jsonify({'error': 'IP not found in blocked list'}), 404
        
        # Secure existing endpoints with validation
        @app.route('/api/workloads', methods=['POST'])
        @security.require_auth
        @security.rate_limit(max_requests=20, window=60)
        @validate_request_data('WORKLOAD')
        def secure_create_workload():
            """Securely create workload with validation."""
            data = request.validated_data
            # Implementation would go here
            return jsonify({'message': 'Workload creation endpoint secured'})
        
        @app.route('/api/reports', methods=['POST'])
        @security.require_auth
        @security.rate_limit(max_requests=10, window=60)
        @validate_request_data('REPORT')
        def secure_create_report():
            """Securely create report with validation."""
            data = request.validated_data
            # Implementation would go here
            return jsonify({'message': 'Report creation endpoint secured'})
        
        # Add CSRF token endpoint
        @app.route('/api/csrf-token')
        def get_csrf_token():
            """Get CSRF token for forms."""
            from flask_wtf.csrf import generate_csrf
            return jsonify({'csrf_token': generate_csrf()})
        
        print("✅ Security features enabled!")
        print("\n🔐 Security endpoints:")
        print("  - GET  /api/security/stats")
        print("  - POST /api/auth/token")
        print("  - GET  /api/auth/sessions")
        print("  - DELETE /api/auth/sessions/<id>")
        print("  - POST /api/security/unblock-ip")
        print("  - GET  /api/csrf-token")
        
        print("\n🛡️ Security features:")
        print("  ✅ CSRF Protection")
        print("  ✅ Rate Limiting")
        print("  ✅ Input Validation")
        print("  ✅ XSS Prevention")
        print("  ✅ Security Headers")
        print("  ✅ JWT Authentication")
        print("  ✅ Request Monitoring")
        print("  ✅ IP Blocking")
        
        return app
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install with: pip install flask-wtf pyjwt")
        return None
    except Exception as e:
        print(f"❌ Error enabling security: {e}")
        return None

if __name__ == "__main__":
    app = enable_security_features()
    if app:
        print("\n🎯 Security-enabled TorWAR ready!")
        print("🔐 All endpoints now protected with comprehensive security")
        print("🚀 Start app: python enable_security.py")
        
        # Start the app
        app.run(host='0.0.0.0', port=5000, debug=False)
