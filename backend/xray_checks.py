"""Checks on an uploaded X-ray file before it is stored: its real type, and whether it looks like an X-ray."""
from fastapi import HTTPException, status
from PIL import Image, ImageChops, ImageStat

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MIN_SIDE_PX = 256
# Measured on a 64 x 64 copy, on a 0 to 255 scale. A knee X-ray scores about 0 and 65; a blank image 0 and 0.
MAX_COLOUR = 8  # average difference between colour channels
MIN_CONTRAST = 15  # standard deviation of brightness


def file_suffix(head: bytes) -> str:
    """".png" or ".jpg" from the file's first 132 bytes. The name and extension the client sent are ignored."""
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head[128:132] == b"DICM":
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "DICOM is not supported yet. Export the image as PNG or JPG."
        )
    raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a PNG or JPG image")


def quality_problem(image: Image.Image) -> str | None:
    """Why the image cannot be used, or None when it passes."""
    # ponytail: size, shape, colour and contrast only. It stops photos, logos and blank images.
    # A greyscale photo, or an X-ray of another body part, still passes; that needs a trained check.
    width, height = image.size
    if min(width, height) < MIN_SIDE_PX:
        return f"The image is too small ({width} x {height} pixels). At least {MIN_SIDE_PX} on each side is needed."
    if not 0.5 <= height / width <= 3:
        return "The image is too wide or too tall to be a single knee X-ray."
    small = image.convert("RGB").resize((64, 64))
    red, green, blue = small.split()
    colour = max(
        ImageStat.Stat(ImageChops.difference(red, green)).mean[0],
        ImageStat.Stat(ImageChops.difference(green, blue)).mean[0],
    )
    if colour > MAX_COLOUR:
        return "This looks like a colour picture, not an X-ray. X-rays are black and white."
    if ImageStat.Stat(small.convert("L")).stddev[0] < MIN_CONTRAST:
        return "The image is almost blank. Check the exposure and upload it again."
    return None
