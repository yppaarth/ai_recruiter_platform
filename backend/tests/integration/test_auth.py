import pytest


def test_register_success(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "securepass123",
        "full_name": "New User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "new@example.com"


def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "username": "dupuser", "password": "pass12345"}
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json={**payload, "username": "other"})
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_register_duplicate_username(client):
    client.post("/api/v1/auth/register", json={"email": "a@example.com", "username": "samename", "password": "pass12345"})
    resp = client.post("/api/v1/auth/register", json={"email": "b@example.com", "username": "samename", "password": "pass12345"})
    assert resp.status_code == 400


def test_login_success(client):
    client.post("/api/v1/auth/register", json={
        "email": "login@example.com", "username": "loginuser", "password": "mypassword1"
    })
    resp = client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "mypassword1"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "email": "wp@example.com", "username": "wpuser", "password": "correctpass1"
    })
    resp = client.post("/api/v1/auth/login", json={"email": "wp@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_get_me(client, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "auth@example.com"


def test_get_me_unauthenticated(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)
