import pytest


def test_create_campaign(client, auth_headers):
    resp = client.post("/api/v1/campaigns/", json={
        "name": "Test Campaign",
        "description": "A test campaign",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Campaign"
    assert data["status"] == "draft"
    assert "id" in data


def test_list_campaigns(client, auth_headers):
    client.post("/api/v1/campaigns/", json={"name": "Camp 1"}, headers=auth_headers)
    client.post("/api/v1/campaigns/", json={"name": "Camp 2"}, headers=auth_headers)
    resp = client.get("/api/v1/campaigns/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_get_campaign(client, auth_headers):
    create_resp = client.post("/api/v1/campaigns/", json={"name": "Get Me"}, headers=auth_headers)
    cid = create_resp.json()["id"]
    resp = client.get(f"/api/v1/campaigns/{cid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == cid


def test_update_campaign(client, auth_headers):
    create_resp = client.post("/api/v1/campaigns/", json={"name": "Original"}, headers=auth_headers)
    cid = create_resp.json()["id"]
    resp = client.put(f"/api/v1/campaigns/{cid}", json={"name": "Updated"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


def test_delete_campaign(client, auth_headers):
    create_resp = client.post("/api/v1/campaigns/", json={"name": "Delete Me"}, headers=auth_headers)
    cid = create_resp.json()["id"]
    del_resp = client.delete(f"/api/v1/campaigns/{cid}", headers=auth_headers)
    assert del_resp.status_code == 204
    get_resp = client.get(f"/api/v1/campaigns/{cid}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_clone_campaign(client, auth_headers):
    create_resp = client.post("/api/v1/campaigns/", json={"name": "Original"}, headers=auth_headers)
    cid = create_resp.json()["id"]
    resp = client.post(f"/api/v1/campaigns/{cid}/clone", headers=auth_headers)
    assert resp.status_code == 200
    assert "Copy of Original" in resp.json()["name"]


def test_campaign_not_found(client, auth_headers):
    resp = client.get("/api/v1/campaigns/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404


def test_filter_campaigns_by_status(client, auth_headers):
    client.post("/api/v1/campaigns/", json={"name": "Draft Camp"}, headers=auth_headers)
    resp = client.get("/api/v1/campaigns/?status=draft", headers=auth_headers)
    assert resp.status_code == 200
    for c in resp.json():
        assert c["status"] == "draft"
