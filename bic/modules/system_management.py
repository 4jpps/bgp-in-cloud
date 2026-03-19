from bic.core import BIC_DB
from bic.modules import network_management

def get_all_settings(db_core: BIC_DB) -> dict:
    """Retrieves all settings from the database and returns them as a dictionary."""
    settings_rows = db_core.find_all('settings')
    return {row['key']: row['value'] for row in settings_rows}

def save_all_settings(db_core: BIC_DB, **kwargs):
    """Saves all settings from a form submission and triggers necessary updates."""
    # The handler receives all form fields as kwargs
    for key, value in kwargs.items():
        db_core.insert_or_replace('settings', {'key': key, 'value': value})
    
    # After saving, trigger updates for services that depend on these settings
    network_management.update_bird_configs(db_core)
    # In the future, we might also need to update WireGuard if the endpoint changes.
    
    return {"success": True, "message": "Settings updated and services reconfigured."}
