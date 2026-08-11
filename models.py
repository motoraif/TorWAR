import os, bcrypt, redis
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

# Database connections
mongo_client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://mongodb:27017/'))
mongo = mongo_client.torwarta
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, decode_responses=True)

class User:
    def __init__(self, username, email, password_hash):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = datetime.utcnow()
        self._id = None
    
    def save(self):
        result = mongo.users.insert_one({
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at
        })
        self._id = result.inserted_id
        return self
    
    @staticmethod
    def create(username, email, password):
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(username, email, password_hash)
        return user.save()
    
    @staticmethod
    def authenticate(username, password):
        user_data = mongo.users.find_one({'username': username})
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash']):
            user = User(user_data['username'], user_data['email'], user_data['password_hash'])
            user._id = user_data['_id']
            return user
        return None
    
    @staticmethod
    def get_by_id(user_id):
        user_data = mongo.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            user = User(user_data['username'], user_data['email'], user_data['password_hash'])
            user._id = user_data['_id']
            return user
        return None

class WARReport:
    def __init__(self, user_id, workload_id, data):
        self.user_id = user_id
        self.workload_id = workload_id
        self.data = data
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self._id = None
    
    def save(self):
        result = mongo.war_reports.update_one(
            {'user_id': self.user_id, 'workload_id': self.workload_id},
            {'$set': {
                'data': self.data,
                'updated_at': self.updated_at
            }, '$setOnInsert': {
                'user_id': self.user_id,
                'workload_id': self.workload_id,
                'created_at': self.created_at
            }},
            upsert=True
        )
        self._id = result.upserted_id or result.matched_count
        return self
    
    @staticmethod
    def create_or_update(user_id, workload_id, data):
        report = WARReport(user_id, workload_id, data)
        return report.save()
    
    @staticmethod
    def update_answer(user_id, workload_id, answer_data):
        mongo.war_reports.update_one(
            {'user_id': user_id, 'workload_id': workload_id},
            {'$push': {'data.answers': answer_data}, '$set': {'updated_at': datetime.utcnow()}}
        )
    
    @staticmethod
    def get_by_user(user_id):
        return list(mongo.war_reports.find({'user_id': user_id}))

class TARecommendation:
    def __init__(self, user_id, check_id, data):
        self.user_id = user_id
        self.check_id = check_id
        self.data = data
        self.remediation_plan = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self._id = None
    
    def save(self):
        result = mongo.ta_recommendations.update_one(
            {'user_id': self.user_id, 'check_id': self.check_id},
            {'$set': {
                'data': self.data,
                'updated_at': self.updated_at
            }, '$setOnInsert': {
                'user_id': self.user_id,
                'check_id': self.check_id,
                'created_at': self.created_at
            }},
            upsert=True
        )
        self._id = result.upserted_id or result.matched_count
        return self
    
    @staticmethod
    def create_or_update(user_id, data):
        rec = TARecommendation(user_id, data['check_id'], data)
        return rec.save()
    
    @staticmethod
    def get_by_check_id(user_id, check_id):
        return mongo.ta_recommendations.find_one({'user_id': user_id, 'check_id': check_id})
    
    @staticmethod
    def update_remediation_plan(user_id, check_id, plan):
        mongo.ta_recommendations.update_one(
            {'user_id': user_id, 'check_id': check_id},
            {'$set': {'remediation_plan': plan, 'updated_at': datetime.utcnow()}}
        )
    
    @staticmethod
    def get_by_user(user_id):
        return list(mongo.ta_recommendations.find({'user_id': user_id}))

class ReportVersion:
    def __init__(self, user_id, report_type, content, data_snapshot):
        self.user_id = user_id
        self.report_type = report_type
        self.content = content
        self.data_snapshot = data_snapshot
        self.created_at = datetime.utcnow()
        self._id = None
    
    def save(self):
        result = mongo.report_versions.insert_one({
            'user_id': self.user_id,
            'report_type': self.report_type,
            'content': self.content,
            'data_snapshot': self.data_snapshot,
            'created_at': self.created_at
        })
        self._id = result.inserted_id
        return self
    
    @staticmethod
    def create(user_id, report_type, content, data_snapshot):
        version = ReportVersion(user_id, report_type, content, data_snapshot)
        return version.save()
    
    @staticmethod
    def get_by_user(user_id):
        return list(mongo.report_versions.find({'user_id': user_id}).sort('created_at', -1))
    
    @staticmethod
    def get_by_id(version_id):
        data = mongo.report_versions.find_one({'_id': ObjectId(version_id)})
        if data:
            version = ReportVersion(data['user_id'], data['report_type'], data['content'], data['data_snapshot'])
            version._id = data['_id']
            version.created_at = data['created_at']
            return version
        return None
    
    def to_dict(self):
        return {
            'id': str(self._id),
            'report_type': self.report_type,
            'created_at': self.created_at.isoformat(),
            'content_preview': self.content[:200] + '...' if len(self.content) > 200 else self.content
        }
