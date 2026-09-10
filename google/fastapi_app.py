from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from authlib.integrations.starlette_client import OAuth
import os, ssl

# Custom SSL context to remove VERIFY_STRICT that throws httpx errors against ZScalar cert chain
ssl_context = ssl.create_default_context()
ssl_context.verify_flags &= ~ssl.VERIFY_X509_STRICT

app = FastAPI()

# 1. Load Configurations
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.environ.get('FLASK_SECRET_KEY')
)

# 2. Initialize Authlib Extension
oauth = OAuth()

# 3. Register Google Remote App (Authlib automatically scans app.config for GOOGLE_*)
oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    #authorize_url="https://accounts.google.com/o/oauth2/auth",
    #authorize_params={"scope": "openid email profile"},
    #access_token_url="https://oauth2.googleapis.com/token",
    client_kwargs={"scope": "openid email profile",
                   "verify": ssl_context,
                   'prompt': 'select_account',                  # force to select account
                   "code_challenge_method": 'S256' },           # Adding PKCE on top of Auth Code Flow
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration"
    )


# Goes to Google Auth api
@app.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request,redirect_uri)

# Google Auth callback
@app.get('/authorize')
async def auth_callback(request: Request):
    # Process return token from Google server
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
        
    if user_info:
        request.session['user'] = user_info

    return RedirectResponse('/')

# Main app page
@app.get('/',response_class=HTMLResponse)
async def homepage(request: Request):
    user = request.session.get('user')
    if user:
        return f"Hello, {user['name']} ({user['email']})! <pre class=\"raw-text\" style=\"white-space: pre-wrap;\">{user}</pre> <a href='/logout'>Logout</a>"
    return f"Welcome! <a href='/login'>Login with Google</a>"

# Removes user from Flask session
@app.get('/logout')
def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse('/')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000) # Port and host do not apply when run through uv
