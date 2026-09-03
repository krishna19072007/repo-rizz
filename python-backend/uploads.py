"""
Secure contributor image uploads.

Every upload is treated as hostile input:
- the client-supplied filename is IGNORED entirely (we generate our own),
- the browser-supplied MIME type is IGNORED (we sniff magic bytes),
- size is capped server-side,
- only PNG / JPEG / GIF / WebP magic signatures are accepted,
- stored files get a random UUID name, so no path traversal is possible
  and nothing can overwrite application files.

Uploaded files are served back through GET /api/uploads/{filename} which
only accepts server-generated UUID filenames.
"""

import os
import re
import uuid
import mimetypes

MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB

UPLOADS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "uploads", "contributors"
)

# Magic-byte signatures -> safe extension (extension is chosen by the SERVER).
IMAGE_SIGNATURES = {
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "gif": b"GIF87a",
    "gif2": b"GIF89a",
    "webp": b"WEBP",
}
EXT_BY_SIGNATURE = {
    "png": "png",
    "jpg": "jpg",
    "gif": "gif",
    "gif2": "gif",
    "webp": "webp",
}

# Only server-generated names may be served: 32 hex chars + one known extension.
SAFE_FILENAME_RE = re.compile(r"^[0-9a-f]{32}\.(png|jpg|gif|webp)$")


def detect_image_format(data: bytes) -> str | None:
    """Return a safe extension for the bytes, or None if not a known image."""
    if len(data) < 16:
        return None
    if data.startswith(IMAGE_SIGNATURES["png"]):
        return "png"
    if data.startswith(IMAGE_SIGNATURES["jpg"]):
        return "jpg"
    if data.startswith(IMAGE_SIGNATURES["gif"]) or data.startswith(IMAGE_SIGNATURES["gif2"]):
        return "gif"
    if data.startswith(b"RIFF") and data[8:12] == IMAGE_SIGNATURES["webp"]:
        return "webp"
    return None


def save_image(data: bytes) -> str:
    """Validate and store an image; returns the public URL path.

    Raises ValueError with a safe message on any validation failure.
    """
    if not data:
        raise ValueError("No image file was provided.")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Image is too large. Maximum size is 2 MB.")
    ext = detect_image_format(data)
    if ext is None:
        raise ValueError("Unsupported image format. Use PNG, JPG, GIF or WebP.")

    os.makedirs(UPLOADS_DIR, exist_ok=True)
    # Server-generated name: the client filename is never used.
    filename = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(UPLOADS_DIR, filename), "wb") as f:
        f.write(data)
    return f"/api/uploads/{filename}"


def is_safe_filename(filename: str) -> bool:
    return bool(SAFE_FILENAME_RE.match(filename or ""))


def upload_path(filename: str) -> str:
    """Resolve a validated filename to its on-disk path."""
    return os.path.join(UPLOADS_DIR, filename)


def guess_media_type(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def delete_image_file(url: str) -> None:
    """Remove a stored upload referenced by an API URL, if any.

    Only ever touches files inside UPLOADS_DIR whose name matches the
    strict server-generated pattern — never arbitrary paths.
    """
    if not url:
        return
    filename = url.rsplit("/", 1)[-1]
    if not is_safe_filename(filename):
        return
    try:
        os.remove(upload_path(filename))
    except OSError:
        pass  # missing file is fine