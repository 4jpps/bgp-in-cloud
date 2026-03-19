from bic.core import BIC_DB

def get_all_settings(db_core: BIC_DB):
    """Loads all settings from the database into a single dictionary."""
    settings_list = db_core.find_all('settings')
    return {setting['key']: setting['value'] for setting in settings_list}

def save_all_settings(db_core: BIC_DB, **kwargs):
    """Saves a dictionary of settings to the database."""
    for key, value in kwargs.items():
        # This assumes an "upsert" logic is desired. We try to update,
        # and if it fails (because the key doesn't exist), we insert.
        existing = db_core.find_one('settings', {'key': key})
        if existing:
            db_core.update('settings', existing['id'], {'value': value})
        else:
            # This case shouldn't normally be hit if schema is seeded correctly
            db_core.insert('settings', {'key': key, 'value': value})
    return {"success": True, "message": "Settings saved successfully."}
