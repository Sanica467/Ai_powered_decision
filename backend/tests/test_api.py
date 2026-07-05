"""Integration tests for the API endpoints."""
import io
import json

import pandas as pd
import pytest


@pytest.fixture
def auth_token(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "testuser@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
    })
    if resp.status_code == 400:  # already exists from prior test
        resp = client.post("/api/v1/auth/login", json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        })
    assert resp.status_code in (200, 201)
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _csv_bytes():
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=30, freq="D"),
        "revenue": range(100, 130),
        "profit": range(50, 80),
        "region": ["North", "South"] * 15,
        "customer_count": range(10, 40),
    })
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_register_and_login(client):
    reg = client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "NewPassword123!",
    })
    assert reg.status_code == 201
    login = client.post("/api/v1/auth/login", json={
        "email": "newuser@example.com",
        "password": "NewPassword123!",
    })
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_login_invalid(client):
    resp = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "wrong",
    })
    assert resp.status_code == 401


def test_me_without_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_token(client, auth_token):
    resp = client.get("/api/v1/auth/me", headers=_auth_headers(auth_token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "testuser@example.com"


def test_upload_and_analyze(client, auth_token):
    headers = _auth_headers(auth_token)
    files = {"file": ("test.csv", _csv_bytes(), "text/csv")}
    upload = client.post("/api/v1/upload", files=files, headers=headers)
    assert upload.status_code == 201
    dataset_id = upload.json()["dataset_id"]
    assert upload.json()["row_count"] == 30

    analyze = client.post("/api/v1/analyze", json={"dataset_id": dataset_id}, headers=headers)
    assert analyze.status_code == 200
    assert "quality_score" in analyze.json()
    assert "health_score" in analyze.json()
    assert "target_suggestions" in analyze.json()


def test_diagnosis(client, auth_token):
    headers = _auth_headers(auth_token)
    files = {"file": ("test.csv", _csv_bytes(), "text/csv")}
    upload = client.post("/api/v1/upload", files=files, headers=headers)
    dataset_id = upload.json()["dataset_id"]

    resp = client.post("/api/v1/diagnosis", json={"dataset_id": dataset_id}, headers=headers)
    assert resp.status_code == 200
    assert "issues" in resp.json()
    assert len(resp.json()["issues"]) >= 1


def test_predict(client, auth_token):
    headers = _auth_headers(auth_token)
    files = {"file": ("test.csv", _csv_bytes(), "text/csv")}
    upload = client.post("/api/v1/upload", files=files, headers=headers)
    dataset_id = upload.json()["dataset_id"]

    resp = client.post("/api/v1/predict", json={"dataset_id": dataset_id, "target_column": "revenue"}, headers=headers)
    assert resp.status_code == 200
    assert "best_model" in resp.json()
    assert "model_comparison" in resp.json()


def test_upload_invalid_file_type(client, auth_token):
    headers = _auth_headers(auth_token)
    files = {"file": ("test.txt", b"hello", "text/plain")}
    resp = client.post("/api/v1/upload", files=files, headers=headers)
    assert resp.status_code == 400
