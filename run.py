#!/usr/bin/env python3
import time
from pymongo import MongoClient
import redis

# Wait for services
print("🚀 Starting TorWARTA...")
time.sleep(5)

# Initialize database
try:
    mongo = MongoClient('mongodb://mongodb:27017/')
    db = mongo.torwarta
    
    # Create indexes
    db.accounts.create_index("profile_name", unique=True)
    db.workloads.create_index([("account_id", 1), ("name", 1)])
    db.reports.create_index([("account_id", 1), ("created_at", -1)])
    
    print("✅ Database initialized")
except Exception as e:
    print(f"⚠️  Database init warning: {e}")

# Start app
from app import app
print("🌐 TorWARTA ready at http://localhost")
app.run(host='0.0.0.0', port=5001, debug=False)
