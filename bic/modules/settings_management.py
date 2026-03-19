from bic.core import BIC_DB

def get_all_settings(db_core: BIC_DB) -> dict:
    """Retrieves all settings from the database and returns them as a dictionary."""
    settings_rows = db_core.find_all('settings')
    return {row['key']: row['value'] for row in settings_rows}

def update_settings(db_core: BIC_DB, settings_data: dict):
    """Updates multiple settings in the database."""
    for key, value in settings_data.items():
        db_core.insert_or_replace('settings', {'key': key, 'value': value})
    return {"success": True, "message": "Settings updated successfully."}
