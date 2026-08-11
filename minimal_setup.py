from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    if os.path.exists('/app/data/.initialized'):
        return '<h1>Already installed! <a href="/restart">Restart</a></h1>'
    
    return '''
<html>
<body style="font-family:Arial;padding:50px;background:#f0f0f0">
<div style="max-width:400px;margin:0 auto;background:white;padding:30px;border-radius:10px">
<h2>TorWAR Setup</h2>
<form method="POST" action="/install">
<input name="username" placeholder="Username" style="width:100%;padding:10px;margin:10px 0" required><br>
<input name="email" placeholder="Email" style="width:100%;padding:10px;margin:10px 0" required><br>
<input name="password" type="password" placeholder="Password" style="width:100%;padding:10px;margin:10px 0" required><br>
<button type="submit" style="width:100%;padding:15px;background:#007cba;color:white;border:none;border-radius:5px">Install TorWAR</button>
</form>
</div>
</body>
</html>'''

@app.route('/install', methods=['POST'])
def install():
    print(f"Installing with: {request.form}")
    try:
        os.makedirs('/app/data', exist_ok=True)
        with open('/app/data/.initialized', 'w') as f:
            f.write('installed')
        print("File created successfully")
        
        return '''
<html>
<body style="font-family:Arial;padding:50px;text-align:center;background:#28a745;color:white">
<h1>SUCCESS!</h1>
<p>TorWAR installed! <a href="/restart" style="color:white">Click to restart</a></p>
</body>
</html>'''
    except Exception as e:
        print(f"Error: {e}")
        return f'<h1>ERROR: {e}</h1><a href="/">Try again</a>'

@app.route('/restart')
def restart():
    import sys
    os.execv(sys.executable, [sys.executable, 'app_with_auth.py'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
