import io
import pytest
from fastapi import UploadFile
from backend.app.services.property_service import _resolve_image_url
from backend.app.security.storage import (
    validate_and_save_public_image, delete_from_storage,
    STORAGE_PUBLIC_DIR
)
from backend.app.config import DATABASE_URL

def test_resolve_image_url_cloud_and_local():
    # Fallback when None
    assert _resolve_image_url(None) == "/media/tanta_stadium.jpg"
    assert _resolve_image_url("") == "/media/tanta_stadium.jpg"

    # Local filename gets /media/ prefix
    assert _resolve_image_url("abc.jpg") == "/media/abc.jpg"
    assert _resolve_image_url("/media/custom.png") == "/media/custom.png"

    # Cloud Supabase URL is preserved untouched
    cloud_url = "https://abcdef.supabase.co/storage/v1/object/public/mawa-media/photo123.webp"
    assert _resolve_image_url(cloud_url) == cloud_url


def test_delete_from_storage_local_and_cloud():
    # Test local file creation and deletion
    test_file = STORAGE_PUBLIC_DIR / "dummy_to_delete.txt"
    test_file.write_text("sample content")
    assert test_file.exists()

    delete_from_storage("dummy_to_delete.txt")
    assert not test_file.exists()

    # Cloud URL deletion does not throw when Supabase not configured
    delete_from_storage("https://dummy.supabase.co/storage/v1/object/public/mawa-media/none.webp")


def test_public_image_upload_local_fallback():
    # Valid JPEG image bytes
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color="blue")
    img.save(buf, format="JPEG")
    buf.seek(0)

    upload = UploadFile(filename="unit_test_img.jpg", file=buf)
    saved_filename = validate_and_save_public_image(upload)

    assert saved_filename.endswith(".jpg")
    local_path = STORAGE_PUBLIC_DIR / saved_filename
    assert local_path.exists()

    # Cleanup
    local_path.unlink()
