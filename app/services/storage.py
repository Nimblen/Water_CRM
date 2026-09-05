import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile

from app.core.config import get_settings


settings = get_settings()

BASE_UPLOAD_DIR = Path(settings.UPLOAD_DIR)
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 1024 * 1024  # 1 MB

EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def save_image(
    file: UploadFile,
    *,
    directory: str = "",
) -> str:
    content_type = file.content_type

    if content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Недопустимый тип файла",
        )

    extension = EXT_BY_TYPE.get(content_type)

    if extension is None:
        raise HTTPException(
            status_code=400,
            detail="Неподдерживаемый тип изображения",
        )

    upload_dir = BASE_UPLOAD_DIR / directory
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}{extension}"
    filepath = upload_dir / filename

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_size = 0

    try:
        async with aiofiles.open(filepath, "wb") as output:
            while chunk := await file.read(CHUNK_SIZE):
                total_size += len(chunk)

                if total_size > max_size:
                    raise HTTPException(
                        status_code=400,
                        detail="Файл слишком большой",
                    )

                await output.write(chunk)

    except Exception:
        filepath.unlink(missing_ok=True)
        raise

    finally:
        await file.close()

    if directory:
        return f"/uploads/{directory}/{filename}"

    return f"/uploads/{filename}"