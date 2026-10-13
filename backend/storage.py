"""Where uploaded X-rays and overlays are kept: always on local disk, with an optional private copy on Cloudinary."""
import logging
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from .config import settings

logger = logging.getLogger(__name__)

# The copy on Cloudinary is made only when STORAGE_BACKEND=cloudinary and CLOUDINARY_URL is set.
_mirror = False
if settings.storage_backend == "cloudinary" and settings.cloudinary_url:
    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(cloudinary_url=settings.cloudinary_url)
        _mirror = True
    except Exception as e:
        logger.warning("Failed to configure Cloudinary: %s", e)


def save(source: BinaryIO, suffix: str) -> str:
    """Store a file locally (the models and the image endpoints read it from there) and mirror it if enabled."""
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    key = f"{uuid.uuid4().hex}{suffix}"
    local_path = settings.upload_dir / key

    with open(local_path, "wb") as target:
        shutil.copyfileobj(source, target)

    if _mirror:
        try:
            cloudinary.uploader.upload(
                str(local_path),
                public_id=Path(key).stem,
                folder="sarcoscan",
                resource_type="image",
                # "authenticated" keeps the X-ray off any public URL: it opens only with a URL signed by
                # our API secret. The default type, "upload", would make every X-ray public.
                type="authenticated",
            )
        except Exception as e:
            logger.error("Cloudinary upload failed: %s", e)

    return key


def path(key: str) -> Path:
    # Keys come from save(). Anything with a folder in it is refused, so a bad row cannot point outside uploads.
    if Path(key).name != key:
        raise ValueError("Not a storage key")
    return settings.upload_dir / key
