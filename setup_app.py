#!/usr/bin/env python3
from flask import Flask, request, redirect, Response
from database_config import create_app
from database_models import db, User
from werkzeug.security import generate_password_hash
import os

# Create Flask app using the same config as main app
app, db_instance, migrate = create_app()

@app.route('/')
def setup():
    if os.path.exists('/app/data/.initialized'):
        return redirect('/login')
    
    html = '''<!DOCTYPE html>
<html>
<head>
    <title>TorWAR Setup</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
        }
        .setup-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            overflow: hidden;
            max-width: 400px;
            margin: 0 auto;
        }
        .setup-header {
            background: #ff9500;
            color: white;
            padding: 2rem;
            text-align: center;
        }
        .setup-body { padding: 2rem; }
        .btn-setup {
            background: #ff9500;
            border: none;
            color: white;
            padding: 0.75rem;
            border-radius: 25px;
            width: 100%;
        }
        .form-control { margin-bottom: 1rem; padding: 0.75rem; }
        .alert { margin-bottom: 1rem; padding: 0.75rem; border-radius: 6px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="setup-card">
            <div class="setup-header">
                <h2><i class="bi bi-gear-fill"></i> TorWAR Setup</h2>
                <p style="margin:0;">Initialize Installation</p>
            </div>
            <div class="setup-body">
                <form method="POST">
                    <input type="text" name="admin_username" class="form-control" placeholder="Admin Username" required>
                    <input type="email" name="admin_email" class="form-control" placeholder="Admin Email" required>
                    <input type="password" name="admin_password" class="form-control" placeholder="Admin Password" required>
                    <button type="submit" class="btn btn-setup">Initialize TorWAR</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>'''
    return Response(html, mimetype='text/html')

@app.route('/', methods=['POST'])
def setup_post():
    try:
        # Create database tables
        db.create_all()
        
        # Create admin user
        admin_user = User(
            username=request.form['admin_username'],
            email=request.form['admin_email'],
            password_hash=generate_password_hash(request.form['admin_password']),
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        
        # Mark as initialized
        with open('/app/data/.initialized', 'w') as f:
            f.write('1')
        
        # Success message and redirect to restart
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Setup Complete</title>
    <meta http-equiv="refresh" content="3;url=/">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            text-align: center;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>✅ TorWAR Initialized Successfully!</h2>
        <p>Restarting application...</p>
    </div>
</body>
</html>'''
        return Response(html, mimetype='text/html')
        
    except Exception as e:
        error_html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Setup Error</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background: #f8f9fa; padding: 2rem; }}
        .error {{ background: white; padding: 2rem; border-radius: 8px; max-width: 500px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="error">
        <h3>❌ Setup Failed</h3>
        <p>Error: {str(e)}</p>
        <a href="/" class="btn btn-primary">Try Again</a>
    </div>
</body>
</html>'''
        return Response(error_html, mimetype='text/html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
