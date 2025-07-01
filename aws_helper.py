#!/usr/bin/env python3
"""
AWS Helper Module for TorWAR
Author: Mohamed Toraif

Manages AWS sessions and credentials consistently across the TorWAR application.
Provides centralized AWS client management and session handling.

Author: Mohamed Toraif
License: MIT
"""

import boto3
from botocore.exceptions import ClientError
from flask import session

def get_aws_session():
    """
    Get an AWS session based on the stored session information.
    Returns None if no valid session can be created.
    """
    if 'aws_region' not in session:
        return None
    
    try:
        region = session['aws_region']
        profile = session.get('aws_profile')
        
        # Create session
        if profile and profile != 'default':
            aws_session = boto3.Session(profile_name=profile, region_name=region)
        else:
            aws_session = boto3.Session(region_name=region)
        
        return aws_session
        
    except Exception as e:
        print(f"Error creating AWS session: {e}")
        return None


def get_wellarchitected_client():
    """
    Get a Well-Architected client using the current session.
    """
    aws_session = get_aws_session()
    if not aws_session:
        return None
    
    try:
        return aws_session.client('wellarchitected')
    except Exception as e:
        print(f"Error creating Well-Architected client: {e}")
        return None


def test_aws_connection():
    """
    Test the AWS connection by making a simple API call.
    Returns (success: bool, message: str, account_info: dict)
    """
    try:
        aws_session = get_aws_session()
        if not aws_session:
            return False, "No AWS session available", {}
        
        # Test STS connection
        sts_client = aws_session.client('sts')
        identity = sts_client.get_caller_identity()
        
        # Test Well-Architected connection
        wa_client = aws_session.client('wellarchitected')
        workloads = wa_client.list_workloads(MaxResults=1)
        
        account_info = {
            'account_id': identity.get('Account'),
            'user_id': identity.get('UserId'),
            'arn': identity.get('Arn'),
            'region': aws_session.region_name,
            'workload_count': len(workloads.get('WorkloadSummaries', []))
        }
        
        return True, f"Connected as {identity.get('Arn')}", account_info
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnauthorizedOperation':
            return False, "Insufficient permissions for Well-Architected service", {}
        elif error_code == 'InvalidUserID.NotFound':
            return False, "Invalid AWS credentials", {}
        else:
            return False, f"AWS API Error: {e.response['Error']['Message']}", {}
    except Exception as e:
        return False, f"Connection error: {str(e)}", {}


def get_account_alias():
    """
    Get the AWS account alias if available.
    """
    try:
        aws_session = get_aws_session()
        if not aws_session:
            return None
        
        iam_client = aws_session.client('iam')
        aliases = iam_client.list_account_aliases()
        
        if aliases['AccountAliases']:
            return aliases['AccountAliases'][0]
        else:
            return None
            
    except Exception:
        return None


def clear_current_session():
    """Clear the current session (placeholder for compatibility)."""
    # Since we're using profile-based authentication only,
    # this function is mainly for compatibility with the logout route
    pass
