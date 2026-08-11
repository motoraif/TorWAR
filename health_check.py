from flask import jsonify
from database_models import db
from sqlalchemy import text
import redis
import os

def setup_health_checks(app):
    """Setup health check endpoints"""
    
    @app.route('/health')
    def health_check():
        """Basic health check"""
        return jsonify({'status': 'healthy', 'service': 'torwar'})
    
    @app.route('/health/detailed')
    def detailed_health_check():
        """Detailed health check with dependencies"""
        status = {'status': 'healthy', 'checks': {}}
        
        # Database check
        try:
            db.session.execute(text('SELECT 1'))
            status['checks']['database'] = 'healthy'
        except Exception as e:
            status['checks']['database'] = f'unhealthy: {str(e)}'
            status['status'] = 'unhealthy'
        
        # Redis check
        try:
            r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, db=0)
            r.ping()
            status['checks']['redis'] = 'healthy'
        except Exception as e:
            status['checks']['redis'] = f'unhealthy: {str(e)}'
            status['status'] = 'unhealthy'
        
        return jsonify(status), 200 if status['status'] == 'healthy' else 503
