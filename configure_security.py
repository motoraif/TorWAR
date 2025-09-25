#!/usr/bin/env python3
"""
TorWAR Security Configuration CLI
Author: Mohamed Toraif
"""

import argparse
import sys
from security_configurator import security_config

def show_current_config():
    """Show current security configuration."""
    print("🔐 Current Security Configuration")
    print("=" * 40)
    
    config = security_config.config
    
    print("\n📋 Core Security:")
    print(f"  Secret Key Length: {len(config['SECRET_KEY'])} chars")
    print(f"  JWT Secret Length: {len(config['JWT_SECRET_KEY'])} chars")
    
    print("\n🔑 Authentication:")
    print(f"  JWT Expiry: {config['JWT_EXPIRY_HOURS']} hours")
    print(f"  Session Timeout: {config['SESSION_TIMEOUT']} seconds")
    
    print("\n⏱️ Rate Limiting:")
    print(f"  Global: {config['RATE_LIMIT_GLOBAL']} req/hour")
    print(f"  Auth: {config['RATE_LIMIT_AUTH']} req/hour")
    print(f"  API: {config['RATE_LIMIT_API']} req/hour")
    
    print("\n🛡️ Security Thresholds:")
    print(f"  Failed Login Threshold: {config['FAILED_LOGIN_THRESHOLD']}")
    print(f"  IP Block Duration: {config['IP_BLOCK_DURATION']} seconds")
    
    print("\n🔒 HTTPS Settings:")
    print(f"  HTTPS Enabled: {config['HTTPS_ENABLED']}")
    print(f"  Force HTTPS: {config['FORCE_HTTPS']}")
    print(f"  Secure Cookies: {config['SECURE_COOKIES']}")
    
    print("\n🛡️ CSRF Protection:")
    print(f"  CSRF Time Limit: {config['CSRF_TIME_LIMIT']} seconds")
    print(f"  Exempt Endpoints: {len(config['CSRF_EXEMPT_ENDPOINTS'])}")

def validate_config():
    """Validate current security configuration."""
    print("🔍 Validating Security Configuration")
    print("=" * 40)
    
    issues = security_config.validate_config()
    
    if not issues:
        print("✅ All security settings are valid!")
        return True
    else:
        print("❌ Configuration issues found:")
        for key, issue in issues.items():
            print(f"  - {key}: {issue}")
        return False

def generate_secrets():
    """Generate new secret keys."""
    print("🔑 Generating New Secret Keys")
    print("=" * 40)
    
    import secrets
    
    secret_key = secrets.token_hex(32)
    jwt_secret = secrets.token_hex(32)
    
    print(f"SECRET_KEY={secret_key}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    
    print("\n💡 Add these to your .env file")

def create_env_template():
    """Create environment template file."""
    print("📄 Creating Environment Template")
    print("=" * 40)
    
    template = security_config.get_environment_template()
    
    with open('.env.template', 'w') as f:
        f.write(template)
    
    print("✅ Template created: .env.template")
    print("💡 Copy to .env and customize for your environment")

def configure_production():
    """Configure for production environment."""
    print("🚀 Configuring for Production")
    print("=" * 40)
    
    # Update production settings
    security_config.update_config('HTTPS_ENABLED', True)
    security_config.update_config('FORCE_HTTPS', True)
    security_config.update_config('SECURE_COOKIES', True)
    security_config.update_config('DEBUG_SECURITY', False)
    security_config.update_config('DISABLE_CSRF_IN_DEV', False)
    
    # Stricter rate limits
    security_config.update_config('RATE_LIMIT_AUTH', 5)
    security_config.update_config('FAILED_LOGIN_THRESHOLD', 5)
    
    print("✅ Production configuration applied")
    print("\n📋 Production Settings:")
    print("  - HTTPS enforced")
    print("  - Secure cookies enabled")
    print("  - Stricter rate limits")
    print("  - Debug disabled")
    
    # Validate production config
    issues = security_config.validate_config()
    if issues:
        print("\n⚠️ Production issues to resolve:")
        for key, issue in issues.items():
            print(f"  - {key}: {issue}")

def configure_development():
    """Configure for development environment."""
    print("🛠️ Configuring for Development")
    print("=" * 40)
    
    # Update development settings
    security_config.update_config('HTTPS_ENABLED', False)
    security_config.update_config('FORCE_HTTPS', False)
    security_config.update_config('SECURE_COOKIES', False)
    security_config.update_config('DEBUG_SECURITY', True)
    
    # Relaxed rate limits
    security_config.update_config('RATE_LIMIT_GLOBAL', 1000)
    security_config.update_config('RATE_LIMIT_AUTH', 50)
    security_config.update_config('FAILED_LOGIN_THRESHOLD', 20)
    
    print("✅ Development configuration applied")
    print("\n📋 Development Settings:")
    print("  - HTTPS disabled")
    print("  - Relaxed rate limits")
    print("  - Debug enabled")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description='TorWAR Security Configuration Tool')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Show config command
    subparsers.add_parser('show', help='Show current configuration')
    
    # Validate config command
    subparsers.add_parser('validate', help='Validate configuration')
    
    # Generate secrets command
    subparsers.add_parser('secrets', help='Generate new secret keys')
    
    # Create template command
    subparsers.add_parser('template', help='Create environment template')
    
    # Environment presets
    subparsers.add_parser('production', help='Configure for production')
    subparsers.add_parser('development', help='Configure for development')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'show':
        show_current_config()
    elif args.command == 'validate':
        valid = validate_config()
        sys.exit(0 if valid else 1)
    elif args.command == 'secrets':
        generate_secrets()
    elif args.command == 'template':
        create_env_template()
    elif args.command == 'production':
        configure_production()
    elif args.command == 'development':
        configure_development()

if __name__ == "__main__":
    main()
