#!/usr/bin/env python3
"""Database initialization script for TorWAR"""

import os
import time
import sqlalchemy
from database_config import create_app, init_database

def wait_for_db():
    """Wait for database to be ready"""
    max_retries = 30
    for i in range(max_retries):
        try:
            app, db_instance, migrate = create_app()
            with app.app_context():
                # Test connection
                db_instance.engine.execute(sqlalchemy.text('SELECT 1'))
            print("✅ Database connection established")
            return app, db_instance
        except Exception as e:
            print(f"⏳ Waiting for database... ({i+1}/{max_retries}): {e}")
            time.sleep(2)
    
    raise Exception("❌ Could not connect to database after 60 seconds")

def initialize_database():
    """Initialize database with tables and default data"""
    try:
        app, db_instance = wait_for_db()
        
        with app.app_context():
            print("🔧 Creating database tables...")
            init_database()
            print("✅ Database initialization completed")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    initialize_database()
