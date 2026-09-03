"""
Contributors persistence.

Default: local SQLite database (zero configuration, works immediately).

Optional: Supabase Postgres when SUPABASE_URL and
SUPABASE_SERVICE_ROLE_KEY are set in the backend `.env`. The matching
migration lives in `supabase/migrations/` at the repository root and
enables Row Level Security (public SELECT only; writes happen through
the backend using the service-role key, which bypasses RLS).

The store layer only handles persistence. Authorization is enforced by
the API layer (admin session + CSRF) BEFORE any of these functions run.
"""

import os
import sqlite3
import threading
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv(
    "CONTRIBUTORS_DB_PATH",
    os.path.join(BASE_DIR, "data", "contributors.db"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS contributors (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    github_username  TEXT NOT NULL UNIQUE,
    display_name     TEXT NOT NULL,
    github_url       TEXT NOT NULL,
    role             TEXT NOT NULL DEFAULT '',
    description      TEXT NOT NULL DEFAULT '',
    avatar_url       TEXT NOT NULL DEFAULT '',
    custom_avatar_url TEXT NOT NULL DEFAULT '',
    display_order    INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);
"""

# Rows are returned in this exact shape by every backend store.
ROW_FIELDS = [
    "id",
    "github_username",
    "display_name",
    "github_url",
    "role",
    "description",
    "avatar_url",
    "custom_avatar_url",
    "display_order",
    "created_at",
    "updated_at",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_duplicate_error(exc: Exception) -> bool:
    """Detect unique-constraint violations from any backend store.

    Classifies store exceptions so the API layer can answer 409 for
    duplicate GitHub usernames without knowing which store is in use.
    """
    message = str(exc).lower()
    return "unique" in message or "duplicate" in message


SQLITE_MAX_INT = 2**63 - 1


def _id_in_range(contributor_id: int) -> bool:
    """SQLite INTEGER is signed 64-bit; binding anything larger raises
    OverflowError. Out-of-range ids simply cannot exist -> not found."""
    return isinstance(contributor_id, int) and 0 <= contributor_id <= SQLITE_MAX_INT


class SQLiteContributorStore:
    def __init__(self, db_path: str | None = None):
        # Read the env var at construction time so tests can isolate
        # each run to its own database file.
        if db_path is None:
            db_path = os.getenv("CONTRIBUTORS_DB_PATH", DB_PATH)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA busy_timeout = 5000")
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(SCHEMA)
            self._conn.commit()

    def _rows(self, result) -> list[dict]:
        return [dict(r) for r in result]

    def list_contributors(self) -> list[dict]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM contributors ORDER BY display_order ASC, id ASC"
            )
            return self._rows(cur.fetchall())

    def get_contributor(self, contributor_id: int) -> dict | None:
        if not _id_in_range(contributor_id):
            return None
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM contributors WHERE id = ?", (contributor_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def create_contributor(self, data: dict) -> dict:
        now = _now()
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT INTO contributors (
                    github_username, display_name, github_url, role,
                    description, avatar_url, custom_avatar_url,
                    display_order, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["github_username"],
                    data["display_name"],
                    data["github_url"],
                    data.get("role", ""),
                    data.get("description", ""),
                    data.get("avatar_url", ""),
                    data.get("custom_avatar_url", ""),
                    data.get("display_order", 0),
                    now,
                    now,
                ),
            )
            self._conn.commit()
            new_id = cur.lastrowid
        # NOTE: fetch outside the lock — the lock is not reentrant
        return self.get_contributor(new_id)

    def update_contributor(self, contributor_id: int, data: dict) -> dict | None:
        existing = self.get_contributor(contributor_id)
        if existing is None:
            return None
        merged = {**existing, **data, "updated_at": _now()}
        with self._lock:
            self._conn.execute(
                """
                UPDATE contributors SET
                    github_username = ?, display_name = ?, github_url = ?,
                    role = ?, description = ?, avatar_url = ?,
                    custom_avatar_url = ?, display_order = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    merged["github_username"],
                    merged["display_name"],
                    merged["github_url"],
                    merged["role"],
                    merged["description"],
                    merged["avatar_url"],
                    merged["custom_avatar_url"],
                    merged["display_order"],
                    merged["updated_at"],
                    contributor_id,
                ),
            )
            self._conn.commit()
        return self.get_contributor(contributor_id)

    def delete_contributor(self, contributor_id: int) -> bool:
        if not _id_in_range(contributor_id):
            return False
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM contributors WHERE id = ?", (contributor_id,)
            )
            self._conn.commit()
            return cur.rowcount > 0


class SupabaseContributorStore:
    """Optional Supabase-backed store (used only when configured)."""

    def __init__(self, url: str, service_role_key: str):
        try:
            from supabase import create_client
        except ImportError as exc:  # pragma: no cover - env dependent
            raise RuntimeError(
                "Supabase configured but the 'supabase' package is not "
                "installed. Run: pip install supabase"
            ) from exc
        self._client = create_client(url, service_role_key)
        self._table = "contributors"

    def _first(self, result) -> dict | None:
        data = result.data if hasattr(result, "data") else result
        if isinstance(data, list) and data:
            return dict(data[0])
        if isinstance(data, dict):
            return dict(data)
        return None

    def list_contributors(self) -> list[dict]:
        result = (
            self._client.table(self._table)
            .select("*")
            .order("display_order", desc=False)
            .order("id", desc=False)
            .execute()
        )
        return [dict(r) for r in (result.data if hasattr(result, "data") else result)]

    def get_contributor(self, contributor_id: int) -> dict | None:
        result = (
            self._client.table(self._table)
            .select("*")
            .eq("id", contributor_id)
            .execute()
        )
        return self._first(result)

    def create_contributor(self, data: dict) -> dict:
        payload = {
            "github_username": data["github_username"],
            "display_name": data["display_name"],
            "github_url": data["github_url"],
            "role": data.get("role", ""),
            "description": data.get("description", ""),
            "avatar_url": data.get("avatar_url", ""),
            "custom_avatar_url": data.get("custom_avatar_url", ""),
            "display_order": data.get("display_order", 0),
        }
        result = self._client.table(self._table).insert(payload).execute()
        return self._first(result)

    def update_contributor(self, contributor_id: int, data: dict) -> dict | None:
        existing = self.get_contributor(contributor_id)
        if existing is None:
            return None
        payload = {
            "github_username": data.get("github_username", existing["github_username"]),
            "display_name": data.get("display_name", existing["display_name"]),
            "github_url": data.get("github_url", existing["github_url"]),
            "role": data.get("role", existing["role"]),
            "description": data.get("description", existing["description"]),
            "avatar_url": data.get("avatar_url", existing["avatar_url"]),
            "custom_avatar_url": data.get("custom_avatar_url", existing["custom_avatar_url"]),
            "display_order": data.get("display_order", existing["display_order"]),
        }
        result = (
            self._client.table(self._table)
            .update(payload)
            .eq("id", contributor_id)
            .execute()
        )
        return self._first(result)

    def delete_contributor(self, contributor_id: int) -> bool:
        result = (
            self._client.table(self._table)
            .delete()
            .eq("id", contributor_id)
            .execute()
        )
        return self._first(result) is not None


_store = None
_store_lock = threading.Lock()


def get_store():
    """Return the configured contributor store (Supabase or SQLite)."""
    global _store
    with _store_lock:
        if _store is not None:
            return _store
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        if url and key:
            _store = SupabaseContributorStore(url, key)
        else:
            _store = SQLiteContributorStore()
        return _store


def reset_store_cache() -> None:
    """For tests: drop the cached store so a new DB path takes effect."""
    global _store
    with _store_lock:
        _store = None