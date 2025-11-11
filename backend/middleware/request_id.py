# backend/middleware/request_id.py
import uuid
from flask import g, request

def assign_request_id(app):
    @app.before_request
    def add_request_id():
        g.request_id = str(uuid.uuid4())
