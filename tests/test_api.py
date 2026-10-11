"""
Automated Pytest Suite for FastAPI Authentication, RBAC, and CRUD Operations
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_auth_login_admin():
    response = client.post("/auth/login", data={"username": "admin", "password": "Admin123!"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "Admin"


def test_auth_login_invalid():
    response = client.post("/auth/login", data={"username": "admin", "password": "WrongPassword"})
    assert response.status_code == 401


def test_patient_listing_and_rbac():
    # Login as admin
    login_res = client.post("/auth/login", data={"username": "admin", "password": "Admin123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch patients
    res = client.get("/patients?limit=5", headers=headers)
    assert res.status_code == 200
    patients = res.json()
    assert isinstance(patients, list)
    assert len(patients) <= 5


def test_analytics_overview():
    login_res = client.post("/auth/login", data={"username": "analyst", "password": "Analyst123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/analytics/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_patients" in data
    assert "readmission_rate_percent" in data
