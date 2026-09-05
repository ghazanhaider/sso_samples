from flask import Flask, url_for, session, redirect
from authlib.integrations.flask_client import OAuth
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Initialize Authlib OAuth client
oauth = OAuth(app)

# Register Facebook OAuth 2.0 configuration
oauth.register(
    name='facebook',
    client_id='YOUR_FACEBOOK_APP_ID',
    client_secret='YOUR_FACEBOOK_APP_SECRET',
    access_token_url='https://graph.facebook.com/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    api_base_url='https://graph.facebook.com/',
    client_kwargs={'scope': 'email public_profile'}, # Essential user scopes
)

@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)

@app.route('/auth')
def auth():
        # Fetch access token from Facebook
    token = oauth.facebook.authorize_access_token()
        
    # Retrieve user information using Facebook Graph API
    resp = oauth.facebook.get('me?fields=id,name,email,picture')
    user_info = resp.json()
    
    # Store user profile data into session
    session['user'] = user_info
    return f"Hello, {user_info['name']}!"

