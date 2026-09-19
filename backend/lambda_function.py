"""
Entry point AWS Lambda calls. This wraps the existing Flask app — none of
the route logic in app.py changes.
"""
import awsgi
from app import app


def lambda_handler(event, context):
    return awsgi.response(app, event, context)