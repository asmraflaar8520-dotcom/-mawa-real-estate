import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_token(email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]

def test_favorites_workflow():
    buyer_token = get_token("buyer.ahmed@mawa.eg", "BuyerPass123!")

    # 1. Fetch available properties
    props_res = client.get("/api/properties")
    assert props_res.status_code == 200
    props = props_res.json()
    assert len(props) > 0
    target_prop_id = props[0]["id"]

    # 2. Add to favorites
    fav_add = client.post(
        f"/api/properties/{target_prop_id}/favorite",
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    assert fav_add.status_code == 200
    assert fav_add.json()["is_favorite"] is True
    assert fav_add.json()["property_id"] == target_prop_id

    # 3. Retrieve favorites list
    fav_list = client.get(
        "/api/properties/favorites",
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    assert fav_list.status_code == 200
    fav_ids = [p["id"] for p in fav_list.json()]
    assert target_prop_id in fav_ids

    # 4. Remove from favorites (toggle off)
    fav_remove = client.post(
        f"/api/properties/{target_prop_id}/favorite",
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    assert fav_remove.status_code == 200
    assert fav_remove.json()["is_favorite"] is False

    # 5. Verify removed
    fav_list_after = client.get(
        "/api/properties/favorites",
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    assert fav_list_after.status_code == 200
    fav_ids_after = [p["id"] for p in fav_list_after.json()]
    assert target_prop_id not in fav_ids_after

def test_unauthenticated_favorite_rejected():
    props_res = client.get("/api/properties")
    target_prop_id = props_res.json()[0]["id"]

    unauth_res = client.post(f"/api/properties/{target_prop_id}/favorite")
    assert unauth_res.status_code == 401
