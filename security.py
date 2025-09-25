#!/usr/bin/env python3
"""
TorWAR Security Module
Author: Mohamed Toraif
"""

from flask import request, jsonify, session, abort
from flask_wtf.csrf import CSRFProtect
from functools import wraps
import time
import hashlib
import secrets
import re
from typing import Dict, List, Optional

class SecurityManager:
    """Comprehensive security management for TorWAR."""
    
    def __init__(self):
        self.rate_limits = {}
        self.failed_attempts = {}
        self.csrf = CSRFProtect()
    
    def init_app(self, app):
        """Initialize security with Flask app."""
        # CSRF Protection
        self.csrf.init_app(app)
        
        # Security headers
        @app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; font-src 'self' cdn.jsdelivr.net cdnjs.cloudflare.com; img-src 'self' data:;"
            return response
        
        print("✅ Security headers configured")
    
    def rate_limit(self, max_requests=60, window=60):
        """Rate limiting decorator."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                key = f"{func.__name__}:{client_ip}"
                
                now = time.time()
                
                # Clean old entries
                if key in self.rate_limits:
                    self.rate_limits[key] = [
                        timestamp for timestamp in self.rate_limits[key]
                        if now - timestamp < window
                    ]
                else:
                    self.rate_limits[key] = []
                
                # Check rate limit
                if len(self.rate_limits[key]) >= max_requests:
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                
                # Add current request
                self.rate_limits[key].append(now)
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_auth(self, func):
        """Require AWS authentication."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'aws_authenticated' not in session or not session.get('aws_authenticated'):
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return abort(401)
            return func(*args, **kwargs)
        return wrapper
    
    def validate_input(self, data: Dict, rules: Dict) -> Dict:
        """Validate input data against rules."""
        errors = {}
        
        for field, rule in rules.items():
            value = data.get(field)
            
            # Required check
            if rule.get('required', False) and not value:
                errors[field] = 'This field is required'
                continue
            
            if value is None:
                continue
            
            # Type check
            expected_type = rule.get('type')
            if expected_type and not isinstance(value, expected_type):
                errors[field] = f'Expected {expected_type.__name__}'
                continue
            
            # Length check
            if isinstance(value, str):
                min_len = rule.get('min_length', 0)
                max_len = rule.get('max_length', 10000)
                if len(value) < min_len:
                    errors[field] = f'Minimum length is {min_len}'
                elif len(value) > max_len:
                    errors[field] = f'Maximum length is {max_len}'
            
            # Pattern check
            pattern = rule.get('pattern')
            if pattern and isinstance(value, str):
                if not re.match(pattern, value):
                    errors[field] = 'Invalid format'
            
            # Custom validator
            validator = rule.get('validator')
            if validator and callable(validator):
                try:
                    validator(value)
                except ValueError as e:
                    errors[field] = str(e)
        
        return errors
    
    def sanitize_input(self, data: str) -> str:
        """Sanitize input to prevent XSS."""
        if not isinstance(data, str):
            return data
        
        # Basic XSS prevention
        data = data.replace('<script', '&lt;script')
        data = data.replace('</script>', '&lt;/script&gt;')
        data = data.replace('javascript:', 'javascript&#58;')
        data = data.replace('on', '&#111;n')  # Prevent onclick, onload, etc.
        
        return data
    
    def generate_session_token(self) -> str:
        """Generate secure session token."""
        return secrets.token_urlsafe(32)
    
    def hash_password(self, password: str) -> str:
        """Hash password securely."""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{pwd_hash.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            salt, pwd_hash = hashed.split(':')
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == pwd_hash
        except:
            return False

# Global security manager
security = SecurityManager()
