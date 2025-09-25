#!/usr/bin/env python3
"""
TorWAR Security Configuration Manager
Author: Mohamed Toraif
"""

import os
import secrets
from typing import Dict, Any

class SecurityConfigurator:
    """Dynamic security configuration manager."""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load security configuration from environment."""
        return {
            # Core Security
            'SECRET_KEY': os.getenv('SECRET_KEY') or self._generate_secret_key(),
            'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY') or self._generate_secret_key(),
            
            # Authentication
            'JWT_EXPIRY_HOURS': int(os.getenv('JWT_EXPIRY_HOURS', '24')),
            'SESSION_TIMEOUT': int(os.getenv('SESSION_TIMEOUT', '3600')),
            
            # Rate Limiting
            'RATE_LIMIT_GLOBAL': int(os.getenv('RATE_LIMIT_GLOBAL', '100')),
            'RATE_LIMIT_AUTH': int(os.getenv('RATE_LIMIT_AUTH', '10')),
            'RATE_LIMIT_API': int(os.getenv('RATE_LIMIT_API', '60')),
            
            # Security Thresholds
            'FAILED_LOGIN_THRESHOLD': int(os.getenv('FAILED_LOGIN_THRESHOLD', '10')),
            'IP_BLOCK_DURATION': int(os.getenv('IP_BLOCK_DURATION', '300')),
            'SUSPICIOUS_REQUEST_THRESHOLD': int(os.getenv('SUSPICIOUS_REQUEST_THRESHOLD', '100')),
            
            # HTTPS
            'HTTPS_ENABLED': os.getenv('HTTPS_ENABLED', 'false').lower() == 'true',
            'FORCE_HTTPS': os.getenv('FORCE_HTTPS', 'false').lower() == 'true',
            'SECURE_COOKIES': os.getenv('SECURE_COOKIES', 'false').lower() == 'true',
            
            # CSRF
            'CSRF_TIME_LIMIT': int(os.getenv('CSRF_TIME_LIMIT', '3600')),
            'CSRF_EXEMPT_ENDPOINTS': os.getenv('CSRF_EXEMPT_ENDPOINTS', '').split(','),
            
            # Content Security Policy
            'CSP_DEFAULT_SRC': os.getenv('CSP_DEFAULT_SRC', "'self'"),
            'CSP_SCRIPT_SRC': os.getenv('CSP_SCRIPT_SRC', "'self' 'unsafe-inline' cdn.jsdelivr.net"),
            'CSP_STYLE_SRC': os.getenv('CSP_STYLE_SRC', "'self' 'unsafe-inline' cdn.jsdelivr.net"),
            'CSP_IMG_SRC': os.getenv('CSP_IMG_SRC', "'self' data:"),
            
            # Logging
            'SECURITY_LOG_LEVEL': os.getenv('SECURITY_LOG_LEVEL', 'INFO'),
            'SECURITY_LOG_FILE': os.getenv('SECURITY_LOG_FILE', 'logs/security.log'),
            'AUTH_LOG_FILE': os.getenv('AUTH_LOG_FILE', 'logs/auth.log'),
            
            # Development
            'DEBUG_SECURITY': os.getenv('DEBUG_SECURITY', 'false').lower() == 'true',
            'DISABLE_CSRF_IN_DEV': os.getenv('DISABLE_CSRF_IN_DEV', 'false').lower() == 'true',
        }
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key."""
        return secrets.token_hex(32)
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask-compatible configuration."""
        return {
            'SECRET_KEY': self.config['SECRET_KEY'],
            'WTF_CSRF_ENABLED': not self.config['DISABLE_CSRF_IN_DEV'],
            'WTF_CSRF_TIME_LIMIT': self.config['CSRF_TIME_LIMIT'],
            'SESSION_COOKIE_SECURE': self.config['SECURE_COOKIES'],
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': self.config['SESSION_TIMEOUT'],
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
        }
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers configuration."""
        csp = f"default-src {self.config['CSP_DEFAULT_SRC']}; " \
              f"script-src {self.config['CSP_SCRIPT_SRC']}; " \
              f"style-src {self.config['CSP_STYLE_SRC']}; " \
              f"img-src {self.config['CSP_IMG_SRC']};"
        
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Content-Security-Policy': csp,
        }
        
        if self.config['HTTPS_ENABLED']:
            headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return headers
    
    def get_rate_limits(self) -> Dict[str, Dict[str, int]]:
        """Get rate limiting configuration."""
        return {
            'global': {
                'max_requests': self.config['RATE_LIMIT_GLOBAL'],
                'window': 3600  # 1 hour
            },
            'auth': {
                'max_requests': self.config['RATE_LIMIT_AUTH'],
                'window': 3600  # 1 hour
            },
            'api': {
                'max_requests': self.config['RATE_LIMIT_API'],
                'window': 3600  # 1 hour
            }
        }
    
    def update_config(self, key: str, value: Any) -> bool:
        """Update configuration value."""
        if key in self.config:
            self.config[key] = value
            return True
        return False
    
    def validate_config(self) -> Dict[str, str]:
        """Validate security configuration."""
        issues = {}
        
        # Check secret keys
        if len(self.config['SECRET_KEY']) < 32:
            issues['SECRET_KEY'] = 'Secret key should be at least 32 characters'
        
        if len(self.config['JWT_SECRET_KEY']) < 32:
            issues['JWT_SECRET_KEY'] = 'JWT secret key should be at least 32 characters'
        
        # Check HTTPS settings
        if self.config['SECURE_COOKIES'] and not self.config['HTTPS_ENABLED']:
            issues['SECURE_COOKIES'] = 'Secure cookies require HTTPS to be enabled'
        
        # Check rate limits
        if self.config['RATE_LIMIT_GLOBAL'] < 10:
            issues['RATE_LIMIT_GLOBAL'] = 'Global rate limit too restrictive (minimum 10)'
        
        return issues
    
    def get_environment_template(self) -> str:
        """Generate environment template with current values."""
        template = "# TorWAR Security Configuration\n"
        template += "# Generated configuration template\n\n"
        
        for key, value in self.config.items():
            if isinstance(value, bool):
                value = str(value).lower()
            elif isinstance(value, list):
                value = ','.join(value)
            
            template += f"{key}={value}\n"
        
        return template

# Global configurator
security_config = SecurityConfigurator()
