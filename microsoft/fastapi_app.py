from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from authlib.integrations.starlette_client import OAuth
from authlib.oauth2.rfc7523 import PrivateKeyJWT
import os, ssl, json

# Custom SSL context to remove VERIFY_STRICT that throws httpx errors against ZScalar cert chain
ssl_context = ssl.create_default_context()
ssl_context.verify_flags &= ~ssl.VERIFY_X509_STRICT

app = FastAPI()

# 1. Load Configurations
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get('FLASK_SECRET_KEY')
)

## VARIABLES
TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_ONETEST_CLIENT_ID")
#CLIENT_SECRET = os.getenv("AZURE_ONETEST_CLIENT_SECRET")
AZURE_ONETEST_CERT_THUMBPRINT=os.getenv("AZURE_ONETEST_CERT_THUMBPRINT")
AZURE_TOKEN_ENDPOINT = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# Load the Private Key for signing client assertions
with open("private.pem", "r") as f:
    PRIVATE_KEY = f.read()


private_key_auth = PrivateKeyJWT(
    token_endpoint=AZURE_TOKEN_ENDPOINT,
    headers={"alg": "RS256", "typ":"JWT", "x5t": AZURE_ONETEST_CERT_THUMBPRINT}
)

# 2. Initialize Authlib Extension
oauth = OAuth()

## OAuth register
client = oauth.register(
    name='azure',
    client_id=os.getenv("AZURE_ONETEST_CLIENT_ID"),
    #client_secret=os.getenv("AZURE_ONETEST_CLIENT_SECRET"),
    client_secret=PRIVATE_KEY,
    server_metadata_url=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile User.Read",   #"openid email profile User.Read",
                   "verify": ssl_context,
                   'prompt': 'select_account',                  # force to select account
                   # Pass the x5t (or kid) header that Azure expects in the JWT header
                   "token_placement": "header",
                   "code_challenge_method": 'S256' },           # Adding PKCE on top of Auth Code Flow}
    # Instruct Authlib not to send a basic auth secret header
    token_endpoint_auth_method=private_key_auth
    )


## Routes

# Goes to Entra login
@app.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth_callback')
    return await oauth.azure.authorize_redirect(request,redirect_uri)

# Entra Auth callback
@app.get('/authorize')
async def auth_callback(request: Request):
    # Process return token from Entra
    token = await oauth.azure.authorize_access_token(request)
    #print(f"TOKEN DEBUG: {token}")
    user_info = token.get('userinfo')

    if user_info:
        request.session['user'] = user_info

    return RedirectResponse('/')

# Main app page
@app.get('/',response_class=HTMLResponse)
async def homepage(request: Request):
    user = request.session.get('user')

    page = f"Hello, "
    if user:
        page += f"{user['name']} ({user['email']})! <br> <pre class=\"raw-text\" style=\"white-space: pre-wrap;\">{user}</pre><a href='/logout'>Logout</a>"
    else:
        page = "Welcome! <a href='/login'>Login with Entra</a>"

    return page

# Removes user from Flask session
@app.get('/logout')
def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse('/')

### Previous endpoints


@app.get("/dashboard")
def dashboard(request: Request):
    # Access user details embedded in the existing Entra token
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
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000) # Port and host do not apply when run through uv
