"""
Unit tests for SupabaseContributorStore's column translation.

The Supabase contributors table names its columns `name` and a single
`image_url` while the rest of the app uses the canonical shape
(display_name, avatar_url, custom_avatar_url). These tests lock the
translation in place. They are network-free: the mapping helpers are
staticmethods and never touch the Supabase client.
"""

import pytest

from contributors_store import SupabaseContributorStore

DB_ROW = {
    "id": 1,
    "name": "Octo Cat",
    "github_username": "octocat",
    "github_url": "https://github.com/octocat",
    "role": "Core Engineer",
    "description": "Builds things.",
    "image_url": "/api/uploads/abcdef0123456789abcdef0123456789.png",
    "display_order": 2,
    "created_at": "2026-09-04T10:00:00+00:00",
    "updated_at": "2026-09-04T10:00:00+00:00",
}

CANONICAL = {
    "id": 1,
    "display_name": "Octo Cat",
    "github_username": "octocat",
    "github_url": "https://github.com/octocat",
    "role": "Core Engineer",
    "description": "Builds things.",
    "custom_avatar_url": "/api/uploads/abcdef0123456789abcdef0123456789.png",
    "avatar_url": "",
    "display_order": 2,
    "created_at": "2026-09-04T10:00:00+00:00",
    "updated_at": "2026-09-04T10:00:00+00:00",
}


def test_row_to_canonical_maps_name_and_image_url():
    row = SupabaseContributorStore._from_db(DB_ROW)
    assert row["display_name"] == "Octo Cat"
    assert row["custom_avatar_url"] == DB_ROW["image_url"]
    assert row["avatar_url"] == ""
    assert row["github_username"] == "octocat"  # untouched fields pass through


def test_row_to_canonical_handles_null_image_url():
    row = SupabaseContributorStore._from_db({**DB_ROW, "image_url": None})
    assert row["custom_avatar_url"] == ""


def test_canonical_to_db_prefers_custom_image():
    db = SupabaseContributorStore._to_db({**CANONICAL, "avatar_url": "https://github.com/x.png"})
    assert db["name"] == "Octo Cat"
    assert db["image_url"] == CANONICAL["custom_avatar_url"]
    assert "avatar_url" not in db and "custom_avatar_url" not in db


def test_canonical_to_db_falls_back_to_avatar_url():
    db = SupabaseContributorStore._to_db(
        {**CANONICAL, "custom_avatar_url": "", "avatar_url": "https://github.com/x.png"}
    )
    assert db["image_url"] == "https://github.com/x.png"


def test_roundtrip_preserves_contributor_fields():
    row = SupabaseContributorStore._from_db(DB_ROW)
    db = SupabaseContributorStore._to_db(row)
    back = SupabaseContributorStore._from_db(
        {**DB_ROW, "name": db["name"], "image_url": db["image_url"]}
    )
    assert back["display_name"] == CANONICAL["display_name"]
    assert back["custom_avatar_url"] == CANONICAL["custom_avatar_url"]
