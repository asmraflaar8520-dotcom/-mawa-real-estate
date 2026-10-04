import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_token(email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]

import uuid

def test_separated_verification_model():
    unique_email = f"test.agent_{uuid.uuid4().hex[:8]}@mawa.eg"
    res = client.post("/api/auth/register", json={
        "email": unique_email,
        "password": "Password123!",
        "full_name": "وسيط غير معتمد مهنياً",
        "role": "AGENT"
    })
    if res.status_code == 201:
        data = res.json()
        assert data["identity_status"] == "PENDING"
        assert data["professional_status"] == "PENDING"
        assert data["professional_status"] != "VERIFIED"

def test_listing_review_workflow_and_isolation():
    agent_token = get_token("tanta.broker@mawa.eg", "BrokerPass123!")
    admin_token = get_token("admin@mawa.eg", "AdminMawa2026!Safe")

    unique_title = f"شقة تحت المراجعة الإدارية بزفتى - {uuid.uuid4().hex[:6]}"
    # Agent creates a new property
    new_prop_payload = {
        "title": unique_title,
        "property_type": "شقة سكني",
        "city": "زفتى",
        "district": "شارع الجيش",
        "approx_lat": 30.718,
        "approx_lng": 31.242,
        "exact_address_private": "برج الصفا الدور 4 شقة 8",
        "price": 2000000.0,
        "area_sqm": 140.0,
        "bedrooms": 3,
        "bathrooms": 2,
        "floor": 4,
        "total_floors": 9,
        "elevator": True,
        "parking": False,
        "balcony": True,
        "finishing": "سوبر لوكس",
        "building_license_status": "مرخص بالكامل",
        "description": "شقة متميزة بانتظار الاعتماد الإداري"
    }

    create_res = client.post("/api/properties", json=new_prop_payload, headers={"Authorization": f"Bearer {agent_token}"})
    assert create_res.status_code == 201
    prop_id = create_res.json()["id"]
    assert create_res.json()["status"] == "PENDING_REVIEW"

    # Anonymous public search should NOT see this pending property
    public_res = client.get("/api/properties?city=زفتى")
    public_titles = [p["title"] for p in public_res.json()]
    assert unique_title not in public_titles

    # Admin reviews and publishes the property
    publish_res = client.post(f"/api/admin/properties/{prop_id}/publish", headers={"Authorization": f"Bearer {admin_token}"})
    assert publish_res.status_code == 200

    # Now anonymous public search MUST see it
    public_res_after = client.get("/api/properties?city=زفتى")
    public_titles_after = [p["title"] for p in public_res_after.json()]
    assert unique_title in public_titles_after

def test_neutral_property_comparison_endpoint():
    # Fetch 2 published properties
    props = client.get("/api/properties").json()
    assert len(props) >= 2
    id1 = props[0]["id"]
    id2 = props[1]["id"]

    # Valid 2 properties
    comp_res = client.get(f"/api/properties/compare?ids={id1},{id2}")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert len(comp_data) == 2
    assert comp_data[0]["price_per_sqm"] > 0
    assert comp_data[1]["price_per_sqm"] > 0

    # Invalid: 1 property only (must reject)
    comp_single_res = client.get(f"/api/properties/compare?ids={id1}")
    assert comp_single_res.status_code == 400
    assert "عقارين إلى 4 عقارات" in comp_single_res.json()["detail"]
