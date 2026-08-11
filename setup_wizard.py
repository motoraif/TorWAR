from flask import request, redirect, url_for, flash, make_response, Response
from database_models import db, User
from werkzeug.security import generate_password_hash
import os

def register_setup_routes(app):
    @app.before_request
    def check_setup():
        # Skip for setup routes completely
        if request.endpoint in ['setup', 'setup_post']:
            return
            
        # Skip for static files and favicon
        if request.path and (request.path.startswith('/static') or request.path == '/favicon.ico'):
            return
            
        # Check if setup is needed
        if not os.path.exists('/app/data/.initialized'):
            return redirect(url_for('setup'))
    
    @app.route('/setup')
    def setup():
        if os.path.exists('/app/data/.initialized'):
            return redirect(url_for('login'))
        
        # Return direct Response object to bypass all template processing
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Setup - TorWAR</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <style>
        :root { --torwar-primary: #ff9500; }
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
        .auth-body { padding: 2rem; }
        .btn-torwar {
            background: var(--torwar-primary);
            border: none;
            color: white;
            padding: 0.75rem 2rem;
            border-radius: 25px;
            font-weight: 500;
            width: 100%;
        }
        .btn-torwar:hover { background: #e6850e; }
        .form-control {
            border-radius: 6px;
            border: 1px solid #ddd;
            padding: 0.75rem;
            margin-bottom: 1rem;
        }
        .form-control:focus {
            border-color: var(--torwar-primary);
            box-shadow: 0 0 0 0.2rem rgba(255, 149, 0, 0.25);
            outline: none;
        }
    </style>
</head>
<body>
    <div style="width: 100%; max-width: 400px; margin: 0 auto; padding: 20px;">
        <div class="auth-card">
            <div class="auth-header">
                <h2><i class="bi bi-gear-fill"></i> TorWAR</h2>
                <p style="margin: 0;">Initial Setup Required</p>
            </div>
            <div class="auth-body">
                <h4 style="margin-bottom: 1.5rem;">Setup Administrator</h4>
                <form method="POST">
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Admin Username</label>
                    <input type="text" name="admin_username" class="form-control" placeholder="Enter admin username" required>
                    
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Admin Email</label>
                    <input type="email" name="admin_email" class="form-control" placeholder="Enter admin email" required>
                    
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Admin Password</label>
                    <input type="password" name="admin_password" class="form-control" placeholder="Enter admin password" required>
                    
                    <button type="submit" class="btn-torwar">Initialize TorWAR</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>'''
        return Response(html, mimetype='text/html')
    
    @app.route('/setup', methods=['POST'])
    def setup_post():
        if os.path.exists('/app/data/.initialized'):
            return redirect(url_for('login'))
        
        try:
            db.create_all()
            
            admin_user = User(
                username=request.form['admin_username'],
                email=request.form['admin_email'],
                password_hash=generate_password_hash(request.form['admin_password']),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            
            with open('/app/data/.initialized', 'w') as f:
                f.write('1')
            
            return redirect(url_for('login'))
            
        except Exception as e:
            return redirect(url_for('setup'))
