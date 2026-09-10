## Google Flask SSO

flask_app.py
```
python3.14 -m venv venv
pip install -r requirements.txt
python3 flask_app.py
```

## Google FastAPI SSO

fastapi_app.py
```
uv init --no-package
uv add 'fastapi[standard]'
uv add fastapi authlib itsdangerous
uv run fastapi dev fastapi_app.py --port 5000
```
