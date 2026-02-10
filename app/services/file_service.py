import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class FileValidationError(Exception):
    pass


async def save_resume(file: UploadFile) -> str:
    if not file.filename:
        raise FileValidationError("No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise FileValidationError(f"Invalid content type: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise FileValidationError("File exceeds maximum size of 10 MB")

    safe_filename = f"{uuid.uuid4()}_{Path(file.filename).name}"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / safe_filename

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    return str(file_path)


def get_resume_path(relative_path: str) -> Path | None:
    path = Path(relative_path)
    # Prevent path traversal
    try:
        path.resolve().relative_to(Path(settings.UPLOAD_DIR).resolve())
    except ValueError:
        return None
    if not path.exists():
        return None
    return path
