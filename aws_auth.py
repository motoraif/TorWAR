#!/usr/bin/env python3
"""
AWS Authentication Module for TorWAR
Author: Mohamed Toraif

Handles AWS authentication using AWS CLI profiles and session management
for the TorWAR Well-Architected Review Tool.

Author: Mohamed Toraif
License: MIT
"""

import boto3
import os
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError, TokenRetrievalError

class AWSAuthenticator:
    """Handles AWS authentication using profiles only."""
    
    def __init__(self):
        self.session = None
        self.credentials = None
        self.region = None
        self.account_id = None
        self.user_info = None
    
    def get_available_profiles(self):
        """Get available AWS profiles from ~/.aws/config and ~/.aws/credentials."""
        profiles = []
        
        try:
            # Get profiles from boto3 session
            session = boto3.Session()
            profiles = session.available_profiles
            
            # If no profiles found, try to read files directly
            if not profiles:
                import configparser
                
                # Try to read credentials file
                cred_file = os.path.expanduser('~/.aws/credentials')
                if os.path.exists(cred_file):
                    try:
                        config = configparser.ConfigParser()
                        config.read(cred_file)
                        profiles.extend(config.sections())
                    except Exception as e:
                        print(f"Error reading credentials file: {e}")
                
                # Try to read config file for additional profiles
                config_file = os.path.expanduser('~/.aws/config')
                if os.path.exists(config_file):
                    try:
                        config = configparser.ConfigParser()
                        config.read(config_file)
                        for section in config.sections():
                            if section.startswith('profile '):
                                profile_name = section[8:]  # Remove 'profile ' prefix
                                if profile_name not in profiles:
                                    profiles.append(profile_name)
                    except Exception as e:
                        print(f"Error reading config file: {e}")
            
            # Ensure we have at least a default profile
            if not profiles:
                profiles = ['default']
            
            return sorted(profiles)
            
        except Exception as e:
            print(f"Error getting profiles: {e}")
            return ['default']
    
    def authenticate_with_profile(self, profile_name, region='me-south-1'):
        """Authenticate using AWS profile."""
        try:
            # Create session with profile
            if profile_name and profile_name != 'default':
                self.session = boto3.Session(profile_name=profile_name, region_name=region)
            else:
                self.session = boto3.Session(region_name=region)
            
            # Test credentials with STS
            sts_client = self.session.client('sts')
            identity = sts_client.get_caller_identity()
            
            self.account_id = identity.get('Account')
            self.region = region
            self.user_info = {
                'UserId': identity.get('UserId'),
                'Account': identity.get('Account'),
                'Arn': identity.get('Arn'),
                'Profile': profile_name
            }
            
            # Test Well-Architected access
            try:
                wa_client = self.session.client('wellarchitected')
                test_response = wa_client.list_workloads(MaxResults=1)
                workload_count = len(test_response.get('WorkloadSummaries', []))
                
                return True, f"Authenticated as {identity.get('Arn')} with {workload_count} workloads accessible"
            except Exception as wa_error:
                return False, f"Authentication succeeded but Well-Architected access failed: {str(wa_error)}"
            
        except TokenRetrievalError as e:
            return False, f"Token retrieval error: {str(e)}"
        except NoCredentialsError:
            return False, f"No credentials found for profile '{profile_name}'"
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['InvalidClientTokenId', 'UnrecognizedClientException']:
                return False, f"Invalid or expired credentials for profile '{profile_name}'. Please update your AWS access keys."
            return False, f"AWS error: {e.response['Error']['Message']}"
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    def get_session_info(self):
        """Get current session information."""
        if not self.session or not self.user_info:
            return None
        
        return {
            'account_id': self.account_id,
            'region': self.region,
            'user_info': self.user_info,
            'auth_time': datetime.now(timezone.utc).isoformat()
        }
    
    def is_authenticated(self):
        """Check if currently authenticated."""
        return self.session is not None and self.user_info is not None
    
    def clear_authentication(self):
        """Clear current authentication."""
        self.session = None
        self.credentials = None
        self.region = None
        self.account_id = None
        self.user_info = None

# Global authenticator instance
_aws_authenticator = None

def get_aws_authenticator():
    """Get the global AWS authenticator instance."""
    global _aws_authenticator
    if _aws_authenticator is None:
        _aws_authenticator = AWSAuthenticator()
    return _aws_authenticator

def require_aws_auth(f):
    """Decorator to require AWS authentication."""
    from functools import wraps
    from flask import session, redirect, url_for, flash
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'aws_region' not in session:
            flash('Please authenticate with AWS first', 'warning')
            return redirect(url_for('aws_login'))
        return f(*args, **kwargs)
    return decorated_function
