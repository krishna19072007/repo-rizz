"""
Contributors HTTP API.

This module owns the contributor feature's HTTP surface: input validation
(models), the admin gate, and every /api/contributors, /api/admin/contributors
and /api/uploads route. It depends on:

- admin_auth        -> session + CSRF primitives (authorization)
- contributors_store-> persistence (SQLite default / optional Supabase)
- uploads           -> secure image file handling

main.py only mounts this router; it holds no contributor logic.
"""

import os
import re
import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from admin_auth import require_admin, verify_csrf
from contributors_store import get_store, is_duplicate_error
import uploads as uploads_module

logger = logging.getLogger("repo_rizz.contributors")

router = APIRouter()

# ===========================================================================
# Validation
# ===========================================================================

GITHUB_USERNAME_RE = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$")
GITHUB_URL_PATH_RE = re.compile(r"^/[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)?$")


def validate_github_url(url: str) -> str:
    """HTTPS + github.com only. Rejects javascript:, data:, file:, etc."""
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("GitHub URL must use HTTPS.")
    if parsed.netloc.lower() not in ("github.com", "www.github.com"):
        raise ValueError("GitHub URL must point to github.com.")
    if parsed.username or parsed.password:
        raise ValueError("GitHub URL must not contain credentials.")
    if parsed.query or parsed.fragment:
        raise ValueError("GitHub URL must not contain query parameters or fragments.")
    if not GITHUB_URL_PATH_RE.match(parsed.path.rstrip("/")):
        raise ValueError("GitHub URL has an invalid path.")
    return url


def clean_text(value: str, field: str, max_len: int, allow_newlines: bool) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field} cannot be empty.")
    if len(value) > max_len:
        raise ValueError(f"{field} must be at most {max_len} characters.")
    for ch in value:
        if ord(ch) < 32 and ch not in ("\n" if allow_newlines else "") and ch != "\t":
            raise ValueError(f"{field} contains invalid characters.")
    return value


class ContributorCreate(BaseModel):
    # Fail closed: reject unknown fields (e.g. smuggled avatar_url /
    # custom_avatar_url / isAdmin) instead of silently ignoring them.
    model_config = ConfigDict(extra="forbid")

    github_username: str = Field(min_length=1, max_length=39)
    display_name: str = Field(min_length=1, max_length=100)
    role: str = Field(default="", max_length=80)
    description: str = Field(default="", max_length=500)
    github_url: str | None = Field(default=None, max_length=200)
    display_order: int = Field(default=0, ge=0, le=9999)

    @field_validator("github_username")
    @classmethod
    def check_username(cls, v: str) -> str:
        v = v.strip()
        if not GITHUB_USERNAME_RE.match(v):
            raise ValueError("GitHub username may only contain letters, numbers and single hyphens.")
        return v

    @field_validator("display_name")
    @classmethod
    def check_display_name(cls, v: str) -> str:
        return clean_text(v, "Display name", 100, allow_newlines=False)

    @field_validator("role")
    @classmethod
    def check_role(cls, v: str) -> str:
        return clean_text(v, "Role", 80, allow_newlines=False) if v else v

    @field_validator("description")
    @classmethod
    def check_description(cls, v: str) -> str:
        return clean_text(v, "Description", 500, allow_newlines=True) if v else v

    @field_validator("github_url")
    @classmethod
    def check_github_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_github_url(v)


class ContributorUpdate(BaseModel):
    """All fields optional; only provided fields are applied."""
    model_config = ConfigDict(extra="forbid")

    github_username: str | None = Field(default=None, min_length=1, max_length=39)
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=200)
    display_order: int | None = Field(default=None, ge=0, le=9999)

    @field_validator("github_username")
    @classmethod
    def check_username(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not GITHUB_USERNAME_RE.match(v):
            raise ValueError("GitHub username may only contain letters, numbers and single hyphens.")
        return v

    @field_validator("display_name")
    @classmethod
    def check_display_name(cls, v: str | None) -> str | None:
        return clean_text(v, "Display name", 100, allow_newlines=False) if v is not None else v

    @field_validator("role")
    @classmethod
    def check_role(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return clean_text(v, "Role", 80, allow_newlines=False) if v else v

    @field_validator("description")
    @classmethod
    def check_description(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return clean_text(v, "Description", 500, allow_newlines=True) if v else v

    @field_validator("github_url")
    @classmethod
    def check_github_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_github_url(v)


# ===========================================================================
# Authorization
# ===========================================================================

def admin_guard(request: Request) -> dict:
    """FastAPI dependency: requires a valid admin session AND its CSRF token.

    Raises 401 / 403 instead of returning, so a route only has to declare
    `_session: dict = Depends(admin_guard)` — authorization is enforced
    server-side on every privileged route with no per-route ceremony.
    """
    session = require_admin(request)
    if session is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if not verify_csrf(request, session):
        raise HTTPException(status_code=403, detail="CSRF validation failed.")
    return session


def _store_error(exc: Exception, action: str) -> None:
    """Map store exceptions to HTTP errors (duplicate -> 409, else 500)."""
    if isinstance(exc, HTTPException):
        raise exc
    if is_duplicate_error(exc):
        raise HTTPException(
            status_code=409,
            detail="A contributor with this GitHub username already exists.",
        )
    logger.exception("contributor_%s_failed", action)
    raise HTTPException(
        status_code=500,
        detail=f"Could not {action.replace('_', ' ')} contributor.",
    )


# ===========================================================================
# Public API
# ===========================================================================

@router.get("/api/contributors")
def list_contributors():
    """Public read-only endpoint. Never returns secrets or admin data."""
    try:
        rows = get_store().list_contributors()
        return {"contributors": rows}
    except HTTPException:
        raise
    except Exception:
        logger.exception("contributors_list_failed")
        raise HTTPException(status_code=500, detail="Could not load contributors.")


# ===========================================================================
# Admin contributor management
# ===========================================================================

@router.post("/api/admin/contributors")
def admin_create_contributor(req: ContributorCreate, _session: dict = Depends(admin_guard)):
    payload = req.model_dump()
    if not payload.get("github_url"):
        payload["github_url"] = f"https://github.com/{payload['github_username']}"
    try:
        row = get_store().create_contributor(payload)
    except Exception as exc:
        _store_error(exc, "create")
    logger.info("contributor_created id=%s username=%s", row["id"], row["github_username"])
    return {"contributor": row}


@router.put("/api/admin/contributors/{contributor_id}")
def admin_update_contributor(
    contributor_id: str,
    req: ContributorUpdate,
    _session: dict = Depends(admin_guard),
):
    store = get_store()
    if store.get_contributor(contributor_id) is None:
        raise HTTPException(status_code=404, detail="Contributor not found.")

    data = {
        k: v for k, v in req.model_dump(exclude_unset=True).items() if v is not None
    }
    try:
        row = store.update_contributor(contributor_id, data)
    except Exception as exc:
        _store_error(exc, "update")
    if row is None:
        raise HTTPException(status_code=404, detail="Contributor not found.")
    logger.info("contributor_updated id=%s", contributor_id)
    return {"contributor": row}


@router.delete("/api/admin/contributors/{contributor_id}")
def admin_delete_contributor(contributor_id: str, _session: dict = Depends(admin_guard)):
    store = get_store()
    existing = store.get_contributor(contributor_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Contributor not found.")

    try:
        deleted = store.delete_contributor(contributor_id)
    except Exception as exc:
        _store_error(exc, "delete")
    if not deleted:
        raise HTTPException(status_code=404, detail="Contributor not found.")
    # Remove the uploaded image file if one exists for this contributor.
    uploads_module.delete_image_file(existing.get("custom_avatar_url") or "")
    logger.info("contributor_deleted id=%s", contributor_id)
    return {"ok": True}


@router.post("/api/admin/contributors/{contributor_id}/image")
def admin_upload_image(
    contributor_id: str,
    image: UploadFile = File(...),
    _session: dict = Depends(admin_guard),
):
    store = get_store()
    contributor = store.get_contributor(contributor_id)
    if contributor is None:
        raise HTTPException(status_code=404, detail="Contributor not found.")

    # Read at most MAX+1 bytes so memory stays bounded on huge uploads.
    data = image.file.read(uploads_module.MAX_IMAGE_BYTES + 1)
    try:
        url = uploads_module.save_image(data)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    old_url = contributor.get("custom_avatar_url") or ""
    try:
        row = store.update_contributor(contributor_id, {"custom_avatar_url": url})
    except Exception:
        uploads_module.delete_image_file(url)  # don't leave orphan files
        logger.exception("contributor_image_save_failed id=%s", contributor_id)
        raise HTTPException(status_code=500, detail="Could not save the image.")
    uploads_module.delete_image_file(old_url)
    logger.info("contributor_image_uploaded id=%s", contributor_id)
    return {"contributor": row}


@router.get("/api/uploads/{filename}")
def serve_upload(filename: str):
    """Serve uploaded avatars. Only server-generated UUID names are allowed."""
    if not uploads_module.is_safe_filename(filename):
        raise HTTPException(status_code=404, detail="Not found.")
    path = uploads_module.upload_path(filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Not found.")
    return FileResponse(path, media_type=uploads_module.guess_media_type(filename))
