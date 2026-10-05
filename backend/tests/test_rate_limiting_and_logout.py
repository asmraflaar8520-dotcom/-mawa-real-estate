import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.security.auth_guard import rate_limiter, InMemoryRateLimiter

client = TestClient(app)

def test_logout_revokes_jwt_session():
    # 1. Login
    login_res = client.post("/api/auth/login", json={
        "email": "buyer.ahmed@mawa.eg",
        "password": "BuyerPass123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # 2. Verify active session
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "buyer.ahmed@mawa.eg"

    # 3. Call Logout
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200
    assert "تم تسجيل الخروج" in logout_res.json()["message"]

    # 4. Attempt to use revoked token
    me_after = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_after.status_code == 401
    assert "تم إنهاء هذه الجلسة" in me_after.json()["detail"]

def test_long_arabic_password_hash_and_login():
    # Password with Arabic characters (>72 bytes in UTF-8)
    long_arabic_pass = "كلمة_سر_عربية_طويلة_جداً_تفوق_الحد_الأقصى_للتشفير_بنجاح_وأمان_2026!"
    unique_email = f"test.arabic_{uuid.uuid4().hex[:8]}@mawa.eg"

    reg_res = client.post("/api/auth/register", json={
        "email": unique_email,
        "password": long_arabic_pass,
        "full_name": "مستخدم بكلمة سر عربية",
        "role": "BUYER"
    })
    assert reg_res.status_code == 201

    # Login with the exact same long Arabic password
    login_res = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": long_arabic_pass
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

def test_in_memory_rate_limiter_logic():
    limiter = InMemoryRateLimiter()
    key = "test_ip_client:/test_endpoint"

    # Allow up to 3 requests in 10 seconds
    for _ in range(3):
        assert limiter.check(key, max_requests=3, window_seconds=10, force=True) is True

    # 4th request must be blocked
    assert limiter.check(key, max_requests=3, window_seconds=10, force=True) is False
