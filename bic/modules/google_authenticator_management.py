"""
This module handles all Google Authenticator related logic for the application.
"""

import pyotp
import qrcode
import io
import base64

from bic.core import BIC_DB, get_logger

log = get_logger(__name__)

def generate_secret(db_core: BIC_DB, user_id: str, username: str, issuer_name: str = "BGP in Cloud") -> dict:
    """Generate a new secret for a user and return it along with a QR code."""
    secret = pyotp.random_base32()
    
    # Check if user already has a secret
    existing_secret = db_core.find_one("google_authenticator_secrets", {"user_id": user_id})
    if existing_secret:
        db_core.update("google_authenticator_secrets", existing_secret['id'], {"secret": secret})
    else:
        db_core.insert("google_authenticator_secrets", {"id": pyotp.random_base32(), "user_id": user_id, "secret": secret})

    # Generate QR code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=username, issuer_name=issuer_name)
    
    img = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    qr_code_b64 = base64.b64encode(buf.read()).decode('utf-8')
    
    return {"secret": secret, "qr_code": qr_code_b64}

def verify_otp(db_core: BIC_DB, user_id: str, otp: str) -> bool:
    """Verify a Google Authenticator OTP for a user."""
    secret_data = db_core.find_one("google_authenticator_secrets", {"user_id": user_id})
    if not secret_data:
        log.warning(f"User {user_id} does not have a Google Authenticator secret.")
        return False
        
    totp = pyotp.TOTP(secret_data['secret'])
    return totp.verify(otp)
