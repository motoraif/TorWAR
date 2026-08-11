from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json
import os
import base64
from cryptography.fernet import Fernet

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean(), nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

class AWSConnection(db.Model):
    __tablename__ = 'aws_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    connection_name = db.Column(db.String(100), nullable=False)
    account_id = db.Column(db.String(12), nullable=False)
    auth_method = db.Column(db.String(20), nullable=False)
    
    # For access keys (encrypted)
    access_key_id = db.Column(db.Text)
    secret_access_key = db.Column(db.Text)
    
    # For IAM role
    role_arn = db.Column(db.String(200))
    external_id = db.Column(db.String(100))
    
    # For STS assume role
    assume_role_arn = db.Column(db.String(200))
    session_name = db.Column(db.String(64))
    
    # Common fields
    region = db.Column(db.String(20), default='us-east-1')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    
    @staticmethod
    def get_encryption_key():
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            os.environ['ENCRYPTION_KEY'] = base64.b64encode(key).decode()
        else:
            key = base64.b64decode(key.encode())
        return key
    
    def encrypt_field(self, value):
        if not value:
            return None
        f = Fernet(self.get_encryption_key())
        return f.encrypt(value.encode()).decode()
    
    def decrypt_field(self, encrypted_value):
        if not encrypted_value:
            return None
        f = Fernet(self.get_encryption_key())
        return f.decrypt(encrypted_value.encode()).decode()
    
    def set_access_key(self, access_key):
        self.access_key_id = self.encrypt_field(access_key)
    
    def set_secret_key(self, secret_key):
        self.secret_access_key = self.encrypt_field(secret_key)
    
    def get_access_key(self):
        return self.decrypt_field(self.access_key_id)
    
    def get_secret_key(self):
        return self.decrypt_field(self.secret_access_key)

class AppVersion(db.Model):
    __tablename__ = 'app_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.Text)
    migration_script = db.Column(db.Text)
    deployed_at = db.Column(db.DateTime, default=datetime.utcnow)
    deployed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    deployer = db.relationship('User', backref='deployed_versions')
    
    def is_active(self):
        return self.active

class AWSAccount(db.Model):
    __tablename__ = 'aws_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.String(12), nullable=False)
    account_name = db.Column(db.String(100))
    region = db.Column(db.String(20), nullable=False)
    profile_name = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'account_id', 'region'),)

class TrustedAdvisorRecommendation(db.Model):
    __tablename__ = 'trusted_advisor_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    aws_account_id = db.Column(db.Integer, db.ForeignKey('aws_accounts.id'), nullable=False)
    check_id = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100))
    pillar = db.Column(db.String(100))
    status = db.Column(db.String(50))
    description = db.Column(db.Text)
    resource_count = db.Column(db.Integer, default=0)
    resources_data = db.Column(db.JSON)
    check_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'check_id': self.check_id,
            'name': self.name,
            'category': self.category,
            'pillar': self.pillar,
            'status': self.status,
            'description': self.description,
            'resource_count': self.resource_count,
            'resources_data': self.resources_data,
            'check_metadata': self.check_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DataSyncLog(db.Model):
    __tablename__ = 'data_sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    aws_account_id = db.Column(db.Integer, db.ForeignKey('aws_accounts.id'), nullable=False)
    sync_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    records_synced = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
