#!/usr/bin/env python3
"""
TorWAR - Streamlined Version
AWS Well-Architected Review Tool with Enhanced Report Management

Removed Features:
- Accounts Management
- Custom Rules
- Scheduled Reviews
- Scheduled Reports

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

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

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
    """Home page with dashboard."""
    return render_template('index.html')

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
                answered_questions = sum(1 for answer in answers if answer.get('SelectedChoices'))
                
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
    
    return render_template('select_pillars.html', pillar_stats=pillar_stats, pillars=PILLARS)

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
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('aws_login'))
    
    if 'workload_id' not in session:
        flash('Please select a workload first', 'warning')
        return redirect(url_for('list_workloads'))
    
    try:
        workload_id = session['workload_id']
        wa_client = get_wellarchitected_client()
        
        # Get workload details
        workload_response = wa_client.get_workload(WorkloadId=workload_id)
        workload = workload_response.get('Workload', {})
        
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
        
        # Initialize pillar reviews
        pillar_reviews = {}
        
        for pillar_id, pillar_name in PILLARS.items():
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
                        detailed_answers.append(detailed_answer)
                        
                        # Debug logging
                        question_id = detailed_answer.get('QuestionId', 'Unknown')
                        risk = detailed_answer.get('Risk')
                        selected_choices = detailed_answer.get('SelectedChoices', [])
                        print(f"DEBUG: Question {question_id} - Risk: {risk}, Choices: {len(selected_choices)}")
                        
                        # Update summary counts
                        report_data['summary']['total_questions'] += 1
                        overall_stats['total_questions'] += 1
                        
                        if detailed_answer.get('SelectedChoices'):
                            report_data['summary']['answered_questions'] += 1
                            overall_stats['answered_questions'] += 1
                            pillar_stats['answered_questions'] += 1
                        
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
                        continue
                
                # Calculate pillar completion percentage
                if pillar_stats['total_questions'] > 0:
                    pillar_stats['completion_percentage'] = round(
                        (pillar_stats['answered_questions'] / pillar_stats['total_questions']) * 100, 1
                    )
                
                report_data['pillars'][pillar_id] = {
                    'name': pillar_name,
                    'questions': detailed_answers
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
        
        # Store report data in session for saving
        session['current_report_data'] = {
            'report_data': report_data,
            'overall_stats': overall_stats,
            'risk_counts': risk_counts,
            'pillar_reviews': pillar_reviews,
            'report_version': report_version
        }
        
        return render_template('generate_report.html', 
                             report_data=report_data,
                             workload=workload,
                             pillars=PILLARS,
                             overall_stats=overall_stats,
                             risk_counts=risk_counts,
                             pillar_reviews=pillar_reviews,
                             report_version=report_version)
        
    except Exception as e:
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
        
        # Use stored report data from session, or regenerate if missing
        if 'current_report_data' not in session:
            print("DEBUG: No session data found, regenerating report data")
            flash('Regenerating report data for saving...', 'info')
            
            # Regenerate report data (same logic as generate_report)
            wa_client = get_wellarchitected_client()
            
            # Get workload details
            workload_response = wa_client.get_workload(WorkloadId=workload_id)
            workload = workload_response.get('Workload', {})
            
            # Generate report data
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
            
            # Process all pillars
            for pillar_id, pillar_name in PILLARS.items():
                try:
                    answers = get_all_pillar_answers(wa_client, workload_id, pillar_id)
                    detailed_answers = []
                    
                    for answer in answers:
                        try:
                            detail_response = wa_client.get_answer(
                                WorkloadId=workload_id,
                                LensAlias='wellarchitected',
                                QuestionId=answer['QuestionId']
                            )
                            detailed_answer = detail_response.get('Answer', {})
                            detailed_answers.append(detailed_answer)
                            
                            # Update summary counts
                            report_data['summary']['total_questions'] += 1
                            
                            if detailed_answer.get('SelectedChoices'):
                                report_data['summary']['answered_questions'] += 1
                            
                            risk = detailed_answer.get('Risk', 'UNANSWERED')
                            if risk == 'HIGH':
                                report_data['summary']['high_risks'] += 1
                            elif risk == 'MEDIUM':
                                report_data['summary']['medium_risks'] += 1
                            elif risk == 'LOW':
                                report_data['summary']['low_risks'] += 1
                            elif risk == 'NONE':
                                report_data['summary']['no_risks'] += 1
                                
                        except Exception as e:
                            print(f"Error getting answer details: {e}")
                            continue
                    
                    report_data['pillars'][pillar_id] = {
                        'name': pillar_name,
                        'questions': detailed_answers
                    }
                    
                except Exception as e:
                    print(f"Error processing pillar {pillar_id}: {e}")
                    continue
        else:
            print("DEBUG: Using session data for saving")
            stored_data = session['current_report_data']
            report_data = stored_data['report_data']
        
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
