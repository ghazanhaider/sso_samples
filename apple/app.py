from flask import Flask, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
from joserfc import jwt
from joserfc.jwk import OctKey
import os, time

app = Flask(__name__)

# 1. Load Configurations
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

# 2. Initialize Authlib Extension
oauth = OAuth(app)

# Helper function to generate Apple's client_secret (JWT)
def generate_apple_secret():
    team_id = 'Personal Team'           # 'YOUR_APPLE_TEAM_ID'
    client_id = 'com.example.app'                      # 'YOUR_SERVICES_ID' # e.g., com.example.app
    key_id = ''  #'YOUR_APPLE_KEY_ID'
    
    with open('developer_key.p8', 'r') as f:
        private_key = f.read()
            
    headers = {
        'kid': key_id,
        'alg': 'HS256'
    }
    payload = {
        'iss': team_id,
        'iat': int(time.time()),
        'exp': int(time.time()) + 86400 * 180, # 6 months max
        'aud': 'https://apple.com',
        'sub': client_id,
    }
    key = OctKey.import_key(private_key)
    return jwt.encode(headers, payload, key)
    #return jwt.encode(payload, private_key, algorithm='ES256', headers=headers)


# 3. Register Google Remote App (Authlib automatically scans app.config for GOOGLE_*)
apple = oauth.register(
    name='apple',
    client_id='com.example.app', # os.environ.get('APPLE_CLIENT_ID'), #YOUR_SERVICES_ID
    client_secret=generate_apple_secret(),
    authorize_url="https://apple.com/auth/authorize",
    access_token_url="https://apple.com/auth/token",
    client_kwargs={"scope": "name email", "response_mode": "form_post"}
    )

# Goes to Apple Auth api
@app.route('/login')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return apple.authorize_redirect(redirect_uri)

# Apple Auth callback
@app.route('/authorize', methods=['GET', 'POST']) # Apple responds with "form_post"
def auth_callback():
    # Process return token from Google server
    token = apple.authorize_access_token()
    user_info = apple.parse_id_token(token)
        
    if user_info:
        session['user'] = user_info
                
    return redirect('/')

# Main app page
@app.route('/')
def homepage():
    user = session.get('user')
    if user:
        return f"Hello, {user['name']} ({user['email']})! <a href='/logout'>Logout</a><pre class=\"raw-text\">{user}</pre>"
        # With picture
        # return f"Hello, {user['name']} ({user['email']})! <a href='/logout'>Logout</a><img src=\"{user['picture']}\"><pre class=\"raw-text\">{user}</pre>"
    return "Welcome! <a href='/login'>Login with Apple</a>"

# Removes user from Flask session
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
