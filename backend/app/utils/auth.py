"""Authentication and authorization utilities.

This module provides password hashing, JWT token generation and validation,
and user authentication functions.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string

    Example:
        ```python
        hashed = hash_password("SecurePass123")
        ```
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise

    Example:
        ```python
        is_valid = verify_password("SecurePass123", hashed)
        ```
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token (typically username and role)
        expires_delta: Token expiration time delta. Defaults to config setting.

    Returns:
        Encoded JWT token string

    Example:
        ```python
        token = create_access_token(
            data={"sub": "john_doe", "role": "admin"},
            expires_delta=timedelta(hours=1)
        )
        ```
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_EXPIRATION_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload dict, or None if invalid

    Example:
        ```python
        payload = decode_access_token(token)
        if payload:
            username = payload.get("sub")
        ```
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def get_token_expiration_seconds() -> int:
    """Get the token expiration time in seconds.

    Returns:
        Number of seconds until token expiration

    Example:
        ```python
        expires_in = get_token_expiration_seconds()
        ```
    """
    return settings.JWT_EXPIRATION_MINUTES * 60
