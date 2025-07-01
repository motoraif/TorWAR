#!/usr/bin/env python3
"""
AWS Authentication Routes for TorWAR
Simplified to only support AWS Profile authentication
"""

from flask import render_template, request, redirect, url_for, flash, session, jsonify
from aws_auth import get_aws_authenticator
import boto3

def register_auth_routes(app):
    """Register AWS authentication routes with the Flask app."""
    
    @app.route('/aws-login')
    def aws_login():
        """AWS authentication page."""
        auth = get_aws_authenticator()
        
        # Get available profiles
        profiles = auth.get_available_profiles()
        
        # Check current authentication status from Flask session
        current_auth = None
        if 'aws_authenticated' in session and session.get('aws_authenticated'):
            # Verify the session is still valid
            try:
                from aws_helper import test_aws_connection
                success, message, account_info = test_aws_connection()
                
                if success:
                    current_auth = {
                        'user_info': session.get('aws_user_info', {}),
                        'region': session.get('aws_region'),
                        'account_id': session.get('aws_account_id'),
                        'auth_time': session.get('aws_auth_time')
                    }
                else:
                    # Session is invalid, clear it
                    session.pop('aws_authenticated', None)
                    session.pop('aws_account_id', None)
                    session.pop('aws_region', None)
                    session.pop('aws_profile', None)
                    session.pop('aws_user_info', None)
                    session.pop('aws_auth_time', None)
                    auth.clear_authentication()
            except Exception:
                # Error checking connection, clear session
                session.pop('aws_authenticated', None)
                session.pop('aws_account_id', None)
                session.pop('aws_region', None)
                session.pop('aws_profile', None)
                session.pop('aws_user_info', None)
                session.pop('aws_auth_time', None)
                auth.clear_authentication()
        
        return render_template('aws_login.html', 
                             profiles=profiles, 
                             current_auth=current_auth)
    
    @app.route('/aws-authenticate', methods=['POST'])
    def aws_authenticate():
        """Handle AWS profile authentication."""
        auth = get_aws_authenticator()
        
        profile_name = request.form.get('profile_name', 'default')
        region = request.form.get('region', 'me-south-1')
        
        # Use beyon-marketplace as default if default is selected
        if profile_name == 'default':
            profile_name = 'beyon-marketplace'
        
        try:
            # Authenticate with profile
            success, message = auth.authenticate_with_profile(profile_name, region)
            
            if success:
                # Store authentication info in session
                session_info = auth.get_session_info()
                session['aws_authenticated'] = True
                session['aws_account_id'] = session_info['account_id']
                session['aws_region'] = session_info['region']
                session['aws_profile'] = profile_name
                session['aws_user_info'] = session_info['user_info']
                session['aws_auth_time'] = session_info['auth_time']
                
                flash(f'Successfully authenticated with AWS: {message}', 'success')
                
                # Redirect to original destination or home
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash(f'AWS authentication failed: {message}', 'error')
                
        except Exception as e:
            flash(f'Authentication error: {str(e)}', 'error')
        
        return redirect(url_for('aws_login'))
    
    @app.route('/aws-profile-info')
    def aws_profile_info():
        """Get information about available profiles."""
        auth = get_aws_authenticator()
        profiles = auth.get_available_profiles()
        
        profile_info = []
        for profile in profiles:
            # Test if profile has valid credentials
            try:
                test_session = boto3.Session(profile_name=profile)
                sts_client = test_session.client('sts')
                identity = sts_client.get_caller_identity()
                status = "active"
                account = identity.get('Account', 'Unknown')
            except Exception as e:
                status = "inactive"
                account = "Unknown"
            
            profile_info.append({
                'name': profile,
                'status': status,
                'account': account
            })
        
        return jsonify({'profiles': profile_info})
    
    @app.route('/aws-logout')
    def aws_logout():
        """Logout from AWS."""
        # Get authenticator and clear it
        auth = get_aws_authenticator()
        auth.clear_authentication()
        
        # Clear Flask session
        session.pop('aws_authenticated', None)
        session.pop('aws_account_id', None)
        session.pop('aws_region', None)
        session.pop('aws_profile', None)
        session.pop('aws_user_info', None)
        session.pop('aws_auth_time', None)
        
        # Clear workload selection
        session.pop('workload_id', None)
        session.pop('workload_name', None)
        
        # Clear current session
        from aws_helper import clear_current_session
        clear_current_session()
        
        flash('Successfully logged out from AWS', 'info')
        return redirect(url_for('aws_login'))
    
    @app.route('/aws-clear-session')
    def aws_clear_session():
        """Force clear all session data (for debugging)."""
        # Get authenticator and clear it
        auth = get_aws_authenticator()
        auth.clear_authentication()
        
        # Clear all session data
        session.clear()
        
        # Clear current session
        from aws_helper import clear_current_session
        clear_current_session()
        
        flash('All session data cleared', 'info')
        return redirect(url_for('aws_login'))
