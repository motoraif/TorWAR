#!/usr/bin/env python3
"""
TorWAR Security Configuration
Author: Mohamed Toraif
"""

import os
import secrets

class SecurityConfig:
    """Security configuration for TorWAR."""
    
    @staticmethod
    def get_security_config():
        """Get security configuration settings."""
        return {
            # CSRF Protection
            'SECRET_KEY': os.environ.get('SECRET_KEY') or secrets.token_hex(32),
            'WTF_CSRF_ENABLED': True,
            'WTF_CSRF_TIME_LIMIT': 3600,  # 1 hour
            
            # JWT Configuration
            'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32),
            'JWT_EXPIRY_HOURS': int(os.environ.get('JWT_EXPIRY_HOURS', '24')),
            
            # Rate Limiting
            'RATELIMIT_STORAGE_URL': os.environ.get('REDIS_URL', 'memory://'),
            'RATELIMIT_DEFAULT': '100 per hour',
            
            # Security Headers
            'SECURITY_HEADERS': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Content-Security-Policy': (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
                    "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                    "font-src 'self' cdn.jsdelivr.net cdnjs.cloudflare.com; "
                    "img-src 'self' data:;"
                )
            },
            
            # Session Security
            'SESSION_COOKIE_SECURE': os.environ.get('HTTPS_ENABLED', 'False').lower() == 'true',
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hour
            
            # Input Validation
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max request size
            
            # Security Monitoring
            'SECURITY_LOG_LEVEL': os.environ.get('SECURITY_LOG_LEVEL', 'INFO'),
            'FAILED_LOGIN_THRESHOLD': int(os.environ.get('FAILED_LOGIN_THRESHOLD', '10')),
            'IP_BLOCK_DURATION': int(os.environ.get('IP_BLOCK_DURATION', '300')),  # 5 minutes
        }
    
    @staticmethod
    def configure_security(app):
        """Configure Flask app with security settings."""
        config = SecurityConfig.get_security_config()
        
        for key, value in config.items():
            if key != 'SECURITY_HEADERS':
                app.config[key] = value
        
        print("✅ Security configuration applied")
        return app
    
    @staticmethod
    def get_production_checklist():
        """Get production security checklist."""
        return {
            'environment_variables': [
                'SECRET_KEY - Set unique secret key',
                'JWT_SECRET_KEY - Set unique JWT secret',
                'HTTPS_ENABLED=true - Enable HTTPS',
                'REDIS_URL - Set Redis URL for rate limiting'
            ],
            'security_headers': [
                'Content-Security-Policy configured',
                'HTTPS redirect enabled',
                'Secure cookie settings',
                'CSRF protection active'
            ],
            'monitoring': [
                'Security logs configured',
                'Failed login monitoring',
                'Rate limiting active',
                'IP blocking enabled'
            ],
            'authentication': [
                'JWT tokens configured',
                'Session timeout set',
                'Strong password policy',
                'Multi-factor authentication (recommended)'
            ]
        }
