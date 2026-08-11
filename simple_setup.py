#!/usr/bin/env python3
import os
import sys
sys.path.append('/app')

from flask import Flask, request
from database_config import create_app
from database_models import db, User
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://torwar:torwar123@db:5432/torwar'
app.config['SECRET_KEY'] = 'setup'

# Initialize database
from database_models import db
db.init_app(app)

@app.route('/')
def setup():
    if os.path.exists('/app/data/.initialized'):
        return '<script>window.location.reload();</script>'
    
    return '''<!DOCTYPE html>
<html>
<head><title>TorWAR Setup</title>
<style>
body{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;font-family:Arial}
.card{background:white;border-radius:15px;box-shadow:0 15px 35px rgba(0,0,0,0.1);max-width:400px;margin:0 auto}
.header{background:#ff9500;color:white;padding:2rem;text-align:center}
.body{padding:2rem}
input{width:100%;padding:0.75rem;margin-bottom:1rem;border:1px solid #ddd;border-radius:6px}
button{background:#ff9500;color:white;padding:0.75rem;border:none;border-radius:25px;width:100%;cursor:pointer}
</style>
</head>
<body>
<div class="card">
<div class="header"><h2>🔧 TorWAR Setup</h2></div>
<div class="body">
<form method="POST" action="/install">
<input name="username" placeholder="Admin Username" required>
<input name="email" type="email" placeholder="Admin Email" required>
<input name="password" type="password" placeholder="Admin Password" required>
<button type="submit">Install TorWAR</button>
</form>
</div>
</div>
</body>
</html>'''

@app.route('/install', methods=['POST'])
def install():
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Create admin user
            user = User(
                username=request.form['username'],
                email=request.form['email'],
                password_hash=generate_password_hash(request.form['password']),
                is_admin=True
            )
            db.session.add(user)
            db.session.commit()
            
            # Mark as installed
            os.makedirs('/app/data', exist_ok=True)
            with open('/app/data/.initialized', 'w') as f:
                f.write('installed')
            
            return '''<!DOCTYPE html>
<html>
<head><title>Setup Complete</title>
<meta http-equiv="refresh" content="2;url=/">
<style>body{background:#28a745;color:white;text-align:center;padding:3rem;font-family:Arial}</style>
</head>
<body>
<h1>✅ Installation Complete!</h1>
<p>TorWAR has been successfully installed. Restarting...</p>
</body>
</html>'''
    except Exception as e:
        return f'''<!DOCTYPE html>
<html><body style="padding:2rem;background:#dc3545;color:white;font-family:Arial">
<h2>❌ Installation Failed</h2>
<p>Error: {str(e)}</p>
<a href="/" style="color:white">Try Again</a>
</body></html>'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
