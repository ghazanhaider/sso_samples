# SSO samples

Concepts:

IDp is the ID 'provider'

Application: Created against the IDp, gives back a client_id and either client_secret or a certificate
- Single-Page apps do Auth in client javascript/Angular/Node
- Regular Apps do Auth in the backend (Flask etc)
- Apps can be first-party (mine, or owned by the same client), or third-party (external party accessing my data)
- Third party:
  - Requires explicit client_grant
  - Requires User consent
  - Does not support: OIDC, SAML
  - client_id has 'tpc_' prefix for Auth0
- Apps can be Confidential or Public:
  - Confidential apps can auth with: client_id client_secret, JWT. 
  - Public apps cannot hold or send client_secret: 

Refs:
https://auth0.com/docs/get-started/applications/confidential-and-public-applications


Code Flow:
Authorization Code Flow, Resource Owner Password Flow: Used in Confidential Web Apps
Client Credentials Flow: M2M Confidential App
Authorization Code Flow with PKCE: Public App,
Implicit Flow: Public App, single-page using client javascipt. Insecure, returns tokens direct from `/authorize`

OIDC:
- Openid Scope: You trigger OIDC by adding `openid` to the `scope` parameter in your initial authorization request
- Instead of just returning an OAuth 2.0 access token, the authorization server also issues an `id_token`. This is a signed JSON Web Token (JWT) that contains claims about the user (such as their unique user ID, name, email, and when they logged in)
-  OIDC provides a dedicated `/userinfo` endpoint and discovery endpoints to automatically find the provider's configuration detail

Scopes:
- OAuth 2.0 scopes control what API resources and actions an application can access: Examples `read:reports`, `write:calendar`, `photos:read`, or `api1`
- OAuth 2.0 does not define standard scopes, they're provider-specific
- OIDC scopes control what user identity claims are returned to verify who the user is:
  - `openid` (Mandatory; triggers OIDC behavior and issues an ID token)
  - `profile` (Returns name, nickname, picture, birthdate, etc.
  - `email` (Returns email address and verification status)
  - `phone`
  - `address`
  - `offline_access`


## Authorization Code Flow

1. User: click login -> Webapp
2. Webapp: Auth code request -> IDp `/authorize` (done without loginid or client_id in case session already exists)
3. IDp: Redirect login/auth prompt -> User (Empty prompt | User's login and picture | MFA | Or skipped if already logged in)
4. User: Auth and consent -> IDp
5. IDp: Authorization Code -> Webapp `redirect_uri` with `code` (Single-use authorization code)
- Open ID Connect (OIDC): Adds ID token to make things faster
6. Webapp: Authorization Code for web apps -> IDp `/token` (Direct non-browser connection, fixed known source to IDp)
- `client_id` and `client_secret` or PKCE `code_verifier`
7. IDp (validates)
8. IDp: ID token and access token -> Webapp (might contain user_id)
- `access_token` and `id_token` and optional `refresh_token`
9. Webapp: Request user_data with access token -> IDp
10. IDp: User data -> Webapp


Webapp Endpoints:
`/`: Checks for login, redirects to app or offers login button
`/login`: #2 Auth code request to IDp `/authorize_url` with callback `/authorize`
`/authorize`: #6 Authorization Code for web apps to IDp (we have authn done we can authz now)
`somethin`: #9 We have auth code and a valid user, we can request user_data here on

Notes:
- Add `offline_access` in the `scope` for refresh tokens that need to be long-lived (user profile needed in later steps)


## Microsoft Entra

Microsoft Entra recommends *Authorization Code Flow with PKCE* instead of *Authorization Code Flow*
For Entra, CORS must be setup for the redirect_uri
Against `/authorize` the app might request the `openid`, `offline_access` and `https://graph.microsoft.com/mail.read` permissions

Sample (Stage #2)
```
// Line breaks for legibility only

https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?
client_id=00001111-aaaa-2222-bbbb-3333cccc4444
&response_type=code
&redirect_uri=http%3A%2F%2Flocalhost%2Fmyapp%2F
&response_mode=query
&scope=https%3A%2F%2Fgraph.microsoft.com%2Fmail.read
&state=12345
&code_challenge=YTFjNjI1OWYzMzA3MTI4ZDY2Njg5M2RkNmVjNDE5YmEyZGRhOGYyM2IzNjdmZWFhMTQ1ODg3NDcxY2Nl
&code_challenge_method=S256
```
Ref: https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow

`prompt`: `login` forces login, `none` prevents login throwing error, `consent` grant permissions to app, `select_account` lists
`domain_hint`: Makes account discovery faster
`code_challenge`: PKCE. Recommended
`code_challenge_method`: PKCE should be `S256`
`state`: optional, opentext

Hybrid Flow (OIDC id_token added):
Sample (Stage #2)
```
// Line breaks for legibility only

https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?
client_id=00001111-aaaa-2222-bbbb-3333cccc4444
&response_type=code%20id_token
&redirect_uri=http%3A%2F%2Flocalhost%2Fmyapp%2F
&response_mode=fragment
&scope=openid%20offline_access%20https%3A%2F%2Fgraph.microsoft.com%2Fuser.read
&state=12345
&nonce=abcde
&code_challenge=YTFjNjI1OWYzMzA3MTI4ZDY2Njg5M2RkNmVjNDE5YmEyZGRhOGYyM2IzNjdmZWFhMTQ1ODg3NDcxY2Nl
&code_challenge_method=S256
```
`nonce`: Required for this flow, random string. Included in `id_token` as a claim. Prevents replay attacks
`fragment`: Can cause issues with localhost testing, try `form_post`

Token Sample (Stage #6)
```
// Line breaks for legibility only

POST /{tenant}/oauth2/v2.0/token HTTP/1.1
Host: https://login.microsoftonline.com
Content-Type: application/x-www-form-urlencoded

client_id=11112222-bbbb-3333-cccc-4444dddd5555
&scope=https%3A%2F%2Fgraph.microsoft.com%2Fmail.read
&code=OAAABAAAAiL9Kn2Z27UubvWFPbm0gLWQJVzCTE9UkP3pSx1aXxUjq3n8b2JRLk4OxVXr...
&redirect_uri=http%3A%2F%2Flocalhost%2Fmyapp%2F
&grant_type=authorization_code
&code_verifier=ThisIsntRandomButItNeedsToBe43CharactersLong 
&client_secret=sampleCredentia1s    // NOTE: Only required for web apps. This secret needs to be URL-Encoded.
```
`scope`: Optional. OIDC scopes: profile, openid, email
`redirect_uri`: Same redirect_uri as the authorize stage (#2)
`client_secret_jwt`: In place of `client_secret`, a JWT which is claims signed by the `client_secret` can be sent
`private_key_jwt`: A JWT signed by a certificate and sent under `client_assertion` key

### Response including User Profile:
`access_token`
`expires_at` `expires_in` `ext_expires_in`
`id_token` .  <- Because of the `openid` scope. Is a JWT
`scope`
`token_type` : `Bearer`
`userinfo` :
```
{   'aud': '16df6f47-92f1-4bec-8f83-6db76d8aed24',
    'email': 'ghazan_haider@manuXXXX.com',
    'exp': 1788284448,
    'iat': 1788280548,
    'iss': 'https://login.microsoftonline.com/5d3e2773-e07f-4432-a630-1a0f68a28a05/v2.0',
    'name': 'Ghazan Haider',
    'nbf': 1788280548,
    'nonce': 'WRArO8nTLMNO9lScOBxN',
    'oid': '55622fce-fa3d-450d-8e1a-a82f2af9e8fe',
    'preferred_username': 'haidegh@xxxxx.COM',
    'rh': '1.ARMAcyc-XX_gMkSmMBoPaKKKBUdv3xbxkuxLj4Ntt22K7SQAAGkTAA.',
    'sid': '007ed4da-b029-8c58-b44e-db031c5122fc',
    'sub': 'miW9OSkiRyRw8isvQ8ZjMDQBJIYjd0mFBi97bnoNiSw',
    'tid': '5d3e2773-e07f-4432-a630-1a0f68a28a05',
    'uti': 'n1iaE5aAQUihuHV_0Kg6AA',
    'ver': '2.0'
}
```


## Google

### User Profile returned

```
{   'at_hash': 'B9rSeetCtEpN1C4RWarHLQ', 
    'aud': '752123555212-ptbg8m92onmfheaigdivck1q63npsjk7.apps.googleusercontent.com',
    'azp': '752123555212-ptbg8m92onmfheaigdivck1q63npsjk7.apps.googleusercontent.com',
    'email': 'ghazan.haider@gmail.com',
    'email_verified': True,
    'exp': 1788284962,
    'family_name': 'Haider',
    'given_name': 'Ghazan',
    'iat': 1788281362,
    'iss': 'https://accounts.google.com',
    'name': 'Ghazan Haider',
    'nonce': 'I3j4HnF6V3AGFbGvPiQX',
    'picture': 'https://lh3.googleusercontent.com/a/ACg8ocIm3W21NugjmMxn-rpmKlQYH-dHIoIdZwRuRpRjWglmgey6-Vj58A=s96-c',
    'sub': '100176079168840944107'
}
```

## Github

### User Profile returned
```
{   'avatar_url': 'https://avatars.githubusercontent.com/u/11358860?v=4',
    'bio': None,
    'blog': '',
    'company': 'MyCompany',
    'created_at': '2015-05-08T22:14:08Z',
    'email': None,
    'events_url': 'https://api.github.com/users/ghazanhaider/events{/privacy}',
    'followers': 4,
    'followers_url': 'https://api.github.com/users/ghazanhaider/followers',
    'following': 0,
    'following_url': 'https://api.github.com/users/ghazanhaider/following{/other_user}',
    'gists_url': 'https://api.github.com/users/ghazanhaider/gists{/gist_id}',
    'gravatar_id': '',
    'hireable': None,
    'html_url': 'https://github.com/ghazanhaider',
    'id': 12358860,
    'location': None,
    'login': 'ghazanhaider',
    'name': 'Ghazan Haider',
    'node_id': 'MDQ6VXNlcjEyMzU4ODYw',
    'notification_email': None,
    'organizations_url': 'https://api.github.com/users/ghazanhaider/orgs',
    'public_gists': 17,
    'public_repos': 44,
    'received_events_url': 'https://api.github.com/users/ghazanhaider/received_events',
    'repos_url': 'https://api.github.com/users/ghazanhaider/repos',
    'site_admin': False,
    'starred_url': 'https://api.github.com/users/ghazanhaider/starred{/owner}{/repo}',
    'subscriptions_url': 'https://api.github.com/users/ghazanhaider/subscriptions',
    'twitter_username': None,
    'type': 'User',
    'updated_at': '2026-08-18T17:51:51Z',
    'url': 'https://api.github.com/users/ghazanhaider',
    'user_view_type': 'public'
}
```

## Apple

Apple SSO requires JWT signed by the Apple Developers Key
You must enroll in the Apple Developer Program (online) using your iCloud login
The `Certificates, IDs, & Profiles` is a small link near the bottom, it should output a `.pk8` private key file to use

### User Profile returned
```
```

## Web apps that login into the browser's identity session
- Use: Authorization Code Flow
- The backend app redirects the client's web browser to the Microsoft Entra ID authorize endpoint (/oauth2/v2.0/authorize).
- Cookie Utilization: Because the request runs inside the user's browser, Microsoft Entra ID detects the user's active session cookie.
- Silent Authorization: If a valid session exists and the permissions were previously consented to, Microsoft Entra ID authenticates the request silently without prompting the user to type credentials again.
- Code Issuance: Microsoft Entra ID redirects back to the backend application with an authorization code.
- Token Exchange: The backend app takes this code and securely exchanges it for access, ID, and refresh tokens at the /oauth2/v2.0/token endpoint using its confidential client credentials (secret or certificate) (If we can extract a usable/indexable user_id from the auth code, this step is optional)

Some Flask examples:

- Firefox with Firefox/Mozilla accounts (Unable to login into mozilla-hub.atlassian.net to request FXA client access)

- Google (Works)

- Github (Works)

- Microsoft Entra (Works)

- Apple (Needs $99 Apple Developer Profile)

- Facebook (untested)

And one FastAPI example under `google`

In each folder, run:
```
source .venv/bin/activate
python3 app.py
```

And go to:
`http://127.0.0.1:5000`
