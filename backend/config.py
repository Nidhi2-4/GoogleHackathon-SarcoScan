"""Settings come from environment variables. A .env file in the repo root is loaded if present.

Set ENV_FILE to load a different file, for example ENV_FILE=.env.prod.
"""
import base64
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(os.environ.get("ENV_FILE", ".env"))


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Copy .env.example to .env and fill it in.")
    return value


def _key(name: str) -> bytes:
    raw = base64.b64decode(_env(name))
    if len(raw) != 32:
        raise RuntimeError(f"{name} must be 32 random bytes, base64-encoded.")
    return raw


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret: str
    field_key: bytes  # AES-256-GCM key for patient name and phone
    hash_key: bytes  # HMAC key for the searchable phone hash
    cookie_secure: bool
    upload_dir: Path  # X-rays and overlays; never served as static files
    storage_backend: str = "local"
    cloudinary_url: str = ""
    access_minutes: int = 15
    refresh_days: int = 7


def _load() -> Settings:
    secret = _env("JWT_SECRET")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters.")
    return Settings(
        database_url=_env("DATABASE_URL"),
        jwt_secret=secret,
        field_key=_key("FIELD_KEY"),
        hash_key=_key("HASH_KEY"),
        cookie_secure=os.environ.get("COOKIE_SECURE", "true").lower() != "false",
        upload_dir=Path(os.environ.get("UPLOAD_DIR") or Path(__file__).parent / "uploads"),
        storage_backend=os.environ.get("STORAGE_BACKEND", "local").lower(),
        cloudinary_url=os.environ.get("CLOUDINARY_URL", ""),
    )


settings = _load()
