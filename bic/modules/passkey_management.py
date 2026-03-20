"""
This module handles all Passkey (WebAuthn) related logic for the application.
"""

import os
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers.structs import (
    RegistrationCredential,
    AuthenticationCredential,
    PublicKeyCredentialCreationOptions,
    PublicKeyCredentialRequestOptions,
)
from webauthn.helpers.exceptions import WebAuthnException

from bic.core import BIC_DB, get_logger

log = get_logger(__name__)

RP_ID = os.getenv("RP_ID", "localhost")
RP_NAME = "BGP in Cloud"

def get_registration_options(db_core: BIC_DB, user_id: str, username: str) -> PublicKeyCredentialCreationOptions:
    """Generate registration options for a user."""
    user_credentials = db_core.find_all("webauthn_credentials", {"user_id": user_id})
    
    return generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user_id,
        user_name=username,
        exclude_credentials=[{"type": "public-key", "id": cred['credential_id']} for cred in user_credentials]
    )

def verify_registration(db_core: BIC_DB, user_id: str, credential: dict) -> None:
    """Verify the registration response and save the new credential."""
    try:
        registration_verification = verify_registration_response(
            credential=RegistrationCredential.parse_raw(credential),
            expected_challenge=b"", # In a real app, this would be a challenge from the session
            expected_origin="http://localhost:8000", # In a real app, this would be the actual origin
            expected_rp_id=RP_ID,
        )
        
        # Save the new credential
        new_credential = {
            "id": str(os.urandom(16).hex()),
            "user_id": user_id,
            "credential_id": registration_verification.credential_id,
            "public_key": registration_verification.credential_public_key,
            "sign_count": registration_verification.sign_count,
            "transports": ",".join(credential.get("transports", [])),
        }
        db_core.insert("webauthn_credentials", new_credential)
        log.info(f"Successfully registered new passkey for user {user_id}")
        
    except WebAuthnException as e:
        log.error(f"Passkey registration failed for user {user_id}: {e}")
        raise

def get_authentication_options(db_core: BIC_DB, user_id: str) -> PublicKeyCredentialRequestOptions:
    """Generate authentication options for a user."""
    user_credentials = db_core.find_all("webauthn_credentials", {"user_id": user_id})
    
    return generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=[{"type": "public-key", "id": cred['credential_id']} for cred in user_credentials]
    )

def verify_authentication(db_core: BIC_DB, user_id: str, credential: dict) -> None:
    """Verify the authentication response."""
    user_credentials = db_core.find_all("webauthn_credentials", {"user_id": user_id})
    cred_to_verify = None
    for cred in user_credentials:
        if cred['credential_id'] == credential['id']:
            cred_to_verify = cred
            break
    
    if not cred_to_verify:
        raise WebAuthnException("Credential not found for user")
        
    try:
        authentication_verification = verify_authentication_response(
            credential=AuthenticationCredential.parse_raw(credential),
            expected_challenge=b"", # In a real app, this would be a challenge from the session
            expected_origin="http://localhost:8000", # In a real app, this would be the actual origin
            expected_rp_id=RP_ID,
            credential_public_key=cred_to_verify['public_key'],
            credential_current_sign_count=cred_to_verify['sign_count'],
        )
        
        # Update the sign count
        db_core.update("webauthn_credentials", cred_to_verify['id'], {"sign_count": authentication_verification.new_sign_count})
        log.info(f"Successfully authenticated user {user_id} with passkey")
        
    except WebAuthnException as e:
        log.error(f"Passkey authentication failed for user {user_id}: {e}")
        raise
