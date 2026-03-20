"""
This module handles all YubiKey related logic for the application.
"""

import os
from yubico_client import Yubico

from bic.core import BIC_DB, get_logger

log = get_logger(__name__)

# These would be stored securely in a real application
YUBICO_CLIENT_ID = os.getenv("YUBICO_CLIENT_ID", "")
YUBICO_SECRET_KEY = os.getenv("YUBICO_SECRET_KEY", "")

def associate_yubikey(db_core: BIC_DB, user_id: str, otp: str) -> bool:
    """Associate a YubiKey with a user account."""
    if not YUBICO_CLIENT_ID or not YUBICO_SECRET_KEY:
        log.error("YUBICO_CLIENT_ID and YUBICO_SECRET_KEY must be set in the environment.")
        return False

    client = Yubico(YUBICO_CLIENT_ID, YUBICO_SECRET_KEY)
    try:
        if client.verify(otp):
            device_id = otp[:-32] # The public ID of the YubiKey
            # Check if this device is already associated with another user
            existing = db_core.find_one("yubikey_credentials", {"device_id": device_id})
            if existing:
                log.warning(f"YubiKey {device_id} is already associated with a user.")
                return False
            
            credential_data = {
                "id": str(os.urandom(16).hex()),
                "user_id": user_id,
                "device_id": device_id,
            }
            db_core.insert("yubikey_credentials", credential_data)
            log.info(f"Successfully associated YubiKey {device_id} with user {user_id}")
            return True
    except Exception as e:
        log.error(f"YubiKey verification failed: {e}")
    
    return False

def verify_yubikey(db_core: BIC_DB, user_id: str, otp: str) -> bool:
    """Verify a YubiKey OTP for a user."""
    if not YUBICO_CLIENT_ID or not YUBICO_SECRET_KEY:
        log.error("YUBICO_CLIENT_ID and YUBICO_SECRET_KEY must be set in the environment.")
        return False

    device_id = otp[:-32]
    credential = db_core.find_one("yubikey_credentials", {"user_id": user_id, "device_id": device_id})
    
    if not credential:
        log.warning(f"User {user_id} does not have YubiKey {device_id} associated with their account.")
        return False
        
    client = Yubico(YUBICO_CLIENT_ID, YUBICO_SECRET_KEY)
    try:
        return client.verify(otp)
    except Exception as e:
        log.error(f"YubiKey verification failed: {e}")
    
    return False
