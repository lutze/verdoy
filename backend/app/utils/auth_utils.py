"""
Authentication utilities for LMS Core API.

This module contains utility functions for authentication operations
that are used across the application to avoid circular imports.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Union, Any, Dict
from jose import jwt
from passlib.context import CryptContext

from ..config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time (defaults to settings)
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        jwt.JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise e


def is_token_expired(token: str) -> bool:
    """
    Check if a JWT token is expired.
    
    Args:
        token: JWT token string
        
    Returns:
        True if token is expired, False otherwise
    """
    try:
        payload = decode_access_token(token)
        exp = payload.get("exp")
        if exp is None:
            return True
        
        return datetime.utcnow() > datetime.fromtimestamp(exp)
    except jwt.JWTError:
        return True


def get_token_expiration_time(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Token expiration time or None if invalid
    """
    try:
        payload = decode_access_token(token)
        exp = payload.get("exp")
        if exp is None:
            return None
        
        return datetime.fromtimestamp(exp)
    except jwt.JWTError:
        return None


def validate_token_format(token: str) -> bool:
    """
    Validate the format of a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        True if token format is valid, False otherwise
    """
    if not token or not isinstance(token, str):
        return False
    
    # Basic JWT format validation (3 parts separated by dots)
    parts = token.split('.')
    if len(parts) != 3:
        return False
    
    return True 