from datetime import datetime
import json
import redis
from flask import current_app
from models import db, AWSAccount, TrustedAdvisorRecommendation
from trusted_advisor_helper import get_all_trusted_advisor_recommendations

# Redis configuration
try:
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("✅ Redis connected successfully")
except Exception as e:
    print(f"⚠️ Redis connection failed: {e}")
    redis_client = None

class DataService:
    def __init__(self):
        pass
    
    def get_or_create_aws_account(self, user_id, account_id, region):
        """Get or create AWS account record"""
        with current_app.app_context():
            aws_account = db.session.query(AWSAccount).filter_by(
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
                    created_at=datetime.utcnow()
                )
                db.session.add(aws_account)
                db.session.commit()
                print(f"✅ Created new AWS account record: {account_id}")
            
            return aws_account
    
    def sync_trusted_advisor_data(self, user_id, account_id, region, manual_sync=False):
        """Fast sync - only Trusted Advisor endpoint"""
        try:
            with current_app.app_context():
                aws_account = self.get_or_create_aws_account(user_id, account_id, region)
                print(f"🚀 Fast sync for {account_id} in {region}")
                
                # Get fresh data from AWS API only
                recommendations_data = get_all_trusted_advisor_recommendations()
                
                if 'error' in recommendations_data:
                    return {'success': False, 'error': recommendations_data['error']}
                
                recommendations = recommendations_data.get('recommendations', [])
                
                # Clear existing and add new in one transaction
                db.session.query(TrustedAdvisorRecommendation).filter_by(aws_account_id=aws_account.id).delete()
                
                synced_count = 0
                now = datetime.utcnow()
                
                for rec in recommendations:
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
                        check_metadata=rec.get('check_metadata', {}),
                        created_at=now,
                        updated_at=now
                    )
                    db.session.add(new_rec)
                    synced_count += 1
                
                db.session.commit()
                print(f"✅ Fast sync complete: {synced_count} recommendations")
                
                return {
                    'success': True,
                    'synced_count': synced_count,
                    'message': f'Successfully synced {synced_count} recommendations'
                }
                
        except Exception as e:
            with current_app.app_context():
                db.session.rollback()
            print(f"❌ Fast sync error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_trusted_advisor_data(self, user_id, account_id, region, force_refresh=False):
        """Get Trusted Advisor data with Redis caching"""
        with current_app.app_context():
            # Check Redis cache first
            if redis_client and not force_refresh:
                try:
                    cache_key = f"trusted_advisor_data:{user_id}:{account_id}:{region}"
                    cached_data = redis_client.get(cache_key)
                    if cached_data:
                        print("✅ Returning cached data from Redis")
                        return json.loads(cached_data)
                except Exception as cache_error:
                    print(f"⚠️ Redis cache read error: {cache_error}")
            
            aws_account = db.session.query(AWSAccount).filter_by(
                user_id=user_id,
                account_id=account_id,
                region=region
            ).first()
            
            if not aws_account:
                return {
                    'recommendations': [],
                    'total_recommendations': 0,
                    'last_updated': None
                }
            
            if force_refresh:
                sync_result = self.sync_trusted_advisor_data(user_id, account_id, region)
                if not sync_result['success']:
                    return {'error': sync_result['error']}
            
            # Get recommendations from database
            recommendations = TrustedAdvisorRecommendation.query.filter_by(
                aws_account_id=aws_account.id
            ).all()
            
            # Convert to dict format
            recommendations_data = []
            for rec in recommendations:
                recommendations_data.append({
                    'id': rec.check_id,
                    'name': rec.name,
                    'category': rec.category,
                    'pillar': rec.pillar,
                    'status': rec.status,
                    'description': rec.description,
                    'resource_count': rec.resource_count,
                    'resources': rec.resources_data,
                    'check_metadata': rec.check_metadata
                })
            
            result = {
                'recommendations': recommendations_data,
                'total_recommendations': len(recommendations_data),
                'last_updated': aws_account.updated_at.isoformat() if aws_account.updated_at else None
            }
            
            # Cache the result
            if redis_client:
                try:
                    cache_key = f"trusted_advisor_data:{user_id}:{account_id}:{region}"
                    redis_client.setex(cache_key, 3600, json.dumps(result))
                    print(f"✅ Cached data in Redis")
                except Exception as cache_error:
                    print(f"⚠️ Redis cache write error: {cache_error}")
            
            return result
    
    def get_sync_status(self, user_id, account_id, region):
        """Get sync status for an account"""
        with current_app.app_context():
            try:
                aws_account = db.session.query(AWSAccount).filter_by(
                    user_id=user_id,
                    account_id=account_id,
                    region=region
                ).first()
                
                if not aws_account:
                    return {
                        'status': 'not_synced',
                        'last_sync': None,
                        'records_synced': 0,
                        'error_message': None
                    }
                
                # Get recommendation count
                rec_count = db.session.query(TrustedAdvisorRecommendation).filter_by(
                    aws_account_id=aws_account.id
                ).count()
                
                return {
                    'status': 'completed' if rec_count > 0 else 'not_synced',
                    'last_sync': aws_account.updated_at.isoformat() if aws_account.updated_at else None,
                    'records_synced': rec_count,
                    'error_message': None,
                    'completed_at': aws_account.updated_at.isoformat() if aws_account.updated_at else None
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'last_sync': None,
                    'records_synced': 0,
                    'error_message': str(e)
                }
