import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.entities import User, UserRole

client = TestClient(app)

import uuid

def test_register_buyer_success():
    unique_email = f"test.newbuyer_{uuid.uuid4().hex[:8]}@mawa.eg"
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "full_name": "مشتري تجريبي جديد",
        "phone_number": "01099998888",
        "role": "BUYER"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["email"] == unique_email
    assert data["role"] == "BUYER"
    assert data["identity_status"] == "PENDING"
    assert data["professional_status"] == "NOT_APPLIED"

def test_register_duplicate_email_conflict():
    payload = {
        "email": "buyer.ahmed@mawa.eg",
        "password": "Password123!",
        "full_name": "اسم مكرر",
        "role": "BUYER"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert "البريد الإلكتروني مسجل بالفعل" in response.json()["detail"]

def test_login_invalid_password_fails():
    payload = {
        "email": "buyer.ahmed@mawa.eg",
        "password": "WrongPassword999!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert "بيانات الاعتماد غير صحيحة" in response.json()["detail"]

def test_login_success():
    payload = {
        "email": "buyer.ahmed@mawa.eg",
        "password": "BuyerPass123!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "buyer.ahmed@mawa.eg"
