"""AURXON QuantX — User Persistence & Store.
SQLite WAL-backed store for user identities, roles, and credential hashes.
"""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

from app.auth.schemas import User, UserRole
from app.auth.security import hash_password, verify_password

USER_DB_PATH = Path("data/aurxon_users.sqlite")
USER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class UserStore:
    """Manages persistent user identity records with strict credential protection."""

    def __init__(self, db_path: Path = USER_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT
                );
                """
            )
            conn.commit()

        # Seed default test users if empty
        self._seed_default_users()

    def _seed_default_users(self):
        try:
            if not self.get_user_by_email("admin@aurxon.internal"):
                self.create_user(
                    email="admin@aurxon.internal",
                    password="AdminPassword123!",
                    full_name="Aurxon QuantX Administrator",
                    role=UserRole.ADMIN,
                )
            if not self.get_user_by_email("trader@aurxon.internal"):
                self.create_user(
                    email="trader@aurxon.internal",
                    password="TraderPassword123!",
                    full_name="Aurxon Lead Trader",
                    role=UserRole.TRADER,
                )
        except Exception:
            pass

    def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.TRADER,
    ) -> User:
        """Creates and stores a new user record with hashed password."""
        clean_email = email.strip().lower()
        now_iso = datetime.now(timezone.utc).isoformat()
        user_id = f"USR_{uuid.uuid4().hex[:12].upper()}"
        pwd_hash = hash_password(password)
        name = full_name or clean_email.split("@")[0].title()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (user_id, email, hashed_password, full_name, role, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (user_id, clean_email, pwd_hash, name, role.value, now_iso),
            )
            conn.commit()

        return User(
            user_id=user_id,
            email=clean_email,
            full_name=name,
            role=role,
            is_active=True,
            created_at=now_iso,
        )

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticates a user by email and password; updates last login timestamp."""
        clean_email = email.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, email, hashed_password, full_name, role, is_active, created_at FROM users WHERE email = ?",
                (clean_email,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            if not verify_password(password, row["hashed_password"]):
                return None

            if not row["is_active"]:
                return None

            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute("UPDATE users SET last_login_at = ? WHERE user_id = ?", (now_iso, row["user_id"]))
            conn.commit()

            return User(
                user_id=row["user_id"],
                email=row["email"],
                full_name=row["full_name"],
                role=UserRole(row["role"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )

    authenticate = authenticate_user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieves user by immutable user_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, email, full_name, role, is_active, created_at FROM users WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return User(
                user_id=row["user_id"],
                email=row["email"],
                full_name=row["full_name"],
                role=UserRole(row["role"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieves user by email address."""
        clean_email = email.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, email, full_name, role, is_active, created_at FROM users WHERE email = ?",
                (clean_email,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return User(
                user_id=row["user_id"],
                email=row["email"],
                full_name=row["full_name"],
                role=UserRole(row["role"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )

    def list_users(self) -> List[User]:
        """Lists all registered users in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, email, full_name, role, is_active, created_at FROM users ORDER BY created_at ASC"
            )
            rows = cursor.fetchall()
            return [
                User(
                    user_id=r["user_id"],
                    email=r["email"],
                    full_name=r["full_name"],
                    role=UserRole(r["role"]),
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]


user_store = UserStore()
