#!/usr/bin/env python3
import os
import time
import psycopg2
from sqlalchemy import create_engine, text
from database_models import db, User, TrustedAdvisorRecommendation

def wait_for_db(max_retries=30):
    """Wait for database to be ready"""
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'db'),
                database=os.getenv('DB_NAME', 'torwar_db'),
                user=os.getenv('DB_USER', 'torwar'),
                password=os.getenv('DB_PASSWORD', 'torwar123')
            )
            conn.close()
            return True
        except psycopg2.OperationalError:
            time.sleep(2)
    return False

def init_database(app):
    """Initialize database with proper error handling"""
    if not wait_for_db():
        raise Exception("Database not ready after 60 seconds")
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Test database connection
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            
            print("✅ Database initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            raise
