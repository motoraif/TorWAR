from flask import jsonify
import redis
import psycopg2
import os

def add_health_check(app):
    @app.route('/health')
    def health_check():
        """Health check endpoint for load balancers"""
        try:
            # Check database
            db_url = os.environ.get('DATABASE_URL')
            conn = psycopg2.connect(db_url)
            conn.close()
            
            # Check Redis
            redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
            r = redis.from_url(redis_url)
            r.ping()
            
            return jsonify({
                'status': 'healthy',
                'database': 'ok',
                'redis': 'ok'
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 503
