#!/usr/bin/env python
"""
This module handles the business logic for user management, including authentication,
authorization, and user CRUD operations.
"""

import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
from zxcvbn import zxcvbn
from jose import JWTError, jwt
from bic.core import BIC_DB, get_logger, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Initialize logger and password context
log = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt, truncating to 72 bytes if necessary."""
    # Truncate password to 72 bytes to avoid ValueError from bcrypt
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        log.warning("Password exceeds 72 bytes and will be truncated for hashing.")
        password_bytes = password_bytes[:72]
    return pwd_context.hash(password_bytes)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def is_password_strong(password: str) -> bool:
    """Checks if a password meets minimum strength requirements using zxcvbn.

    A password is considered strong if it is at least 12 characters long and
    has a zxcvbn score of 3 or higher.

    Args:
        password: The password to check.

    Returns:
        True if the password is strong, False otherwise.
    """
    if len(password) < 12:
        return False
    results = zxcvbn(password)
    return results['score'] >= 3

def create_user(db_core: BIC_DB, username: str, email: str, password: str, role: str = 'user', user: dict = None, **kwargs) -> str | None:
    """Creates a new user in the database.

    This function handles new user creation. It ensures the username and email are
    unique, checks for password strength, hashes the password, and inserts the
    new user record into the database. It also creates an audit log entry.

    Args:
        db_core: An instance of the BIC_DB database core.
        username: The desired username for the new user.
        email: The new user's email address.
        password: The new user's plain-text password.
        role: The role to assign to the new user (e.g., 'user', 'admin').
        user: The user performing the action, for audit logging.
        **kwargs: Catches any unused arguments.

    Returns:
        The UUID of the newly created user, or None if creation failed.
    """
    log.info(f"Attempting to create new user: {username}")
    
    # Check if username or email already exists
    if db_core.find_one("users", {"username": username}):
        log.warning(f"Username {username} already exists.")
        return None
    if db_core.find_one("users", {"email": email}):
        log.warning(f"Email {email} already exists.")
        return None

    if not is_password_strong(password):
        log.warning(f"Password for user {username} is not strong enough.")
        return None

    user_data = {
        "id": str(uuid.uuid4()),
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
    }
    
    user_id = db_core.insert("users", user_data)
    if user_id:
        log.info(f"Successfully created user {username} with ID {user_id}")
        actor_id = user['id'] if user else None
        add_audit_log(db_core, user_id=actor_id, action="create_user", details=f"Created user {username} (ID: {user_id})")
        return user_id
    else:
        log.error(f"Failed to insert user {username} into the database.")
        return None

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Creates a new JWT access token.

    Args:
        data: The data to encode in the token payload (e.g., username, role).
        expires_delta: An optional timedelta object for token expiration.
                       Defaults to 15 minutes if not provided.

    Returns:
        The encoded JWT as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def login_user(db_core: BIC_DB, username: str, password: str):
    """Authenticates a user and returns an access token if successful.

    This function checks if the user exists, verifies their password, and, if
    successful, updates their last login time, creates an audit log, and generates
    a new JWT access token.

    Args:
        db_core: An instance of the BIC_DB database core.
        username: The username for the login attempt.
        password: The plain-text password for the login attempt.

    Returns:
        A dictionary containing the access token, or None if authentication fails.
    """
    user = db_core.find_one("users", {"username": username})
    if not user:
        log.warning(f"Login failed for non-existent user: {username}")
        add_audit_log(db_core, action="login_failed", details=f"Attempted login for non-existent user: {username}")
        return None

    if not verify_password(password, user['password_hash']):
        log.warning(f"Login failed for user {username} due to incorrect password.")
        add_audit_log(db_core, user_id=user['id'], action="login_failed", details=f"Failed login attempt for user: {username}")
        return None

    # Update last login time
    db_core.update("users", user['id'], {"last_login": datetime.utcnow().isoformat()})
    add_audit_log(db_core, user_id=user['id'], action="login_success")
    log.info(f"User {username} successfully authenticated.")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def add_audit_log(db_core: BIC_DB, action: str, user_id: str = None, details: str = None):
    """Adds a new entry to the audit log table.

    Args:
        db_core: An instance of the BIC_DB database core.
        action: A string describing the action being logged (e.g., "login_failed").
        user_id: The optional UUID of the user performing the action.
        details: Optional additional details about the event.
    """
    log_data = {
        "user_id": user_id,
        "action": action,
        "details": details
    }
    db_core.insert("audit_log", log_data)

def list_users(db_core: BIC_DB, **kwargs) -> list:
    """Lists all users in the system.

    Args:
        db_core: An instance of the BIC_DB database core.
        **kwargs: Catches any unused arguments.

    Returns:
        A list of dictionaries, where each dictionary represents a user.
    """
    log.info("Fetching all users.")
    return db_core.find_all("users")

def get_user(db_core: BIC_DB, id: str) -> dict | None:
    """Fetches a single user by their ID.

    Args:
        db_core: An instance of the BIC_DB database core.
        id: The UUID of the user to fetch.

    Returns:
        A dictionary representing the user, or None if not found.
    """
    return db_core.find_one("users", {"id": id})

def update_user(db_core: BIC_DB, id: str, username: str, email: str, role: str, password: str = None, user: dict = None, **kwargs):
    """Updates an existing user's information.

    This can update the username, email, and role. If a new password is provided,
    it will be checked for strength and then hashed before being updated.

    Args:
        db_core: An instance of the BIC_DB database core.
        id: The UUID of the user to update.
        username: The user's new username.
        email: The user's new email address.
        role: The user's new role.
        password: An optional new plain-text password.
        user: The user performing the action, for audit logging.
        **kwargs: Catches any unused arguments.
    """
    log.info(f"Updating user {id} ({username})")
    update_data = {
        "username": username,
        "email": email,
        "role": role
    }
    if password:
        if not is_password_strong(password):
            log.warning(f"New password for user {username} is not strong enough.")
            return
        update_data["password_hash"] = hash_password(password)
        log.info(f"Password for user {id} has been updated.")
    
    db_core.update("users", id, update_data)
    actor_id = user['id'] if user else None
    add_audit_log(db_core, user_id=actor_id, action="update_user", details=f"Updated user {username} (ID: {id})")

def delete_user(db_core: BIC_DB, id: str, user: dict = None, **kwargs):
    """Deletes a user from the system.

    Args:
        db_core: An instance of the BIC_DB database core.
        id: The UUID of the user to delete.
        user: The user performing the action, for audit logging.
        **kwargs: Catches any unused arguments.
    """
    deleted_user = get_user(db_core, id)
    if not deleted_user:
        log.error(f"Cannot delete non-existent user with ID: {id}")
        return
    
    log.warning(f"Deleting user {id} ({deleted_user['username']})")
    db_core.delete("users", id)
    actor_id = user['id'] if user else None
    add_audit_log(db_core, user_id=actor_id, action="delete_user", details=f"Deleted user {deleted_user['username']} (ID: {id})")

