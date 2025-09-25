#!/usr/bin/env python3
"""
Optimized AWS Helper with Connection Pooling
Author: Mohamed Toraif
"""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from flask import session
from cache_manager import cache
import threading
from typing import Optional

class OptimizedAWSHelper:
    """Optimized AWS helper with connection pooling and caching."""
    
    _clients = {}
    _lock = threading.Lock()
    
    @classmethod
    def get_config(cls):
        """Get optimized boto3 config."""
        return Config(
            max_pool_connections=50,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=60,
            connect_timeout=10
        )
    
    @classmethod
    def get_session(cls, profile=None, region=None):
        """Get cached AWS session."""
        profile = profile or session.get('aws_profile', 'tau-dev')
        region = region or session.get('aws_region', 'us-east-1')
        
        cache_key = f"session:{profile}:{region}"
        
        with cls._lock:
            if cache_key not in cls._clients:
                try:
                    aws_session = boto3.Session(
                        profile_name=profile,
                        region_name=region
                    )
                    cls._clients[cache_key] = aws_session
                except Exception as e:
                    print(f"Error creating session: {e}")
                    return None
            
            return cls._clients[cache_key]
    
    @classmethod
    def get_client(cls, service_name, profile=None, region=None):
        """Get cached AWS client with connection pooling."""
        profile = profile or session.get('aws_profile', 'tau-dev')
        region = region or session.get('aws_region', 'us-east-1')
        
        cache_key = f"client:{service_name}:{profile}:{region}"
        
        with cls._lock:
            if cache_key not in cls._clients:
                aws_session = cls.get_session(profile, region)
                if not aws_session:
                    return None
                
                try:
                    client = aws_session.client(
                        service_name,
                        config=cls.get_config()
                    )
                    cls._clients[cache_key] = client
                except Exception as e:
                    print(f"Error creating {service_name} client: {e}")
                    return None
            
            return cls._clients[cache_key]
    
    @classmethod
    def test_connection_cached(cls):
        """Test AWS connection with caching."""
        cache_key = f"connection_test:{session.get('aws_profile', 'tau-dev')}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            sts_client = cls.get_client('sts')
            if not sts_client:
                result = (False, "No STS client available", {})
            else:
                identity = sts_client.get_caller_identity()
                wa_client = cls.get_client('wellarchitected')
                
                if wa_client:
                    workloads = wa_client.list_workloads(MaxResults=1)
                    workload_count = len(workloads.get('WorkloadSummaries', []))
                else:
                    workload_count = 0
                
                account_info = {
                    'account_id': identity.get('Account'),
                    'user_id': identity.get('UserId'),
                    'arn': identity.get('Arn'),
                    'region': session.get('aws_region', 'us-east-1'),
                    'workload_count': workload_count
                }
                
                result = (True, f"Connected as {identity.get('Arn')}", account_info)
            
            # Cache for 5 minutes
            cache.set(cache_key, result, ttl=300)
            return result
            
        except Exception as e:
            result = (False, f"Connection error: {str(e)}", {})
            cache.set(cache_key, result, ttl=60)  # Cache errors for 1 minute
            return result
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached clients and sessions."""
        with cls._lock:
            cls._clients.clear()
        cache.clear_pattern("connection_test:*")
        cache.clear_pattern("session:*")

# Backward compatibility functions
def get_aws_session():
    return OptimizedAWSHelper.get_session()

def get_wellarchitected_client():
    return OptimizedAWSHelper.get_client('wellarchitected')

def test_aws_connection():
    return OptimizedAWSHelper.test_connection_cached()

def clear_current_session():
    OptimizedAWSHelper.clear_cache()
