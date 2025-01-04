from flask import request, abort
from functools import wraps

def limit_content_length(max_size):
    """Decorator to limit content length for a specific route."""
    def decorator(f):
        @wraps(f)  # Preserve the original function's metadata
        def wrapper(*args, **kwargs):
            content_length = request.content_length
            if content_length is not None and content_length > max_size:
                abort(413, description="Request is too large.")
            return f(*args, **kwargs)
        return wrapper
    return decorator