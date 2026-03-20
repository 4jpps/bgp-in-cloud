"""
This module handles core system settings and administrative tasks.
"""

import os
import secrets
from bic.core import BIC_DB, get_logger

log = get_logger(__name__)

def get_secret_key(db_core: BIC_DB) -> str:
    """Retrieves the application's SECRET_KEY from the database.

    If the key does not exist, it generates a new cryptographically secure key,
    stores it in the database for persistence, and then returns it.
    """
    secret_key = db_core.get_setting('SECRET_KEY')
    if not secret_key:
        log.warning("SECRET_KEY not found in database. Generating a new one.")
        # Generate a new 64-character hex key for robust security
        secret_key = secrets.token_hex(32)
        db_core.insert_or_replace('settings', {'key': 'SECRET_KEY', 'value': secret_key})
        log.info("New SECRET_KEY has been generated and stored in the database.")
    return secret_key

def get_jwt_algorithm(db_core: BIC_DB) -> str:
    """Retrieves the JWT signing algorithm from the database, defaulting to HS256."""
    return db_core.get_setting('JWT_ALGORITHM', 'HS256')

def get_token_expire_minutes(db_core: BIC_DB) -> int:
    """Retrieves the JWT expiration time in minutes, defaulting to 30."""
    return int(db_core.get_setting('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

def save_all_settings(db_core: BIC_DB, **kwargs):
    """Iterates through kwargs and saves each as a setting in the database."""
    log.info("Saving all system settings.")
    for key, value in kwargs.items():
        # Skip empty values and CSRF token
        if value and key != 'csrf_token':
            db_core.insert_or_replace('settings', {'key': key, 'value': value})
            log.info(f"Saved setting: {key}")
    return {"success": True}
