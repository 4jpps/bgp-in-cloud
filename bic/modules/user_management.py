#!/usr/bin/env python
"""
This module handles the business logic for user management, including authentication,
authorization, and user CRUD operations.
"""

import uuid
from datetime import datetime, timedelta
import bcrypt
from zxcvbn import zxcvbn
from jose import JWTError, jwt
from bic.core import BIC_DB, get_logger
from bic.modules.system_management import get_secret_key, get_jwt_algorithm, get_token_expire_minutes, add_audit_log

# Initialize logger
log = get_logger(__name__)

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    # bcrypt automatically handles the 72-byte limit by truncating.
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hash."""
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    # bcrypt.checkpw implicitly handles the 72-byte limit for the plain_password.
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

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

def create_access_token(db_core: BIC_DB, data: dict, expires_delta: timedelta | None = None):
    """Creates a new JWT access token using settings from the database."""
    to_encode = data.copy()
    
    expire_minutes = get_token_expire_minutes(db_core)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    
    to_encode.update({"exp": expire})
    
    secret_key = get_secret_key(db_core)
    algorithm = get_jwt_algorithm(db_core)
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
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
    
    access_token_expires = timedelta(minutes=get_token_expire_minutes(db_core))
    access_token = create_access_token(
        db_core=db_core,
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

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

