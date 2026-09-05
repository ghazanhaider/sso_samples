import os
import requests
from flask import Flask, url_for, session, redirect, jsonify
from joserfc import jwt
from authlib.integrations.flask_client import OAuth
from authlib.integrations.flask_oauth2 import ResourceProtector, current_token
from authlib.oauth2.rfc6749 import MissingAuthorizationError, UnsupportedTokenTypeError
from authlib.oauth2.rfc6750 import BearerTokenValidator

app = Flask(__name__)
# 1. Load Configurations
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
# 2. Initialize Authlib Extension
oauth = OAuth(app)


# Configure your Entra ID Tenant information
TENANT_ID = os.getenv("AZURE_TENANT_ID")
#AZURE_ONETEST_CLIENT_ID = os.getenv("AZURE_ONETEST_CLIENT_ID")
#AZURE_ONETEST_CLIENT_SECRET = os.getenv("AZURE_ONETEST_CLIENT_SECRET")
# Expected audience can be your API's Application ID URI or Front-end Client ID
#EXPECTED_AUDIENCE = os.getenv("AZURE_AUDIENCE", "api://16df6f47-92f1-4bec-8f83-6db76d8aed24/access_as_user") 
#JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
#ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"

oauth.register(
    name='azure',
    client_id=os.getenv("AZURE_ONETEST_CLIENT_ID"),
    client_secret=os.getenv("AZURE_ONETEST_CLIENT_SECRET"),
    server_metadata_url=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile User.Read"}
    )



class EntraTokenValidator(BearerTokenValidator):
    def __init__(self):
        print(f"EntraTokenValidator INIT")
        super().__init__(realm=None)

    def authenticate_token(self, token_string):
        """Fetches public keys from Microsoft and validates the existing token"""
        try:
            # Fetch Microsoft's public keys dynamically
            print(f"TOKEN:{token_string}")
            res = requests.get(JWKS_URL)
            public_keys = res.json()

            # Decode and validate claims (Signature, Expiration, Audience, Issuer)
            claims = jwt.decode(
                token_string, 
                public_keys,
                claims_options={
                    "iss": {"essential": True, "value": ISSUER},
                    "aud": {"essential": True, "value": EXPECTED_AUDIENCE}
                }
            )
            print(f"CLAIMS:{claims}")
            claims.validate()
            return claims  # This object becomes 'current_token'
        except Exception as e:
            return None

    def request_invalid(self, request):
        print(f"TOKEN INVALID")
        return False

    def token_revoked(self, token):
        print(f"TOKEN REVOKED")
        return False

# 2. Initialize the Authlib Resource Protector
require_oauth = ResourceProtector()
require_oauth.register_token_validator(EntraTokenValidator())


# Goes to Entra login
@app.route('/login')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return oauth.azure.authorize_redirect(redirect_uri)

# Entra Auth callback
@app.route('/authorize')
def auth_callback():
    # Process return token from Entra
    token = oauth.azure.authorize_access_token()
    user_info = token.get('userinfo')

    if user_info:
        session['user'] = user_info
        #session['token'] = token
    return redirect('/')

# Main app page
@app.route('/')
def homepage():
    user = session.get('user')
    if user:
        return f"Hello, {user['name']} ({user['email']})! <pre class=\"raw-text\" style=\"white-space: pre-wrap;\">{user}</pre> <a href='/logout'>Logout</a>"
        #return f"Hello, the token payload is: <pre class=\"raw-text\" style=\"white-space: pre-wrap;\">{user}</pre> <a href='/logout'>Logout</a>"
    return "Welcome! <a href='/login'>Login with Entra</a>"

# Removes user from Flask session
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('token', None)
    return redirect('/')

### Previous endpoints


@app.route("/api/dashboard", methods=["GET"])
@require_oauth()  # Validates the existing Entra session token
def dashboard():
    # Access user details embedded in the existing Entra token
    print(f"DEBUG: {current_token}")
    user_email = current_token.get("preferred_username")
    user_name = current_token.get("name")
    user_roles = current_token.get("roles", [])

    return jsonify({
        "message": "Access granted via existing Microsoft Entra session",
        "user": {
            "name": user_name,
            "email": user_email,
            "roles": user_roles
        }
    })

if __name__ == "__main__":
    print("TEST")
    app.run(host='localhost', port=5000, debug=True)

