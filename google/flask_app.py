from flask import Flask, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os

app = Flask(__name__)

# 1. Load Configurations
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

# 2. Initialize Authlib Extension
oauth = OAuth(app)

# 3. Register Google Remote App (Authlib automatically scans app.config for GOOGLE_*)
oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params={"scope": "openid email profile"},
    access_token_url="https://oauth2.googleapis.com/token",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration"
    )

# Goes to Google Auth api
@app.route('/login')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

# Google Auth callback
@app.route('/authorize')
def auth_callback():
    # Process return token from Google server
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
        
    if user_info:
        session['user'] = user_info
                
    return redirect('/')

# Main app page
@app.route('/')
def homepage():
    user = session.get('user')
    if user:
        return f"Hello, {user['name']} ({user['email']})! <br><pre class=\"raw-text\" style=\"white-space: pre-wrap;\">{user}</pre><br><a href='/logout'>Logout</a>"
        # With picture
        # return f"Hello, {user['name']} ({user['email']})! <a href='/logout'>Logout</a><img src=\"{user['picture']}\"><pre class=\"raw-text\">{user}</pre>"
    return "Welcome! <a href='/login'>Login with Google</a>"

# Removes user from Flask session
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
