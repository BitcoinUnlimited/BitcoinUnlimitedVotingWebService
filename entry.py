# entry point for gunicorn WSGI server
from serve import make_app

app, db = make_app()
