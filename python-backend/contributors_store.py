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
import uuid
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


def _coerce_sqlite_id(value) -> int | None:
    """Accept an id as int or numeric string; None when it cannot be a
    SQLite row id (SQLite INTEGER is signed 64-bit). Non-numeric strings
    and out-of-range values simply cannot exist -> treated as not found."""
    if isinstance(value, str):
        if not value.isdigit():
            return None
        value = int(value)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < 0 or value > SQLITE_MAX_INT:
        return None
    return value


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

    def get_contributor(self, contributor_id) -> dict | None:
        contributor_id = _coerce_sqlite_id(contributor_id)
        if contributor_id is None:
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

    def update_contributor(self, contributor_id, data: dict) -> dict | None:
        contributor_id = _coerce_sqlite_id(contributor_id)
        if contributor_id is None:
            return None
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

    def delete_contributor(self, contributor_id) -> bool:
        contributor_id = _coerce_sqlite_id(contributor_id)
        if contributor_id is None:
            return False
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM contributors WHERE id = ?", (contributor_id,)
            )
            self._conn.commit()
            return cur.rowcount > 0


class SupabaseContributorStore:
    """Supabase-backed store for the project's contributors table.

    The Supabase table (see supabase/migrations/) names its columns
    `name` and a single `image_url`, while the rest of the app uses the
    canonical shape (display_name + avatar_url/custom_avatar_url). This
    class translates at its boundary so every other layer keeps one shape:
      name       <-> display_name
      image_url  <-> custom_avatar_url  (custom uploads are the only
                   writes to the image column; the frontend falls back to
                   the GitHub avatar derived from the username)
    """

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

    @staticmethod
    def _from_db(row: dict) -> dict:
        """Table row (name/image_url) -> canonical contributor shape."""
        row = dict(row)
        row["display_name"] = row.pop("name", "")
        row["custom_avatar_url"] = row.pop("image_url", "") or ""
        row["avatar_url"] = ""
        return row

    @staticmethod
    def _to_db(data: dict) -> dict:
        """Canonical contributor data -> table column values."""
        image = data.get("custom_avatar_url") or data.get("avatar_url") or ""
        return {
            "name": data["display_name"],
            "github_username": data["github_username"],
            "github_url": data["github_url"],
            "role": data.get("role", ""),
            "description": data.get("description", ""),
            "image_url": image,
            "display_order": data.get("display_order", 0),
        }

    def list_contributors(self) -> list[dict]:
        result = (
            self._client.table(self._table)
            .select("*")
            .order("display_order", desc=False)
            .order("id", desc=False)
            .execute()
        )
        return [self._from_db(r) for r in result.data]

    @staticmethod
    def _valid_id(value) -> bool:
        """The contributors table uses a uuid id column; anything that is
        not a UUID cannot exist there and is treated as not found."""
        try:
            uuid.UUID(str(value))
            return True
        except (ValueError, AttributeError):
            return False

    def _username_exists(self, username: str) -> bool:
        result = (
            self._client.table(self._table)
            .select("id")
            .eq("github_username", username)
            .limit(1)
            .execute()
        )
        return bool(result.data)

    def get_contributor(self, contributor_id) -> dict | None:
        if not self._valid_id(contributor_id):
            return None
        result = (
            self._client.table(self._table)
            .select("*")
            .eq("id", contributor_id)
            .execute()
        )
        row = self._first(result)
        return self._from_db(row) if row else None

    def create_contributor(self, data: dict) -> dict:
        # The live table has no unique constraint on github_username, so
        # duplicates are blocked here instead (the API maps the error to
        # 409 via is_duplicate_error). New tables get the constraint from
        # the migration file.
        if self._username_exists(data["github_username"]):
            raise ValueError("duplicate github_username")
        result = self._client.table(self._table).insert(self._to_db(data)).execute()
        return self._from_db(self._first(result))

    def update_contributor(self, contributor_id, data: dict) -> dict | None:
        existing = self.get_contributor(contributor_id)
        if existing is None:
            return None
        merged = {**existing, **data}
        if (
            "github_username" in merged
            and merged["github_username"] != existing["github_username"]
            and self._username_exists(merged["github_username"])
        ):
            raise ValueError("duplicate github_username")
        result = (
            self._client.table(self._table)
            .update(self._to_db(merged))
            .eq("id", contributor_id)
            .execute()
        )
        row = self._first(result)
        return self._from_db(row) if row else None

    def delete_contributor(self, contributor_id) -> bool:
        if not self._valid_id(contributor_id):
            return False
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