"""Authentication API endpoints.

This module provides user registration, login, and token management endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...models.user import Token, User, UserCreate, UserLogin, UserUpdate
from ...storage.user_repo import UserRepository
from ...utils.auth import (create_access_token, get_token_expiration_seconds,
                           hash_password, verify_password)
from ..dependencies import get_user_repo, require_admin, require_auth

router = APIRouter()


class RegisterResponse(BaseModel):
    """Response model for user registration."""

    user: User
    message: str = "User registered successfully"


class LoginResponse(BaseModel):
    """Response model for login."""

    user: User
    token: Token


@router.post(
    "/auth/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_create: UserCreate,
    user_repo: Optional[UserRepository] = Depends(get_user_repo),
):
    """Register a new user.

    Args:
        user_create: User creation data
        user_repo: User repository

    Returns:
        RegisterResponse with created user

    Raises:
        HTTPException: 400 if username/email already exists
        HTTPException: 503 if database unavailable
    """
    if not user_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User repository not available",
        )

    # Check if username already exists
    existing_user = await user_repo.get_user_by_username(user_create.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    existing_email = await user_repo.get_user_by_email(user_create.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash password
    hashed_password = hash_password(user_create.password)

    # Create user
    try:
        user_data = await user_repo.create_user(
            username=user_create.username,
            email=user_create.email,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            role=user_create.role,
            is_active=user_create.is_active,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )

    # Return user (without hashed_password)
    user = User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        full_name=user_data.get("full_name"),
        role=user_data["role"],
        is_active=user_data["is_active"],
        created_at=user_data["created_at"],
        updated_at=user_data.get("updated_at"),
        last_login=user_data.get("last_login"),
    )

    return RegisterResponse(user=user)


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    credentials: UserLogin,
    user_repo: Optional[UserRepository] = Depends(get_user_repo),
):
    """Authenticate user and return JWT token.

    Args:
        credentials: Username and password
        user_repo: User repository

    Returns:
        LoginResponse with user and token

    Raises:
        HTTPException: 401 if credentials invalid
        HTTPException: 403 if user inactive
        HTTPException: 503 if database unavailable
    """
    if not user_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User repository not available",
        )

    # Get user by username
    user_data = await user_repo.get_user_by_username(credentials.username)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Update last login
    await user_repo.update_last_login(user_data["id"])

    # Create access token
    access_token = create_access_token(
        data={"sub": user_data["username"], "role": user_data["role"]},
    )

    # Create token response
    token = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_token_expiration_seconds(),
    )

    # Create user response
    user = User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        full_name=user_data.get("full_name"),
        role=user_data["role"],
        is_active=user_data["is_active"],
        created_at=user_data["created_at"],
        updated_at=user_data.get("updated_at"),
        last_login=user_data.get("last_login"),
    )

    return LoginResponse(user=user, token=token)


@router.get("/auth/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(require_auth),
):
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user from token

    Returns:
        User model with current user information
    """
    return current_user


@router.get("/auth/users", response_model=list[User])
async def list_users(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_admin),
    user_repo: Optional[UserRepository] = Depends(get_user_repo),
):
    """List all users (admin only).

    Args:
        limit: Maximum number of users to return
        offset: Number of users to skip
        current_user: Current authenticated admin user
        user_repo: User repository

    Returns:
        List of User models

    Raises:
        HTTPException: 503 if database unavailable
    """
    if not user_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User repository not available",
        )

    users_data = await user_repo.list_users(limit=limit, offset=offset)

    return [
        User(
            id=u["id"],
            username=u["username"],
            email=u["email"],
            full_name=u.get("full_name"),
            role=u["role"],
            is_active=u["is_active"],
            created_at=u["created_at"],
            updated_at=u.get("updated_at"),
            last_login=u.get("last_login"),
        )
        for u in users_data
    ]


@router.get("/auth/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    user_repo: Optional[UserRepository] = Depends(get_user_repo),
):
    """Get user by ID (admin only).

    Args:
        user_id: User UUID
        current_user: Current authenticated admin user
        user_repo: User repository

    Returns:
        User model

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 503 if database unavailable
    """
    if not user_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User repository not available",
        )

    user_data = await user_repo.get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        full_name=user_data.get("full_name"),
        role=user_data["role"],
        is_active=user_data["is_active"],
        created_at=user_data["created_at"],
        updated_at=user_data.get("updated_at"),
        last_login=user_data.get("last_login"),
    )


@router.patch("/auth/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    user_repo: Optional[UserRepository] = Depends(get_user_repo),
):
    """Update user information (admin only).

    Args:
        user_id: User UUID
        user_update: Fields to update
        current_user: Current authenticated admin user
        user_repo: User repository

    Returns:
        Updated User model

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 503 if database unavailable
    """
    if not user_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User repository not available",
        )

    # Check if user exists
    existing_user = await user_repo.get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Build updates dict
    updates = {}
    if user_update.email is not None:
        updates["email"] = user_update.email
    if user_update.full_name is not None:
        updates["full_name"] = user_update.full_name
    if user_update.role is not None:
        updates["role"] = user_update.role
    if user_update.is_active is not None:
        updates["is_active"] = user_update.is_active
    if user_update.password is not None:
        updates["hashed_password"] = hash_password(user_update.password)

    # Update user
    updated_user_data = await user_repo.update_user(user_id, updates)
    if not updated_user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found after update",
        )

    return User(
        id=updated_user_data["id"],
        username=updated_user_data["username"],
        email=updated_user_data["email"],
        full_name=updated_user_data.get("full_name"),
        role=updated_user_data["role"],
        is_active=updated_user_data["is_active"],
        created_at=updated_user_data["created_at"],
        updated_at=updated_user_data.get("updated_at"),
        last_login=updated_user_data.get("last_login"),
    )


@router.delete("/auth/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    user_repo: Optional[UserRepository] = Depends(get_user_repo),
):
    """Delete user (admin only).

    Args:
        user_id: User UUID
        current_user: Current authenticated admin user
        user_repo: User repository

    Raises:
        HTTPException: 403 if trying to delete self
        HTTPException: 404 if user not found
        HTTPException: 503 if database unavailable
    """
    if not user_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User repository not available",
        )

    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete your own account",
        )

    # Delete user
    deleted = await user_repo.delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
