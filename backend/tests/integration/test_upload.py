from pathlib import Path

from app.models import models  # noqa: F401


def test_resume_upload_preserves_original_filename(client, auth_headers, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.routes.upload.settings.UPLOAD_DIR", str(tmp_path))

    campaign_resp = client.post(
        "/api/v1/campaigns/",
        json={"name": "Resume Upload"},
        headers=auth_headers,
    )
    campaign_id = campaign_resp.json()["id"]

    resp = client.post(
        f"/api/v1/upload/resume/{campaign_id}",
        files={"file": ("Pratham Yadav Resume.pdf", b"%PDF-1.4\nresume", "application/pdf")},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "Pratham Yadav Resume.pdf"
    assert Path(data["path"]).name == "Pratham Yadav Resume.pdf"
    assert Path(data["path"]).exists()


def test_resume_upload_strips_path_from_filename(client, auth_headers, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.routes.upload.settings.UPLOAD_DIR", str(tmp_path))

    campaign_resp = client.post(
        "/api/v1/campaigns/",
        json={"name": "Resume Upload"},
        headers=auth_headers,
    )
    campaign_id = campaign_resp.json()["id"]

    resp = client.post(
        f"/api/v1/upload/resume/{campaign_id}",
        files={"file": ("../../Resume.pdf", b"%PDF-1.4\nresume", "application/pdf")},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "Resume.pdf"
    assert Path(data["path"]).name == "Resume.pdf"
