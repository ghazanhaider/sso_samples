# Microsoft Entra OAuth notes

## Flask SSO

flask_app.py
```
python3.14 -m venv venv
pip install -r requirements.txt
python3 flask_app.py
```

## FastAPI SSO

fastapi_app.py
```
uv init --no-package
uv add 'fastapi[standard]' authlib itsdangerous
uv run fastapi dev fastapi_app.py --port 5000
```



# Certificate instead of Secret

To generate a self-signed certificate pair to use instead of `client_secret`:
```
openssl req -x509 -newkey rsa:2048 -keyout private.pem -out certificate.pem -days 365 -nodes -subj "/CN=FastApiClient"
```

For the thumbprint you cannot use the thumbprint as seen in Azure Entra->app reg -> certificate page (hex format)

Use this format of the certificate:
```
openssl x509 -in certificate.pem -fingerprint -noout | sed 's/SHA1 Fingerprint=//g' | tr -d ':' | xxd -r -ps | base64
```

Basically hex to byte to base64 of the thumbprint seen in the portal `xxd -r -ps | base64`
