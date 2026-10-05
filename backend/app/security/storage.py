import os
import uuid
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io
import httpx
import logging
from backend.app.config import (
    STORAGE_PRIVATE_DIR, STORAGE_PUBLIC_DIR, MAX_UPLOAD_SIZE_MB,
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_STORAGE_MEDIA_BUCKET,
    SUPABASE_STORAGE_DOCS_BUCKET, USE_SUPABASE_STORAGE
)

logger = logging.getLogger("mawa.storage")

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_DOC_EXTS = {".jpg", ".jpeg", ".png", ".pdf"}

ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_DOC_MIMES = {"image/jpeg", "image/png", "application/pdf"}

MAX_FILE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _ensure_supabase_bucket(bucket_name: str, is_public: bool = True) -> bool:
    """
    Checks if a Supabase Storage bucket exists. If not, creates it via REST API.
    """
    if not (SUPABASE_URL and SUPABASE_KEY):
        return False
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{SUPABASE_URL}/storage/v1/bucket/{bucket_name}", headers=headers)
            if resp.status_code == 200:
                return True
            if resp.status_code == 404:
                # Bucket does not exist, create it
                create_payload = {
                    "id": bucket_name,
                    "name": bucket_name,
                    "public": is_public,
                    "file_size_limit": MAX_FILE_BYTES
                }
                c_resp = client.post(f"{SUPABASE_URL}/storage/v1/bucket", headers=headers, json=create_payload)
                return c_resp.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"Could not auto-create Supabase bucket '{bucket_name}': {e}")
    return False


def _upload_to_supabase(
    bucket_name: str,
    filename: str,
    content: bytes,
    content_type: str,
    is_public: bool = True
) -> Optional[str]:
    """
    Uploads file content to Supabase cloud storage.
    Returns public CDN URL if public, or stored object filename if private.
    """
    if not (SUPABASE_URL and SUPABASE_KEY):
        return None
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": content_type,
        "x-upsert": "true"
    }
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{filename}"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(upload_url, headers=headers, content=content)
            if resp.status_code in (200, 201):
                if is_public:
                    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"
                return filename
            elif resp.status_code == 404:
                # Retry once after ensuring bucket exists
                if _ensure_supabase_bucket(bucket_name, is_public=is_public):
                    retry_resp = client.post(upload_url, headers=headers, content=content)
                    if retry_resp.status_code in (200, 201):
                        if is_public:
                            return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"
                        return filename
            logger.warning(f"Supabase upload returned {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.warning(f"Failed to upload {filename} to Supabase: {e}")
    return None


def fetch_private_document_content(filename: str) -> Optional[Tuple[bytes, str]]:
    """
    Fetches private document bytes from Supabase Storage if configured.
    Returns (bytes, content_type) or None.
    """
    if not (SUPABASE_URL and SUPABASE_KEY):
        return None
    try:
        url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_STORAGE_DOCS_BUCKET}/{filename}"
        headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "application/pdf")
                return resp.content, content_type
    except Exception as e:
        logger.warning(f"Could not fetch private document {filename} from Supabase: {e}")
    return None


def delete_from_storage(file_path_or_url: str):
    """
    Deletes a file from either Supabase Storage or local filesystem.
    """
    if not file_path_or_url:
        return
    # Check if Supabase URL
    if SUPABASE_URL and file_path_or_url.startswith(f"{SUPABASE_URL}/storage/v1/object/public/"):
        rel_path = file_path_or_url.replace(f"{SUPABASE_URL}/storage/v1/object/public/", "")
        parts = rel_path.split("/", 1)
        if len(parts) == 2:
            bucket, filename = parts
            try:
                headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY}
                with httpx.Client(timeout=10.0) as client:
                    client.delete(f"{SUPABASE_URL}/storage/v1/object/{bucket}/{filename}", headers=headers)
            except Exception as e:
                logger.warning(f"Could not delete from Supabase storage: {e}")
        return

    # Local file deletion fallback
    filename = Path(file_path_or_url).name
    local_path = STORAGE_PUBLIC_DIR / filename
    if local_path.exists() and local_path.is_file():
        try:
            local_path.unlink()
        except Exception:
            pass


def validate_and_save_public_image(file: UploadFile) -> str:
    """
    Validates content signature (magic bytes), strips EXIF metadata for privacy,
    and securely stores property images in Supabase Storage or public_media.
    Returns relative filename or full CDN URL.
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

    # Magic Bytes Validation for public uploads
    if ext in [".jpg", ".jpeg"] and not content.startswith(b"\xff\xd8\xff"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="محتوى صورة JPEG غير صالح")
    elif ext == ".png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="محتوى صورة PNG غير صالح")
    elif ext == ".webp" and not (content.startswith(b"RIFF") and len(content) > 12 and content[8:12] == b"WEBP"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="محتوى صورة WebP غير صالح")

    # Secure random filename matching actual format
    file_ext = ".webp" if ext == ".webp" else (".png" if ext == ".png" else ".jpg")
    mime_type = "image/webp" if file_ext == ".webp" else ("image/png" if file_ext == ".png" else "image/jpeg")
    secure_filename = f"{uuid.uuid4().hex}{file_ext}"

    # Sanitize image and strip EXIF
    try:
        image = Image.open(io.BytesIO(content))
        image_format = "WEBP" if file_ext == ".webp" else ("PNG" if file_ext == ".png" else "JPEG")
        if image_format == "JPEG" and image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        # Save cleanly to in-memory buffer without metadata/EXIF
        out_buf = io.BytesIO()
        image.save(out_buf, format=image_format, quality=85, optimize=True)
        sanitized_bytes = out_buf.getvalue()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="فشل التحقق من صحة الصورة أو أن محتوى الملف تالف"
        )

    # 1. Cloud Storage: Supabase Storage if configured
    if USE_SUPABASE_STORAGE:
        public_url = _upload_to_supabase(
            SUPABASE_STORAGE_MEDIA_BUCKET,
            secure_filename,
            sanitized_bytes,
            mime_type,
            is_public=True
        )
        if public_url:
            return public_url

    # 2. Local fallback storage
    target_path = STORAGE_PUBLIC_DIR / secure_filename
    if not str(target_path.resolve()).startswith(str(STORAGE_PUBLIC_DIR.resolve())):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="محاولة مسار غير آمنة")

    with open(target_path, "wb") as f:
        f.write(sanitized_bytes)

    return secure_filename


def validate_and_save_private_document(file: UploadFile) -> str:
    """
    Stores sensitive identity/broker documents with randomized UUID in Supabase Private bucket or private_docs.
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
    mime_type = "application/pdf" if ext == ".pdf" else ("image/png" if ext == ".png" else "image/jpeg")

    # 1. Cloud Storage: Supabase Storage if configured
    if USE_SUPABASE_STORAGE:
        cloud_name = _upload_to_supabase(
            SUPABASE_STORAGE_DOCS_BUCKET,
            secure_filename,
            content,
            mime_type,
            is_public=False
        )
        if cloud_name:
            return cloud_name

    # 2. Local fallback storage
    target_path = STORAGE_PRIVATE_DIR / secure_filename
    if not str(target_path.resolve()).startswith(str(STORAGE_PRIVATE_DIR.resolve())):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="محاولة مسار غير آمنة")

    with open(target_path, "wb") as f:
        f.write(content)

    return secure_filename
