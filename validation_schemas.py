#!/usr/bin/env python3
"""
TorWAR Input Validation Schemas
Author: Mohamed Toraif
"""

import re
from security import security

class ValidationSchemas:
    """Input validation schemas for TorWAR endpoints."""
    
    # AWS validation patterns
    AWS_ACCOUNT_ID_PATTERN = r'^\d{12}$'
    AWS_REGION_PATTERN = r'^[a-z0-9-]+$'
    WORKLOAD_ID_PATTERN = r'^[a-zA-Z0-9-_]{1,50}$'
    
    @staticmethod
    def validate_aws_account_id(value):
        """Validate AWS account ID."""
        if not re.match(ValidationSchemas.AWS_ACCOUNT_ID_PATTERN, str(value)):
            raise ValueError('Invalid AWS account ID format')
    
    @staticmethod
    def validate_aws_region(value):
        """Validate AWS region."""
        if not re.match(ValidationSchemas.AWS_REGION_PATTERN, value):
            raise ValueError('Invalid AWS region format')
    
    @staticmethod
    def validate_workload_id(value):
        """Validate workload ID."""
        if not re.match(ValidationSchemas.WORKLOAD_ID_PATTERN, value):
            raise ValueError('Invalid workload ID format')
    
    # Schema definitions
    WORKLOAD_SCHEMA = {
        'id': {
            'required': True,
            'type': str,
            'min_length': 1,
            'max_length': 50,
            'validator': validate_workload_id.__func__
        },
        'name': {
            'required': True,
            'type': str,
            'min_length': 1,
            'max_length': 200
        },
        'description': {
            'required': False,
            'type': str,
            'max_length': 1000
        },
        'aws_account_id': {
            'required': False,
            'type': str,
            'validator': validate_aws_account_id.__func__
        },
        'aws_region': {
            'required': False,
            'type': str,
            'validator': validate_aws_region.__func__
        }
    }
    
    REPORT_SCHEMA = {
        'workload_id': {
            'required': True,
            'type': str,
            'validator': validate_workload_id.__func__
        },
        'name': {
            'required': True,
            'type': str,
            'min_length': 1,
            'max_length': 200
        },
        'user_notes': {
            'required': False,
            'type': str,
            'max_length': 5000
        },
        'report_data': {
            'required': True,
            'type': dict
        }
    }
    
    AWS_LOGIN_SCHEMA = {
        'aws_profile': {
            'required': False,
            'type': str,
            'min_length': 1,
            'max_length': 50,
            'pattern': r'^[a-zA-Z0-9-_]+$'
        },
        'aws_region': {
            'required': True,
            'type': str,
            'validator': validate_aws_region.__func__
        }
    }
    
    CACHE_CLEAR_SCHEMA = {
        'pattern': {
            'required': False,
            'type': str,
            'max_length': 100,
            'pattern': r'^[a-zA-Z0-9*_-]+$'
        }
    }

def validate_request_data(schema_name: str):
    """Decorator to validate request data against schema."""
    def decorator(func):
        from functools import wraps
        from flask import request, jsonify
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            schema = getattr(ValidationSchemas, f"{schema_name}_SCHEMA", None)
            if not schema:
                return jsonify({'error': 'Invalid validation schema'}), 500
            
            # Get request data
            if request.is_json:
                data = request.get_json() or {}
            else:
                data = request.form.to_dict()
            
            # Sanitize input
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    sanitized_data[key] = security.sanitize_input(value)
                else:
                    sanitized_data[key] = value
            
            # Validate data
            errors = security.validate_input(sanitized_data, schema)
            if errors:
                return jsonify({'error': 'Validation failed', 'details': errors}), 400
            
            # Add validated data to request
            request.validated_data = sanitized_data
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
