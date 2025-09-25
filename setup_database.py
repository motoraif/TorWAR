#!/usr/bin/env python3
"""
Database setup script for TorWAR
Creates PostgreSQL database and initializes tables
"""

import os
import sys
import subprocess
from database_config import create_app, init_database

def install_postgresql():
    """Install PostgreSQL if not already installed"""
    try:
        subprocess.run(['psql', '--version'], check=True, capture_output=True)
        print("✅ PostgreSQL is already installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("📦 Installing PostgreSQL...")
        try:
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'postgresql', 'postgresql-contrib', 'python3-psycopg2'], check=True)
            print("✅ PostgreSQL installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install PostgreSQL: {e}")
            return False

def setup_database():
    """Setup PostgreSQL database and user"""
    commands = [
        "sudo -u postgres createuser --interactive --pwprompt torwar",
        "sudo -u postgres createdb -O torwar torwar_db"
    ]
    
    print("🔧 Setting up PostgreSQL database...")
    print("When prompted, enter password: torwar123")
    print("When asked if user should be a superuser, answer 'n'")
    print("When asked if user should create databases, answer 'y'")
    print("When asked if user should create roles, answer 'n'")
    
    for cmd in commands:
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            print(f"⚠️  Command may have failed (might already exist): {cmd}")
    
    print("✅ Database setup completed")

def install_python_dependencies():
    """Install required Python packages"""
    packages = [
        'flask-sqlalchemy',
        'flask-migrate', 
        'flask-user',
        'psycopg2-binary',
        'email-validator'
    ]
    
    print("📦 Installing Python dependencies...")
    for package in packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")

def main():
    print("🚀 TorWAR Database Setup")
    print("=" * 50)
    
    # Install PostgreSQL
    if not install_postgresql():
        sys.exit(1)
    
    # Install Python dependencies
    install_python_dependencies()
    
    # Setup database
    setup_database()
    
    # Initialize Flask app and database
    print("🔧 Initializing database tables...")
    try:
        app, db, migrate, user_manager = create_app()
        
        with app.app_context():
            init_database()
        
        print("✅ Database initialization completed")
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Set environment variable: export DATABASE_URL='postgresql://torwar:torwar123@localhost/torwar_db'")
        print("2. Run the application: python3 app_with_auth.py")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("Please check your PostgreSQL installation and try again")
        sys.exit(1)

if __name__ == '__main__':
    main()
