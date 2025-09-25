#!/usr/bin/env python3
"""
TorWAR Database Service Layer
Author: Mohamed Toraif
"""

from models import db, Workload, Report, RecommendationCache, UserSession
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class DatabaseService:
    """Service layer for database operations."""
    
    @staticmethod
    def init_db(app):
        """Initialize database with app context."""
        db.init_app(app)
        with app.app_context():
            db.create_all()
            print("✅ Database initialized")
    
    # Workload operations
    @staticmethod
    def create_workload(workload_id: str, name: str, description: str = "", 
                       aws_account_id: str = "", aws_region: str = "") -> Workload:
        """Create a new workload."""
        workload = Workload(
            id=workload_id,
            name=name,
            description=description,
            aws_account_id=aws_account_id,
            aws_region=aws_region
        )
        db.session.add(workload)
        db.session.commit()
        return workload
    
    @staticmethod
    def get_workload(workload_id: str) -> Optional[Workload]:
        """Get workload by ID."""
        return Workload.query.get(workload_id)
    
    @staticmethod
    def get_workloads(aws_account_id: str = None) -> List[Workload]:
        """Get all workloads, optionally filtered by account."""
        query = Workload.query
        if aws_account_id:
            query = query.filter_by(aws_account_id=aws_account_id)
        return query.order_by(Workload.updated_at.desc()).all()
    
    @staticmethod
    def update_workload(workload_id: str, **kwargs) -> Optional[Workload]:
        """Update workload fields."""
        workload = Workload.query.get(workload_id)
        if workload:
            for key, value in kwargs.items():
                if hasattr(workload, key):
                    setattr(workload, key, value)
            workload.updated_at = datetime.utcnow()
            db.session.commit()
        return workload
    
    # Report operations
    @staticmethod
    def create_report(workload_id: str, name: str, report_data: Dict, 
                     user_notes: str = "") -> Report:
        """Create a new report."""
        # Calculate risk summary
        risk_summary = DatabaseService._calculate_risk_summary(report_data)
        
        report = Report(
            workload_id=workload_id,
            name=name,
            user_notes=user_notes,
            report_data=report_data,
            risk_summary=risk_summary
        )
        db.session.add(report)
        db.session.commit()
        return report
    
    @staticmethod
    def get_report(report_id: str) -> Optional[Report]:
        """Get report by ID."""
        return Report.query.get(report_id)
    
    @staticmethod
    def get_reports(workload_id: str = None) -> List[Report]:
        """Get reports, optionally filtered by workload."""
        query = Report.query
        if workload_id:
            query = query.filter_by(workload_id=workload_id)
        return query.order_by(Report.created_at.desc()).all()
    
    @staticmethod
    def delete_report(report_id: str) -> bool:
        """Delete a report."""
        report = Report.query.get(report_id)
        if report:
            db.session.delete(report)
            db.session.commit()
            return True
        return False
    
    # Cache operations
    @staticmethod
    def get_cached_data(key: str) -> Optional[Dict]:
        """Get cached data."""
        return RecommendationCache.get_cached(key)
    
    @staticmethod
    def set_cached_data(key: str, data: Dict, ttl_seconds: int = 3600):
        """Set cached data."""
        RecommendationCache.set_cache(key, data, ttl_seconds)
    
    @staticmethod
    def clear_cache(pattern: str = None):
        """Clear cache entries."""
        if pattern:
            RecommendationCache.query.filter(
                RecommendationCache.cache_key.like(f'%{pattern}%')
            ).delete()
        else:
            RecommendationCache.query.delete()
        db.session.commit()
    
    # Session operations
    @staticmethod
    def create_session(session_id: str, aws_profile: str, aws_region: str, 
                      aws_account_id: str) -> UserSession:
        """Create or update user session."""
        session = UserSession.query.get(session_id)
        if session:
            session.aws_profile = aws_profile
            session.aws_region = aws_region
            session.aws_account_id = aws_account_id
            session.last_activity = datetime.utcnow()
        else:
            session = UserSession(
                id=session_id,
                aws_profile=aws_profile,
                aws_region=aws_region,
                aws_account_id=aws_account_id
            )
            db.session.add(session)
        
        db.session.commit()
        return session
    
    @staticmethod
    def cleanup_old_sessions(days: int = 7):
        """Clean up old sessions."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        UserSession.query.filter(UserSession.last_activity < cutoff).delete()
        db.session.commit()
    
    # Helper methods
    @staticmethod
    def _calculate_risk_summary(report_data: Dict) -> Dict:
        """Calculate risk summary from report data."""
        risk_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'NONE': 0}
        
        if 'pillar_data' in report_data:
            for pillar_data in report_data['pillar_data'].values():
                if 'questions' in pillar_data:
                    for question in pillar_data['questions']:
                        risk = question.get('Risk', 'NONE')
                        risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        return risk_counts
    
    @staticmethod
    def get_database_stats() -> Dict:
        """Get database statistics."""
        return {
            'workloads': Workload.query.count(),
            'reports': Report.query.count(),
            'cache_entries': RecommendationCache.query.count(),
            'active_sessions': UserSession.query.filter(
                UserSession.last_activity > datetime.utcnow() - timedelta(hours=24)
            ).count()
        }
