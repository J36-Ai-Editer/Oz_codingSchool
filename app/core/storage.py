from datetime import datetime
from pathlib import Path
from uuid import uuid4


MEDIA_ROOT = Path("media")
XRAY_UPLOAD_DIR = MEDIA_ROOT / "xray"
ALLOWED_XRAY_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_XRAY_IMAGE_SIZE = 5 * 1024 * 1024


def get_allowed_xray_extension(filename: str | None) -> str | None:
    if not filename or "." not in filename:
        return None
    extension = filename.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_XRAY_EXTENSIONS:
        return None
    return extension


def save_xray_image(content: bytes, extension: str, now: datetime) -> str:
    date_path = now.strftime("%Y/%m/%d")
    save_dir = XRAY_UPLOAD_DIR / date_path
    save_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4()}.{extension}"
    save_path = save_dir / filename
    save_path.write_bytes(content)

    return f"/media/xray/{date_path}/{filename}"
