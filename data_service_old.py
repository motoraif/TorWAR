from datetime import datetime
from database_models import db, AWSAccount, TrustedAdvisorRecommendation, DataSyncLog
from trusted_advisor_helper import get_all_trusted_advisor_recommendations

class DataService:
    def __init__(self):
        pass
    
    def get_or_create_aws_account(self, user_id, account_id, region):
        """Get or create AWS account record"""
        aws_account = AWSAccount.query.filter_by(
            user_id=user_id,
            account_id=account_id,
            region=region
        ).first()
        
        if not aws_account:
            aws_account = AWSAccount(
                user_id=user_id,
                account_id=account_id,
                region=region,
                account_name=f"Account {account_id}",
                is_active=True
            )
            db.session.add(aws_account)
            db.session.commit()
        
        return aws_account
    
    def sync_trusted_advisor_data(self, user_id, account_id, region):
        """Sync Trusted Advisor data from AWS API to database"""
        aws_account = self.get_or_create_aws_account(user_id, account_id, region)
        
        # Clear any stuck "in_progress" sync logs first
        stuck_syncs = DataSyncLog.query.filter_by(
            aws_account_id=aws_account.id,
            sync_type='trusted_advisor',
            status='in_progress'
        ).all()
        
        for stuck_sync in stuck_syncs:
            stuck_sync.status = 'error'
            stuck_sync.error_message = 'Sync was interrupted'
        
        db.session.commit()
        
        # Create new sync log
        sync_log = DataSyncLog(
            aws_account_id=aws_account.id,
            sync_type='trusted_advisor',
            status='in_progress'
        )
        db.session.add(sync_log)
        db.session.commit()
        
        try:
            print(f"🔄 Syncing Trusted Advisor data for {account_id} in {region}")
            recommendations_data = get_all_trusted_advisor_recommendations()
            
            if 'error' in recommendations_data:
                raise Exception(recommendations_data['error'])
            
            recommendations = recommendations_data.get('recommendations', [])
            synced_count = 0
            
            for rec in recommendations:
                existing = TrustedAdvisorRecommendation.query.filter_by(
                    aws_account_id=aws_account.id,
                    check_id=rec.get('id', rec.get('checkId', ''))
                ).first()
                
                if existing:
                    existing.name = rec.get('name', '')
                    existing.category = rec.get('category', '')
                    existing.pillar = rec.get('pillar', '')
                    existing.status = rec.get('status', '')
                    existing.description = rec.get('description', '')
                    existing.resource_count = rec.get('resource_count', 0)
                    existing.resources_data = rec.get('resources', [])
                    existing.check_metadata = rec.get('check_metadata', {})
                    existing.updated_at = datetime.utcnow()
                    print(f"✅ Updated: {existing.name}")
                else:
                    new_rec = TrustedAdvisorRecommendation(
                        aws_account_id=aws_account.id,
                        check_id=rec.get('id', rec.get('checkId', '')),
                        name=rec.get('name', ''),
                        category=rec.get('category', ''),
                        pillar=rec.get('pillar', ''),
                        status=rec.get('status', ''),
                        description=rec.get('description', ''),
                        resource_count=rec.get('resource_count', 0),
                        resources_data=rec.get('resources', []),
                        check_metadata=rec.get('check_metadata', {})
                    )
                    db.session.add(new_rec)
                    print(f"✅ Created: {new_rec.name}")
                
                synced_count += 1
            
            db.session.commit()
            
            sync_log.status = 'success'
            sync_log.records_synced = synced_count
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Successfully synced {synced_count} recommendations',
                'synced_count': synced_count
            }
            
        except Exception as e:
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            db.session.commit()
            
            print(f"❌ Sync error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Sync failed: {str(e)}'
            }
    
    def get_trusted_advisor_data(self, user_id, account_id, region, force_refresh=False):
        """Get Trusted Advisor data from database"""
        aws_account = AWSAccount.query.filter_by(
            user_id=user_id,
            account_id=account_id,
            region=region
        ).first()
        
        if not aws_account:
            # Don't auto-sync, just return empty data
            return {
                'recommendations': [],
                'total_recommendations': 0,
                'last_updated': None
            }
        
        if force_refresh:
            sync_result = self.sync_trusted_advisor_data(user_id, account_id, region)
            if not sync_result['success']:
                return {'error': sync_result['error']}
        
        recommendations = TrustedAdvisorRecommendation.query.filter_by(
            aws_account_id=aws_account.id
        ).all()
        
        return {
            'recommendations': [rec.to_dict() for rec in recommendations],
            'total_recommendations': len(recommendations),
            'last_updated': aws_account.created_at.isoformat() if aws_account.created_at else None
        }
    
    def get_sync_status(self, user_id, account_id, region):
        """Get sync status for account"""
        aws_account = AWSAccount.query.filter_by(
            user_id=user_id,
            account_id=account_id,
            region=region
        ).first()
        
        if not aws_account:
            return {'status': 'never_synced'}
        
        latest_sync = DataSyncLog.query.filter_by(
            aws_account_id=aws_account.id,
            sync_type='trusted_advisor'
        ).order_by(DataSyncLog.id.desc()).first()
        
        if not latest_sync:
            return {'status': 'never_synced'}
        
        return {
            'status': latest_sync.status,
            'records_synced': latest_sync.records_synced or 0,
            'error_message': latest_sync.error_message
        }
    
    def save_trusted_advisor_recommendation(self, user_id, rec_data):
        """Save a single trusted advisor recommendation"""
        try:
            # Get or create AWS account (use session data)
            from flask import session
            account_id = session.get('aws_account_id')
            region = session.get('aws_region', 'us-east-1')
            
            if not account_id:
                return False
                
            aws_account = self.get_or_create_aws_account(user_id, account_id, region)
            
            # Check if recommendation already exists
            existing = TrustedAdvisorRecommendation.query.filter_by(
                aws_account_id=aws_account.id,
                check_id=rec_data.get('id', rec_data.get('checkId', ''))
            ).first()
            
            if existing:
                # Update existing
                existing.name = rec_data.get('name', '')
                existing.category = rec_data.get('category', '')
                existing.pillar = rec_data.get('pillar', '')
                existing.status = rec_data.get('status', '')
                existing.description = rec_data.get('description', '')
                existing.resource_count = rec_data.get('resource_count', 0)
                existing.resources_data = rec_data.get('resources', [])
                existing.check_metadata = rec_data.get('check_metadata', {})
            else:
                # Create new
                new_rec = TrustedAdvisorRecommendation(
                    aws_account_id=aws_account.id,
                    user_id=user_id,
                    check_id=rec_data.get('id', rec_data.get('checkId', '')),
                    name=rec_data.get('name', ''),
                    category=rec_data.get('category', ''),
                    pillar=rec_data.get('pillar', ''),
                    status=rec_data.get('status', ''),
                    description=rec_data.get('description', ''),
                    resource_count=rec_data.get('resource_count', 0),
                    resources_data=rec_data.get('resources', []),
                    check_metadata=rec_data.get('check_metadata', {})
                )
                db.session.add(new_rec)
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Error saving recommendation: {e}")
            db.session.rollback()
            return False
    
    def get_trusted_advisor_recommendations(self, user_id, account_id, region):
        """Get trusted advisor recommendations for display"""
        try:
            aws_account = AWSAccount.query.filter_by(
                user_id=user_id,
                account_id=account_id,
                region=region
            ).first()
            
            if not aws_account:
                return {
                    'recommendations': [],
                    'total_recommendations': 0,
                    'category_info': {},
                    'status_counts': {'error': 0, 'warning': 0, 'ok': 0}
                }
            
            recommendations = TrustedAdvisorRecommendation.query.filter_by(
                aws_account_id=aws_account.id
            ).all()
            
            # Process recommendations for display
            rec_list = []
            category_info = {}
            status_counts = {'error': 0, 'warning': 0, 'ok': 0}
            
            for rec in recommendations:
                rec_dict = rec.to_dict()
                rec_list.append(rec_dict)
                
                # Count by status
                status = rec.status.lower() if rec.status else 'unknown'
                if status in status_counts:
                    status_counts[status] += 1
                
                # Group by category
                category = rec.category or 'General'
                if category not in category_info:
                    category_info[category] = []
                category_info[category].append(rec_dict)
            
            return {
                'recommendations': rec_list,
                'total_recommendations': len(rec_list),
                'category_info': category_info,
                'status_counts': status_counts
            }
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return {
                'recommendations': [],
                'total_recommendations': 0,
                'category_info': {},
                'status_counts': {'error': 0, 'warning': 0, 'ok': 0}
            }
