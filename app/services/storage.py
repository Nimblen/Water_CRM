import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import get_settings

settings = get_settings()

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def save_payment_photo(file: UploadFile) -> str:
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Недопустимый тип файла")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(status_code=400, detail="Файл слишком большой")

    ext = EXT_BY_TYPE[file.content_type]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename

    filepath.write_bytes(content)

    return f"/uploads/{filename}"