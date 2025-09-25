#!/usr/bin/env python3
"""
TorWAR Database Models
Author: Mohamed Toraif
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import uuid

db = SQLAlchemy()

class Workload(db.Model):
    """AWS Well-Architected Workload model."""
    __tablename__ = 'workloads'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    aws_account_id = db.Column(db.String(20))
    aws_region = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reports = db.relationship('Report', backref='workload', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'aws_account_id': self.aws_account_id,
            'aws_region': self.aws_region,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'report_count': len(self.reports)
        }

class Report(db.Model):
    """Well-Architected Report model."""
    __tablename__ = 'reports'
    
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    workload_id = db.Column(db.String(50), db.ForeignKey('workloads.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    user_notes = db.Column(db.Text)
    report_data = db.Column(db.JSON)  # Store complete report as JSON
    risk_summary = db.Column(db.JSON)  # Cache risk counts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'workload_id': self.workload_id,
            'name': self.name,
            'user_notes': self.user_notes,
            'risk_summary': self.risk_summary,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RecommendationCache(db.Model):
    """Cache for Trusted Advisor recommendations."""
    __tablename__ = 'recommendation_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(100), unique=True, nullable=False)
    data = db.Column(db.JSON)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def get_cached(cls, key):
        """Get cached data if not expired."""
        cache_entry = cls.query.filter_by(cache_key=key).first()
        if cache_entry and cache_entry.expires_at > datetime.utcnow():
            return cache_entry.data
        return None
    
    @classmethod
    def set_cache(cls, key, data, ttl_seconds=3600):
        """Set cache data with TTL."""
        expires_at = datetime.utcnow().timestamp() + ttl_seconds
        expires_at = datetime.fromtimestamp(expires_at)
        
        cache_entry = cls.query.filter_by(cache_key=key).first()
        if cache_entry:
            cache_entry.data = data
            cache_entry.expires_at = expires_at
        else:
            cache_entry = cls(cache_key=key, data=data, expires_at=expires_at)
            db.session.add(cache_entry)
        
        db.session.commit()

class UserSession(db.Model):
    """User session tracking."""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.String(50), primary_key=True)
    aws_profile = db.Column(db.String(50))
    aws_region = db.Column(db.String(20))
    aws_account_id = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'aws_profile': self.aws_profile,
            'aws_region': self.aws_region,
            'aws_account_id': self.aws_account_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }
