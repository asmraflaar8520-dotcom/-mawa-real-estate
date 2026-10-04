import os
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io
from backend.app.config import STORAGE_PRIVATE_DIR, STORAGE_PUBLIC_DIR, MAX_UPLOAD_SIZE_MB

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_DOC_EXTS = {".jpg", ".jpeg", ".png", ".pdf"}

ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_DOC_MIMES = {"image/jpeg", "image/png", "application/pdf"}

MAX_FILE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

def validate_and_save_public_image(file: UploadFile) -> str:
    """
    Validates, strips EXIF metadata for privacy, and securely stores property images in public_media.
    Returns relative filename.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"نوع الملف غير مسموح به. الصيغ المسموحة: {', '.join(ALLOWED_IMAGE_EXTS)}"
        )

    content = file.file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"حجم الملف يتجاوز الحد المسموح به ({MAX_UPLOAD_SIZE_MB} ميجابايت)"
        )

    # Secure random filename
    secure_filename = f"{uuid.uuid4().hex}{ext if ext != '.webp' else '.jpg'}"
    target_path = STORAGE_PUBLIC_DIR / secure_filename

    try:
        # Sanitize image and strip EXIF
        image = Image.open(io.BytesIO(content))
        image_format = "JPEG" if image.format in ["JPEG", "JPG"] or ext in [".jpg", ".jpeg"] else image.format
        if image.mode in ("RGBA", "P") and image_format == "JPEG":
            image = image.convert("RGB")

        # Save cleanly without metadata/EXIF
        image.save(target_path, format=image_format, quality=85, optimize=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="فشل التحقق من صحة الصورة أو أن محتوى الملف تالف"
        )

    return secure_filename

def validate_and_save_private_document(file: UploadFile) -> str:
    """
    Stores sensitive identity/broker documents in private_docs with randomized UUID.
    Never exposed publicly.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_DOC_EXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"نوع الوثيقة غير مسموح به. الصيغ المسموحة: {', '.join(ALLOWED_DOC_EXTS)}"
        )

    content = file.file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"حجم الملف يتجاوز الحد المسموح به ({MAX_UPLOAD_SIZE_MB} ميجابايت)"
        )

    # Magic Bytes Validation
    if ext == ".pdf" and not content.startswith(b"%PDF"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="محتوى ملف PDF غير صالح")
    elif ext in [".jpg", ".jpeg"] and not content.startswith(b"\xff\xd8\xff"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="محتوى صورة JPEG غير صالح")
    elif ext == ".png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="محتوى صورة PNG غير صالح")

    secure_filename = f"priv_doc_{uuid.uuid4().hex}{ext}"
    target_path = STORAGE_PRIVATE_DIR / secure_filename

    # Prevent path traversal
    if not str(target_path.resolve()).startswith(str(STORAGE_PRIVATE_DIR.resolve())):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="محاولة مسار غير آمنة")

    with open(target_path, "wb") as f:
        f.write(content)

    return secure_filename
