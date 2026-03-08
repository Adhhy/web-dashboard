import os
from pathlib import Path

"""
Configuration settings.
Environment variables will be configured later.
"""

class Config:
    """Base configuration."""
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / 'data'
    AUTH_DB_PATH = DATA_DIR / 'auth.db'
    
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-123')
