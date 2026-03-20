#!/usr/bin/env python
"""
This module provides authentication and authorization helpers.
"""

from functools import wraps
from fastapi import Depends, HTTPException
from bic.webapp import get_current_user

def role_required(required_role: str):
    """A decorator to restrict access to a route to users with a specific role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = await get_current_user(kwargs['request'])
            if not user or user['role'] != required_role:
                raise HTTPException(status_code=403, detail="Forbidden")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
