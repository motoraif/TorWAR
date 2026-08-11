import os
from datetime import timedelta

class Config:
    """Centralized configuration management"""
    
    # Database
    DB_HOST = os.getenv('DB_HOST', 'db')
    DB_NAME = os.getenv('DB_NAME', 'torwar_db')
    DB_USER = os.getenv('DB_USER', 'torwar')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'torwar123')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'torwar-dev-key-change-in-production')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # AWS
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_PROFILE = os.getenv('AWS_PROFILE')
    
    # Application
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = ['SECRET_KEY']
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required config: {missing}")
        return True
