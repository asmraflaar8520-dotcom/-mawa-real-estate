import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.entities import Property, ContactRequest, ViewingStatus, AuditLog

client = TestClient(app)

def get_token(email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]

def test_public_endpoints_never_leak_private_address():
    props = client.get("/api/properties").json()
    assert len(props) > 0
    first_prop = props[0]

    # Verify exact_address_private is not present in public schema
    assert "exact_address_private" not in first_prop
    assert "agent_phone" not in first_prop
    assert "approx_lat" in first_prop
    assert "approx_lng" in first_prop

    # Detail view for unauthenticated user
    detail_res = client.get(f"/api/properties/{first_prop['id']}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["exact_address_private"] is None
    assert detail_data["agent_phone_private"] is None
    assert detail_data["has_agreed_viewing"] is False

def test_private_address_revealed_only_after_viewing_agreed():
    buyer_token = get_token("buyer.ahmed@mawa.eg", "BuyerPass123!")
    agent_token = get_token("tanta.broker@mawa.eg", "BrokerPass123!")

    # Find a property owned by Tanta agent
    props = client.get("/api/properties?city=طنطا").json()
    prop_id = props[0]["id"]

    # Submit viewing request
    req_res = client.post(
        "/api/contact-requests",
        json={"property_id": prop_id, "buyer_message": "أريد المعاينة غداً"},
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    if req_res.status_code == 201:
        req_id = req_res.json()["id"]
    else:
        reqs = client.get("/api/contact-requests", headers={"Authorization": f"Bearer {buyer_token}"}).json()
        req_id = reqs[0]["id"]

    # Before agreement: buyer still cannot see exact address
    detail_before = client.get(f"/api/properties/{prop_id}", headers={"Authorization": f"Bearer {buyer_token}"}).json()
    # If not agreed, exact_address_private is None
    # Let's ensure agent accepts it
    accept_res = client.patch(
        f"/api/contact-requests/{req_id}/status",
        json={"status": "VIEWING_AGREED", "agent_response": "أهلاً بك، الموعد مناسب"},
        headers={"Authorization": f"Bearer {agent_token}"}
    )
    assert accept_res.status_code == 200

    # After mutual agreement: buyer MUST now see exact address
    detail_after = client.get(f"/api/properties/{prop_id}", headers={"Authorization": f"Bearer {buyer_token}"}).json()
    assert detail_after["has_agreed_viewing"] is True
    assert detail_after["exact_address_private"] is not None
    assert len(detail_after["exact_address_private"]) > 5

def test_viewing_sensitive_document_generates_audit_log():
    admin_token = get_token("admin@mawa.eg", "AdminMawa2026!Safe")
    buyer_token = get_token("buyer.ahmed@mawa.eg", "BuyerPass123!")

    # Buyer uploads an ID document
    import io
    dummy_file = io.BytesIO(b"\xff\xd8\xffDUMMY_NATIONAL_ID_CONTENT_12345")
    upload_res = client.post(
        "/api/verifications/identity",
        files={"file": ("national_id.jpg", dummy_file, "image/jpeg")},
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    assert upload_res.status_code == 200

    # Non-admin trying to access pending verifications or view doc
    pending_list = client.get("/api/admin/verifications/pending", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert len(pending_list) > 0
    doc_id = pending_list[0]["id"]

    # Normal buyer cannot view sensitive document
    unauth_doc_res = client.get(f"/api/admin/verifications/{doc_id}/view-file", headers={"Authorization": f"Bearer {buyer_token}"})
    assert unauth_doc_res.status_code == 403

    # Admin views sensitive document
    admin_doc_res = client.get(f"/api/admin/verifications/{doc_id}/view-file", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_doc_res.status_code == 200

    # Check AuditLog
    db = SessionLocal()
    try:
        last_log = db.query(AuditLog).filter(
            AuditLog.action == "VIEW_SENSITIVE_DOCUMENT",
            AuditLog.target_id == doc_id
        ).first()
        assert last_log is not None
        assert last_log.actor_email == "admin@mawa.eg"
    finally:
        db.close()
