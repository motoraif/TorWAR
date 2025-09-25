#!/usr/bin/env python3
"""
TorWAR Security Middleware
Author: Mohamed Toraif
"""

from flask import request, jsonify, session, g
import time
import hashlib
import os
from datetime import datetime, timedelta

class SecurityMiddleware:
    """Security middleware for request processing."""
    
    def __init__(self):
        self.blocked_ips = set()
        self.suspicious_requests = {}
        self.request_signatures = {}
    
    def init_app(self, app):
        """Initialize security middleware with Flask app."""
        
        @app.before_request
        def security_before_request():
            """Security checks before each request."""
            
            # Get client IP
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            g.client_ip = client_ip
            
            # Check blocked IPs
            if client_ip in self.blocked_ips:
                return jsonify({'error': 'Access denied'}), 403
            
            # Check for suspicious patterns
            if self._is_suspicious_request():
                self._log_suspicious_activity()
                return jsonify({'error': 'Suspicious activity detected'}), 429
            
            # Request signature for replay attack prevention
            if request.method in ['POST', 'PUT', 'DELETE']:
                signature = self._generate_request_signature()
                if signature in self.request_signatures:
                    # Check if it's a recent duplicate (within 5 minutes)
                    if time.time() - self.request_signatures[signature] < 300:
                        return jsonify({'error': 'Duplicate request detected'}), 409
                
                self.request_signatures[signature] = time.time()
                
                # Clean old signatures
                cutoff = time.time() - 300
                self.request_signatures = {
                    sig: timestamp for sig, timestamp in self.request_signatures.items()
                    if timestamp > cutoff
                }
        
        @app.after_request
        def security_after_request(response):
            """Security processing after each request."""
            
            # Log failed authentication attempts
            if response.status_code == 401:
                self._log_failed_auth()
            
            # Add security headers (if not already added)
            if 'X-Content-Type-Options' not in response.headers:
                response.headers['X-Content-Type-Options'] = 'nosniff'
            
            return response
        
        print("✅ Security middleware initialized")
    
    def _is_suspicious_request(self) -> bool:
        """Check if request shows suspicious patterns."""
        client_ip = g.client_ip
        
        # Check request frequency
        now = time.time()
        if client_ip not in self.suspicious_requests:
            self.suspicious_requests[client_ip] = []
        
        # Clean old requests (last 60 seconds)
        self.suspicious_requests[client_ip] = [
            timestamp for timestamp in self.suspicious_requests[client_ip]
            if now - timestamp < 60
        ]
        
        # Add current request
        self.suspicious_requests[client_ip].append(now)
        
        # Check if too many requests
        if len(self.suspicious_requests[client_ip]) > 100:  # More than 100 requests per minute
            return True
        
        # Check for common attack patterns
        user_agent = request.headers.get('User-Agent', '').lower()
        suspicious_agents = ['sqlmap', 'nikto', 'nmap', 'masscan', 'nessus']
        if any(agent in user_agent for agent in suspicious_agents):
            return True
        
        # Check for SQL injection patterns in query parameters
        query_string = request.query_string.decode('utf-8', errors='ignore').lower()
        sql_patterns = ['union select', 'drop table', 'insert into', 'delete from', '1=1', '1\'=\'1']
        if any(pattern in query_string for pattern in sql_patterns):
            return True
        
        return False
    
    def _generate_request_signature(self) -> str:
        """Generate unique signature for request."""
        # Include method, path, and body hash
        content = f"{request.method}:{request.path}"
        
        if request.data:
            content += f":{hashlib.md5(request.data).hexdigest()}"
        
        # Include client IP to prevent cross-client replay
        content += f":{g.client_ip}"
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _log_suspicious_activity(self):
        """Log suspicious activity."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'client_ip': g.client_ip,
            'method': request.method,
            'path': request.path,
            'user_agent': request.headers.get('User-Agent', ''),
            'query_string': request.query_string.decode('utf-8', errors='ignore')
        }
        
        # Log to file (in production, use proper logging system)
        log_file = os.path.join('logs', 'security.log')
        os.makedirs('logs', exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(f"SUSPICIOUS: {log_entry}\n")
    
    def _log_failed_auth(self):
        """Log failed authentication attempts."""
        client_ip = g.client_ip
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'client_ip': client_ip,
            'method': request.method,
            'path': request.path,
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        # Log to file
        log_file = os.path.join('logs', 'auth_failures.log')
        os.makedirs('logs', exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(f"AUTH_FAIL: {log_entry}\n")
        
        # Track failed attempts per IP
        if client_ip not in self.suspicious_requests:
            self.suspicious_requests[client_ip] = []
        
        # If too many failed attempts, temporarily block IP
        failed_attempts = len([
            timestamp for timestamp in self.suspicious_requests[client_ip]
            if time.time() - timestamp < 300  # Last 5 minutes
        ])
        
        if failed_attempts > 10:  # More than 10 failed attempts in 5 minutes
            self.blocked_ips.add(client_ip)
            print(f"⚠️ Temporarily blocked IP: {client_ip}")
    
    def unblock_ip(self, ip_address: str) -> bool:
        """Manually unblock an IP address."""
        if ip_address in self.blocked_ips:
            self.blocked_ips.remove(ip_address)
            return True
        return False
    
    def get_security_stats(self) -> dict:
        """Get security statistics."""
        return {
            'blocked_ips': len(self.blocked_ips),
            'active_request_signatures': len(self.request_signatures),
            'monitored_ips': len(self.suspicious_requests),
            'blocked_ip_list': list(self.blocked_ips)
        }

# Global security middleware
security_middleware = SecurityMiddleware()
