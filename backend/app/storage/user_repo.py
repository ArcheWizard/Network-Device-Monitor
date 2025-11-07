"""User repository for SQLite database.

This module provides CRUD operations for user management in SQLite.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import aiosqlite


class UserRepository:
    """Repository for managing users in SQLite database."""

    def __init__(self, conn: aiosqlite.Connection):
        """Initialize user repository.

        Args:
            conn: SQLite database connection
        """
        self._conn = conn

    async def create_user(
        self,
        username: str,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        role: str = "viewer",
        is_active: bool = True,
    ) -> dict:
        """Create a new user.

        Args:
            username: Unique username
            email: User email address
            hashed_password: Hashed password
            full_name: Optional full name
            role: User role (admin, operator, viewer)
            is_active: Whether user is active

        Returns:
            Created user data as dictionary

        Raises:
            aiosqlite.IntegrityError: If username or email already exists
        """
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        created_at = int(now.timestamp())

        await self._conn.execute(
            """
            INSERT INTO users (id, username, email, hashed_password, full_name, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                email,
                hashed_password,
                full_name,
                role,
                1 if is_active else 0,
                created_at,
            ),
        )
        await self._conn.commit()

        user = await self.get_user_by_id(user_id)
        if not user:
            raise RuntimeError(f"Failed to create user {username}")
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User data dictionary or None if not found
        """
        async with self._conn.execute(
            """
            SELECT id, username, email, hashed_password, full_name, role,
                   is_active, created_at, updated_at, last_login
            FROM users WHERE id = ?
            """,
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "hashed_password": row[3],
                "full_name": row[4],
                "role": row[5],
                "is_active": bool(row[6]),
                "created_at": (
                    datetime.fromtimestamp(row[7], tz=timezone.utc) if row[7] else None
                ),
                "updated_at": (
                    datetime.fromtimestamp(row[8], tz=timezone.utc) if row[8] else None
                ),
                "last_login": (
                    datetime.fromtimestamp(row[9], tz=timezone.utc) if row[9] else None
                ),
            }

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username.

        Args:
            username: Username to search for

        Returns:
            User data dictionary or None if not found
        """
        async with self._conn.execute(
            """
            SELECT id, username, email, hashed_password, full_name, role,
                   is_active, created_at, updated_at, last_login
            FROM users WHERE username = ?
            """,
            (username,),
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "hashed_password": row[3],
                "full_name": row[4],
                "role": row[5],
                "is_active": bool(row[6]),
                "created_at": (
                    datetime.fromtimestamp(row[7], tz=timezone.utc) if row[7] else None
                ),
                "updated_at": (
                    datetime.fromtimestamp(row[8], tz=timezone.utc) if row[8] else None
                ),
                "last_login": (
                    datetime.fromtimestamp(row[9], tz=timezone.utc) if row[9] else None
                ),
            }

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email.

        Args:
            email: Email address to search for

        Returns:
            User data dictionary or None if not found
        """
        async with self._conn.execute(
            """
            SELECT id, username, email, hashed_password, full_name, role,
                   is_active, created_at, updated_at, last_login
            FROM users WHERE email = ?
            """,
            (email,),
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "hashed_password": row[3],
                "full_name": row[4],
                "role": row[5],
                "is_active": bool(row[6]),
                "created_at": (
                    datetime.fromtimestamp(row[7], tz=timezone.utc) if row[7] else None
                ),
                "updated_at": (
                    datetime.fromtimestamp(row[8], tz=timezone.utc) if row[8] else None
                ),
                "last_login": (
                    datetime.fromtimestamp(row[9], tz=timezone.utc) if row[9] else None
                ),
            }

    async def list_users(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List all users with pagination.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of user dictionaries (without hashed_password)
        """
        users = []
        async with self._conn.execute(
            """
            SELECT id, username, email, full_name, role, is_active,
                   created_at, updated_at, last_login
            FROM users
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ) as cur:
            async for row in cur:
                users.append(
                    {
                        "id": row[0],
                        "username": row[1],
                        "email": row[2],
                        "full_name": row[3],
                        "role": row[4],
                        "is_active": bool(row[5]),
                        "created_at": (
                            datetime.fromtimestamp(row[6], tz=timezone.utc)
                            if row[6]
                            else None
                        ),
                        "updated_at": (
                            datetime.fromtimestamp(row[7], tz=timezone.utc)
                            if row[7]
                            else None
                        ),
                        "last_login": (
                            datetime.fromtimestamp(row[8], tz=timezone.utc)
                            if row[8]
                            else None
                        ),
                    }
                )
        return users

    async def update_user(self, user_id: str, updates: dict) -> Optional[dict]:
        """Update user information.

        Args:
            user_id: User UUID
            updates: Dictionary of fields to update

        Returns:
            Updated user data or None if user not found
        """
        # Build dynamic UPDATE query based on provided fields
        allowed_fields = ["email", "full_name", "role", "is_active", "hashed_password"]
        update_fields = []
        update_values = []

        for field in allowed_fields:
            if field in updates:
                update_fields.append(f"{field} = ?")
                value = updates[field]
                # Convert boolean to integer for SQLite
                if field == "is_active" and isinstance(value, bool):
                    value = 1 if value else 0
                update_values.append(value)

        if not update_fields:
            # No valid fields to update
            return await self.get_user_by_id(user_id)

        # Add updated_at timestamp
        update_fields.append("updated_at = ?")
        update_values.append(int(datetime.now(timezone.utc).timestamp()))
        update_values.append(user_id)

        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"

        async with self._conn.execute(query, tuple(update_values)):
            pass
        await self._conn.commit()

        return await self.get_user_by_id(user_id)

    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp.

        Args:
            user_id: User UUID
        """
        now = int(datetime.now(timezone.utc).timestamp())
        await self._conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (now, user_id),
        )
        await self._conn.commit()

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user.

        Args:
            user_id: User UUID

        Returns:
            True if user was deleted, False if not found
        """
        async with self._conn.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        ) as cur:
            await self._conn.commit()
            return cur.rowcount > 0

    async def count_users(self) -> int:
        """Count total number of users.

        Returns:
            Total number of users
        """
        async with self._conn.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0
