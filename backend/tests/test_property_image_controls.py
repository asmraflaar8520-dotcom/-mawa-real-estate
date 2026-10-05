import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_token(email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]

def test_image_upload_and_delete_with_bola_protection():
    agent1_token = get_token("tanta.broker@mawa.eg", "BrokerPass123!")
    agent2_token = get_token("mahalla.broker@mawa.eg", "BrokerPass123!")

    # 1. Get a property owned by Tanta agent
    props = client.get("/api/properties?city=طنطا").json()
    tanta_prop_id = props[0]["id"]

    # 2. Upload valid image as owner agent
    dummy_jpg = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00")
    # Add minimal JPEG dummy payload
    upload_res = client.post(
        f"/api/properties/{tanta_prop_id}/images",
        files={"file": ("photo.jpg", dummy_jpg, "image/jpeg")},
        data={"is_primary": "false"},
        headers={"Authorization": f"Bearer {agent1_token}"}
    )
    # Note: Pillow will attempt to open it. If minimal dummy fails image decode, we create a valid 1x1 image with PIL
    if upload_res.status_code != 200:
        from PIL import Image
        img_buf = io.BytesIO()
        img = Image.new("RGB", (100, 100), color=(10, 50, 100))
        img.save(img_buf, format="JPEG")
        img_buf.seek(0)

        upload_res = client.post(
            f"/api/properties/{tanta_prop_id}/images",
            files={"file": ("real_sample.jpg", img_buf, "image/jpeg")},
            data={"is_primary": "false"},
            headers={"Authorization": f"Bearer {agent1_token}"}
        )

    assert upload_res.status_code == 200
    img_data = upload_res.json()
    img_id = img_data["id"]
    assert img_data["is_primary"] is False

    # 3. Agent 2 (intruder) tries to delete Agent 1's property image (BOLA attack)
    intruder_del = client.delete(
        f"/api/properties/{tanta_prop_id}/images/{img_id}",
        headers={"Authorization": f"Bearer {agent2_token}"}
    )
    assert intruder_del.status_code == 403

    # 4. Agent 1 (legitimate owner) deletes image
    owner_del = client.delete(
        f"/api/properties/{tanta_prop_id}/images/{img_id}",
        headers={"Authorization": f"Bearer {agent1_token}"}
    )
    assert owner_del.status_code == 204
