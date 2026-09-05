from flask import Flask, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os

app = Flask(__name__)

# 1. Load Configurations
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

# 2. Initialize Authlib Extension
oauth = OAuth(app)

# 3. Register Github oauth provider to Authlib
github = oauth.register(
    name='github',
    client_id=os.environ.get('GITHUB_CLIENT_ID'),
    client_secret=os.environ.get('GITHUB_CLIENT_SECRET'),
    authorize_url="https://github.com/login/oauth/authorize",
#    authorize_params={"scope": "openid email profile"},
    access_token_url="https://github.com/login/oauth/access_token",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"}
#    server_metadata_url="https://auth.mozilla.auth0.com/.well-known/openid-configuration"
    )

# Goes to Githb Auth api
@app.route('/login')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return oauth.github.authorize_redirect(redirect_uri)

# OIDC Auth callback
@app.route('/authorize')
def auth_callback():
    # Process return token from Github server
    token = github.authorize_access_token()
    #user_info = token.get('userinfo')
    # Fetch authenticated user profile data from GitHub's API
    resp = github.get('user')
    user_info = resp.json()
        
    if user_info:
        session['user'] = user_info
                
    return redirect('/')

# Main app page
@app.route('/')
def homepage():
    user = session.get('user')
    if user:
        return f"Hello, {user['name']} ({user['email']})! <a href='/logout'>Logout</a><pre class=\"raw-text\">{user}</pre>"
    return "Welcome! <a href='/login'>Login with Github</a>"

# Removes user from Flask session
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
