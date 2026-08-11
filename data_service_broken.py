from datetime import datetime
from database_models import db, AWSAccount, TrustedAdvisorRecommendation, DataSyncLog
from trusted_advisor_helper import get_all_trusted_advisor_recommendations
import json

class DataService:
    def __init__(self):
        pass
    
    def get_or_create_aws_account(self, user_id, account_id, region, account_name=None, profile_name=None):
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
                account_name=account_name,
                profile_name=profile_name
            )
            db.session.add(aws_account)
            db.session.commit()
            print(f"✅ Created AWS account record: {account_id} in {region}")
        else:
            # Update last accessed
            aws_account.last_accessed = datetime.utcnow()
            if account_name:
                aws_account.account_name = account_name
            if profile_name:
                aws_account.profile_name = profile_name
            db.session.commit()
        
        return aws_account
    
    def sync_trusted_advisor_data(self, user_id, account_id, region):
        """Sync Trusted Advisor data from AWS API to database"""
        # Get or create AWS account
        aws_account = self.get_or_create_aws_account(user_id, account_id, region)
        
        # Check if sync is already in progress
        existing_sync = DataSyncLog.query.filter_by(
            aws_account_id=aws_account.id,
            sync_type='trusted_advisor',
            status='in_progress'
        ).first()
        
        if existing_sync:
            return {
                'success': False,
                'error': 'Sync already in progress',
                'message': 'Please wait for the current sync to complete'
            }
        
        # Create sync log
        sync_log = DataSyncLog(
            aws_account_id=aws_account.id,
            sync_type='trusted_advisor',
            status='in_progress'
        )
        db.session.add(sync_log)
        db.session.commit()
        
        try:
            # Get data from AWS API
            print(f"🔄 Syncing Trusted Advisor data for {account_id} in {region}")
            recommendations_data = get_all_trusted_advisor_recommendations()
            
            if 'error' in recommendations_data:
                raise Exception(recommendations_data['error'])
            
            recommendations = recommendations_data.get('recommendations', [])
            synced_count = 0
            
            for rec in recommendations:
                # Update or create recommendation
                existing = TrustedAdvisorRecommendation.query.filter_by(
                    aws_account_id=aws_account.id,
                    check_id=rec.get('id', rec.get('checkId', ''))
                ).first()
                
                if existing:
                    # Update existing
                    existing.name = rec.get('name', '')
                    existing.category = rec.get('category', '')
                    existing.pillar = rec.get('pillar', '')
                    existing.status = rec.get('status', '')
                    existing.description = rec.get('description', '')
                    existing.resource_count = rec.get('resource_count', 0)
                    existing.resources_data = rec.get('resources', [])
                    existing.check_metadata = rec.get('check_metadata', {})
                    existing.updated_at = datetime.utcnow()
                    print(f"✅ Updated existing recommendation: {existing.name}")
                else:
                    # Create new
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
                    print(f"✅ Created new recommendation: {new_rec.name}")
                
                synced_count += 1
            
            # Commit all changes
            db.session.commit()
            
            # Update sync log
            sync_log.status = 'success'
            sync_log.completed_at = datetime.utcnow()
            sync_log.records_synced = synced_count
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Successfully synced {synced_count} recommendations',
                'synced_count': synced_count
            }
            
        except Exception as e:
            # Update sync log with error
            sync_log.status = 'error'
            sync_log.completed_at = datetime.utcnow()
            sync_log.error_message = str(e)
            db.session.commit()
            
            print(f"❌ Sync error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Sync failed: {str(e)}'
            }
                
                synced_count += 1
            
            # Update sync log
            sync_log.status = 'success'
            sync_log.records_synced = synced_count
            sync_log.completed_at = datetime.utcnow()
            
            db.session.commit()
            print(f"✅ Synced {synced_count} Trusted Advisor recommendations")
            
            return {
                'success': True,
                'synced_count': synced_count,
                'message': f'Successfully synced {synced_count} recommendations'
            }
            
        except Exception as e:
            # Update sync log with error
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            
            print(f"❌ Error syncing Trusted Advisor data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_trusted_advisor_recommendations(self, user_id, account_id, region, force_refresh=False):
        """Get Trusted Advisor recommendations from database or sync from AWS"""
        aws_account = AWSAccount.query.filter_by(
            user_id=user_id,
            account_id=account_id,
            region=region
        ).first()
        
        if not aws_account:
            # No account found, sync data first
            sync_result = self.sync_trusted_advisor_data(user_id, account_id, region)
            if not sync_result['success']:
                return {'error': sync_result['error']}
            aws_account = AWSAccount.query.filter_by(
                user_id=user_id,
                account_id=account_id,
                region=region
            ).first()
        
        # Check if we need to refresh data
        if force_refresh:
            sync_result = self.sync_trusted_advisor_data(user_id, account_id, region)
            if not sync_result['success']:
                return {'error': sync_result['error']}
        
        # Get recommendations from database
        recommendations = TrustedAdvisorRecommendation.query.filter_by(
            aws_account_id=aws_account.id
        ).order_by(TrustedAdvisorRecommendation.updated_at.desc()).all()
        
        # Format for frontend
        formatted_recommendations = []
        categories = {}
        
        for rec in recommendations:
            formatted_rec = {
                'id': rec.check_id,
                'name': rec.name,
                'category': rec.category,
                'pillar': rec.pillar,
                'status': rec.status,
                'description': rec.description,
                'resource_count': rec.resource_count,
                'resources': rec.resources_data or [],
                'last_updated': rec.updated_at.isoformat() if rec.updated_at else None,
                'metadata': rec.check_metadata or {}
            }
            formatted_recommendations.append(formatted_rec)
            
            # Group by category
            if rec.category not in categories:
                categories[rec.category] = []
            categories[rec.category].append(formatted_rec)
        
        return {
            'recommendations': formatted_recommendations,
            'categories': categories,
            'total_checks': len(formatted_recommendations),
            'last_updated': aws_account.last_accessed.isoformat() if aws_account.last_accessed else None,
            'from_database': True
        }
    
    def get_sync_status(self, user_id, account_id, region):
        """Get latest sync status for an AWS account"""
        aws_account = AWSAccount.query.filter_by(
            user_id=user_id,
            account_id=account_id,
            region=region
        ).first()
        
        if not aws_account:
            return {'status': 'no_account'}
        
        latest_sync = DataSyncLog.query.filter_by(
            aws_account_id=aws_account.id,
            sync_type='trusted_advisor'
        ).order_by(DataSyncLog.started_at.desc()).first()
        
        if not latest_sync:
            return {'status': 'never_synced'}
        
        return {
            'status': latest_sync.status,
            'started_at': latest_sync.started_at.isoformat(),
            'completed_at': latest_sync.completed_at.isoformat() if latest_sync.completed_at else None,
            'records_synced': latest_sync.records_synced,
            'error_message': latest_sync.error_message
        }
    
    def save_trusted_advisor_recommendation(self, user_id, recommendation_data):
        """Save Trusted Advisor recommendation to database"""
        try:
            # Get or create AWS account first
            aws_account = self.get_or_create_aws_account(
                user_id, 
                recommendation_data['account_id'], 
                recommendation_data['region']
            )
            
            # Create or update recommendation
            recommendation = TrustedAdvisorRecommendation.query.filter_by(
                aws_account_id=aws_account.id,
                check_id=recommendation_data['check_id']
            ).first()
            
            if not recommendation:
                recommendation = TrustedAdvisorRecommendation(
                    aws_account_id=aws_account.id,
                    check_id=recommendation_data['check_id']
                )
                db.session.add(recommendation)
            
            # Update fields
            recommendation.name = recommendation_data['name']
            recommendation.category = recommendation_data['category']
            recommendation.description = recommendation_data['description']
            recommendation.status = recommendation_data['status']
            recommendation.resource_count = recommendation_data['resources_flagged']
            recommendation.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving recommendation: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_trusted_advisor_recommendations(self, user_id, account_id, region):
        """Get Trusted Advisor recommendations from database"""
        try:
            # Get AWS account
            aws_account = AWSAccount.query.filter_by(
                user_id=user_id,
                account_id=account_id,
                region=region
            ).first()
            
            if not aws_account:
                return {
                    'recommendations': [],
                    'categories': {},
                    'category_info': {},
                    'total_recommendations': 0,
                    'aws_account_id': account_id,
                    'aws_region': region
                }
            
            # Get all recommendations for this AWS account
            recommendations = TrustedAdvisorRecommendation.query.filter_by(
                aws_account_id=aws_account.id
            ).all()
            
            # Group by category
            categories = {}
            category_info = {}
            
            for rec in recommendations:
                category = rec.category.lower().replace(' ', '_')
                
                if category not in categories:
                    categories[category] = []
                    category_info[category] = {
                        'name': rec.category,
                        'count': 0
                    }
                
                categories[category].append({
                    'id': rec.check_id,
                    'name': rec.name,
                    'description': rec.description,
                    'status': rec.status,
                    'resources_flagged': rec.resource_count,
                    'category': rec.category,
                    'check_id': rec.check_id,
                    'resource_count': rec.resource_count,
                    'updated_at': rec.updated_at.strftime('%Y-%m-%d %H:%M:%S') if rec.updated_at else None
                })
                
                category_info[category]['count'] += 1
            
            return {
                'recommendations': recommendations,
                'categories': categories,
                'category_info': category_info,
                'total_recommendations': len(recommendations),
                'aws_account_id': account_id,
                'aws_region': region
            }
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            import traceback
            traceback.print_exc()
            return {
                'recommendations': [],
                'categories': {},
                'category_info': {},
                'total_recommendations': 0,
                'aws_account_id': account_id,
                'aws_region': region
            }
