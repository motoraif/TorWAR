from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import bcrypt
import os

class MongoDB:
    def __init__(self):
        mongo_host = os.getenv('MONGO_HOST', 'localhost')
        mongo_port = int(os.getenv('MONGO_PORT', 27017))
        username = os.getenv('MONGO_USERNAME', 'torwar')
        password = os.getenv('MONGO_PASSWORD', 'torwar123')
        
        self.client = MongoClient(
            host=mongo_host,
            port=mongo_port,
            username=username,
            password=password,
            authSource='admin'
        )
        self.db = self.client.torwar_db
        
    def get_collection(self, name):
        return self.db[name]

# Initialize MongoDB connection
mongo = MongoDB()

class User:
    collection = mongo.get_collection('users')
    
    def __init__(self, username, email, password_hash=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = datetime.utcnow()
        self.is_active = True
        
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        
    def save(self):
        user_data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
        result = self.collection.insert_one(user_data)
        self._id = result.inserted_id
        return self
        
    @classmethod
    def find_by_username(cls, username):
        user_data = cls.collection.find_one({'username': username})
        if user_data:
            user = cls(user_data['username'], user_data['email'], user_data['password_hash'])
            user._id = user_data['_id']
            user.created_at = user_data['created_at']
            user.is_active = user_data['is_active']
            return user
        return None
        
    @classmethod
    def find_by_email(cls, email):
        user_data = cls.collection.find_one({'email': email})
        if user_data:
            user = cls(user_data['username'], user_data['email'], user_data['password_hash'])
            user._id = user_data['_id']
            return user
        return None
        
    def get_id(self):
        return str(self._id)

class AWSConnection:
    collection = mongo.get_collection('aws_connections')
    
    def __init__(self, user_id, profile_name, auth_type='access_key', access_key=None, secret_key=None, 
                 role_arn=None, external_id=None, source_profile_id=None, region='us-east-1'):
        self.user_id = user_id
        self.profile_name = profile_name
        self.auth_type = auth_type  # 'access_key', 'iam_role', 'cross_account'
        self.access_key = access_key
        self.secret_key = secret_key
        self.role_arn = role_arn
        self.external_id = external_id
        self.source_profile_id = source_profile_id  # For IAM role auth
        self.region = region
        self.created_at = datetime.utcnow()
        self.is_active = True
        
    def save(self):
        conn_data = {
            'user_id': self.user_id,
            'profile_name': self.profile_name,
            'auth_type': self.auth_type,
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'role_arn': self.role_arn,
            'external_id': self.external_id,
            'source_profile_id': self.source_profile_id,
            'region': self.region,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
        result = self.collection.insert_one(conn_data)
        self._id = result.inserted_id
        return self
        
    @classmethod
    def find_by_user(cls, user_id):
        connections = []
        for conn_data in cls.collection.find({'user_id': user_id, 'is_active': True}):
            conn = cls(
                conn_data['user_id'], 
                conn_data['profile_name'],
                conn_data.get('auth_type', 'access_key'),
                conn_data.get('access_key'),
                conn_data.get('secret_key'),
                conn_data.get('role_arn'),
                conn_data.get('external_id'),
                conn_data.get('source_profile_id'),
                conn_data['region']
            )
            conn._id = conn_data['_id']
            connections.append(conn)
        return connections
        
    @classmethod
    def find_by_id(cls, connection_id):
        from bson import ObjectId
        conn_data = cls.collection.find_one({'_id': ObjectId(connection_id)})
        if conn_data:
            conn = cls(
                conn_data['user_id'], 
                conn_data['profile_name'],
                conn_data.get('auth_type', 'access_key'),
                conn_data.get('access_key'),
                conn_data.get('secret_key'),
                conn_data.get('role_arn'),
                conn_data.get('external_id'),
                conn_data.get('source_profile_id'),
                conn_data['region']
            )
            conn._id = conn_data['_id']
            return conn
        return None

class Recommendation:
    collection = mongo.get_collection('recommendations')
    archive_collection = mongo.get_collection('recommendations_archive')
    
    def __init__(self, user_id, check_id, name, category, status, description, resources=None, version=None):
        self.user_id = user_id
        self.check_id = check_id
        self.name = name
        self.category = category
        self.status = status
        self.description = description
        self.resources = resources or []
        self.version = version or 1
        self.created_at = datetime.utcnow()
        
    def save(self):
        rec_data = {
            'user_id': self.user_id,
            'check_id': self.check_id,
            'name': self.name,
            'category': self.category,
            'status': self.status,
            'description': self.description,
            'resources': self.resources,
            'version': self.version,
            'created_at': self.created_at
        }
        result = self.collection.insert_one(rec_data)
        self._id = result.inserted_id
        return self
        
    @classmethod
    def archive_and_clear(cls, user_id):
        """Archive current recommendations and clear active collection"""
        # Get current recommendations
        current_recs = list(cls.collection.find({'user_id': user_id}))
        
        if current_recs:
            # Add archive timestamp and move to archive
            archive_timestamp = datetime.utcnow()
            for rec in current_recs:
                rec['archived_at'] = archive_timestamp
                rec['is_archived'] = True
            
            cls.archive_collection.insert_many(current_recs)
        
        # Clear current recommendations
        result = cls.collection.delete_many({'user_id': user_id})
        return len(current_recs), result.deleted_count
        
    @classmethod
    def get_next_version(cls, user_id):
        """Get next version number for user's recommendations"""
        latest = cls.archive_collection.find_one(
            {'user_id': user_id}, 
            sort=[('version', -1)]
        )
        return (latest['version'] + 1) if latest else 1
        
    @classmethod
    def find_by_user(cls, user_id):
        recommendations = []
        for rec_data in cls.collection.find({'user_id': user_id}):
            rec = cls(rec_data['user_id'], rec_data['check_id'], rec_data['name'],
                     rec_data['category'], rec_data['status'], rec_data['description'],
                     rec_data['resources'], rec_data.get('version', 1))
            rec._id = rec_data['_id']
            rec.created_at = rec_data['created_at']
            recommendations.append(rec)
        return recommendations
        
    @classmethod
    def get_archived_versions(cls, user_id):
        """Get list of archived versions for user"""
        pipeline = [
            {'$match': {'user_id': user_id, 'is_archived': True}},
            {'$group': {
                '_id': '$version',
                'count': {'$sum': 1},
                'archived_at': {'$first': '$archived_at'}
            }},
            {'$sort': {'_id': -1}}
        ]
        return list(cls.archive_collection.aggregate(pipeline))
        
    @classmethod
    def get_archived_recommendations(cls, user_id, version):
        """Get archived recommendations for specific version"""
        recommendations = []
        for rec_data in cls.archive_collection.find({'user_id': user_id, 'version': version}):
            rec = cls(rec_data['user_id'], rec_data['check_id'], rec_data['name'],
                     rec_data['category'], rec_data['status'], rec_data['description'],
                     rec_data['resources'], rec_data['version'])
            rec._id = rec_data['_id']
            rec.created_at = rec_data['created_at']
            rec.archived_at = rec_data['archived_at']
            recommendations.append(rec)
        return recommendations
        
    @classmethod
    def delete_by_user(cls, user_id):
        return cls.collection.delete_many({'user_id': user_id})
        
    @classmethod
    def remove_duplicates(cls, user_id):
        """Remove duplicate recommendations for a user based on check_id"""
        pipeline = [
            {'$match': {'user_id': user_id}},
            {'$group': {
                '_id': {'user_id': '$user_id', 'check_id': '$check_id'},
                'docs': {'$push': '$$ROOT'},
                'count': {'$sum': 1}
            }},
            {'$match': {'count': {'$gt': 1}}}
        ]
        
        duplicates = list(cls.collection.aggregate(pipeline))
        removed_count = 0
        
        for dup in duplicates:
            docs = dup['docs']
            # Keep the first document, remove the rest
            for doc in docs[1:]:
                cls.collection.delete_one({'_id': doc['_id']})
                removed_count += 1
                
        return removed_count
