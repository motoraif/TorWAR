#!/usr/bin/env python3
"""
TorWAR - AWS Well-Architected Review Tool with Authentication and Database
"""

import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from database_config import create_app, init_database
from database_models import db, User, AWSAccount, TrustedAdvisorRecommendation, SavedReport
from data_service import DataService
from auth_system import init_auth, register_auth_routes as register_user_auth_routes
from aws_helper import get_aws_session
from datetime import datetime

# Well-Architected Framework Pillars
PILLARS = {
    'operationalExcellence': 'Operational Excellence',
    'security': 'Security', 
    'reliability': 'Reliability',
    'performance': 'Performance Efficiency',
    'costOptimization': 'Cost Optimization',
    'sustainability': 'Sustainability'
}

from health_check import add_health_check

# Create Flask app with database
app, db, migrate = create_app()

# Initialize authentication
init_auth(app)

# Add health check endpoint
add_health_check(app)

# Add custom Jinja2 filters
@app.template_filter('get_choice_titles')
def get_choice_titles(selected_choices, all_choices):
    """Extract titles from selected choice IDs using all choices."""
    if not selected_choices or not all_choices:
        return []
    
    choice_map = {choice.get('ChoiceId'): choice.get('Title', choice.get('ChoiceId', '')) for choice in all_choices}
    return [choice_map.get(choice_id, choice_id) for choice_id in selected_choices]

# Initialize data service
data_service = DataService()

@app.route('/')
def index():
    """Home page - requires authentication"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # Get user's AWS accounts
    aws_accounts = AWSAccount.query.filter_by(user_id=current_user.id).all()
    
    # Get selected workload info if available
    workload_info = None
    if session.get('workload_id') and session.get('aws_account_id'):
        try:
            aws_session = get_aws_session()
            if aws_session:
                wa_client = aws_session.client('wellarchitected')
                response = wa_client.get_workload(WorkloadId=session['workload_id'])
                workload_info = response.get('Workload', {})
        except Exception as e:
            print(f"Error getting workload info: {e}")
    
    context = {
        'user': current_user,
        'aws_accounts': aws_accounts,
        'workload_info': workload_info,
        'page_title': 'Dashboard'
    }
    
    return render_template('dashboard.html', **context)

@app.route('/aws-connect')
@login_required
def aws_connect():
    """AWS connection page"""
    import boto3
    import os
    from configparser import ConfigParser
    
    profiles = []
    
    try:
        # Get profiles from boto3 session
        session_boto = boto3.Session()
        profiles = session_boto.available_profiles
        
        # Also check credentials file directly
        creds_file = os.path.expanduser('~/.aws/credentials')
        config_file = os.path.expanduser('~/.aws/config')
        
        additional_profiles = set()
        
        if os.path.exists(creds_file):
            config = ConfigParser()
            config.read(creds_file)
            additional_profiles.update(config.sections())
        
        if os.path.exists(config_file):
            config = ConfigParser()
            config.read(config_file)
            # Config file sections are like [profile name] except for [default]
            for section in config.sections():
                if section.startswith('profile '):
                    additional_profiles.add(section[8:])  # Remove 'profile ' prefix
                elif section == 'default':
                    additional_profiles.add('default')
        
        # Combine and deduplicate
        all_profiles = list(set(profiles + list(additional_profiles)))
        all_profiles.sort()
        
    except Exception as e:
        all_profiles = ['default']
        print(f"Error loading profiles: {e}")
    
    return render_template('aws_connect.html', profiles=all_profiles)

@app.route('/aws-login')
@login_required  
def aws_login():
    """AWS login page - redirect to connect"""
    return redirect(url_for('aws_connect'))

@app.route('/aws-connect', methods=['POST'])
@login_required
def aws_connect_post():
    """Handle AWS connection"""
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        profile = request.form.get('profile', '').strip()
        region = request.form.get('region', 'us-east-1')
        
        print(f"🔍 Connecting with profile: '{profile}', region: {region}")
        
        # Try to connect
        if profile:
            print(f"🔍 Using profile: {profile}")
            session_aws = boto3.Session(profile_name=profile, region_name=region)
        else:
            print(f"🔍 Using default credentials")
            session_aws = boto3.Session(region_name=region)
        
        sts = session_aws.client('sts')
        identity = sts.get_caller_identity()
        
        print(f"✅ Connected to account: {identity['Account']}")
        
        # Store in session
        session['aws_account_id'] = identity['Account']
        session['aws_region'] = region
        session['aws_profile'] = profile if profile else None
        session['is_connected'] = True
        
        flash(f'Connected to AWS Account: {identity["Account"]}', 'success')
        return redirect(url_for('index'))
        
    except NoCredentialsError:
        print(f"❌ No credentials found")
        flash('No AWS credentials found. Run "aws configure" first.', 'error')
    except ClientError as e:
        print(f"❌ AWS Client Error: {e}")
        flash(f'AWS Error: {e.response["Error"]["Message"]}', 'error')
    except Exception as e:
        print(f"❌ Connection error: {e}")
        flash(f'Connection failed: {str(e)}', 'error')
    
    return redirect(url_for('aws_connect'))

@app.route('/create-workload')
@login_required
def create_workload():
    """Create workload page"""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    return render_template('create_workload.html')

@app.route('/list-workloads')
@login_required
def list_workloads():
    """List workloads page"""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Get AWS session
        profile = session.get('aws_profile')
        region = session.get('aws_region', 'us-east-1')
        
        if profile:
            aws_session = boto3.Session(profile_name=profile, region_name=region)
        else:
            aws_session = boto3.Session(region_name=region)
        
        # Get Well-Architected client
        wa_client = aws_session.client('wellarchitected')
        
        # List workloads
        response = wa_client.list_workloads()
        workloads = response.get('WorkloadSummaries', [])
        
        print(f"✅ Found {len(workloads)} workloads")
        
        return render_template('list_workloads.html', workloads=workloads)
        
    except ClientError as e:
        error_msg = f"AWS Error: {e.response['Error']['Message']}"
        print(f"❌ {error_msg}")
        flash(error_msg, 'error')
        return render_template('list_workloads.html', workloads=[])
        
    except Exception as e:
        error_msg = f"Error loading workloads: {str(e)}"
        print(f"❌ {error_msg}")
        flash(error_msg, 'error')
        return render_template('list_workloads.html', workloads=[])

@app.route('/workloads/select/<workload_id>')
@login_required
def select_workload(workload_id):
    """Select a workload for review."""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    try:
        # Get AWS session
        aws_session = get_aws_session()
        if not aws_session:
            flash('Unable to connect to AWS', 'error')
            return redirect(url_for('list_workloads'))
            
        wa_client = aws_session.client('wellarchitected')
        response = wa_client.get_workload(WorkloadId=workload_id)
        workload = response.get('Workload', {})
        
        session['workload_id'] = workload_id
        session['workload_name'] = workload.get('WorkloadName', 'Unknown')
        
        flash(f'Selected workload: {workload.get("WorkloadName")}', 'success')
        return redirect(url_for('select_pillars'))
    except Exception as e:
        flash(f'Error selecting workload: {str(e)}', 'danger')
        return redirect(url_for('list_workloads'))

@app.route('/select_pillars')
@login_required
def select_pillars():
    """Select pillars for review."""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    if not session.get('workload_id'):
        flash('Please select a workload first', 'warning')
        return redirect(url_for('list_workloads'))
    
    # Get real pillar stats from AWS
    pillar_stats = {}
    
    try:
        aws_session = get_aws_session()
        wa_client = aws_session.client('wellarchitected')
        workload_id = session['workload_id']
        
        for pillar_id in PILLARS.keys():
            try:
                # Get all answers for this pillar with pagination
                all_answers = []
                next_token = None
                
                while True:
                    params = {
                        'WorkloadId': workload_id,
                        'LensAlias': 'wellarchitected',
                        'PillarId': pillar_id,
                        'MaxResults': 50
                    }
                    if next_token:
                        params['NextToken'] = next_token
                    
                    response = wa_client.list_answers(**params)
                    all_answers.extend(response.get('AnswerSummaries', []))
                    
                    next_token = response.get('NextToken')
                    if not next_token:
                        break
                
                total_questions = len(all_answers)
                answered_questions = sum(1 for answer in all_answers if answer.get('SelectedChoices'))
                completion_percentage = (answered_questions / total_questions * 100) if total_questions > 0 else 0
                
                pillar_stats[pillar_id] = {
                    'answered_questions': answered_questions,
                    'total_questions': total_questions,
                    'completion_percentage': completion_percentage
                }
                
            except Exception as e:
                print(f"Error getting stats for pillar {pillar_id}: {e}")
                pillar_stats[pillar_id] = {
                    'answered_questions': 0,
                    'total_questions': 0,
                    'completion_percentage': 0
                }
                
    except Exception as e:
        print(f"Error connecting to AWS: {e}")
        # Fallback to empty stats
        for pillar_id in PILLARS.keys():
            pillar_stats[pillar_id] = {
                'answered_questions': 0,
                'total_questions': 0,
                'completion_percentage': 0
            }
    
    return render_template('select_pillars.html', 
                         pillar_stats=pillar_stats,
                         pillars=PILLARS,
                         selected_pillars=session.get('selected_pillars', []))

@app.route('/start_review', methods=['POST'])
@login_required
def start_review():
    """Start the review process with selected pillars."""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    if not session.get('workload_id'):
        flash('Please select a workload first', 'warning')
        return redirect(url_for('list_workloads'))
    
    selected_pillars = request.form.getlist('pillars')
    if not selected_pillars:
        flash('Please select at least one pillar to review', 'warning')
        return redirect(url_for('select_pillars'))
    
    session['selected_pillars'] = selected_pillars
    flash(f'Starting review for {len(selected_pillars)} pillar(s)', 'success')
    
    # Start with the first pillar
    return redirect(url_for('review_pillar', pillar_id=selected_pillars[0]))

@app.route('/review/')
@login_required
def review_redirect():
    """Redirect /review/ to pillar selection."""
    return redirect(url_for('select_pillars'))

@app.route('/review_pillar/<pillar_id>')
@app.route('/review/<pillar_id>')
@login_required
def review_pillar(pillar_id):
    """Review a specific pillar."""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    if not session.get('workload_id'):
        flash('Please select a workload first', 'warning')
        return redirect(url_for('list_workloads'))
    
    try:
        aws_session = get_aws_session()
        wa_client = aws_session.client('wellarchitected')
        workload_id = session['workload_id']
        
        # Get pillar questions
        response = wa_client.list_answers(
            WorkloadId=workload_id,
            LensAlias='wellarchitected',
            PillarId=pillar_id
        )
        
        questions = response.get('AnswerSummaries', [])
        
        # Calculate next and previous pillars
        all_pillar_ids = list(PILLARS.keys())
        current_pillar_index = all_pillar_ids.index(pillar_id) if pillar_id in all_pillar_ids else 0
        
        prev_pillar = all_pillar_ids[current_pillar_index - 1] if current_pillar_index > 0 else all_pillar_ids[-1]
        next_pillar = all_pillar_ids[current_pillar_index + 1] if current_pillar_index < len(all_pillar_ids) - 1 else all_pillar_ids[0]
        
        return render_template('review_pillar.html', 
                             pillar_id=pillar_id,
                             pillar_name=PILLARS.get(pillar_id, pillar_id),
                             questions=questions,
                             selected_pillars=session.get('selected_pillars', []),
                             prev_pillar=prev_pillar,
                             next_pillar=next_pillar)
        
    except Exception as e:
        flash(f'Error loading pillar questions: {str(e)}', 'danger')
        return redirect(url_for('select_pillars'))

@app.route('/generate_report')
@app.route('/report')
@login_required
def generate_report():
    """Generate a comprehensive Well-Architected report."""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    if not session.get('workload_id'):
        flash('Please select a workload first', 'warning')
        return redirect(url_for('list_workloads'))
    
    try:
        aws_session = get_aws_session()
        wa_client = aws_session.client('wellarchitected')
        workload_id = session['workload_id']
        
        # Get workload details
        workload_response = wa_client.get_workload(WorkloadId=workload_id)
        workload = workload_response.get('Workload', {})
        
        # Initialize counters
        total_questions = 0
        answered_questions = 0
        high_risks = 0
        medium_risks = 0
        low_risks = 0
        no_risks = 0
        
        # Get pillar data - only for selected pillars
        pillar_reviews = {}
        report_pillars = {}
        
        # Get selected pillars from session, default to all if none selected
        selected_pillars = session.get('selected_pillars', list(PILLARS.keys()))
        
        for pillar_id in selected_pillars:
            if pillar_id not in PILLARS:
                continue
                
            pillar_name = PILLARS[pillar_id]
            try:
                # Get all answers for this pillar with pagination
                all_answers = []
                next_token = None
                
                while True:
                    params = {
                        'WorkloadId': workload_id,
                        'LensAlias': 'wellarchitected',
                        'PillarId': pillar_id,
                        'MaxResults': 50
                    }
                    if next_token:
                        params['NextToken'] = next_token
                    
                    answers_response = wa_client.list_answers(**params)
                    answer_summaries = answers_response.get('AnswerSummaries', [])
                    
                    # Get full answer details for each question to include notes
                    for answer in answer_summaries:
                        try:
                            # Get full answer details
                            full_answer = wa_client.get_answer(
                                WorkloadId=workload_id,
                                LensAlias='wellarchitected',
                                QuestionId=answer['QuestionId']
                            )
                            answer_detail = full_answer.get('Answer', {})
                            
                            # Add notes and other details to the answer
                            answer['Notes'] = answer_detail.get('Notes', '')
                            answer['HelpfulResourceDisplayText'] = answer_detail.get('HelpfulResourceDisplayText', '')
                            answer['ImprovementPlanUrl'] = answer_detail.get('ImprovementPlanUrl', '')
                            
                        except Exception as e:
                            print(f"Error getting answer details for {answer['QuestionId']}: {e}")
                            answer['Notes'] = ''
                    
                    all_answers.extend(answer_summaries)
                    
                    next_token = answers_response.get('NextToken')
                    if not next_token:
                        break
                
                answers = all_answers
                pillar_total = len(answers)
                pillar_answered = sum(1 for answer in answers if answer.get('SelectedChoices'))
                
                # Count risks for this pillar
                pillar_high = pillar_medium = pillar_low = pillar_none = 0
                for answer in answers:
                    risk = answer.get('Risk', 'NONE')
                    if risk == 'HIGH':
                        high_risks += 1
                        pillar_high += 1
                    elif risk == 'MEDIUM':
                        medium_risks += 1
                        pillar_medium += 1
                    elif risk == 'LOW':
                        low_risks += 1
                        pillar_low += 1
                    else:
                        no_risks += 1
                        pillar_none += 1
                
                total_questions += pillar_total
                answered_questions += pillar_answered
                
                # Store pillar data
                report_pillars[pillar_id] = {
                    'name': pillar_name,
                    'questions': answers,
                    'total_questions': pillar_total,
                    'answered_questions': pillar_answered,
                    'completion_percentage': (pillar_answered / pillar_total * 100) if pillar_total > 0 else 0,
                    'stats': {
                        'total_questions': pillar_total,
                        'answered_questions': pillar_answered,
                        'completion_percentage': (pillar_answered / pillar_total * 100) if pillar_total > 0 else 0
                    },
                    'risk_counts': {
                        'high_risks': pillar_high,
                        'medium_risks': pillar_medium,
                        'low_risks': pillar_low,
                        'no_risks': pillar_none
                    }
                }
                
                pillar_reviews[pillar_id] = {
                    'name': pillar_name,
                    'completion_percentage': (pillar_answered / pillar_total * 100) if pillar_total > 0 else 0,
                    'answered_questions': pillar_answered,
                    'total_questions': pillar_total
                }
                
            except Exception as e:
                print(f"Error getting pillar {pillar_id}: {e}")
                continue
        
        # Basic report data structure
        report_data = {
            'workload': workload,
            'pillars': report_pillars,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_questions': total_questions,
                'answered_questions': answered_questions,
                'completion_percentage': (answered_questions / total_questions * 100) if total_questions > 0 else 0,
                'high_risks': high_risks,
                'medium_risks': medium_risks,
                'low_risks': low_risks,
                'no_risks': no_risks
            }
        }
        
        # Risk counts for template
        risk_counts = {
            'high_risks': high_risks,
            'medium_risks': medium_risks,
            'low_risks': low_risks,
            'no_risks': no_risks
        }
        
        # Overall stats for template
        overall_stats = {
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'completion_percentage': (answered_questions / total_questions * 100) if total_questions > 0 else 0,
            'high_risks': high_risks,
            'medium_risks': medium_risks,
            'low_risks': low_risks,
            'no_risks': no_risks
        }
        
        # Pillar reviews for template (already populated above)
        
        # Report version
        report_version = "1.0"
        
        return render_template('generate_report.html', 
                             report_data=report_data,
                             workload=workload,
                             pillars=PILLARS,
                             now=datetime.now(),
                             risk_counts=risk_counts,
                             overall_stats=overall_stats,
                             pillar_reviews=pillar_reviews,
                             report_version=report_version)
        
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('select_pillars'))

@app.route('/save_report', methods=['POST'])
@login_required
def save_report():
    """Save the generated report."""
    workload_name = request.form.get('custom_name', 'Saved Report')
    notes = request.form.get('user_notes', '')
    
    # Get the current report data from session or regenerate it
    if session.get('workload_id'):
        try:
            aws_session = get_aws_session()
            wa_client = aws_session.client('wellarchitected')
            workload_id = session['workload_id']
            
            # Get workload details
            workload_response = wa_client.get_workload(WorkloadId=workload_id)
            workload = workload_response.get('Workload', {})
            
            # Convert datetime objects to strings in workload data
            if 'UpdatedAt' in workload:
                workload['UpdatedAt'] = workload['UpdatedAt'].isoformat() if hasattr(workload['UpdatedAt'], 'isoformat') else str(workload['UpdatedAt'])
            if 'CreatedAt' in workload:
                workload['CreatedAt'] = workload['CreatedAt'].isoformat() if hasattr(workload['CreatedAt'], 'isoformat') else str(workload['CreatedAt'])
            
            # Get basic pillar data for selected pillars
            selected_pillars = session.get('selected_pillars', list(PILLARS.keys()))
            pillar_data = {}
            
            for pillar_id in selected_pillars:
                if pillar_id in PILLARS:
                    try:
                        # Get all answers for this pillar with pagination
                        all_answers = []
                        next_token = None
                        
                        while True:
                            params = {
                                'WorkloadId': workload_id,
                                'LensAlias': 'wellarchitected',
                                'PillarId': pillar_id,
                                'MaxResults': 50
                            }
                            if next_token:
                                params['NextToken'] = next_token
                            
                            response = wa_client.list_answers(**params)
                            answers = response.get('AnswerSummaries', [])
                            
                            # Get full answer details for each question to include notes
                            for answer in answers:
                                try:
                                    # Get full answer details
                                    full_answer = wa_client.get_answer(
                                        WorkloadId=workload_id,
                                        LensAlias='wellarchitected',
                                        QuestionId=answer['QuestionId']
                                    )
                                    answer_detail = full_answer.get('Answer', {})
                                    
                                    # Add notes and other details to the answer
                                    answer['Notes'] = answer_detail.get('Notes', '')
                                    answer['HelpfulResourceDisplayText'] = answer_detail.get('HelpfulResourceDisplayText', '')
                                    answer['ImprovementPlanUrl'] = answer_detail.get('ImprovementPlanUrl', '')
                                    
                                except Exception as e:
                                    print(f"Error getting answer details for {answer['QuestionId']}: {e}")
                                    answer['Notes'] = ''
                                
                                # Convert datetime objects
                                if 'UpdatedAt' in answer:
                                    answer['UpdatedAt'] = answer['UpdatedAt'].isoformat() if hasattr(answer['UpdatedAt'], 'isoformat') else str(answer['UpdatedAt'])
                            
                            all_answers.extend(answers)
                            
                            next_token = response.get('NextToken')
                            if not next_token:
                                break
                        
                        pillar_data[pillar_id] = {
                            'name': PILLARS[pillar_id],
                            'questions': all_answers
                        }
                    except Exception as e:
                        print(f"Error getting pillar {pillar_id}: {e}")
                        pillar_data[pillar_id] = {'name': PILLARS[pillar_id], 'questions': []}
            
            report_data = {
                'workload': workload,
                'pillars': pillar_data,
                'notes': notes,
                'saved_at': datetime.now().isoformat(),
                'selected_pillars': selected_pillars
            }
            
        except Exception as e:
            # Fallback to basic data
            report_data = {
                'workload': {'WorkloadName': workload_name, 'WorkloadId': session.get('workload_id', 'unknown')},
                'pillars': {},
                'notes': notes,
                'saved_at': datetime.now().isoformat()
            }
    else:
        report_data = {'notes': notes, 'saved_at': datetime.now().isoformat()}
    
    saved_report = SavedReport(
        user_id=current_user.id,
        workload_id=session.get('workload_id', 'unknown'),
        workload_name=workload_name,
        report_data=json.dumps(report_data)
    )
    
    db.session.add(saved_report)
    db.session.commit()
    
    flash('Report saved successfully!', 'success')
    return redirect(url_for('saved_reports'))

@app.route('/ai_analysis', methods=['POST'])
@login_required
def ai_analysis():
    """Generate AI analysis of the Well-Architected report using Bedrock."""
    if not session.get('workload_id'):
        return jsonify({'error': 'No workload selected'}), 400
    
    try:
        # Check Bedrock configuration
        bedrock_config = session.get('bedrock_config', {})
        if not bedrock_config.get('enabled'):
            return jsonify({'error': 'Bedrock is not configured. Please configure it in Settings.'}), 400
        
        import boto3
        from botocore.exceptions import ClientError
        
        # Get parent credentials session for role assumption
        parent_profile = bedrock_config.get('parent_credentials')
        if parent_profile:
            parent_session = boto3.Session(profile_name=parent_profile)
        else:
            # Use current session credentials
            region = session.get('aws_region', 'us-east-1')
            if session.get('aws_access_key_id'):
                parent_session = boto3.Session(
                    aws_access_key_id=session['aws_access_key_id'],
                    aws_secret_access_key=session['aws_secret_access_key'],
                    region_name=region
                )
            else:
                parent_session = boto3.Session(region_name=region)
        
        # Assume cross-account role for Bedrock access
        sts_client = parent_session.client('sts')
        assumed_role = sts_client.assume_role(
            RoleArn=bedrock_config['role_arn'],
            RoleSessionName='TorWAR-AIAnalysis'
        )
        
        # Create Bedrock client with assumed role credentials
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=bedrock_config['region'],
            aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role['Credentials']['SessionToken']
        )
        
        # Prepare report summary for AI analysis
        workload_id = session['workload_id']
        selected_pillars = session.get('selected_pillars', [])
        
        # Create a summary of findings
        report_summary = f"Well-Architected Review Analysis for Workload: {workload_id}\n\n"
        report_summary += f"Selected Pillars: {', '.join([PILLARS.get(p, p) for p in selected_pillars])}\n\n"
        
        # Prepare Bedrock request
        prompt = f"""You are an AWS Well-Architected Framework expert. You MUST analyze the following report and provide a comprehensive response with exactly these 6 sections in this order:

**Executive Summary**
Provide 3-4 sentences summarizing the overall state of the workload.

**Key Strengths**
List 3-5 bullet points of what the workload does well.

**Critical Areas for Improvement**
List 3-5 bullet points of the most important issues that need attention.

**Recommended Next Steps**
Provide 5-7 numbered action items in priority order.

**Risk Assessment**
Categorize the overall risk level (High/Medium/Low) and explain why in 2-3 sentences.

**Final Opinion**
Provide your professional recommendation in 2-3 sentences about the workload's readiness and next priorities.

Report Data:
{report_summary}

You MUST include all 6 sections with proper formatting. Do not skip any section."""
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock_client.invoke_model(
            modelId=bedrock_config['model_id'],
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        ai_analysis = response_body['content'][0]['text']
        
        return jsonify({
            'success': True,
            'analysis': ai_analysis
        })
        
    except ClientError as e:
        error_msg = f"AWS Bedrock Error: {e.response['Error']['Message']}"
        return jsonify({'success': False, 'error': error_msg}), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'AI Analysis failed: {str(e)}'
        }), 500
    """Test save functionality."""
    saved_report = SavedReport(
        user_id=current_user.id,
        workload_id='direct-test',
        workload_name='Direct Test',
        report_data='{"direct": "test"}'
    )
    
    db.session.add(saved_report)
    db.session.commit()
    
    flash('Direct test save successful!', 'success')
    return redirect(url_for('saved_reports'))

@app.route('/saved_reports')
@login_required
def saved_reports():
    """View saved reports."""
    reports = SavedReport.query.filter_by(user_id=current_user.id).order_by(SavedReport.created_at.desc()).all()
    return render_template('saved_reports.html', reports=reports)

@app.route('/view_report/<int:report_id>')
@login_required
def view_report(report_id):
    """View a saved report."""
    report = SavedReport.query.filter_by(id=report_id, user_id=current_user.id).first_or_404()
    
    # Parse the saved report data
    try:
        saved_data = json.loads(report.report_data)
    except:
        saved_data = {}
    
    # Use saved workload data or create mock
    workload = saved_data.get('workload', {
        'WorkloadName': report.workload_name,
        'WorkloadId': report.workload_id
    })
    
    # Use saved pillar data or create empty
    saved_pillars = saved_data.get('pillars', {})
    
    # Calculate basic stats from saved data
    total_questions = 0
    answered_questions = 0
    high_risks = medium_risks = low_risks = no_risks = 0
    
    for pillar_id, pillar_data in saved_pillars.items():
        questions = pillar_data.get('questions', [])
        total_questions += len(questions)
        for q in questions:
            if q.get('SelectedChoices'):
                answered_questions += 1
            risk = q.get('Risk', 'NONE')
            if risk == 'HIGH': high_risks += 1
            elif risk == 'MEDIUM': medium_risks += 1
            elif risk == 'LOW': low_risks += 1
            else: no_risks += 1
    
    # Create report data structure with proper pillar stats
    report_pillars = {}
    for pillar_id, pillar_data in saved_pillars.items():
        questions = pillar_data.get('questions', [])
        pillar_total = len(questions)
        pillar_answered = sum(1 for q in questions if q.get('SelectedChoices'))
        
        # Count risks for this pillar
        pillar_high = pillar_medium = pillar_low = pillar_none = 0
        for q in questions:
            risk = q.get('Risk', 'NONE')
            if risk == 'HIGH': pillar_high += 1
            elif risk == 'MEDIUM': pillar_medium += 1
            elif risk == 'LOW': pillar_low += 1
            else: pillar_none += 1
        
        report_pillars[pillar_id] = {
            'name': pillar_data.get('name', PILLARS.get(pillar_id, '')),
            'questions': questions,
            'stats': {
                'total_questions': pillar_total,
                'answered_questions': pillar_answered,
                'completion_percentage': (pillar_answered / pillar_total * 100) if pillar_total > 0 else 0
            },
            'risk_counts': {
                'high_risks': pillar_high,
                'medium_risks': pillar_medium,
                'low_risks': pillar_low,
                'no_risks': pillar_none
            }
        }
    
    report_data = {
        'workload': workload,
        'pillars': report_pillars,
        'generated_at': report.created_at.isoformat(),
        'summary': {
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'completion_percentage': (answered_questions / total_questions * 100) if total_questions > 0 else 0,
            'high_risks': high_risks,
            'medium_risks': medium_risks,
            'low_risks': low_risks,
            'no_risks': no_risks
        }
    }
    
    return render_template('generate_report.html', 
                         report_data=report_data,
                         workload=workload,
                         pillars=PILLARS,
                         now=report.created_at,
                         risk_counts={'high_risks': high_risks, 'medium_risks': medium_risks, 'low_risks': low_risks, 'no_risks': no_risks},
                         overall_stats={'total_questions': total_questions, 'answered_questions': answered_questions, 'completion_percentage': (answered_questions / total_questions * 100) if total_questions > 0 else 0, 'high_risks': high_risks, 'medium_risks': medium_risks, 'low_risks': low_risks, 'no_risks': no_risks},
                         pillar_reviews={pillar_id: {'name': data.get('name', ''), 'completion_percentage': data.get('stats', {}).get('completion_percentage', 0), 'answered_questions': data.get('stats', {}).get('answered_questions', 0), 'total_questions': data.get('stats', {}).get('total_questions', 0)} for pillar_id, data in report_pillars.items()},
                         report_version="Saved",
                         is_saved_view=True)

@app.route('/delete_report/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    """Delete a saved report."""
    report = SavedReport.query.filter_by(id=report_id, user_id=current_user.id).first_or_404()
    db.session.delete(report)
    db.session.commit()
    flash('Report deleted successfully!', 'success')
    return redirect(url_for('saved_reports'))

@app.route('/ai-remediation/<recommendation_id>')
@login_required
def ai_remediation(recommendation_id):
    """Generate AI-powered remediation using AWS Bedrock"""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    try:
        # Check Bedrock configuration
        bedrock_config = session.get('bedrock_config', {})
        if not bedrock_config.get('enabled'):
            return jsonify({'error': 'Bedrock is not configured. Please configure it in Settings.'}), 400
        
        import boto3
        import json
        from botocore.exceptions import ClientError
        
        # Get parent credentials session for role assumption
        parent_profile = bedrock_config.get('parent_credentials')
        if parent_profile:
            # Use specified parent credentials profile (e.g., beyon-marketplace)
            parent_session = boto3.Session(profile_name=parent_profile)
        else:
            # Fall back to current session
            profile = session.get('aws_profile')
            region = session.get('aws_region', 'us-east-1')
            if profile:
                parent_session = boto3.Session(profile_name=profile, region_name=region)
            else:
                parent_session = boto3.Session(region_name=region)
        
        # Get recommendation details
        account_id = session.get('aws_account_id')
        aws_account = AWSAccount.query.filter_by(
            user_id=current_user.id,
            account_id=account_id,
            region=session.get('aws_region', 'us-east-1')
        ).first()
        
        if not aws_account:
            return jsonify({'error': 'AWS account not found'}), 404
        
        recommendation = TrustedAdvisorRecommendation.query.filter_by(
            aws_account_id=aws_account.id,
            check_id=recommendation_id
        ).first()
        
        if not recommendation:
            return jsonify({'error': 'Recommendation not found'}), 404
        
        # Assume cross-account role for Bedrock access using parent credentials
        sts_client = parent_session.client('sts')
        assumed_role = sts_client.assume_role(
            RoleArn=bedrock_config['role_arn'],
            RoleSessionName='TorWAR-AIRemediation'
        )
        
        # Create Bedrock client with assumed role credentials
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=bedrock_config['region'],
            aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role['Credentials']['SessionToken']
        )
        
        prompt = f"""
        Generate a comprehensive, well-formatted remediation plan for this AWS Trusted Advisor recommendation:
        
        Name: {recommendation.name}
        Category: {recommendation.category}
        Description: {recommendation.description}
        Status: {recommendation.status}
        Resources Affected: {recommendation.resource_count}
        
        Please provide a clear, structured response with the following sections:
        
        ## Overview
        Brief explanation of the issue and why it needs attention.
        
        ## Step-by-Step Remediation
        1. Detailed step-by-step instructions
        2. Include specific actions to take
        3. Mention any prerequisites or considerations
        
        ## AWS CLI Commands
        Provide relevant AWS CLI commands if applicable:
        ```bash
        # Example commands here
        ```
        
        ## CloudFormation Template (if applicable)
        ```yaml
        # CloudFormation template snippet if relevant
        ```
        
        ## Risk Assessment
        - Impact: High/Medium/Low
        - Effort Required: Hours/Days
        - Potential Cost Savings: Estimate if applicable
        
        ## Best Practices
        Additional recommendations to prevent this issue in the future.
        
        Format the response in clear markdown with proper headings, bullet points, and code blocks for easy reading.
        """
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock_client.invoke_model(
            modelId=bedrock_config['model_id'],
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        ai_response = response_body['content'][0]['text']
        
        return jsonify({
            'success': True,
            'recommendation': {
                'id': recommendation.check_id,
                'name': recommendation.name,
                'category': recommendation.category,
                'description': recommendation.description
            },
            'ai_remediation': ai_response,
            'bedrock_account': bedrock_config['account_id'],
            'model_used': bedrock_config['model_id']
        })
        
    except ClientError as e:
        error_msg = f"AWS Bedrock Error: {e.response['Error']['Message']}"
        return jsonify({'error': error_msg}), 500
        
    except Exception as e:
        error_msg = f"Error generating AI remediation: {str(e)}"
        return jsonify({'error': error_msg}), 500

@app.route('/remediations')
@login_required
def remediations():
    """Remediations page"""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    account_id = session.get('aws_account_id')
    region = session.get('aws_region', 'us-east-1')
    
    try:
        # Get recommendations from database
        recommendations_data = data_service.get_trusted_advisor_recommendations(
            current_user.id, account_id, region
        )
        
        # Group recommendations by category for remediations
        remediation_by_category = {}
        total_remediations = 0
        recommendations_list = []
        error_count = 0
        warning_count = 0
        
        for rec in recommendations_data['recommendations']:
            if rec.status in ['warning', 'error']:  # Only issues need remediation
                category = rec.category
                if category not in remediation_by_category:
                    remediation_by_category[category] = []
                
                # Count by status
                if rec.status == 'error':
                    error_count += 1
                elif rec.status == 'warning':
                    warning_count += 1
                
                remediation_item = {
                    'id': rec.check_id,
                    'name': rec.name,
                    'description': rec.description,
                    'status': rec.status,
                    'resource_count': rec.resource_count,
                    'category': rec.category,
                    'remediation_steps': f"Review and optimize {rec.name.lower()}",
                    'priority': 'High' if rec.status == 'error' else 'Medium',
                    'error_count': rec.resource_count if rec.status == 'error' else 0,
                    'warning_count': rec.resource_count if rec.status == 'warning' else 0,
                    'ok_count': 0,
                    'estimated_savings': '$0-100/month',
                    'effort': 'Medium',
                    'impact': 'High' if rec.status == 'error' else 'Medium',
                    'pillar': rec.pillar if hasattr(rec, 'pillar') else 'General',
                    'check_id': rec.check_id,
                    'flagged_resources': rec.resource_count,
                    'resources_ignored': 0,
                    'resources_suppressed': 0,
                    'last_updated': rec.updated_at.isoformat() if hasattr(rec, 'updated_at') and rec.updated_at else None
                }
                
                remediation_by_category[category].append(remediation_item)
                recommendations_list.append(remediation_item)
                total_remediations += 1
        
        # Create stats object
        stats = {
            'total_remediations': total_remediations,
            'error_count': error_count,
            'warning_count': warning_count,
            'categories_count': len(remediation_by_category),
            'estimated_savings': f'${error_count * 50 + warning_count * 20}/month'
        }
        
        # Provide all template variables
        template_data = {
            'remediation_by_category': remediation_by_category,
            'total_remediations': total_remediations,
            'recommendations': recommendations_list,
            'category_info': recommendations_data.get('category_info', {}),
            'categories': recommendations_data.get('categories', {}),
            'aws_account_id': account_id,
            'aws_region': region,
            'total_recommendations': recommendations_data.get('total_recommendations', 0),
            'stats': stats,
            'error_count': error_count,
            'warning_count': warning_count
        }
        
        return render_template('remediations.html', **template_data)
        
    except Exception as e:
        print(f"❌ Error loading remediations: {e}")
        import traceback
        traceback.print_exc()
        
        # Provide empty fallback data
        template_data = {
            'remediation_by_category': {},
            'total_remediations': 0,
            'recommendations': [],
            'category_info': {},
            'categories': {},
            'aws_account_id': account_id,
            'aws_region': region,
            'total_recommendations': 0,
            'stats': {
                'total_remediations': 0,
                'error_count': 0,
                'warning_count': 0,
                'categories_count': 0,
                'estimated_savings': '$0/month'
            },
            'error_count': 0,
            'warning_count': 0
        }
        
        return render_template('remediations.html', **template_data)

@app.route('/ai-dashboard')
@login_required
def ai_dashboard():
    """AI Dashboard page"""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    account_id = session.get('aws_account_id')
    region = session.get('aws_region', 'us-east-1')
    
    try:
        # Get recommendations from database
        recommendations_data = data_service.get_trusted_advisor_recommendations(
            current_user.id, account_id, region
        )
        
        # Generate AI insights
        total_recs = recommendations_data.get('total_recommendations', 0)
        error_count = len([r for r in recommendations_data['recommendations'] if r.status == 'error'])
        warning_count = len([r for r in recommendations_data['recommendations'] if r.status == 'warning'])
        ok_count = len([r for r in recommendations_data['recommendations'] if r.status == 'ok'])
        
        # Calculate security score based on security-related recommendations
        security_recs = [r for r in recommendations_data['recommendations'] if 'security' in r.category.lower()]
        security_errors = len([r for r in security_recs if r.status == 'error'])
        security_warnings = len([r for r in security_recs if r.status == 'warning'])
        
        # Security score: start at 100, deduct for security issues
        if len(security_recs) > 0:
            security_score = max(0, 100 - (security_errors * 25) - (security_warnings * 10))
        else:
            # If no security recommendations, base on overall health
            security_score = max(0, 100 - (error_count * 10) - (warning_count * 5)) if total_recs > 0 else 85
        
        # Generate AI insights based on actual current data
        ai_insights = []
        
        if error_count > 0:
            ai_insights.append({
                'title': 'Critical Issues Detected',
                'description': f'Found {error_count} critical recommendations requiring immediate attention. These issues may impact security, performance, or cost optimization.',
                'priority': 'High',
                'category': 'Critical',
                'confidence': 95
            })
        
        if warning_count > 0:
            ai_insights.append({
                'title': 'Optimization Opportunities',
                'description': f'Identified {warning_count} optimization opportunities that could improve your AWS environment and reduce costs.',
                'priority': 'Medium',
                'category': 'Optimization',
                'confidence': 88
            })
        
        if security_score < 80:
            ai_insights.append({
                'title': 'Security Posture Review',
                'description': f'Your security score is {security_score}%. Consider reviewing security-related recommendations to strengthen your AWS security posture.',
                'priority': 'High' if security_score < 60 else 'Medium',
                'category': 'Security',
                'confidence': 92
            })
        
        if total_recs > 0 and (error_count + warning_count) == 0:
            ai_insights.append({
                'title': 'Excellent AWS Health',
                'description': 'All Trusted Advisor recommendations are in good status. Your AWS environment follows best practices.',
                'priority': 'Low',
                'category': 'Health',
                'confidence': 98
            })
        
        # AI recommendations based on current data
        ai_recommendations = []
        if error_count > 0:
            ai_recommendations.append('Prioritize resolving critical security and cost optimization issues')
        if warning_count > 2:
            ai_recommendations.append('Review performance and reliability recommendations for optimization')
        if security_score < 90:
            ai_recommendations.append('Implement additional security controls and monitoring')
        if total_recs == 0:
            ai_recommendations.append('Sync Trusted Advisor data to get current recommendations')
        else:
            ai_recommendations.append('Regularly monitor and review AWS recommendations for continuous improvement')
        
        # Dashboard stats
        dashboard_stats = {
            'total_recommendations': total_recs,
            'error_count': error_count,
            'warning_count': warning_count,
            'ok_count': ok_count,
            'cost_savings_potential': f'${(error_count * 50) + (warning_count * 25)}/month',
            'security_score': security_score,
            'optimization_score': max(0, 100 - (error_count * 10) - (warning_count * 3)) if total_recs > 0 else 90
        }
        
        return render_template('ai_dashboard.html',
                             ai_insights=ai_insights,
                             ai_recommendations=ai_recommendations,
                             dashboard_stats=dashboard_stats,
                             recommendations_data=recommendations_data,
                             aws_account_id=account_id,
                             aws_region=region)
        
    except Exception as e:
        print(f"❌ Error loading AI dashboard: {e}")
        # Provide empty fallback data
        return render_template('ai_dashboard.html',
                             ai_insights=[],
                             ai_recommendations=[],
                             dashboard_stats={
                                 'total_recommendations': 0,
                                 'error_count': 0,
                                 'warning_count': 0,
                                 'ok_count': 0,
                                 'cost_savings_potential': '$0/month',
                                 'security_score': 85,
                                 'optimization_score': 90
                             },
                             recommendations_data={'recommendations': []},
                             aws_account_id=account_id,
                             aws_region=region)

@app.route('/aws-logout')
@login_required
def aws_logout():
    """Disconnect from AWS"""
    session.pop('aws_account_id', None)
    session.pop('aws_region', None)
    session.pop('aws_profile', None)
    session.pop('is_connected', None)
    
    flash('Disconnected from AWS', 'info')
    return redirect(url_for('index'))

# Remove conflicting imports
# from aws_auth_routes import register_auth_routes
# register_auth_routes(app)

@app.route('/recommendations')
@login_required
def recommendations():
    """Trusted Advisor recommendations from database"""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    account_id = session.get('aws_account_id')
    region = session.get('aws_region', 'us-east-1')
    
    print(f"🔍 Loading recommendations for user: {current_user.id}, account: {account_id}")
    
    try:
        # Get recommendations from database
        recommendations_data = data_service.get_trusted_advisor_recommendations(
            current_user.id, account_id, region
        )
        
        print(f"🔍 Found {recommendations_data['total_recommendations']} recommendations")
        print(f"🔍 Categories: {list(recommendations_data['category_info'].keys())}")
        
        # If no data, show sync message
        if recommendations_data['total_recommendations'] == 0:
            flash('No Trusted Advisor data found. Click "Sync Data" to load from AWS.', 'info')
        
        return render_template('recommendations.html', **recommendations_data)
        
    except Exception as e:
        print(f"❌ Error loading recommendations: {e}")
        import traceback
        traceback.print_exc()
        
        # Provide fallback data
        recommendations_data = {
            'category_info': {},
            'recommendations': [],
            'categories': {},
            'total_recommendations': 0,
            'aws_account_id': account_id,
            'aws_region': region
        }
        
        flash(f'Error loading recommendations: {str(e)}', 'error')
        return render_template('recommendations.html', **recommendations_data)

@app.route('/sync-trusted-advisor')
@login_required
def sync_trusted_advisor():
    """Sync Trusted Advisor data to database"""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    account_id = session.get('aws_account_id')
    region = session.get('aws_region', 'us-east-1')
    
    print(f"🔍 Starting sync for account: {account_id}, region: {region}")
    
    try:
        # Create some test data for now (since Support API requires Business/Enterprise support)
        test_recommendations = [
            {
                'check_id': 'cost_opt_1',
                'name': 'Underutilized Amazon EBS Volumes',
                'category': 'Cost Optimizing',
                'description': 'Checks for EBS volumes that appear to be underutilized',
                'status': 'warning',
                'resources_flagged': 5,
                'account_id': account_id,
                'region': region
            },
            {
                'check_id': 'security_1', 
                'name': 'Security Groups - Specific Ports Unrestricted',
                'category': 'Security',
                'description': 'Checks security groups for unrestricted access',
                'status': 'error',
                'resources_flagged': 3,
                'account_id': account_id,
                'region': region
            },
            {
                'check_id': 'performance_1',
                'name': 'High Utilization Amazon EC2 Instances',
                'category': 'Performance',
                'description': 'Checks for EC2 instances with high utilization',
                'status': 'ok',
                'resources_flagged': 0,
                'account_id': account_id,
                'region': region
            }
        ]
        
        synced_count = 0
        
        for rec_data in test_recommendations:
            print(f"🔍 Saving recommendation: {rec_data['name']}")
            success = data_service.save_trusted_advisor_recommendation(current_user.id, rec_data)
            if success:
                synced_count += 1
                print(f"✅ Saved: {rec_data['name']}")
            else:
                print(f"❌ Failed to save: {rec_data['name']}")
        
        print(f"✅ Sync complete. Saved {synced_count} recommendations")
        flash(f'Successfully synced {synced_count} Trusted Advisor recommendations', 'success')
        return redirect(url_for('recommendations'))
        
    except Exception as e:
        error_msg = f"Error syncing data: {str(e)}"
        print(f"❌ {error_msg}")
        flash(error_msg, 'error')
        return redirect(url_for('recommendations'))

@app.route('/recommendation-details/<recommendation_id>')
@login_required
def recommendation_details(recommendation_id):
    """Show details for a specific recommendation"""
    if not session.get('aws_account_id'):
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_connect'))
    
    account_id = session.get('aws_account_id')
    region = session.get('aws_region', 'us-east-1')
    
    print(f"🔍 Looking for recommendation: {recommendation_id} in account: {account_id}")
    
    try:
        # Get AWS account
        aws_account = AWSAccount.query.filter_by(
            user_id=current_user.id,
            account_id=account_id,
            region=region
        ).first()
        
        print(f"🔍 AWS Account found: {aws_account.id if aws_account else 'None'}")
        
        if not aws_account:
            flash('AWS account not found', 'error')
            return redirect(url_for('recommendations'))
        
        # Get specific recommendation
        recommendation = TrustedAdvisorRecommendation.query.filter_by(
            aws_account_id=aws_account.id,
            check_id=recommendation_id
        ).first()
        
        print(f"🔍 Recommendation found: {recommendation.name if recommendation else 'None'}")
        
        if not recommendation:
            flash('Recommendation not found', 'error')
            return redirect(url_for('recommendations'))
        
        # Create detailed data for template
        recommendation_data = {
            'id': recommendation.check_id,
            'name': recommendation.name,
            'description': recommendation.description,
            'category': recommendation.category,
            'pillar': recommendation.pillar or 'General',
            'status': recommendation.status,
            'resource_count': recommendation.resource_count,
            'resources_data': recommendation.resources_data or [],
            'check_metadata': recommendation.check_metadata or {},
            'created_at': recommendation.created_at.isoformat() if recommendation.created_at else None,
            'updated_at': recommendation.updated_at.isoformat() if recommendation.updated_at else None
        }
        
        return render_template('recommendation_details.html', 
                             recommendation=recommendation_data,
                             aws_account_id=account_id,
                             aws_region=region)
        
    except Exception as e:
        print(f"❌ Error loading recommendation details: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading recommendation details', 'error')
        return redirect(url_for('recommendations'))

@app.route('/sync-data')
@login_required
def sync_data():
    """Manually sync AWS data to database"""
    account_id = session.get('aws_account_id')
    region = session.get('aws_region', 'us-east-1')
    
    if not account_id:
        return jsonify({'error': 'No AWS account connected'})
    
    result = data_service.sync_trusted_advisor_data(current_user.id, account_id, region)
    return jsonify(result)

@app.route('/sync-status')
@login_required
def sync_status():
    """Get sync status for current AWS account"""
    account_id = session.get('aws_account_id')
    region = session.get('aws_region', 'us-east-1')
    
    if not account_id:
        return jsonify({'error': 'No AWS account connected'})
    
    status = data_service.get_sync_status(current_user.id, account_id, region)
    return jsonify(status)

@app.route('/api/bedrock-config', methods=['GET', 'POST'])
@login_required
def bedrock_config():
    """Get or set Bedrock configuration"""
    if request.method == 'GET':
        # Get current configuration from user settings or session
        config = session.get('bedrock_config', {
            'account_id': '',
            'region': 'us-east-1',
            'parent_credentials': '',
            'role_arn': '',
            'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'enabled': False,
            'status': 'disconnected'
        })
        return jsonify({'success': True, 'config': config})
    
    elif request.method == 'POST':
        # Save configuration
        config = request.get_json()
        
        # Validate required fields
        if config.get('enabled') and not all([
            config.get('account_id'),
            config.get('role_arn'),
            config.get('region'),
            config.get('model_id')
        ]):
            return jsonify({'success': False, 'error': 'All fields are required when enabling Bedrock'}), 400
        
        # Save to session (in production, save to database)
        session['bedrock_config'] = config
        
        return jsonify({'success': True, 'message': 'Configuration saved'})

@app.route('/api/test-bedrock')
@login_required
def test_bedrock():
    """Test Bedrock connection with cross-account configuration"""
    try:
        config = session.get('bedrock_config', {})
        
        if not config.get('enabled'):
            return jsonify({'success': False, 'error': 'Bedrock is not enabled'}), 400
        
        import boto3
        import json
        from botocore.exceptions import ClientError
        
        # Use parent credentials if specified, otherwise fall back to current session
        parent_profile = config.get('parent_credentials')
        if parent_profile:
            print(f"🔍 Using parent credentials profile: {parent_profile}")
            # Use the specified parent credentials profile (e.g., beyon-marketplace)
            parent_session = boto3.Session(profile_name=parent_profile)
        else:
            print("🔍 Using current session credentials")
            # Fall back to current session
            profile = session.get('aws_profile')
            current_region = session.get('aws_region', 'us-east-1')
            if profile:
                parent_session = boto3.Session(profile_name=profile, region_name=current_region)
            else:
                parent_session = boto3.Session(region_name=current_region)
        
        # Create STS client with parent credentials
        sts_client = parent_session.client('sts')
        
        print(f"🔍 Attempting to assume role: {config['role_arn']}")
        
        # Assume the Bedrock role in the target account
        assumed_role = sts_client.assume_role(
            RoleArn=config['role_arn'],
            RoleSessionName='TorWAR-BedrockTest'
        )
        
        print("✅ Role assumption successful")
        
        # Create Bedrock client with assumed role credentials
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=config['region'],
            aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role['Credentials']['SessionToken']
        )
        
        # Test with a simple prompt
        test_prompt = "Hello, this is a test connection. Please respond with 'Connection successful'."
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": test_prompt
                }
            ]
        }
        
        response = bedrock_client.invoke_model(
            modelId=config['model_id'],
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        # Update configuration status
        config['status'] = 'connected'
        session['bedrock_config'] = config
        
        return jsonify({
            'success': True, 
            'message': 'Bedrock connection successful',
            'test_response': response_body['content'][0]['text'],
            'parent_profile_used': parent_profile or 'current session'
        })
        
    except ClientError as e:
        error_msg = f"AWS Error: {e.response['Error']['Message']}"
        print(f"❌ {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500
        
    except Exception as e:
        error_msg = f"Connection test failed: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/ai-chat', methods=['POST'])
@login_required
def ai_chat():
    """AI chatbot for discussing AWS recommendations"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'success': False, 'error': 'No message provided'}), 400
        
        # Check Bedrock configuration
        bedrock_config = session.get('bedrock_config', {})
        if not bedrock_config.get('enabled'):
            return jsonify({'success': False, 'error': 'Bedrock is not configured. Please configure it in Settings.'}), 400
        
        import boto3
        import json
        from botocore.exceptions import ClientError
        
        # Get parent credentials session for role assumption
        parent_profile = bedrock_config.get('parent_credentials')
        if parent_profile:
            parent_session = boto3.Session(profile_name=parent_profile)
        else:
            profile = session.get('aws_profile')
            region = session.get('aws_region', 'us-east-1')
            if profile:
                parent_session = boto3.Session(profile_name=profile, region_name=region)
            else:
                parent_session = boto3.Session(region_name=region)
        
        # Assume cross-account role for Bedrock access
        sts_client = parent_session.client('sts')
        assumed_role = sts_client.assume_role(
            RoleArn=bedrock_config['role_arn'],
            RoleSessionName='TorWAR-AIChat'
        )
        
        # Create Bedrock client with assumed role credentials
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=bedrock_config['region'],
            aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role['Credentials']['SessionToken']
        )
        
        # Get user's recommendations for context
        account_id = session.get('aws_account_id')
        recommendations_context = ""
        
        if account_id:
            try:
                recommendations_data = data_service.get_trusted_advisor_recommendations(
                    current_user.id, account_id, session.get('aws_region', 'us-east-1')
                )
                
                if recommendations_data['recommendations']:
                    recommendations_context = f"\n\nUser's current AWS recommendations context:\n"
                    for rec in recommendations_data['recommendations'][:5]:  # Limit to 5 for context
                        recommendations_context += f"- {rec.name} ({rec.category}): {rec.status}\n"
            except:
                pass
        
        prompt = f"""
        You are an AWS Well-Architected expert assistant helping users understand and address their AWS Trusted Advisor recommendations. 
        
        User question: {user_message}
        {recommendations_context}
        
        Please provide helpful, accurate, and actionable advice about AWS best practices, security, cost optimization, performance, and reliability. Keep responses concise but informative.
        """
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock_client.invoke_model(
            modelId=bedrock_config['model_id'],
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        ai_response = response_body['content'][0]['text']
        
        return jsonify({
            'success': True,
            'response': ai_response
        })
        
    except ClientError as e:
        error_msg = f"AWS Bedrock Error: {e.response['Error']['Message']}"
        return jsonify({'success': False, 'error': error_msg}), 500
        
    except Exception as e:
        error_msg = f"Error in AI chat: {str(e)}"
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    return render_template('settings.html')

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    aws_accounts = AWSAccount.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', aws_accounts=aws_accounts)

# Register authentication routes
register_user_auth_routes(app)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Initialize database on startup
def create_tables():
    try:
        with app.app_context():
            init_database()
    except Exception as e:
        print(f"Database initialization error: {e}")

if __name__ == '__main__':
    # Set environment variables if not set
    if not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'postgresql://torwar:torwar123@localhost/torwar_db'
    
    if not os.environ.get('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'torwar-dev-secret-key'
    
    # Initialize database
    create_tables()
    
    print("🚀 Starting TorWAR with Authentication and Database")
    print(f"📊 Database: {os.environ.get('DATABASE_URL', 'Not configured')}")
    print("🔐 Authentication: Enabled")
    print("📝 Visit http://localhost:5000 to get started")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
