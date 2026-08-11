#!/usr/bin/env python3
import time
from pymongo import MongoClient
import redis

# Wait for services
print("Waiting for services...")
time.sleep(10)

try:
    mongo = MongoClient('mongodb://mongodb:27017/')
    mongo.server_info()
    print("MongoDB ready")
except:
    print("MongoDB not ready, continuing anyway")

try:
    r = redis.Redis(host='redis', port=6379)
    r.ping()
    print("Redis ready")
except:
    print("Redis not ready, continuing anyway")

# Start app
print("Starting TorWARTA...")
import app
app.app.run(host='0.0.0.0', port=5001, debug=False)
