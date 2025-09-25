import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from database_models import db, User

def create_app():
    app = Flask(__name__)
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'postgresql://torwar:torwar123@localhost/torwar_db')
    
    # Handle Heroku postgres URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'torwar-secret-key-change-in-production')
    app.config['WTF_CSRF_ENABLED'] = True
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    return app, db, migrate

def init_database():
    """Initialize database with tables and default data"""
    from database_models import AppVersion
    
    # Create all tables
    db.create_all()
    
    # Add initial version
    if not AppVersion.query.first():
        initial_version = AppVersion(
            version='1.0.0',
            description='Initial TorWAR release with PostgreSQL integration'
        )
        db.session.add(initial_version)
        db.session.commit()
        print("✅ Database initialized with initial version")
    
    print("✅ Database tables created successfully")
