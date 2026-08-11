from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

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
    
    # Relationships
    aws_accounts = db.relationship('AWSAccount', backref='user', lazy=True, cascade='all, delete-orphan')
    workloads = db.relationship('Workload', backref='user', lazy=True, cascade='all, delete-orphan')
    recommendations = db.relationship('TrustedAdvisorRecommendation', backref='user', lazy=True)
    
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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = db.Column(db.DateTime)
    
    # Relationships
    recommendations = db.relationship('TrustedAdvisorRecommendation', backref='aws_account', lazy=True)
    sync_logs = db.relationship('DataSyncLog', backref='aws_account', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'account_id', 'region'),)

class TrustedAdvisorRecommendation(db.Model):
    """Trusted Advisor Recommendation model."""
    __tablename__ = 'trusted_advisor_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    aws_account_id = db.Column(db.Integer, db.ForeignKey('aws_accounts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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
    """Data synchronization log model."""
    __tablename__ = 'data_sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    aws_account_id = db.Column(db.Integer, db.ForeignKey('aws_accounts.id'), nullable=False)
    sync_type = db.Column(db.String(50), nullable=False)  # 'trusted_advisor', etc.
    status = db.Column(db.String(50), nullable=False)  # 'in_progress', 'success', 'error'
    records_synced = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class Workload(db.Model):
    __tablename__ = 'workloads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    aws_account_id = db.Column(db.Integer, db.ForeignKey('aws_accounts.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    environment = db.Column(db.String(20))  # dev, staging, prod
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviews = db.relationship('WellArchitectedReview', backref='workload', lazy=True, cascade='all, delete-orphan')
    
    aws_account = db.relationship('AWSAccount', backref='workloads')

class WellArchitectedReview(db.Model):
    __tablename__ = 'well_architected_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    workload_id = db.Column(db.Integer, db.ForeignKey('workloads.id'), nullable=False)
    review_name = db.Column(db.String(100), nullable=False)
    pillar = db.Column(db.String(50))  # operational_excellence, security, reliability, etc.
    status = db.Column(db.String(20), default='in_progress')
    score = db.Column(db.Float)
    answers_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TrustedAdvisorRecommendation(db.Model):
    __tablename__ = 'trusted_advisor_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    aws_account_id = db.Column(db.Integer, db.ForeignKey('aws_accounts.id'), nullable=False)
    check_id = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    pillar = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False)  # ok, warning, error
    description = db.Column(db.Text)
    resource_count = db.Column(db.Integer, default=0)
    resources_data = db.Column(db.JSON)
    check_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('aws_account_id', 'check_id'),)

class DataSyncLog(db.Model):
    __tablename__ = 'data_sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    aws_account_id = db.Column(db.Integer, db.ForeignKey('aws_accounts.id'), nullable=False)
    sync_type = db.Column(db.String(50), nullable=False)  # trusted_advisor, well_architected
    status = db.Column(db.String(20), nullable=False)  # success, error, in_progress
    records_synced = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    aws_account = db.relationship('AWSAccount', backref='sync_logs')

class AppVersion(db.Model):
    __tablename__ = 'app_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.Text)
    migration_script = db.Column(db.Text)
    deployed_at = db.Column(db.DateTime, default=datetime.utcnow)
    deployed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    deployer = db.relationship('User', backref='deployed_versions')

class SavedReport(db.Model):
    __tablename__ = 'saved_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workload_id = db.Column(db.String(255), nullable=False)
    workload_name = db.Column(db.String(255), nullable=False)
    report_data = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='saved_reports')
