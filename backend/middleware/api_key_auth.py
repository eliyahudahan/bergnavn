# backend/middleware/api_key_auth.py
# Simple API key middleware for sensitive endpoints

import os
from functools import wraps
from flask import request, jsonify

def require_api_key(f):
    """
    Decorator that enforces API key validation.
    Checks for header: X-API-KEY or query param: api_key
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        expected_key = os.getenv("BERGNAVN_API_KEY")
        provided_key = (
            request.headers.get("X-API-KEY")
            or request.args.get("api_key")
            or None
        )

        if not expected_key:
            return jsonify({
                "status": "error",
                "message": "Server misconfigured: API key missing in environment"
            }), 500

        if provided_key != expected_key:
            return jsonify({
                "status": "unauthorized",
                "message": "Invalid or missing API key"
            }), 401

        return f(*args, **kwargs)
    return decorated
