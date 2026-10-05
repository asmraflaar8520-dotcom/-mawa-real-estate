import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_token(email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]

def test_report_submission_and_admin_resolution():
    buyer_token = get_token("buyer.ahmed@mawa.eg", "BuyerPass123!")
    admin_token = get_token("admin@mawa.eg", "AdminMawa2026!Safe")

    # 1. Fetch a property
    props = client.get("/api/properties").json()
    prop_id = props[0]["id"]

    # 2. Buyer submits a report
    report_payload = {
        "property_id": prop_id,
        "reason": "FAKE_PRICE",
        "details": "السعر المكتوب لا يطابق الواقع في منطقة الاستاد بطنطا"
    }
    submit_res = client.post(
        "/api/reports",
        json=report_payload,
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    assert submit_res.status_code == 201
    report_id = submit_res.json()["id"]
    assert submit_res.json()["is_resolved"] is False

    # 3. Non-admin attempting to resolve report (Must be forbidden)
    unauth_resolve = client.patch(
        f"/api/admin/reports/{report_id}/resolve",
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    assert unauth_resolve.status_code == 403

    # 4. Admin lists reports
    admin_list = client.get(
        "/api/admin/reports",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_list.status_code == 200
    report_ids = [r["id"] for r in admin_list.json()]
    assert report_id in report_ids

    # 5. Admin resolves report
    resolve_res = client.patch(
        f"/api/admin/reports/{report_id}/resolve",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["is_resolved"] is True

    # 6. Verify audit log entry
    logs_res = client.get(
        "/api/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert logs_res.status_code == 200
    audit_actions = [l["action"] for l in logs_res.json()]
    assert "RESOLVE_REPORT" in audit_actions
