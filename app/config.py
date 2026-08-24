import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present (with override=True)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=True)


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key-change-me')
    ADMIN_PASSWORD = str(os.getenv('ADMIN_PASSWORD', 'admin123')).strip()

    # Database configuration
    db_env = os.getenv('DATABASE_URL')
    if db_env:
        if db_env.startswith('sqlite:///') and not db_env.startswith('sqlite:////'):
            # Relative SQLite path
            rel_path = db_env.replace('sqlite:///', '')
            db_path = BASE_DIR / rel_path
            db_path.parent.mkdir(parents=True, exist_ok=True)
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        else:
            SQLALCHEMY_DATABASE_URI = db_env
    else:
        default_db = BASE_DIR / 'data' / 'dictation.db'
        default_db.parent.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{default_db}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
