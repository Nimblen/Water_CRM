import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile, HTTPException

from app.core.config import get_settings

settings = get_settings()

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 1024 * 1024

EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def save_payment_photo(file: UploadFile) -> str:
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Недопустимый тип файла")

    filename = f"{uuid.uuid4()}{EXT_BY_TYPE[file.content_type]}"
    filepath = UPLOAD_DIR / filename

    total_size = 0

    try:
        async with aiofiles.open(filepath, "wb") as out:
            while chunk := await file.read(CHUNK_SIZE):
                total_size += len(chunk)

                if total_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                    raise HTTPException(400, "Файл слишком большой")

                await out.write(chunk)

    except Exception:
        filepath.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    return f"/uploads/{filename}"