from flask import Flask, request, redirect
import os
import sys
sys.path.append('/app')

# Import database components
from database_config import create_app
from database_models import db, User
from werkzeug.security import generate_password_hash

# Create Flask app with proper database config
app, db_instance, migrate = create_app()

@app.route('/')
def setup():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Setup - TorWAR</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <style>
        :root {
            --torwar-primary: #ff9500;
            --torwar-secondary: #1a1a1a;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
        }
        
        .auth-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .auth-header {
            background: var(--torwar-primary);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        
        .auth-body {
            padding: 2rem;
        }
        
        .btn-torwar {
            background: var(--torwar-primary);
            border: none;
            color: white;
            padding: 0.75rem 2rem;
            border-radius: 25px;
            font-weight: 500;
        }
        
        .btn-torwar:hover {
            background: #e6850e;
            color: white;
        }
        
        .form-control:focus {
            border-color: var(--torwar-primary);
            box-shadow: 0 0 0 0.2rem rgba(255, 149, 0, 0.25);
        }
        
        .progress-step {
            display: none;
        }
        
        .progress-step.active {
            display: block;
        }
        
        .setup-progress {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .progress-item {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
            color: rgba(255,255,255,0.7);
        }
        
        .progress-item.completed {
            color: #28a745;
        }
        
        .progress-item.active {
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="auth-card">
                    <div class="auth-header">
                        <h2><i class="bi bi-gear-fill"></i> TorWAR</h2>
                        <p class="mb-0">AWS Well-Architected Review Tool</p>
                    </div>
                    <div class="auth-body">
                        <h4 class="mb-4">Initial Setup</h4>
                        <p class="text-muted mb-4">Welcome! Let's set up your TorWAR installation with an administrator account.</p>
                        
                        <form method="POST" action="/do-install">
                            <div class="mb-3">
                                <label for="admin_username" class="form-label">Administrator Username</label>
                                <input type="text" name="username" class="form-control" placeholder="Enter username" required>
                                <div class="form-text">This will be your login username</div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="admin_email" class="form-label">Administrator Email</label>
                                <input type="email" name="email" class="form-control" placeholder="Enter email address" required>
                                <div class="form-text">Used for notifications and password recovery</div>
                            </div>
                            
                            <div class="mb-4">
                                <label for="admin_password" class="form-label">Administrator Password</label>
                                <input type="password" name="password" class="form-control" placeholder="Enter secure password" required>
                                <div class="form-text">Choose a strong password (8+ characters)</div>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-torwar">
                                    <i class="bi bi-rocket-takeoff me-2"></i>Install TorWAR
                                </button>
                            </div>
                        </form>
                        
                        <hr class="my-4">
                        
                        <div class="text-center">
                            <small class="text-muted">
                                <i class="bi bi-shield-check me-1"></i>
                                Your data is encrypted and secure
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

@app.route('/do-install', methods=['POST'])
def do_install():
    print("=== SETUP STARTING ===")
    try:
        username = request.form['username']
        email = request.form['email'] 
        password = request.form['password']
        print(f"Creating user: {username}, {email}")
        
        with app.app_context():
            print("Creating database tables...")
            db.create_all()
            print("Database tables created!")
            
            print("Creating admin user...")
            admin_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created!")
            
            print("Creating directories...")
            os.makedirs('/app/data/reports', exist_ok=True)
            os.makedirs('/app/data/workloads', exist_ok=True)
            os.makedirs('/app/logs', exist_ok=True)
            print("Directories created!")
            
            print("Creating init file...")
            with open('/app/data/.initialized', 'w') as f:
                f.write('installed')
            print("Init file created!")
            
        print("=== SETUP COMPLETE ===")
        
        return '''<html><body style="background:green;color:white;text-align:center;padding:50px">
        <h1>Setup Complete!</h1>
        <p>Restarting in 3 seconds...</p>
        <script>setTimeout(() => window.location.href = '/restart', 3000);</script>
        </body></html>'''
        
    except Exception as e:
        print(f"=== SETUP FAILED: {e} ===")
        import traceback
        traceback.print_exc()
        return f'<html><body style="background:red;color:white;padding:50px"><h1>Setup Failed</h1><p>{e}</p><a href="/">Try Again</a></body></html>'

@app.route('/restart')
def restart():
    # Restart the application by exec to main app
    os.execv(sys.executable, [sys.executable, '/app/app_with_auth.py'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
