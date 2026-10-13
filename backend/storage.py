"""Where uploaded X-rays and overlays are kept.

STORAGE_BACKEND=cloudinary (the hosted API): only on Cloudinary, as private "authenticated" images that
open only with a URL signed by our API secret. Nothing stays on the server's disk; the model gets a
temporary copy that is deleted after the analysis.
STORAGE_BACKEND=local (the default; local development and the tests): in backend/uploads/.
"""
import contextlib
import shutil
import tempfile
import urllib.request
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO

from .config import settings

_cloud = settings.storage_backend == "cloudinary"
if _cloud:
    # Fail at startup rather than quietly keeping patient X-rays on a disk that is wiped on restart.
    if not settings.cloudinary_url:
        raise RuntimeError("STORAGE_BACKEND=cloudinary needs CLOUDINARY_URL. See .env.example.")
    import cloudinary
    import cloudinary.uploader
    import cloudinary.utils

    cloudinary.config(cloudinary_url=settings.cloudinary_url, secure=True)

FOLDER = "sarcoscan"


def backend() -> str:
    return "cloudinary" if _cloud else "local"


def _check(key: str) -> str:
    # Keys come from save(). Anything with a folder in it is refused, so a bad row cannot point elsewhere.
    if Path(key).name != key or not Path(key).suffix:
        raise ValueError("Not a storage key")
    return key


def save(source: BinaryIO, suffix: str) -> str:
    """Store a file and return its key, a random name such as "3f2a….png"."""
    key = f"{uuid.uuid4().hex}{suffix}"
    if _cloud:
        cloudinary.uploader.upload(
            source, public_id=f"{FOLDER}/{Path(key).stem}", resource_type="image",
            type="authenticated",  # the default, "upload", would make every X-ray public
        )
    else:
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        with open(settings.upload_dir / key, "wb") as target:
            shutil.copyfileobj(source, target)
    return key


def save_file(file_path: Path) -> str:
    with open(file_path, "rb") as source:
        return save(source, file_path.suffix)


def read(key: str) -> bytes:
    """The stored file's bytes, for the authenticated image endpoints."""
    _check(key)
    if not _cloud:
        return (settings.upload_dir / key).read_bytes()
    url, _ = cloudinary.utils.cloudinary_url(
        f"{FOLDER}/{Path(key).stem}", resource_type="image", type="authenticated",
        sign_url=True, format=Path(key).suffix.lstrip("."),
    )
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


@contextlib.contextmanager
def working_copy(key: str) -> Iterator[Path]:
    """A temporary file holding the stored image, for the model. The folder and anything the model
    writes next to the image (its overlay) are deleted when the block ends; save what you need first."""
    with tempfile.TemporaryDirectory(prefix="sarcoscan-") as folder:
        copy = Path(folder) / _check(key)
        copy.write_bytes(read(key))
        yield copy
