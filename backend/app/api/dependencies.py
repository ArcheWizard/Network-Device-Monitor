"""API dependencies for authentication and authorization.

This module provides FastAPI dependencies for protecting routes with
authentication and role-based access control.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import settings
from ..models.user import User
from ..storage.user_repo import UserRepository
from ..utils.auth import decode_access_token

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


def get_user_repo(request: Request) -> Optional[UserRepository]:
    """Get user repository from app state.

    Args:
        request: FastAPI request object

    Returns:
        UserRepository instance or None if not initialized
    """
    return getattr(request.app.state, "user_repo", None)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repo: Optional[UserRepository] = Depends(get_user_repo),
) -> Optional[User]:
    """Get current authenticated user from JWT token.

    This dependency can be used to optionally authenticate users.
    Returns None if no token provided or authentication not required.

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer token credentials
        user_repo: User repository instance

    Returns:
        User model if authenticated, None otherwise

    Raises:
        HTTPException: If token is invalid or user not found (only when REQUIRE_AUTH=True)
    """
    # If authentication is not required, allow access
    if not settings.REQUIRE_AUTH:
        return None

    # If no credentials provided
    if not credentials:
        if settings.REQUIRE_AUTH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    # Decode token
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract username from token
    username: Optional[str] = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    if not user_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User repository not available",
        )

    user_data = await user_repo.get_user_by_username(username)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Return User model (without hashed_password)
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


async def require_auth(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Require authentication for a route.

    This dependency enforces authentication regardless of REQUIRE_AUTH setting.
    Use this for routes that should always be protected.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        User model

    Raises:
        HTTPException: If user is not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_role(*allowed_roles: str):
    """Create a dependency that requires specific user roles.

    Args:
        *allowed_roles: Roles that are allowed to access the route

    Returns:
        Dependency function

    Example:
        ```python
        @router.get("/admin")
        async def admin_route(user: User = Depends(require_role("admin"))):
            return {"message": "Admin access granted"}
        ```
    """

    async def check_role(current_user: User = Depends(require_auth)) -> User:
        """Check if user has required role.

        Args:
            current_user: Current authenticated user

        Returns:
            User model if role is allowed

        Raises:
            HTTPException: If user doesn't have required role
        """
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return check_role


# Convenience dependencies for common roles
require_admin = require_role("admin")
require_operator = require_role("admin", "operator")
require_viewer = require_role("admin", "operator", "viewer")
