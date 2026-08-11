import logging
from flask import jsonify, render_template
from sqlalchemy.exc import SQLAlchemyError
import boto3
from botocore.exceptions import BotoCoreError, ClientError

def setup_error_handlers(app):
    """Setup comprehensive error handling"""
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        app.logger.error(f'Database Error: {error}')
        return jsonify({'error': 'Database connection failed'}), 500
    
    @app.errorhandler(ClientError)
    def aws_error(error):
        app.logger.error(f'AWS Error: {error}')
        return jsonify({'error': 'AWS service unavailable'}), 503
    
    @app.errorhandler(Exception)
    def general_error(error):
        app.logger.error(f'Unexpected Error: {error}')
        return jsonify({'error': 'Internal server error'}), 500
