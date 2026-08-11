from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import boto3, json, os, configparser, io, traceback, threading, time
from botocore.config import Config
from datetime import datetime, timedelta
from pymongo import MongoClient
import redis
from bson import ObjectId

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'torwarta-secret-key')
app.permanent_session_lifetime = timedelta(hours=24)

# Database connections
mongo = MongoClient('mongodb://mongodb:27017/')
db = mongo.torwarta
cache = redis.Redis(host='redis', port=6379, decode_responses=True)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User:
    def __init__(self, username):
        self.username = username
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    def get_id(self): return self.username

@login_manager.user_loader
def load_user(username): return User(username)

@app.route('/')
def index(): return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() or request.form
        if data.get('username') == 'admin' and data.get('password') == 'password':
            login_user(User('admin'))
            session.permanent = True
            return jsonify({'success': True})
        return jsonify({'error': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    accounts = list(db.accounts.find({}, {'_id': 0}))
    active_account = session.get('active_account')
    active_region = session.get('active_region', 'us-east-1')
    return render_template('dashboard.html', accounts=accounts, active_account=active_account, active_region=active_region)

@app.route('/api/upload-credentials', methods=['POST'])
@login_required
def upload_credentials():
    try:
        if 'credentials_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['credentials_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        content = file.read().decode('utf-8')
        config = configparser.ConfigParser()
        config.read_string(content)
        
        imported_count = 0
        for profile in config.sections():
            if profile != 'default':
                account_data = {
                    'profile_name': profile,
                    'access_key': config[profile].get('aws_access_key_id'),
                    'secret_key': config[profile].get('aws_secret_access_key'),
                    'region': config[profile].get('region', 'us-east-1'),
                    'role_arn': config[profile].get('role_arn'),
                    'account_id': config[profile].get('account_id'),
                    'source_profile': config[profile].get('source_profile'),
                    'created_at': datetime.utcnow()
                }
                
                # Remove None values
                account_data = {k: v for k, v in account_data.items() if v is not None}
                
                db.accounts.update_one(
                    {'profile_name': profile},
                    {'$set': account_data},
                    upsert=True
                )
                imported_count += 1
        
        return jsonify({'success': True, 'message': f'Imported {imported_count} accounts'})
    except Exception as e:
        return jsonify({'error': f'Failed to parse credentials: {str(e)}'}), 400

@app.route('/api/accounts')
@login_required
def get_accounts():
    accounts = list(db.accounts.find({}, {'_id': 0, 'access_key': 0, 'secret_key': 0}))
    return jsonify(accounts)

@app.route('/api/switch-account', methods=['POST'])
@login_required
def switch_account():
    data = request.get_json()
    account_id = data.get('account_id')
    region = data.get('region', 'us-east-1')
    
    session['active_account'] = account_id
    session['active_region'] = region
    session.permanent = True
    
    return jsonify({'success': True, 'active_account': account_id, 'active_region': region})

@app.route('/api/ta/recommendations')
@login_required
def ta_recommendations():
    try:
        # Get account from session or parameter
        account_name = session.get('active_account') or request.args.get('account')
        
        if not account_name:
            return jsonify({'error': 'No active account selected'}), 400
        
        # Get account info
        account = db.accounts.find_one({'profile_name': account_name})
        if not account:
            return jsonify({'error': f'Account {account_name} not found'}), 400
        
        # Use direct credentials if available
        if account.get('access_key') and account.get('secret_key'):
            client = boto3.client('support',
                aws_access_key_id=account['access_key'],
                aws_secret_access_key=account['secret_key'],
                region_name='us-east-1',
                config=Config(read_timeout=5, connect_timeout=3)
            )
        elif account.get('role_arn') and account.get('source_profile'):
            # Use role_arn with source_profile (AWS CLI style)
            source_account = db.accounts.find_one({'profile_name': account['source_profile']})
            if not source_account or not source_account.get('access_key'):
                return jsonify({'error': f'Source profile {account["source_profile"]} not found or missing credentials'}), 400
            
            sts = boto3.client('sts',
                aws_access_key_id=source_account['access_key'],
                aws_secret_access_key=source_account['secret_key'],
                region_name='us-east-1'
            )
            
            try:
                assumed = sts.assume_role(
                    RoleArn=account['role_arn'],
                    RoleSessionName=f"TorWARTA-{account_name}"
                )
            except Exception as assume_error:
                if 'AccessDenied' in str(assume_error):
                    return jsonify({'error': f'Cannot assume role {account["role_arn"]} - check permissions'}), 403
                else:
                    return jsonify({'error': f'Assume role failed: {str(assume_error)}'}), 400
            
            client = boto3.client('support',
                aws_access_key_id=assumed['Credentials']['AccessKeyId'],
                aws_secret_access_key=assumed['Credentials']['SecretAccessKey'],
                aws_session_token=assumed['Credentials']['SessionToken'],
                region_name='us-east-1'
            )
        else:
            # Use assume role with main account
            main_account = db.accounts.find_one({'profile_name': 'beyon-marketplace'})
            if not main_account or not main_account.get('access_key'):
                return jsonify({'error': 'No main account for assume role'}), 400
            
            account_id = account.get('account_id')
            if not account_id:
                return jsonify({'error': f'No account_id for assume role: {account_name}'}), 400
            
            role_arn = f"arn:aws:iam::{account_id}:role/OrganizationAccountAccessRole"
            
            # Assume role using STS
            sts = boto3.client('sts',
                aws_access_key_id=main_account['access_key'],
                aws_secret_access_key=main_account['secret_key'],
                region_name='us-east-1'
            )
            
            try:
                assumed = sts.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName=f"TorWARTA-{account_name}"
                )
            except Exception as assume_error:
                if 'AccessDenied' in str(assume_error):
                    return jsonify({'error': f'Cannot assume role in {account_name} - check OrganizationAccountAccessRole exists'}), 403
                else:
                    return jsonify({'error': f'Assume role failed: {str(assume_error)}'}), 400
            
            client = boto3.client('support',
                aws_access_key_id=assumed['Credentials']['AccessKeyId'],
                aws_secret_access_key=assumed['Credentials']['SecretAccessKey'],
                aws_session_token=assumed['Credentials']['SessionToken'],
                region_name='us-east-1'
            )
        
        print(f"Checking TA for account: {account_name}, role_arn: {account.get('role_arn', 'N/A')}")
        
        print(f"Checking TA for account: {account_name}, role_arn: {account.get('role_arn', 'N/A')}")
        
        # Use threading to prevent blocking
        recommendations = []
        error_msg = None
        
        def fetch_ta_data():
            nonlocal recommendations, error_msg
            try:
                checks = client.describe_trusted_advisor_checks(language='en')
                print(f"Total TA checks available: {len(checks['checks'])}")
                
                for check in checks['checks']:
                    try:
                        result = client.describe_trusted_advisor_check_result(
                            checkId=check['id'],
                            language='en'
                        )
                        status = result['result']['status']
                        flagged_count = len(result['result'].get('flaggedResources', []))
                        
                        if status in ['warning', 'error']:
                            print(f"ISSUE FOUND - {check['name']}: {status}, Flagged: {flagged_count}")
                            recommendations.append({
                                'name': check['name'],
                                'status': result['result']['status'],
                                'category': check['category'],
                                'resource_count': flagged_count
                            })
                    except Exception as e:
                        print(f"Error checking {check['name']}: {str(e)}")
                        continue
            except Exception as e:
                print(f"TA API Error: {str(e)}")
                if 'SubscriptionRequiredException' in str(e):
                    error_msg = 'Premium Support subscription required for Trusted Advisor API'
                else:
                    error_msg = f'TA API Error: {str(e)}'
        
        # Start thread and wait with timeout
        thread = threading.Thread(target=fetch_ta_data)
        thread.start()
        thread.join(timeout=30)  # 30 second timeout
        
        if thread.is_alive():
            return jsonify({'error': 'TA API request timed out - Premium Support may be required'}), 408
        
        if error_msg:
            return jsonify({'error': error_msg}), 400
            
        return jsonify(recommendations)
        recommendations = []
        
        print(f"Total TA checks available: {len(checks['checks'])}")
        
        for check in checks['checks']:
            try:
                result = client.describe_trusted_advisor_check_result(
                    checkId=check['id'],
                    language='en'
                )
                status = result['result']['status']
                flagged_count = len(result['result'].get('flaggedResources', []))
                
                if status in ['warning', 'error']:
                    print(f"ISSUE FOUND - {check['name']}: {status}, Flagged: {flagged_count}")
                    recommendations.append({
                        'name': check['name'],
                        'status': result['result']['status'],
                        'category': check['category'],
                        'resource_count': flagged_count
                    })
            except Exception as e:
                print(f"Error checking {check['name']}: {str(e)}")
                continue
        
        return jsonify(recommendations)
        
    except Exception as e:
        error_msg = str(e)
        if 'SubscriptionRequiredException' in error_msg:
            return jsonify({'error': 'Premium Support required'}), 400
        elif 'AccessDenied' in error_msg:
            return jsonify({'error': 'Access denied - check permissions'}), 403
        else:
            return jsonify({'error': f'API Error: {error_msg}'}), 500

@app.route('/api/war/workloads', methods=['GET', 'POST'])
@login_required
def war_workloads():
    if request.method == 'POST':
        data = request.json
        workload = {
            'name': data['name'],
            'description': data.get('description', ''),
            'account_id': session.get('active_account'),
            'region': session.get('active_region'),
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        result = db.workloads.insert_one(workload)
        return jsonify({'success': True, 'workload_id': str(result.inserted_id)})
    
    workloads = list(db.workloads.find({
        'account_id': session.get('active_account'),
        'region': session.get('active_region')
    }))
    for w in workloads: w['_id'] = str(w['_id'])
    return jsonify(workloads)

@app.route('/api/reports', methods=['GET', 'POST'])
@login_required
def reports():
    if request.method == 'POST':
        data = request.json
        
        report = {
            'title': data['title'],
            'account_id': session.get('active_account'),
            'region': session.get('active_region'),
            'created_at': datetime.utcnow(),
            'version': 1
        }
        
        result = db.reports.insert_one(report)
        return jsonify({'success': True, 'report_id': str(result.inserted_id)})
    
    reports = list(db.reports.find({
        'account_id': session.get('active_account'),
        'region': session.get('active_region')
    }).sort('created_at', -1))
    for r in reports: r['_id'] = str(r['_id'])
    return jsonify(reports)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
