from flask import Flask, request, jsonify, redirect
import os
import sys
sys.path.append('/app')

from database_config import create_app
from database_models import db, User
from werkzeug.security import generate_password_hash

app, db_instance, migrate = create_app()

@app.route('/')
def setup():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TorWARTA Setup</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <style>
        :root {
            --torwar-primary: #ff9500;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            overflow-x: hidden;
        }
        
        .setup-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .setup-card {
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 3rem;
            backdrop-filter: blur(15px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            max-width: 600px;
            width: 100%;
            text-align: center;
        }
        
        .step {
            display: none;
            opacity: 0;
            transform: translateX(50px);
            transition: all 0.5s ease;
        }
        
        .step.active {
            display: block;
            opacity: 1;
            transform: translateX(0);
        }
        
        .step.prev {
            transform: translateX(-50px);
        }
        
        .logo {
            font-size: 3rem;
            color: var(--torwar-primary);
            margin-bottom: 1rem;
        }
        
        .progress-bar {
            height: 4px;
            background: rgba(255,255,255,0.2);
            border-radius: 2px;
            margin: 2rem 0;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--torwar-primary);
            border-radius: 2px;
            transition: width 0.5s ease;
            width: 0%;
        }
        
        .btn-primary {
            background: var(--torwar-primary);
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 25px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .btn-primary:hover {
            background: #e6850e;
            transform: translateY(-2px);
        }
        
        .form-control {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            border-radius: 10px;
            padding: 0.75rem;
            margin-bottom: 1rem;
        }
        
        .form-control::placeholder {
            color: rgba(255,255,255,0.7);
        }
        
        .form-control:focus {
            background: rgba(255,255,255,0.15);
            border-color: var(--torwar-primary);
            box-shadow: 0 0 0 0.2rem rgba(255, 149, 0, 0.25);
            color: white;
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        .feature-item {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 1.5rem;
            text-align: center;
        }
        
        .feature-icon {
            font-size: 2rem;
            color: var(--torwar-primary);
            margin-bottom: 0.5rem;
        }
        
        .installation-step {
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 1rem 0;
            opacity: 0.3;
            transition: all 0.5s ease;
        }
        
        .installation-step.active {
            opacity: 1;
        }
        
        .installation-step.completed {
            opacity: 1;
            color: #28a745;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .spinner {
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top: 2px solid var(--torwar-primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 0.5rem;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        .btn-primary:disabled {
            background: #6c757d;
            border-color: #6c757d;
            cursor: not-allowed;
            opacity: 0.6;
        }
    </style>
</head>
<body>
    <div class="setup-container">
        <div class="setup-card">
            <div class="logo">
                <i class="bi bi-shield-check"></i>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            
            <!-- Step 1: Welcome -->
            <div class="step active" id="step1">
                <h1 class="display-5 fw-bold mb-4">Welcome to TorWARTA</h1>
                <p class="lead mb-4">Toraif Well Architected & Trusted Advisor Tool</p>
                <p class="mb-4">Streamline your AWS architecture reviews with automated assessments and comprehensive reporting.</p>
                
                <div class="feature-grid">
                    <div class="feature-item">
                        <div class="feature-icon"><i class="bi bi-speedometer2"></i></div>
                        <h6>Automated Reviews</h6>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon"><i class="bi bi-graph-up-arrow"></i></div>
                        <h6>Actionable Insights</h6>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon"><i class="bi bi-file-earmark-text"></i></div>
                        <h6>Professional Reports</h6>
                    </div>
                </div>
                
                <button class="btn btn-primary btn-lg" onclick="nextStep()">
                    <i class="bi bi-arrow-right me-2"></i>Get Started
                </button>
            </div>
            
            <!-- Step 2: Admin Setup -->
            <div class="step" id="step2">
                <h2 class="mb-4">Create Administrator Account</h2>
                <p class="mb-4">Set up your admin credentials to manage TorWARTA</p>
                
                <form id="setupForm">
                    <input type="text" id="firstName" class="form-control" placeholder="First Name" required oninput="validateForm()">
                    <input type="text" id="lastName" class="form-control" placeholder="Last Name" required oninput="validateForm()">
                    <input type="text" id="username" class="form-control" placeholder="Username" required oninput="validateForm()">
                    <input type="email" id="email" class="form-control" placeholder="Email Address" required oninput="validateForm()">
                    <input type="password" id="password" class="form-control" placeholder="Password" required oninput="validateForm()">
                </form>
                
                <div class="mt-4">
                    <button class="btn btn-outline-light me-2" onclick="prevStep()">
                        <i class="bi bi-arrow-left me-2"></i>Back
                    </button>
                    <button class="btn btn-primary" id="installBtn" onclick="startInstallation()" disabled>
                        <i class="bi bi-rocket-takeoff me-2"></i>Install TorWARTA
                    </button>
                </div>
            </div>
            
            <!-- Step 3: Installation -->
            <div class="step" id="step3">
                <h2 class="mb-4">Installing TorWARTA</h2>
                <p class="mb-4">Setting up your Toraif Well Architected & Trusted Advisor Tool...</p>
                
                <div id="installationSteps">
                    <div class="installation-step" id="install1">
                        <div class="spinner"></div>
                        Creating database tables...
                    </div>
                    <div class="installation-step" id="install2">
                        <div class="spinner"></div>
                        Setting up administrator account...
                    </div>
                    <div class="installation-step" id="install3">
                        <div class="spinner"></div>
                        Initializing data directories...
                    </div>
                    <div class="installation-step" id="install4">
                        <div class="spinner"></div>
                        Configuring security settings...
                    </div>
                    <div class="installation-step" id="install5">
                        <div class="spinner"></div>
                        Finalizing installation...
                    </div>
                </div>
            </div>
            
            <!-- Step 4: Success -->
            <div class="step" id="step4">
                <div class="pulse mb-4">
                    <i class="bi bi-check-circle-fill" style="font-size: 4rem; color: #28a745;"></i>
                </div>
                
                <h1 class="mb-4">🎉 Installation Complete!</h1>
                <p class="lead mb-4">TorWARTA is ready to use</p>
                
                <div class="mb-4">
                    <p><strong>Next Steps:</strong></p>
                    <p>Login → Connect AWS → Start Reviews</p>
                </div>
                
                <div class="mt-4">
                    <div class="spinner me-2"></div>
                    Starting application...
                </div>
            </div>
        </div>
    </div>
    
    <script>
    let currentStep = 1;
    const totalSteps = 4;
    
    function updateProgress() {
        const progress = (currentStep / totalSteps) * 100;
        document.getElementById('progressFill').style.width = progress + '%';
    }
    
    function validateForm() {
        const firstName = document.getElementById('firstName')?.value || '';
        const lastName = document.getElementById('lastName')?.value || '';
        const username = document.getElementById('username')?.value || '';
        const email = document.getElementById('email')?.value || '';
        const password = document.getElementById('password')?.value || '';
        
        const allFieldsFilled = firstName && lastName && username && email && password;
        const installBtn = document.getElementById('installBtn');
        
        if (installBtn) {
            installBtn.disabled = !allFieldsFilled;
        }
    }
    
    function nextStep() {
        if (currentStep < totalSteps) {
            document.getElementById('step' + currentStep).classList.remove('active');
            document.getElementById('step' + currentStep).classList.add('prev');
            currentStep++;
            document.getElementById('step' + currentStep).classList.add('active');
            updateProgress();
        }
    }
    
    function prevStep() {
        if (currentStep > 1) {
            document.getElementById('step' + currentStep).classList.remove('active');
            currentStep--;
            document.getElementById('step' + currentStep).classList.remove('prev');
            document.getElementById('step' + currentStep).classList.add('active');
            updateProgress();
        }
    }
    
    async function startInstallation() {
        const firstName = document.getElementById('firstName').value;
        const lastName = document.getElementById('lastName').value;
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        if (!firstName || !lastName || !username || !email || !password) {
            alert('Please fill in all fields');
            return;
        }
        
        nextStep(); // Go to installation step
        
        // Animate installation steps
        const steps = ['install1', 'install2', 'install3', 'install4', 'install5'];
        
        for (let i = 0; i < steps.length; i++) {
            document.getElementById(steps[i]).classList.add('active');
            
            if (i === 0) {
                // Actually perform installation on first step
                try {
                    const response = await fetch('/install', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            firstName: firstName,
                            lastName: lastName,
                            username: username,
                            email: email,
                            password: password
                        })
                    });
                    
                    const result = await response.json();
                    if (!result.success) {
                        throw new Error(result.error);
                    }
                } catch (error) {
                    alert('Installation failed: ' + error.message);
                    return;
                }
            }
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Mark as completed
            const stepEl = document.getElementById(steps[i]);
            stepEl.classList.add('completed');
            stepEl.innerHTML = '<i class="bi bi-check-circle me-2"></i>' + stepEl.textContent.replace('...', ' ✓');
        }
        
        // Go to success step
        setTimeout(() => {
            nextStep();
            
            // Auto-redirect to main app
            setTimeout(() => {
                // Since .initialized file is created, startup.py will launch main app
                window.location.href = '/restart-app';
            }, 3000);
        }, 1000);
    }
    
    // Initialize progress
    updateProgress();
    </script>
</body>
</html>'''

@app.route('/install', methods=['POST'])
def install():
    print("=== INSTALLATION STARTING ===")
    try:
        data = request.get_json()
        print(f"Received data: {data}")
        
        firstName = data['firstName']
        lastName = data['lastName']
        username = data['username']
        email = data['email'] 
        password = data['password']
        print(f"Creating user: {firstName} {lastName} ({username}, {email})")
        
        print("1. Starting database operations...")
        with app.app_context():
            print("2. Creating database tables...")
            db.create_all()
            print("3. Database tables created successfully!")
            
            print("4. Checking for existing users...")
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"5. User {username} already exists, skipping creation...")
            else:
                print("5. Creating admin user...")
                admin_user = User(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    first_name=firstName,
                    last_name=lastName
                )
                db.session.add(admin_user)
                print("6. Admin user added to session...")
                
                db.session.commit()
                print("7. Database commit successful!")
            
            print("7. Creating directories...")
            os.makedirs('/app/data/reports', exist_ok=True)
            os.makedirs('/app/data/workloads', exist_ok=True)
            os.makedirs('/app/logs', exist_ok=True)
            print("8. Directories created!")
            
            print("9. Creating initialization file...")
            with open('/app/data/.initialized', 'w') as f:
                f.write('installed')
            print("10. Initialization file created!")
        
        print("=== INSTALLATION COMPLETE ===")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"=== INSTALLATION FAILED: {e} ===")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/restart-app')
def restart_app():
    # Create a simple restart page that triggers container restart
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Restarting TorWARTA</title>
    <meta http-equiv="refresh" content="3;url=/">
    <style>
        body {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            text-align: center;
            padding: 50px;
            font-family: Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .restart-card {
            background: rgba(255,255,255,0.1);
            padding: 3rem;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="restart-card">
        <h1>🚀 Starting TorWARTA...</h1>
        <div class="spinner"></div>
        <p>Application is initializing, please wait...</p>
        <small>You will be redirected automatically</small>
    </div>
    <script>
        // Force restart by making container restart
        setTimeout(() => {
            fetch('/force-restart', {method: 'POST'}).catch(() => {});
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        }, 1000);
    </script>
</body>
</html>'''

@app.route('/force-restart', methods=['POST'])
def force_restart():
    # Exit the setup process so startup.py can restart with main app
    import os
    import signal
    import threading
    
    def delayed_exit():
        import time
        time.sleep(1)
        os._exit(0)
    
    # Start exit in background thread
    threading.Thread(target=delayed_exit, daemon=True).start()
    
    return 'Restarting...', 200

@app.route('/launch')
def launch():
    # Redirect to restart
    return redirect('/restart-app')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
