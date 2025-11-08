"""Authentication manager for handling JWT tokens and user sessions."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication state, token storage, and API authentication."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self._token: Optional[str] = None
        self._user: Optional[Dict[str, Any]] = None
        self._token_expiry: Optional[datetime] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._token_file = Path.home() / ".network-device-monitor" / "token.json"
        self._token_file.parent.mkdir(parents=True, exist_ok=True)

    @property
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated with valid token."""
        if not self._token:
            return False
        if self._token_expiry and datetime.utcnow() >= self._token_expiry:
            logger.info("Token expired")
            self._token = None
            self._user = None
            return False
        return True

    @property
    def current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user information."""
        return self._user if self.is_authenticated else None

    @property
    def user_role(self) -> Optional[str]:
        """Get current user's role."""
        if self._user:
            return self._user.get("role")
        return None

    def is_admin(self) -> bool:
        """Check if current user has admin role."""
        return self.user_role == "admin"

    def is_operator(self) -> bool:
        """Check if current user has operator or higher role."""
        return self.user_role in ("admin", "operator")

    def is_viewer(self) -> bool:
        """Check if current user has viewer or higher role."""
        return self.user_role in ("admin", "operator", "viewer")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with authentication headers."""
        if self._client is None:
            headers = {}
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=10.0,
                headers=headers,
            )
        return self._client

    async def aclose(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def login(self, username: str, password: str) -> bool:
        """
        Authenticate user and store token.

        Args:
            username: User's username
            password: User's password

        Returns:
            True if login successful, False otherwise
        """
        try:
            client = await self._get_client()

            # Ensure we're sending JSON with explicit Content-Type header
            response = await client.post(
                "/api/auth/login",
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            # Backend returns {user: {...}, token: {access_token, token_type, expires_in}}
            token_data = data.get("token", data)  # Fallback to data for backward compatibility
            user_data = data.get("user")

            self._token = token_data["access_token"]
            token_type = token_data.get("token_type", "bearer")

            # Update client headers
            if self._client:
                self._client.headers["Authorization"] = f"{token_type.capitalize()} {self._token}"

            # Calculate token expiry (default 1 hour if not specified)
            expires_in = token_data.get("expires_in", 3600)
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            # Store user info if provided, otherwise fetch it
            if user_data:
                self._user = user_data
            else:
                await self.fetch_current_user()

            # Save token to disk
            self._save_token()

            logger.info(f"Successfully logged in as {username}")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Login failed: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.exception(f"Login error: {e}")
            return False

    async def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Register a new user.

        Args:
            username: Desired username
            email: User's email
            password: User's password
            full_name: User's full name (optional)

        Returns:
            Tuple of (success, error_message)
        """
        try:
            client = await self._get_client()
            payload = {
                "username": username,
                "email": email,
                "password": password,
            }
            if full_name:
                payload["full_name"] = full_name

            # Ensure we're sending JSON with explicit Content-Type header
            response = await client.post(
                "/api/auth/register",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            logger.info(f"Successfully registered user {username}")
            return True, None

        except httpx.HTTPStatusError as e:
            error_msg = e.response.text
            try:
                error_data = e.response.json()
                detail = error_data.get("detail", error_msg)
                # Handle validation errors (list of dicts) vs simple string errors
                if isinstance(detail, list):
                    # Extract validation error messages
                    error_msg = "; ".join([err.get("msg", str(err)) for err in detail])
                else:
                    error_msg = str(detail)
            except Exception:
                pass
            logger.error(f"Registration failed: {error_msg}")
            return False, error_msg

        except Exception as e:
            logger.exception(f"Registration error: {e}")
            return False, str(e)

    async def fetch_current_user(self) -> bool:
        """
        Fetch current user information from API.

        Returns:
            True if successful, False otherwise
        """
        if not self._token:
            return False

        try:
            client = await self._get_client()
            response = await client.get("/api/auth/me")
            response.raise_for_status()
            self._user = response.json()
            username = self._user.get("username") if self._user else "unknown"
            logger.info(f"Fetched user info: {username}")
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning("Token invalid or expired")
                self._token = None
                self._user = None
            return False
        except Exception as e:
            logger.exception(f"Error fetching user: {e}")
            return False

    def logout(self) -> None:
        """Clear authentication state and remove stored token."""
        self._token = None
        self._user = None
        self._token_expiry = None
        if self._client:
            self._client.headers.pop("Authorization", None)
        self._remove_token()
        logger.info("Logged out")

    def _save_token(self) -> None:
        """Save token to disk for persistence across sessions."""
        try:
            data = {
                "token": self._token,
                "expiry": self._token_expiry.isoformat() if self._token_expiry else None,
                "user": self._user,
            }
            self._token_file.write_text(json.dumps(data, indent=2))
            self._token_file.chmod(0o600)  # Restrict permissions
            logger.debug(f"Saved token to {self._token_file}")
        except Exception as e:
            logger.exception(f"Failed to save token: {e}")

    def _remove_token(self) -> None:
        """Remove stored token file."""
        try:
            if self._token_file.exists():
                self._token_file.unlink()
                logger.debug(f"Removed token file {self._token_file}")
        except Exception as e:
            logger.exception(f"Failed to remove token: {e}")

    async def load_saved_token(self) -> bool:
        """
        Load token from disk and validate it.

        Returns:
            True if token loaded and valid, False otherwise
        """
        try:
            if not self._token_file.exists():
                return False

            data = json.loads(self._token_file.read_text())
            self._token = data.get("token")
            expiry_str = data.get("expiry")
            self._user = data.get("user")

            if expiry_str:
                self._token_expiry = datetime.fromisoformat(expiry_str)

            # Update client headers
            if self._token and self._client:
                self._client.headers["Authorization"] = f"Bearer {self._token}"

            # Validate token by fetching user
            if self.is_authenticated:
                if await self.fetch_current_user():
                    username = self._user.get("username") if self._user else "unknown"
                    logger.info(f"Loaded saved token for {username}")
                    return True

            # Token invalid or expired
            self.logout()
            return False

        except Exception as e:
            logger.exception(f"Failed to load token: {e}")
            return False

    async def check_auth_required(self) -> bool:
        """
        Check if the backend requires authentication.

        Returns:
            True if authentication is required, False if optional
        """
        try:
            client = httpx.AsyncClient(base_url=self.base_url, timeout=5.0)
            try:
                # Try to access a protected endpoint without auth
                response = await client.get("/api/devices")
                # If we get 200, auth is optional
                if response.status_code == 200:
                    return False
                # If we get 401, auth is required
                if response.status_code == 401:
                    return True
                return False
            finally:
                await client.aclose()
        except Exception as e:
            logger.exception(f"Failed to check auth requirement: {e}")
            return False


# Convenience function for quick auth check
async def check_auth_enabled(base_url: str = "http://localhost:8000") -> bool:
    """Check if authentication is enabled on the backend."""
    manager = AuthManager(base_url)
    try:
        return await manager.check_auth_required()
    finally:
        await manager.aclose()
