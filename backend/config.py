import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'

    SECRET_KEY = os.getenv('SECRET_KEY', '')
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not set. Generate a secure random key and add it to your .env file. "
            "You can generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'apollo_metrics')
    MYSQL_SSL_CA = os.getenv('MYSQL_SSL_CA', '')

    LLM_API_KEY = os.getenv('LLM_API_KEY', '')
    LLM_API_BASE_URL = os.getenv('LLM_API_BASE_URL', '')
    LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', '')

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    CLEANED_FOLDER = os.path.join(BASE_DIR, 'cleaned')
    MODELS_FOLDER = os.path.join(BASE_DIR, 'models')
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'reports')

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
