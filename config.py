import os
from pathlib import Path

"""
Configuration settings.
Environment variables will be configured later.
"""

class Config:
    """Base configuration."""
    BASE_DIR = Path(__file__).resolve().parent
    
    # Detect Render environment
    IS_RENDER = os.environ.get('RENDER', 'false').lower() == 'true'
    
    # Database Path Handling (Render Free Tier compatible)
    # Note: Free tier does not support persistent disks, so we use a local directory.
    DATA_DIR = BASE_DIR / 'data'
    
    # Ensure data directory exists
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create data directory at {DATA_DIR}: {e}")
    
    AUTH_DB_PATH = DATA_DIR / 'auth.db'
    
    # Secret Key Management
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        if IS_RENDER:
            # In production, we fail fast if the secret key is missing
            raise RuntimeError("CRITICAL: SECRET_KEY environment variable is not set in production!")
        else:
            # Safe fallback for local development
            SECRET_KEY = 'dev-key-123-fallback'
    
    DEBUG = not IS_RENDER
    ATTENDANCE_THRESHOLD_MINUTES = 35
