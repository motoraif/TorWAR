from database_models import db
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from cryptography.fernet import Fernet
import os
import base64

class AWSConnection(db.Model):
    __tablename__ = 'aws_connections'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, db.ForeignKey('users.id'), nullable=False)
    connection_name = Column(String(100), nullable=False)
    account_id = Column(String(12), nullable=False)
    auth_method = Column(String(20), nullable=False)  # 'access_keys', 'iam_role', 'sts_assume'
    
    # For access keys (encrypted)
    access_key_id = Column(Text)
    secret_access_key = Column(Text)
    
    # For IAM role
    role_arn = Column(String(200))
    external_id = Column(String(100))
    
    # For STS assume role
    assume_role_arn = Column(String(200))
    session_name = Column(String(64))
    
    # Common fields
    region = Column(String(20), default='us-east-1')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    
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
