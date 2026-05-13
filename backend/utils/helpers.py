import os
import re
import secrets
from functools import wraps
from flask import session, jsonify
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(filename):
    name, ext = os.path.splitext(secure_filename(filename))
    return f"{name}_{secrets.token_hex(8)}{ext}"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required. Please log in.'}), 401
        return f(*args, **kwargs)
    return decorated_function


def sanitize_column_name(col):
    return re.sub(r'[^a-zA-Z0-9_]', '', str(col).strip().replace(' ', '_'))
