#!/usr/bin/env python3
"""
TorWAR - AWS Well-Architected Review Tool
Author: Mohamed Toraif
Description: Streamlined AWS Well-Architected Review Tool with Enhanced Report Management

A comprehensive web application for conducting AWS Well-Architected Framework reviews
with advanced report generation, comparison, and management capabilities.

Features:
- AWS Profile Authentication
- Workload Management
- Interactive Well-Architected Reviews
- Professional Report Generation
- Report Comparison and Versioning
- Print-Optimized Layouts

Author: Mohamed Toraif
Created: 2024
License: MIT

Enhanced Features:
- Advanced Report Saving and Management
- Report Versioning and Comparison
- Improved Report Viewing
"""

import os
import json
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from botocore.exceptions import ClientError
from aws_helper import get_wellarchitected_client, test_aws_connection
from aws_auth_routes import register_auth_routes
from report_manager import ReportManager
from trusted_advisor_helper import (
    get_all_trusted_advisor_recommendations,
    get_trusted_advisor_summary,
    get_trusted_advisor_check_categories,
    refresh_trusted_advisor_check
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Debug control - only print DEBUG messages if explicitly enabled
DEBUG_ENABLED = os.environ.get('DEBUG_REPORTS', 'false').lower() == 'true'

def debug_print(message):
    """Print debug message only if DEBUG_REPORTS environment variable is true."""
    if DEBUG_ENABLED:
        print(f"DEBUG: {message}")
    # In production, this does nothing, improving performance

def is_question_answered(question_data):
    """
    Determine if a question is answered based on SelectedChoices.
    Handles various edge cases like empty arrays, null values, etc.
    """
    selected_choices = question_data.get('SelectedChoices', [])
    
    # Handle None or undefined
    if selected_choices is None:
        return False
    
    # Handle empty list
    if not selected_choices:
        return False
    
    # Handle list with empty/null elements
    if isinstance(selected_choices, list):
        # Check if there are any non-empty, non-null choice selections
        valid_choices = [choice for choice in selected_choices if choice and str(choice).strip()]
        return len(valid_choices) > 0
    
    # Handle non-list values (shouldn't happen but just in case)
    return bool(selected_choices)

# Custom Jinja2 filter for choice mapping
def get_choice_titles(selected_choices, all_choices):
    """Map choice IDs to their titles."""
    if not selected_choices or not all_choices:
        return []
    
    titles = []
    for choice_id in selected_choices:
        for choice in all_choices:
            if choice.get('ChoiceId') == choice_id:
                titles.append(choice.get('Title', choice_id))
                break
        else:
            # Choice ID not found, add it as-is for debugging
            titles.append(f"{choice_id} (ID not found)")
    
    return titles

# Register the filter
app.jinja_env.filters['get_choice_titles'] = get_choice_titles

# Initialize Report Manager with correct data directory
data_dir = os.path.join(os.path.dirname(__file__), 'data', 'reports')
report_manager = ReportManager(data_dir)

# Register AWS authentication routes
register_auth_routes(app)

# Well-Architected Framework Pillars
PILLARS = {
    'operationalExcellence': 'Operational Excellence',
    'security': 'Security', 
    'reliability': 'Reliability',
    'performance': 'Performance Efficiency',
    'costOptimization': 'Cost Optimization',
    'sustainability': 'Sustainability'
}

def ensure_data_directories():
    """Ensure required data directories exist."""
    # Use current directory instead of /app for development
    base_dir = os.path.dirname(os.path.abspath(__file__))
    directories = [
        os.path.join(base_dir, 'data'),
        os.path.join(base_dir, 'data', 'reports'),
        os.path.join(base_dir, 'data', 'workloads'),
        os.path.join(base_dir, 'logs')
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Directory ensured: {directory}")
        except PermissionError:
            print(f"❌ Permission error creating {directory}: [Errno 13] Permission denied: '{directory}'")
        except Exception as e:
            print(f"❌ Error creating {directory}: {e}")

# Ensure directories exist on startup
ensure_data_directories()

@app.context_processor
def inject_globals():
    """Inject global variables into all templates."""
    from datetime import datetime
    
    # Check if properly authenticated (both session and valid connection)
    is_connected = False
    if 'aws_authenticated' in session and session.get('aws_authenticated'):
        is_connected = 'aws_region' in session and session.get('aws_region') is not None
    
    return {
        'is_connected': is_connected,
        'workload_id': session.get('workload_id'),
        'workload_name': session.get('workload_name'),
        'aws_account_id': session.get('aws_account_id'),
        'aws_account_alias': session.get('aws_account_alias'),
        'aws_region': session.get('aws_region'),
        'pillars': PILLARS,
        'now': datetime.now()
    }

@app.route('/')
def index():
    """Home page with dashboard including Trusted Advisor overview."""
    if DEBUG_ENABLED:
        print("DEBUG: Accessing main dashboard")
    
    # Check if user is authenticated with AWS
    aws_connected = 'aws_region' in session
    
    context = {
        'aws_connected': aws_connected,
        'aws_region': session.get('aws_region', 'Not connected'),
        'account_id': session.get('account_id', 'Not connected')
    }
    
    if aws_connected:
        try:
            # Get Well-Architected workloads count
            wa_client = get_wellarchitected_client()
            if wa_client:
                workloads_response = wa_client.list_workloads(MaxResults=50)
                context['workload_count'] = len(workloads_response.get('WorkloadSummaries', []))
            else:
                context['workload_count'] = 0
            
            # Get Trusted Advisor summary
            ta_summary = get_trusted_advisor_summary()
            context['trusted_advisor'] = ta_summary
            
            if DEBUG_ENABLED:
                print(f"DEBUG: Trusted Advisor available: {ta_summary.get('available', False)}")
                if ta_summary.get('available'):
                    print(f"DEBUG: TA High Priority: {ta_summary.get('high_priority_count', 0)}")
                    print(f"DEBUG: TA Medium Priority: {ta_summary.get('medium_priority_count', 0)}")
            
        except Exception as e:
            if DEBUG_ENABLED:
                print(f"DEBUG: Error getting dashboard data: {e}")
            context['workload_count'] = 0
            context['trusted_advisor'] = {'available': False, 'error': str(e)}
    else:
        context['workload_count'] = 0
        context['trusted_advisor'] = {'available': False, 'error': 'Not connected to AWS'}
    
    return render_template('index.html', **context)

@app.route('/aws-status')
def aws_status():
    """Show AWS connection status and details."""
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    try:
        from aws_helper import test_aws_connection, get_account_alias
        
        # Test connection
        success, message, account_info = test_aws_connection()
        
        if success:
            # Get additional account information
            account_alias = get_account_alias()
            
            connection_details = {
                'status': 'Connected',
                'message': message,
                'account_id': account_info.get('account_id'),
                'account_alias': account_alias,
                'user_id': account_info.get('user_id'),
                'arn': account_info.get('arn'),
                'region': account_info.get('region'),
                'profile': session.get('aws_profile', 'default'),
                'workload_count': account_info.get('workload_count', 0),
                'auth_time': session.get('aws_auth_time')
            }
        else:
            connection_details = {
                'status': 'Error',
                'message': message,
                'account_id': session.get('aws_account_id'),
                'region': session.get('aws_region'),
                'profile': session.get('aws_profile', 'default'),
                'auth_time': session.get('aws_auth_time')
            }
        
        return render_template('aws_status.html', details=connection_details)
        
    except Exception as e:
        flash(f'Error checking AWS status: {str(e)}', 'error')
        return redirect(url_for('index'))

# ============================================================================
# WORKLOAD MANAGEMENT
# ============================================================================

@app.route('/workloads')
def list_workloads():
    """List all workloads in the account."""
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    try:
        wa_client = get_wellarchitected_client()
        if not wa_client:
            flash('Unable to connect to AWS Well-Architected service', 'error')
            return redirect(url_for('index'))
            
        response = wa_client.list_workloads()
        workloads = response.get('WorkloadSummaries', [])
        
        return render_template('list_workloads.html', workloads=workloads)
    except Exception as e:
        flash(f'Error listing workloads: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/workloads/select/<workload_id>')
def select_workload(workload_id):
    """Select a workload for review."""
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    try:
        wa_client = get_wellarchitected_client()
        response = wa_client.get_workload(WorkloadId=workload_id)
        workload = response.get('Workload', {})
        
        session['workload_id'] = workload_id
        session['workload_name'] = workload.get('WorkloadName', 'Unknown')
        
        flash(f'Selected workload: {workload.get("WorkloadName")}', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error selecting workload: {str(e)}', 'danger')
        return redirect(url_for('list_workloads'))

@app.route('/workloads/create', methods=['GET', 'POST'])
def create_workload():
    """Create a new workload."""
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        environment = request.form.get('environment')
        account_id = request.form.get('account_id')
        review_owner = request.form.get('review_owner')
        
        if not all([name, description, environment, account_id, review_owner]):
            flash('All fields are required', 'danger')
            return render_template('create_workload.html')
        
        try:
            wa_client = get_wellarchitected_client()
            response = wa_client.create_workload(
                WorkloadName=name,
                Description=description,
                Environment=environment,
                AccountIds=[account_id],
                AwsRegions=[session['aws_region']],
                Lenses=['wellarchitected'],
                ReviewOwner=review_owner
            )
            
            workload_id = response['WorkloadId']
            flash(f'Workload "{name}" created successfully!', 'success')
            return redirect(url_for('select_workload', workload_id=workload_id))
            
        except Exception as e:
            flash(f'Error creating workload: {str(e)}', 'danger')
    
    return render_template('create_workload.html')

# ============================================================================
# PILLAR SELECTION AND REVIEW
# ============================================================================

def get_all_pillar_answers(wa_client, workload_id, pillar_id):
    """
    Get all answers for a pillar with proper pagination handling.
    
    Args:
        wa_client: AWS Well-Architected client
        workload_id: The workload ID
        pillar_id: The pillar ID
        
    Returns:
        List of all answer summaries for the pillar
    """
    all_answers = []
    next_token = None
    
    while True:
        params = {
            'WorkloadId': workload_id,
            'LensAlias': 'wellarchitected',
            'PillarId': pillar_id
        }
        
        if next_token:
            params['NextToken'] = next_token
        
        response = wa_client.list_answers(**params)
        answers = response.get('AnswerSummaries', [])
        all_answers.extend(answers)
        
        next_token = response.get('NextToken')
        if not next_token:
            break
    
    return all_answers

@app.route('/select_pillars')
def select_pillars():
    """Select pillars for review."""
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    if 'workload_id' not in session:
        flash('Please select a workload first', 'warning')
        return redirect(url_for('list_workloads'))
    
    # Get question counts for each pillar
    pillar_stats = {}
    wa_client = get_wellarchitected_client()
    workload_id = session['workload_id']
    
    if wa_client:
        for pillar_id in PILLARS.keys():
            try:
                # Use pagination helper to get all answers
                answers = get_all_pillar_answers(wa_client, workload_id, pillar_id)
                
                total_questions = len(answers)
                # Use standardized answered questions counting
                answered_questions = sum(1 for answer in answers if is_question_answered(answer))
                
                # Count risk levels
                risk_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'NONE': 0, 'UNANSWERED': 0}
                for answer in answers:
                    risk = answer.get('Risk', 'UNANSWERED')
                    risk_counts[risk] = risk_counts.get(risk, 0) + 1
                
                pillar_stats[pillar_id] = {
                    'total_questions': total_questions,
                    'answered_questions': answered_questions,
                    'unanswered_questions': total_questions - answered_questions,
                    'risk_counts': risk_counts,
                    'completion_percentage': round((answered_questions / total_questions * 100) if total_questions > 0 else 0, 1)
                }
                
            except Exception as e:
                print(f"Error getting stats for pillar {pillar_id}: {e}")
                pillar_stats[pillar_id] = {
                    'total_questions': 0,
                    'answered_questions': 0,
                    'unanswered_questions': 0,
                    'risk_counts': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'NONE': 0, 'UNANSWERED': 0},
                    'completion_percentage': 0
                }
    
    return render_template('select_pillars.html', 
                         pillar_stats=pillar_stats, 
                         pillars=PILLARS,
                         selected_pillars=session.get('selected_pillars', []))

@app.route('/routes')
def list_routes():
    """List all available routes for debugging."""
    routes_info = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':  # Skip static file routes
            routes_info.append(f"{rule.rule} -> {rule.endpoint}")
    
    return f"""
    <html>
    <head><title>TorWAR Routes</title></head>
    <body>
        <h1>TorWAR Available Routes</h1>
        <ul>
            {''.join(f'<li><code>{route}</code></li>' for route in sorted(routes_info))}
        </ul>
        <p><a href="/">← Back to Home</a></p>
    </body>
    </html>
    """

@app.route('/review/')
def review_redirect():
    """Redirect /review/ to pillar selection."""
    return redirect(url_for('select_pillars'))

@app.route('/start_review', methods=['POST'])
def start_review():
    """Start the review process with selected pillars."""
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    if 'workload_id' not in session:
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

@app.route('/review_pillar/<pillar_id>')
@app.route('/review/<pillar_id>')  # Add alias for common URL pattern
def review_pillar(pillar_id):
    """Review questions for a specific pillar."""
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    if 'workload_id' not in session:
        flash('Please select a workload first', 'warning')
        return redirect(url_for('list_workloads'))
    
    # Allow direct pillar access - don't require selected_pillars in session
    # If selected_pillars exists, use it for progress tracking
    # If not, treat this as a direct pillar review
    
    try:
        wa_client = get_wellarchitected_client()
        workload_id = session['workload_id']
        
        # Associate lens with workload
        try:
            wa_client.associate_lenses(
                WorkloadId=workload_id,
                LensAliases=['wellarchitected']
            )
        except ClientError as e:
            if 'ConflictException' not in str(e):
                raise e
        
        # Get questions for this pillar
        answers = get_all_pillar_answers(wa_client, workload_id, pillar_id)
        
        # Get detailed question information
        detailed_questions = []
        for index, answer in enumerate(answers, 1):  # Start numbering from 1
            try:
                question_response = wa_client.get_answer(
                    WorkloadId=workload_id,
                    LensAlias='wellarchitected',
                    QuestionId=answer['QuestionId']
                )
                question_data = question_response.get('Answer', {})
                # Add question number to the data
                question_data['QuestionNumber'] = index
                detailed_questions.append(question_data)
            except Exception as e:
                print(f"Error getting question details: {e}")
                continue
        
        # Calculate progress - handle both sequential and direct access
        selected_pillars = session.get('selected_pillars', [])
        
        if selected_pillars and pillar_id in selected_pillars:
            # Sequential review mode - show progress within selected pillars
            current_index = selected_pillars.index(pillar_id)
            progress_percentage = ((current_index + 1) / len(selected_pillars)) * 100
        else:
            # Direct pillar access mode - set up single pillar context
            selected_pillars = [pillar_id]
            current_index = 0
            progress_percentage = 100  # Single pillar = 100% of this review
        
        # Calculate next and previous pillars based on all available pillars
        all_pillar_ids = list(PILLARS.keys())
        current_pillar_index = all_pillar_ids.index(pillar_id) if pillar_id in all_pillar_ids else 0
        
        # Previous pillar (wrap around to last if at beginning)
        prev_pillar = all_pillar_ids[current_pillar_index - 1] if current_pillar_index > 0 else all_pillar_ids[-1]
        
        # Next pillar (wrap around to first if at end)
        next_pillar = all_pillar_ids[current_pillar_index + 1] if current_pillar_index < len(all_pillar_ids) - 1 else all_pillar_ids[0]
        
        return render_template('review_pillar.html', 
                             pillar_id=pillar_id,
                             pillar_name=PILLARS.get(pillar_id, pillar_id),
                             questions=detailed_questions,
                             selected_pillars=selected_pillars,
                             current_index=current_index,
                             progress_percentage=progress_percentage,
                             is_direct_access=pillar_id not in session.get('selected_pillars', []),
                             prev_pillar=prev_pillar,
                             next_pillar=next_pillar)
        
    except Exception as e:
        flash(f'Error loading pillar questions: {str(e)}', 'danger')
        return redirect(url_for('select_pillars'))

@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer_question(question_id):
    """Answer a specific question."""
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    if 'workload_id' not in session:
        flash('Please select a workload first', 'warning')
        return redirect(url_for('list_workloads'))
    
    if request.method == 'POST':
        # Handle form submission
        return handle_answer_submission(question_id)
    
    # Handle GET request - display the question
    try:
        wa_client = get_wellarchitected_client()
        workload_id = session['workload_id']
        
        # Get pillar_id from query parameters
        pillar_id = request.args.get('pillar_id', '')
        
        # Get all questions for this pillar to determine question number
        question_number = 1  # Default
        if pillar_id:
            try:
                all_answers = get_all_pillar_answers(wa_client, workload_id, pillar_id)
                for index, answer in enumerate(all_answers, 1):
                    if answer['QuestionId'] == question_id:
                        question_number = index
                        break
            except Exception as e:
                print(f"Error getting question number: {e}")
        
        # Get question details
        response = wa_client.get_answer(
            WorkloadId=workload_id,
            LensAlias='wellarchitected',
            QuestionId=question_id
        )
        
        raw_answer = response.get('Answer', {})
        
        # Restructure the data to match template expectations
        answer = {
            'Question': {
                'Title': raw_answer.get('QuestionTitle', ''),
                'Description': raw_answer.get('QuestionDescription', ''),
                'QuestionId': raw_answer.get('QuestionId', ''),
                'Choices': raw_answer.get('Choices', []),
                'QuestionNumber': question_number  # Add question number
            },
            'SelectedChoices': raw_answer.get('SelectedChoices', []),
            'ChoiceAnswers': raw_answer.get('ChoiceAnswers', []),
            'IsApplicable': raw_answer.get('IsApplicable', True),
            'Risk': raw_answer.get('Risk', ''),
            'Notes': raw_answer.get('Notes', ''),
            'HelpfulResourceUrl': raw_answer.get('HelpfulResourceUrl', ''),
            'ImprovementPlanUrl': raw_answer.get('ImprovementPlanUrl', '')
        }
        
        # Get navigation information
        prev_question = get_previous_question_id(wa_client, workload_id, pillar_id, question_id)
        next_question = get_next_question_id(wa_client, workload_id, pillar_id, question_id)
        
        return render_template('answer_question.html', 
                             answer=answer, 
                             pillar_id=pillar_id,
                             prev_question=prev_question,
                             next_question=next_question)
        
    except Exception as e:
        flash(f'Error loading question: {str(e)}', 'danger')
        return redirect(url_for('select_pillars'))

def get_previous_question_id(wa_client, workload_id, pillar_id, current_question_id):
    """Get the ID of the previous question in the pillar."""
    try:
        all_answers = get_all_pillar_answers(wa_client, workload_id, pillar_id)
        question_ids = [answer['QuestionId'] for answer in all_answers]
        
        if current_question_id in question_ids:
            current_index = question_ids.index(current_question_id)
            if current_index > 0:
                return question_ids[current_index - 1]
        
        return None
    except Exception as e:
        print(f"Error getting previous question: {e}")
        return None

def get_next_question_id(wa_client, workload_id, pillar_id, current_question_id):
    """Get the ID of the next question in the pillar."""
    try:
        all_answers = get_all_pillar_answers(wa_client, workload_id, pillar_id)
        question_ids = [answer['QuestionId'] for answer in all_answers]
        
        if current_question_id in question_ids:
            current_index = question_ids.index(current_question_id)
            if current_index < len(question_ids) - 1:
                return question_ids[current_index + 1]
        
        return None
    except Exception as e:
        print(f"Error getting next question: {e}")
        return None

def handle_answer_submission(question_id):
    """Handle the form submission for answering a question."""
    try:
        wa_client = get_wellarchitected_client()
        workload_id = session['workload_id']
        pillar_id = request.form.get('pillar_id', '')
        
        # Get form data
        not_applicable = request.form.get('not_applicable') == 'true'
        reason = request.form.get('reason', '') if not_applicable else ''
        selected_choices = request.form.getlist('choices') if not not_applicable else []
        notes = request.form.get('notes', '')
        
        # Prepare the update data
        update_data = {
            'WorkloadId': workload_id,
            'LensAlias': 'wellarchitected',
            'QuestionId': question_id,
            'SelectedChoices': selected_choices,
            'Notes': notes,
            'IsApplicable': not not_applicable
        }
        
        if not_applicable and reason:
            update_data['Reason'] = reason
        
        # Update the answer
        wa_client.update_answer(**update_data)
        
        flash('Answer saved successfully!', 'success')
        
        # Handle navigation buttons
        if 'prev_question' in request.form:
            # Navigate to previous question
            prev_question_id = get_previous_question_id(wa_client, workload_id, pillar_id, question_id)
            if prev_question_id:
                return redirect(url_for('answer_question', question_id=prev_question_id, pillar_id=pillar_id))
            else:
                flash('This is the first question in the pillar', 'info')
        elif 'next_question' in request.form or 'save_and_next' in request.form:
            # Navigate to next question
            next_question_id = get_next_question_id(wa_client, workload_id, pillar_id, question_id)
            if next_question_id:
                return redirect(url_for('answer_question', question_id=next_question_id, pillar_id=pillar_id))
            else:
                flash('This is the last question in the pillar', 'info')
                return redirect(url_for('review_pillar', pillar_id=pillar_id))
        
        # Default: stay on current question
        return redirect(url_for('answer_question', question_id=question_id, pillar_id=pillar_id))
        
    except Exception as e:
        flash(f'Error saving answer: {str(e)}', 'danger')
        return redirect(url_for('answer_question', question_id=question_id, pillar_id=request.form.get('pillar_id', '')))

@app.route('/save_answer', methods=['POST'])
def save_answer():
    """Save an answer to a question."""
    if 'aws_region' not in session:
        return jsonify({'success': False, 'message': 'Not connected to AWS'})
    
    if 'workload_id' not in session:
        return jsonify({'success': False, 'message': 'No workload selected'})
    
    try:
        question_id = request.json.get('question_id')
        selected_choices = request.json.get('selected_choices', [])
        notes = request.json.get('notes', '')
        is_applicable = request.json.get('is_applicable', True)
        
        wa_client = get_wellarchitected_client()
        workload_id = session['workload_id']
        
        # Update the answer
        wa_client.update_answer(
            WorkloadId=workload_id,
            LensAlias='wellarchitected',
            QuestionId=question_id,
            SelectedChoices=selected_choices,
            Notes=notes,
            IsApplicable=is_applicable
        )
        
        return jsonify({'success': True, 'message': 'Answer saved successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================================================
# ENHANCED REPORT MANAGEMENT
# ============================================================================

@app.route('/generate_report')
@app.route('/report')  # Add alias for common URL pattern
def generate_report():
    """Generate a comprehensive Well-Architected report."""
    if DEBUG_ENABLED:
        print("DEBUG: Starting report generation")
    
    if 'aws_region' not in session:
        debug_print("No AWS region in session")
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    if 'workload_id' not in session:
        debug_print("No workload_id in session")
        flash('Please select a workload first', 'warning')
        return redirect(url_for('list_workloads'))
    
    try:
        workload_id = session['workload_id']
        debug_print(f"Processing workload: {workload_id}")
        
        wa_client = get_wellarchitected_client()
        if not wa_client:
            debug_print("Failed to get Well-Architected client")
            flash('Unable to connect to AWS Well-Architected service', 'error')
            return redirect(url_for('index'))
        
        debug_print("Got Well-Architected client successfully")
        
        # Get workload details
        debug_print("Getting workload details")
        workload_response = wa_client.get_workload(WorkloadId=workload_id)
        workload = workload_response.get('Workload', {})
        debug_print(f"Processing workload: {workload.get('WorkloadName', 'Unknown')}")
        
        # Initialize data structures
        report_data = {
            'workload': workload,
            'pillars': {},
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_questions': 0,
                'answered_questions': 0,
                'high_risks': 0,
                'medium_risks': 0,
                'low_risks': 0,
                'no_risks': 0
            }
        }
        
        # Initialize overall statistics
        overall_stats = {
            'total_questions': 0,
            'answered_questions': 0,
            'not_applicable_questions': 0,
            'unanswered_questions': 0,
            'completion_percentage': 0
        }
        
        # Initialize risk counts
        risk_counts = {
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'NONE': 0
        }
        
        # Get selected pillars from session, default to all if none selected
        selected_pillars = session.get('selected_pillars', list(PILLARS.keys()))
        debug_print(f"Processing {len(selected_pillars)} pillars: {selected_pillars}")
        
        # Initialize pillar reviews
        pillar_reviews = {}
        
        # Only process selected pillars
        for pillar_id in selected_pillars:
            if pillar_id not in PILLARS:
                debug_print(f"Unknown pillar ID {pillar_id}, skipping")
                continue
                
            pillar_name = PILLARS[pillar_id]
            debug_print(f"Processing pillar: {pillar_id} - {pillar_name}")
            
            try:
                # Get answers for this pillar using pagination
                answers = get_all_pillar_answers(wa_client, workload_id, pillar_id)
                detailed_answers = []
                
                # Initialize pillar-specific statistics
                pillar_stats = {
                    'total_questions': len(answers),
                    'answered_questions': 0,
                    'not_applicable_questions': 0,
                    'completion_percentage': 0
                }
                
                pillar_risk_counts = {
                    'HIGH': 0,
                    'MEDIUM': 0,
                    'LOW': 0,
                    'NONE': 0
                }
                
                for answer in answers:
                    try:
                        # Get detailed answer
                        detail_response = wa_client.get_answer(
                            WorkloadId=workload_id,
                            LensAlias='wellarchitected',
                            QuestionId=answer['QuestionId']
                        )
                        detailed_answer = detail_response.get('Answer', {})
                        
                        # Ensure we have choice data - the get_answer call should include it
                        choices = detailed_answer.get('Choices', [])
                        selected_choices = detailed_answer.get('SelectedChoices', [])
                        question_id = detailed_answer.get('QuestionId', 'Unknown')
                        
                        # Debug logging
                        debug_print(f"Question {question_id}")
                        print(f"  - Selected Choices: {selected_choices}")
                        print(f"  - Available Choices: {len(choices)}")
                        
                        if choices:
                            print(f"  - First choice example: {choices[0].get('ChoiceId')} -> {choices[0].get('Title', 'No Title')}")
                        else:
                            print(f"  - WARNING: No choices data in response for {question_id}")
                            # Add empty choices list to prevent template errors
                            detailed_answer['Choices'] = []
                        
                        detailed_answers.append(detailed_answer)
                        
                        # Debug logging
                        question_id = detailed_answer.get('QuestionId', 'Unknown')
                        risk = detailed_answer.get('Risk')
                        selected_choices = detailed_answer.get('SelectedChoices', [])
                        debug_print(f"Question {question_id} - Risk: {risk}, Choices: {len(selected_choices)}")
                        
                        # Use standardized logic for determining if a question is answered
                        is_answered = is_question_answered(detailed_answer)
                        
                        if is_answered:
                            report_data['summary']['answered_questions'] += 1
                            overall_stats['answered_questions'] += 1
                            pillar_stats['answered_questions'] += 1
                            debug_print(f"Question {question_id} marked as ANSWERED - Choices: {detailed_answer.get('SelectedChoices', [])}")
                        else:
                            debug_print(f"Question {question_id} marked as UNANSWERED - Choices: {detailed_answer.get('SelectedChoices', [])}")
                            debug_print(f"Question {question_id} - SelectedChoices type: {type(detailed_answer.get('SelectedChoices'))}, value: {repr(detailed_answer.get('SelectedChoices'))}")
                        
                        if not detailed_answer.get('IsApplicable', True):
                            overall_stats['not_applicable_questions'] += 1
                            pillar_stats['not_applicable_questions'] += 1
                        
                        risk = detailed_answer.get('Risk', 'UNANSWERED')
                        if risk == 'HIGH':
                            report_data['summary']['high_risks'] += 1
                            risk_counts['HIGH'] += 1
                            pillar_risk_counts['HIGH'] += 1
                            print(f"DEBUG: Found HIGH risk for {question_id}")
                        elif risk == 'MEDIUM':
                            report_data['summary']['medium_risks'] += 1
                            risk_counts['MEDIUM'] += 1
                            pillar_risk_counts['MEDIUM'] += 1
                            print(f"DEBUG: Found MEDIUM risk for {question_id}")
                        elif risk == 'LOW':
                            report_data['summary']['low_risks'] += 1
                            risk_counts['LOW'] += 1
                            pillar_risk_counts['LOW'] += 1
                            print(f"DEBUG: Found LOW risk for {question_id}")
                        elif risk == 'NONE':
                            report_data['summary']['no_risks'] += 1
                            risk_counts['NONE'] += 1
                            pillar_risk_counts['NONE'] += 1
                            print(f"DEBUG: Found NONE risk for {question_id}")
                        else:
                            print(f"DEBUG: Question {question_id} has no risk assessment (unanswered)")
                            
                    except Exception as e:
                        print(f"Error getting answer details for {answer['QuestionId']}: {e}")
                        # Create a minimal question entry so it's still counted in the pillar
                        minimal_answer = {
                            'QuestionId': answer.get('QuestionId', 'Unknown'),
                            'QuestionTitle': answer.get('QuestionTitle', 'Question details unavailable'),
                            'Risk': 'UNANSWERED',
                            'SelectedChoices': [],
                            'Choices': [],
                            'Notes': f'Error loading question details: {str(e)}'
                        }
                        detailed_answers.append(minimal_answer)
                        continue
                
                # Add pillar question count to overall totals
                pillar_question_count = len(answers)
                report_data['summary']['total_questions'] += pillar_question_count
                overall_stats['total_questions'] += pillar_question_count
                
                # Calculate pillar completion percentage
                if pillar_stats['total_questions'] > 0:
                    pillar_stats['completion_percentage'] = round(
                        (pillar_stats['answered_questions'] / pillar_stats['total_questions']) * 100, 1
                    )
                
                report_data['pillars'][pillar_id] = {
                    'name': pillar_name,
                    'questions': detailed_answers,
                    'stats': pillar_stats,
                    'risk_counts': pillar_risk_counts
                }
                
                # Add to pillar reviews for template
                pillar_reviews[pillar_id] = {
                    'PillarName': pillar_name,
                    'RiskCounts': pillar_risk_counts,
                    'Statistics': pillar_stats,
                    'stats': pillar_stats,  # Add this for template compatibility
                    'risk_counts': pillar_risk_counts  # Add this for template compatibility
                }
                
                # Debug logging for pillar summary
                print(f"DEBUG: Pillar {pillar_id} summary:")
                print(f"  Total questions: {pillar_stats['total_questions']}")
                print(f"  Answered questions: {pillar_stats['answered_questions']}")
                print(f"  Risk counts: {pillar_risk_counts}")
                
                # Special debugging for Security pillar
                if pillar_id == 'security':
                    print(f"DEBUG: SECURITY PILLAR DETAILED ANALYSIS:")
                    print(f"  Questions processed: {len(detailed_answers)}")
                    answered_count = 0
                    for i, q in enumerate(detailed_answers):
                        is_answered = is_question_answered(q)
                        if is_answered:
                            answered_count += 1
                        print(f"    Q{i+1} ({q.get('QuestionId', 'Unknown')}): {'ANSWERED' if is_answered else 'UNANSWERED'} - Choices: {q.get('SelectedChoices', [])}")
                    print(f"  Manual count of answered questions: {answered_count}")
                    print(f"  Pillar stats answered count: {pillar_stats['answered_questions']}")
                    if answered_count != pillar_stats['answered_questions']:
                        print(f"  ⚠️ MISMATCH DETECTED! Manual: {answered_count}, Stats: {pillar_stats['answered_questions']}")
                
                # Add debugging for all pillars to catch the issue
                print(f"DEBUG: {pillar_name} PILLAR ANALYSIS:")
                answered_count_check = sum(1 for q in detailed_answers if is_question_answered(q))
                print(f"  Questions processed: {len(detailed_answers)}")
                print(f"  Manual answered count: {answered_count_check}")
                print(f"  Stats answered count: {pillar_stats['answered_questions']}")
                if answered_count_check != pillar_stats['answered_questions']:
                    print(f"  ⚠️ MISMATCH DETECTED in {pillar_name}! Manual: {answered_count_check}, Stats: {pillar_stats['answered_questions']}")
                    # Fix the mismatch
                    pillar_stats['answered_questions'] = answered_count_check
                    print(f"  ✅ CORRECTED: Updated stats to {answered_count_check}")
                
                
            except Exception as e:
                print(f"Error processing pillar {pillar_id}: {e}")
                continue
        
        # Calculate overall completion percentage
        overall_stats['unanswered_questions'] = overall_stats['total_questions'] - overall_stats['answered_questions']
        if overall_stats['total_questions'] > 0:
            overall_stats['completion_percentage'] = round(
                (overall_stats['answered_questions'] / overall_stats['total_questions']) * 100, 1
            )
        
        # Report version
        report_version = "1.0"
        
        # Debug logging for overall summary
        print(f"DEBUG: Overall report summary:")
        print(f"  Total questions: {overall_stats['total_questions']}")
        print(f"  Answered questions: {overall_stats['answered_questions']}")
        print(f"  Completion: {overall_stats['completion_percentage']}%")
        print(f"  Overall risk counts: {risk_counts}")
        print(f"  Pillar reviews keys: {list(pillar_reviews.keys())}")
        
        # Debug: Check individual pillar question counts
        pillar_question_totals = {}
        for pillar_id, pillar_data in report_data['pillars'].items():
            pillar_question_totals[pillar_id] = len(pillar_data.get('questions', []))
            print(f"  {pillar_data['name']}: {pillar_question_totals[pillar_id]} questions")
        
        total_from_pillars = sum(pillar_question_totals.values())
        print(f"DEBUG: Total questions from selected pillars: {total_from_pillars}")
        print(f"DEBUG: Total questions from counter: {overall_stats['total_questions']}")
        print(f"DEBUG: Selected pillars: {selected_pillars}")
        print(f"DEBUG: Processed {len(report_data['pillars'])} pillars out of {len(PILLARS)} total pillars")
        
        if total_from_pillars != overall_stats['total_questions']:
            print(f"WARNING: Question count mismatch! Pillar sum: {total_from_pillars}, Counter: {overall_stats['total_questions']}")
            # Use the pillar sum as it's more accurate
            overall_stats['total_questions'] = total_from_pillars
            report_data['summary']['total_questions'] = total_from_pillars
        
        # Don't store large report data in session to avoid cookie size limits
        # The save_report function will regenerate the data when needed
        print("DEBUG: Report generation completed successfully")
        
        
        return render_template('generate_report.html', 
                             report_data=report_data,
                             workload=workload,
                             pillars=PILLARS,
                             overall_stats=overall_stats,
                             risk_counts=risk_counts,
                             pillar_reviews=pillar_reviews,
                             report_version=report_version)
        
    except Exception as e:
        print(f"DEBUG: Exception in generate_report: {str(e)}")
        print(f"DEBUG: Exception type: {type(e).__name__}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/save_report', methods=['GET', 'POST'])
def save_report():
    """Save the current report with user-provided metadata."""
    if 'aws_region' not in session:
        return jsonify({'success': False, 'message': 'Not connected to AWS'})
    
    if 'workload_id' not in session:
        return jsonify({'success': False, 'message': 'No workload selected'})
    
    # Handle GET requests by redirecting to generate_report
    if request.method == 'GET':
        flash('Please use the Save Report button from the report page', 'info')
        return redirect(url_for('generate_report'))
    
    # Handle POST requests (actual save functionality)
    try:
        # Get form data
        custom_name = request.form.get('custom_name', '').strip()
        user_notes = request.form.get('user_notes', '').strip()
        
        workload_id = session['workload_id']
        workload_name = session['workload_name']
        
        # Debug logging
        print(f"DEBUG: Save report request for workload {workload_id}")
        print(f"DEBUG: Session keys: {list(session.keys())}")
        print(f"DEBUG: Has current_report_data: {'current_report_data' in session}")
        
        # Always regenerate report data to avoid session size issues
        print("DEBUG: Regenerating report data for saving...")
        flash('Generating report data for saving...', 'info')
        
        # Use a simplified approach - just call the report generation logic
        try:
            # Get the report data by calling the same logic as generate_report
            # but without rendering the template
            wa_client = get_wellarchitected_client()
            workload_response = wa_client.get_workload(WorkloadId=workload_id)
            workload = workload_response.get('Workload', {})
            
            # Initialize basic report structure
            report_data = {
                'workload': workload,
                'pillars': {},
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'summary': {
                    'total_questions': 0,
                    'answered_questions': 0,
                    'high_risks': 0,
                    'medium_risks': 0,
                    'low_risks': 0,
                    'no_risks': 0
                }
            }
            
            # Get basic pillar data for saving
            for pillar_id, pillar_name in PILLARS.items():
                try:
                    answers = get_all_pillar_answers(wa_client, workload_id, pillar_id)
                    report_data['pillars'][pillar_id] = {
                        'name': pillar_name,
                        'question_count': len(answers)
                    }
                    report_data['summary']['total_questions'] += len(answers)
                except Exception as e:
                    print(f"Error processing pillar {pillar_id}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error generating report data for saving: {e}")
            flash('Error generating report data', 'error')
            return redirect(url_for('generate_report'))
        
        # Save report using ReportManager
        report_id = report_manager.save_report(
            workload_id=workload_id,
            workload_name=workload_name,
            report_data=report_data,
            user_notes=user_notes,
            custom_name=custom_name
        )
        
        flash(f'Report saved successfully! Report ID: {report_id}', 'success')
        return redirect(url_for('saved_reports'))
        
    except Exception as e:
        flash(f'Error saving report: {str(e)}', 'danger')
        return redirect(url_for('generate_report'))

@app.route('/saved_reports')
def saved_reports():
    """View all saved reports."""
    try:
        # Get all saved reports
        all_reports = report_manager.get_saved_reports()
        
        # Group by workload for better organization
        workload_reports = {}
        for report in all_reports:
            workload_id = report['workload_id']
            if workload_id not in workload_reports:
                workload_reports[workload_id] = {
                    'workload_name': report['workload_name'],
                    'reports': []
                }
            workload_reports[workload_id]['reports'].append(report)
        
        return render_template('saved_reports.html', 
                             workload_reports=workload_reports,
                             all_reports=all_reports)
        
    except Exception as e:
        flash(f'Error loading saved reports: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/view_saved_report/<report_id>')
def view_saved_report(report_id):
    """View a specific saved report."""
    try:
        report = report_manager.get_report(report_id)
        if not report:
            flash('Report not found', 'error')
            return redirect(url_for('saved_reports'))
        
        # Extract data for the new template
        report_data = report.get('report_data', {})
        metadata = report.get('metadata', {})
        
        # Create pillar_reviews structure for template compatibility
        pillar_reviews = {}
        overall_risk_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'NONE': 0}
        
        if 'pillars' in report_data:
            for pillar_id, pillar_data in report_data['pillars'].items():
                questions = pillar_data.get('questions', [])
                
                # Calculate pillar statistics
                total_questions = len(questions)
                answered_questions = sum(1 for q in questions if q.get('SelectedChoices'))
                
                # Calculate risk counts for this pillar
                pillar_risk_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'NONE': 0}
                for question in questions:
                    risk = question.get('Risk')
                    if risk in pillar_risk_counts:
                        pillar_risk_counts[risk] += 1
                        overall_risk_counts[risk] += 1  # Add to overall counts
                
                pillar_reviews[pillar_id] = {
                    'stats': {
                        'total_questions': total_questions,
                        'answered_questions': answered_questions,
                        'completion_percentage': (answered_questions / total_questions * 100) if total_questions > 0 else 0
                    },
                    'risk_counts': pillar_risk_counts
                }
        
        # Create overall statistics
        overall_stats = {
            'total_questions': metadata.get('summary', {}).get('total_questions', 0),
            'answered_questions': metadata.get('summary', {}).get('answered_questions', 0),
            'completion_percentage': 0
        }
        
        if overall_stats['total_questions'] > 0:
            overall_stats['completion_percentage'] = round(
                (overall_stats['answered_questions'] / overall_stats['total_questions']) * 100, 1
            )
        
        # Use calculated risk counts instead of metadata
        risk_counts = overall_risk_counts
        
        # Create workload object for template
        workload = {
            'WorkloadName': metadata.get('workload_name', 'Unknown Workload')
        }
        
        return render_template('view_saved_report.html', 
                             report=report,
                             report_data=report_data,
                             workload=workload,
                             pillars=PILLARS,
                             overall_stats=overall_stats,
                             risk_counts=risk_counts,
                             pillar_reviews=pillar_reviews,
                             report_version=metadata.get('version', '1.0'))
        
    except Exception as e:
        flash(f'Error loading report: {str(e)}', 'danger')
        return redirect(url_for('saved_reports'))

@app.route('/delete_report/<report_id>', methods=['POST'])
def delete_report(report_id):
    """Delete a saved report."""
    try:
        success = report_manager.delete_report(report_id)
        if success:
            flash('Report deleted successfully', 'success')
        else:
            flash('Error deleting report', 'error')
            
    except Exception as e:
        flash(f'Error deleting report: {str(e)}', 'danger')
    
    return redirect(url_for('saved_reports'))

@app.route('/compare_reports')
def compare_reports():
    """Compare saved reports."""
    try:
        # Get all saved reports for comparison
        all_reports = report_manager.get_saved_reports()
        
        # Group by workload
        workload_reports = {}
        for report in all_reports:
            workload_id = report['workload_id']
            if workload_id not in workload_reports:
                workload_reports[workload_id] = {
                    'workload_name': report['workload_name'],
                    'reports': []
                }
            workload_reports[workload_id]['reports'].append(report)
        
        return render_template('compare_reports.html', 
                             workload_reports=workload_reports)
        
    except Exception as e:
        flash(f'Error loading reports for comparison: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/compare_reports_result')
def compare_reports_result():
    """Show comparison results between two reports."""
    report_id1 = request.args.get('report1')
    report_id2 = request.args.get('report2')
    
    if not report_id1 or not report_id2:
        flash('Please select two reports to compare', 'warning')
        return redirect(url_for('compare_reports'))
    
    if report_id1 == report_id2:
        flash('Please select two different reports to compare', 'warning')
        return redirect(url_for('compare_reports'))
    
    try:
        comparison = report_manager.compare_reports(report_id1, report_id2)
        
        return render_template('comparison_result.html', 
                             comparison=comparison,
                             pillars=PILLARS)
        
    except Exception as e:
        flash(f'Error comparing reports: {str(e)}', 'danger')
        return redirect(url_for('compare_reports'))

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_wa_client():
    """Get a Well-Architected client using session info."""
    return get_wellarchitected_client()

@app.route('/simple-auth', methods=['GET', 'POST'])
def simple_auth():
    """Simple authentication route for debugging."""
    if request.method == 'GET':
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Simple Auth - TorWAR</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h4>Simple AWS Authentication</h4>
                            </div>
                            <div class="card-body">
                                <form method="POST" action="/simple-auth">
                                    <div class="mb-3">
                                        <label class="form-label">Profile:</label>
                                        <input type="text" class="form-control" name="profile_name" value="beyon-marketplace" readonly>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Region:</label>
                                        <input type="text" class="form-control" name="region" value="me-south-1" readonly>
                                    </div>
                                    <button type="submit" class="btn btn-primary w-100">
                                        Authenticate Now
                                    </button>
                                </form>
                                <div class="mt-3">
                                    <a href="/aws_login" class="btn btn-outline-secondary">Back to Main Login</a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
    
    # Handle POST request
    try:
        from aws_auth import get_aws_authenticator
        
        auth = get_aws_authenticator()
        profile_name = request.form.get('profile_name', 'beyon-marketplace')
        region = request.form.get('region', 'me-south-1')
        
        print(f"Simple auth: Profile={profile_name}, Region={region}")
        
        # Authenticate
        success, message = auth.authenticate_with_profile(profile_name, region)
        
        if success:
            # Store in session
            session_info = auth.get_session_info()
            session['aws_authenticated'] = True
            session['aws_account_id'] = session_info['account_id']
            session['aws_region'] = session_info['region']
            session['aws_profile'] = profile_name
            session['aws_user_info'] = session_info['user_info']
            session['aws_auth_time'] = session_info['auth_time']
            
            flash(f'Successfully authenticated: {message}', 'success')
            return redirect(url_for('index'))
        else:
            flash(f'Authentication failed: {message}', 'error')
            return redirect(url_for('simple_auth'))
            
    except Exception as e:
        print(f"Simple auth error: {e}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('simple_auth'))

@app.route('/test-auth')
def test_auth():
    """Simple test page for authentication debugging."""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Auth</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h2>Test Authentication Form</h2>
            <form method="POST" action="/aws-authenticate" id="testForm">
                <div class="mb-3">
                    <label for="profile_name" class="form-label">Profile:</label>
                    <select class="form-select" name="profile_name" id="profile_name">
                        <option value="beyon-marketplace" selected>beyon-marketplace</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label for="region" class="form-label">Region:</label>
                    <select class="form-select" name="region" id="region">
                        <option value="me-south-1" selected>me-south-1</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">Test Submit</button>
            </form>
            
            <div class="mt-4">
                <button onclick="testSubmit()" class="btn btn-secondary">Test via JavaScript</button>
            </div>
            
            <div id="debug" class="mt-4"></div>
        </div>
        
        <script>
        function testSubmit() {
            const form = document.getElementById('testForm');
            const debug = document.getElementById('debug');
            
            debug.innerHTML = '<h5>Debug Info:</h5>';
            debug.innerHTML += '<p>Form action: ' + form.action + '</p>';
            debug.innerHTML += '<p>Form method: ' + form.method + '</p>';
            
            const formData = new FormData(form);
            debug.innerHTML += '<h6>Form Data:</h6>';
            for (let [key, value] of formData.entries()) {
                debug.innerHTML += '<p>' + key + ': ' + value + '</p>';
            }
            
            // Submit the form
            form.submit();
        }
        
        document.getElementById('testForm').addEventListener('submit', function(e) {
            console.log('Form submitted!');
            document.getElementById('debug').innerHTML = '<p class="text-success">Form submitted successfully!</p>';
        });
        </script>
    </body>
    </html>
    '''

@app.route('/recommendations')
def recommendations():
    """Display Trusted Advisor recommendations page."""
    if DEBUG_ENABLED:
        print("DEBUG: Accessing Trusted Advisor recommendations page")
    
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    try:
        # Get all recommendations
        recommendations_data = get_all_trusted_advisor_recommendations()
        
        if 'error' in recommendations_data:
            flash(f'Trusted Advisor Error: {recommendations_data["error"]}', 'warning')
            return render_template('recommendations.html', 
                                 recommendations=[], 
                                 categories={},
                                 error=recommendations_data['error'])
        
        recommendations = recommendations_data.get('recommendations', [])
        categories = recommendations_data.get('categories', {})
        
        # Get category information
        category_info = get_trusted_advisor_check_categories()
        
        # Calculate statistics
        stats = {
            'total': len(recommendations),
            'high_priority': len([r for r in recommendations if r.get('status') == 'error']),
            'medium_priority': len([r for r in recommendations if r.get('status') == 'warning']),
            'low_priority': len([r for r in recommendations if r.get('status') == 'ok']),
            'total_resources': sum(r.get('resource_count', 0) for r in recommendations)
        }
        
        if DEBUG_ENABLED:
            print(f"DEBUG: Found {len(recommendations)} Trusted Advisor recommendations")
        
        return render_template('recommendations.html',
                             recommendations=recommendations,
                             categories=categories,
                             category_info=category_info,
                             stats=stats,
                             last_updated=recommendations_data.get('last_updated'))
    
    except Exception as e:
        if DEBUG_ENABLED:
            print(f"DEBUG: Error in recommendations route: {e}")
        flash(f'Error retrieving Trusted Advisor recommendations: {str(e)}', 'error')
        return render_template('recommendations.html', 
                             recommendations=[], 
                             categories={},
                             error=str(e))

@app.route('/recommendations/refresh/<check_id>')
def refresh_recommendation(check_id):
    """Refresh a specific Trusted Advisor check."""
    if DEBUG_ENABLED:
        print(f"DEBUG: Refreshing Trusted Advisor check: {check_id}")
    
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    try:
        success = refresh_trusted_advisor_check(check_id)
        if success:
            flash('Trusted Advisor check refresh initiated. Results will be updated shortly.', 'success')
        else:
            flash('Failed to refresh Trusted Advisor check. Please try again.', 'error')
    except Exception as e:
        flash(f'Error refreshing check: {str(e)}', 'error')
    
    return redirect(url_for('recommendations'))

@app.route('/api/trusted-advisor/summary')
def api_trusted_advisor_summary():
    """API endpoint for Trusted Advisor summary data."""
    if 'aws_region' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        summary = get_trusted_advisor_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Get configuration from environment variables
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting TorWAR (Streamlined) on {host}:{port}")
    print(f"🐛 Debug mode: {debug_mode}")
    print(f"📁 Data directory: /app/data")
    print(f"📝 Log directory: /app/logs")
    
    app.run(host=host, port=port, debug=debug_mode)
