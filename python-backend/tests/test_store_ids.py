"""
Hermetic tests for contributor id handling.

SQLite rows use integer ids and the Supabase table uses uuid ids. Both
stores treat ids they cannot possibly contain as "not found" so the API
answers 404 instead of 500 or 422.
"""

import pytest

from contributors_store import SupabaseContributorStore, _coerce_sqlite_id

VALID_UUID = "15777e3d-6f83-4cc2-be52-29ed61ecb724"


# --- SQLite: integer id coercion -------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        (1, 1),
        ("1", 1),
        ("0", 0),
        (2**63 - 1, 2**63 - 1),
        ("abc", None),
        ("", None),
        ("-5", None),
        (str(2**80), None),  # beyond signed 64-bit
        (-5, None),
        (2**80, None),
        (True, None),  # bool is an int subclass; must not coerce to 1
        (None, None),
        (12.5, None),
    ],
)
def test_sqlite_id_coercion(value, expected):
    assert _coerce_sqlite_id(value) == expected


# --- Supabase: uuid id validation ------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        (VALID_UUID, True),
        ("123", False),          # an int id cannot exist in a uuid column
        ("not-a-uuid", False),
        ("", False),
        (None, False),
        (123, False),
        ("15777e3d6f834cc2be5229ed61ecb724", True),  # compact uuid accepted
    ],
)
def test_supabase_uuid_id_validation(value, expected):
    assert SupabaseContributorStore._valid_id(value) is expected
