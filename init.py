#!/usr/bin/env python3
import os, time, sys
from pymongo import MongoClient
import redis

def wait_for_services():
    """Wait for MongoDB and Redis to be ready"""
    print("🔄 Waiting for services to be ready...")
    
    # Wait for MongoDB
    max_retries = 30
    for i in range(max_retries):
        try:
            mongo = MongoClient('mongodb://mongodb:27017/', serverSelectionTimeoutMS=2000)
            mongo.server_info()
            print("✅ MongoDB ready")
            break
        except Exception as e:
            if i == max_retries - 1:
                print(f"❌ MongoDB failed to start: {e}")
                sys.exit(1)
            print(f"⏳ Waiting for MongoDB... ({i+1}/{max_retries})")
            time.sleep(2)
    
    # Wait for Redis
    for i in range(max_retries):
        try:
            r = redis.Redis(host='redis', port=6379)
            r.ping()
            print("✅ Redis ready")
            break
        except Exception as e:
            if i == max_retries - 1:
                print(f"❌ Redis failed to start: {e}")
                sys.exit(1)
            print(f"⏳ Waiting for Redis... ({i+1}/{max_retries})")
            time.sleep(2)

def init_database():
    """Initialize database with indexes and default data"""
    print("🗄️  Initializing database...")
    
    try:
        mongo = MongoClient('mongodb://mongodb:27017/')
        db = mongo.torwarta
        
        # Create collections and indexes
        collections = {
            'accounts': [('profile_name', 1)],
            'workloads': [('account_id', 1), ('name', 1), ('region', 1)],
            'reports': [('account_id', 1), ('created_at', -1), ('version', -1)],
            'questions': [('workload_id', 1)],
            'ta_recommendations': [('account_id', 1)],
            'answers': [('workload_id', 1), ('question_id', 1)]
        }
        
        for collection_name, indexes in collections.items():
            collection = db[collection_name]
            for index in indexes:
                if isinstance(index, tuple):
                    collection.create_index([index])
                else:
                    collection.create_index(index)
        
        # Create unique indexes
        db.accounts.create_index("profile_name", unique=True)
        
        # Create default admin user
        if not db.users.find_one({"username": "admin"}):
            db.users.insert_one({
                "username": "admin",
                "password": "password",
                "role": "admin",
                "created_at": "2025-01-01T00:00:00Z"
            })
            print("👤 Default admin user created")
        
        print("✅ Database initialized with indexes")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

def setup_cache():
    """Setup Redis cache with default configurations"""
    print("🚀 Setting up cache...")
    
    try:
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        # Set cache TTL configurations
        cache_config = {
            'cache:ttl:ta_recommendations': 3600,  # 1 hour
            'cache:ttl:war_questions': 1800,       # 30 minutes
            'cache:ttl:reports': 86400,            # 24 hours
            'cache:ttl:accounts': 7200             # 2 hours
        }
        
        for key, ttl in cache_config.items():
            r.set(key, ttl)
        
        print("✅ Cache configured")
        
    except Exception as e:
        print(f"❌ Cache setup failed: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = ['/app/data', '/app/logs', '/app/uploads']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Directories created")

if __name__ == '__main__':
    print("🚀 TorWARTA Initialization Starting...")
    print("=" * 50)
    
    create_directories()
    wait_for_services()
    init_database()
    setup_cache()
    
    print("=" * 50)
    print("✅ TorWARTA initialization complete!")
    print("🌐 Application ready to start...")
    print("📊 Dashboard: http://localhost")
    print("🔐 Login: admin / password")
