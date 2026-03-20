"""
This module handles core system settings and administrative tasks.
"""

import os
import secrets
import gzip
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
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

def get_all_settings(db_core: BIC_DB, **kwargs) -> dict:
    """Retrieves all settings from the database and returns them as a dictionary."""
    settings_list = db_core.find_all('settings')
    settings_dict = {setting['key']: setting['value'] for setting in settings_list}
    log.info(f"Loaded {len(settings_dict)} settings from the database.")
    return settings_dict

def add_audit_log(db_core: BIC_DB, action: str, user_id: str = None, details: str = None):
    """Adds a new entry to the audit log table."""
    log_data = {
        "user_id": user_id,
        "action": action,
        "details": details
    }
    db_core.insert("audit_log", log_data)

def get_audit_logs(db_core: BIC_DB, **kwargs) -> list:
    """Retrieves all audit log entries, joining with the users table."""
    log.info("Fetching all audit logs.")
    query = """
        SELECT a.id, u.username, a.action, a.details, a.timestamp
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.timestamp DESC
    """
    return db_core.query_to_dict(query)

def save_all_settings(db_core: BIC_DB, **kwargs):
    """Iterates through kwargs and saves each as a setting in the database."""
    log.info("Saving all system settings.")
    for key, value in kwargs.items():
        # Skip empty values and CSRF token
        if value and key != 'csrf_token':
            db_core.insert_or_replace('settings', {'key': key, 'value': value})
            log.info(f"Saved setting: {key}")
    return {"success": True}

# --- Backup and Restore ---

def list_backups(**kwargs) -> list:
    """Lists all available database backups."""
    backup_dir = Path("backups")
    if not backup_dir.exists():
        return []
    
    backups = []
    for f in backup_dir.glob("*.db.gz"):
        stat = f.stat()
        backups.append({
            "filename": f.name,
            "created_at": datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
            "size": f"{stat.st_size / 1024:.2f} KB",
        })
    return sorted(backups, key=lambda x: x['created_at'], reverse=True)

def create_backup(db_core: BIC_DB, **kwargs):
    """Creates a gzipped backup of the current SQLite database."""
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"bic_backup_{timestamp}.db.gz"
    backup_path = backup_dir / backup_filename
    
    # Use the sqlite3 .backup command to a temporary file, then gzip it
    temp_backup_path = backup_dir / "temp_backup.db"
    
    try:
        # Ensure the source connection is closed to safely copy
        source_conn = sqlite3.connect(db_core.db_path)
        backup_conn = sqlite3.connect(temp_backup_path)
        with backup_conn:
            source_conn.backup(backup_conn)
        backup_conn.close()
        source_conn.close()

        # Gzip the temporary file
        with open(temp_backup_path, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        log.info(f"Successfully created database backup: {backup_path}")
        return {"success": True}
    except Exception as e:
        log.error(f"Failed to create backup: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
    finally:
        # Clean up the temporary uncompressed backup
        if temp_backup_path.exists():
            temp_backup_path.unlink()

def restore_backup(db_core: BIC_DB, filename: str, **kwargs):
    """Restores the database from a gzipped backup file."""
    backup_dir = Path("backups")
    backup_path = backup_dir / filename
    
    if not backup_path.exists():
        log.error(f"Restore failed: Backup file not found at {backup_path}")
        return {"success": False, "error": "Backup file not found."}

    # The application will be restarted by the supervisor after this
    log.warning(f"Restoring database from {filename}. Application will restart.")
    
    try:
        with gzip.open(backup_path, 'rb') as f_in:
            with open(db_core.db_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        log.info("Database restore successful. Restarting application...")
        # In a real deployment, a process manager would handle the restart.
        # For development, we can exit and let the reloader handle it.
        os._exit(1) # Force exit
        return {"success": True}
    except Exception as e:
        log.error(f"Failed to restore backup: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

def delete_backup(filename: str, **kwargs):
    """Deletes a specific backup file."""
    backup_dir = Path("backups")
    backup_path = backup_dir / filename
    
    if backup_path.exists():
        try:
            backup_path.unlink()
            log.info(f"Successfully deleted backup: {filename}")
            return {"success": True}
        except Exception as e:
            log.error(f"Failed to delete backup {filename}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    else:
        log.warning(f"Attempted to delete non-existent backup: {filename}")
        return {"success": False, "error": "File not found."}

