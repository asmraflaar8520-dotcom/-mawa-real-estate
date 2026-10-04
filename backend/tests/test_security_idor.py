import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.entities import Property, ContactRequest, ViewingStatus

client = TestClient(app)

def get_token(email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]

def test_idor_contact_request_forbidden_for_other_users():
    # 1. Login as buyer Ahmed and submit a viewing request
    buyer_token = get_token("buyer.ahmed@mawa.eg", "BuyerPass123!")
    
    # Get a property in Tanta
    props_res = client.get("/api/properties")
    prop_id = props_res.json()[0]["id"]

    create_res = client.post(
        "/api/contact-requests",
        json={"property_id": prop_id, "buyer_message": "طلب معاينة خاص بأحمد"},
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    # Could be 201 or 400 if already exists
    if create_res.status_code == 201:
        req_id = create_res.json()["id"]
    else:
        reqs = client.get("/api/contact-requests", headers={"Authorization": f"Bearer {buyer_token}"}).json()
        req_id = reqs[0]["id"]

    # 2. Register a totally separate third-party buyer
    third_party_res = client.post("/api/auth/register", json={
        "email": "intruder.user@mawa.eg",
        "password": "Password123!",
        "full_name": "مستخدم متطفل",
        "role": "BUYER"
    })
    if third_party_res.status_code == 201:
        intruder_token = third_party_res.json()["access_token"]
    else:
        intruder_token = get_token("intruder.user@mawa.eg", "Password123!")

    # 3. Intruder attempts to read buyer Ahmed's contact request by ID
    intruder_access_res = client.get(
        f"/api/contact-requests/{req_id}",
        headers={"Authorization": f"Bearer {intruder_token}"}
    )
    assert intruder_access_res.status_code == 403
    assert "غير مصرح لك باستعراض بيانات هذا الطلب" in intruder_access_res.json()["detail"]

    # 4. Intruder attempts to maliciously cancel or change status of buyer Ahmed's request
    intruder_update_res = client.patch(
        f"/api/contact-requests/{req_id}/status",
        json={"status": "CANCELLED"},
        headers={"Authorization": f"Bearer {intruder_token}"}
    )
    assert intruder_update_res.status_code == 403

def test_idor_property_modification_forbidden_for_other_agents():
    # Agent 1 (Tanta) owns properties
    # Agent 2 (Mahalla) attempts to patch Agent 1's property
    agent2_token = get_token("mahalla.broker@mawa.eg", "BrokerPass123!")

    db = SessionLocal()
    try:
        tanta_agent = db.query(Property).filter(Property.city == "طنطا").first()
        tanta_prop_id = tanta_agent.id
    finally:
        db.close()

    # Agent 2 attempts to change price of Tanta Agent's property
    tamper_res = client.patch(
        f"/api/properties/{tanta_prop_id}",
        json={"price": 100000.0, "title": "تم التعديل بدون وجه حق"},
        headers={"Authorization": f"Bearer {agent2_token}"}
    )
    assert tamper_res.status_code == 403
    assert "غير مصرح لك بتعديل هذا العقار" in tamper_res.json()["detail"]

def test_admin_endpoints_strictly_forbidden_for_normal_users():
    buyer_token = get_token("buyer.ahmed@mawa.eg", "BuyerPass123!")
    res = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {buyer_token}"})
    assert res.status_code == 403
    assert "يتطلب هذا الإجراء صلاحيات إدارة عليا" in res.json()["detail"]
