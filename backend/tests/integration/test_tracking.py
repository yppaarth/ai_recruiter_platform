import pytest
import uuid


def _make_email(db, campaign_id, contact_id, user_id):
    from app.models.models import Email, EmailStatus
    email = Email(
        id=str(uuid.uuid4()),
        campaign_id=campaign_id,
        contact_id=contact_id,
        user_id=user_id,
        subject="Test Subject",
        body="Test body",
        status=EmailStatus.SENT.value,
        tracking_pixel_id=str(uuid.uuid4()),
    )
    db.add(email)
    db.commit()
    db.refresh(email)
    return email


def test_tracking_open(client, auth_headers, db):
    # Create campaign and contact
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": "track@example.com", "username": "trackuser", "password": "trackpass1"
    })
    user_id = reg_resp.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    camp_resp = client.post("/api/v1/campaigns/", json={"name": "Track Camp"}, headers=headers)
    cid = camp_resp.json()["id"]

    from app.models.models import Contact
    contact = Contact(
        id=str(uuid.uuid4()),
        campaign_id=cid,
        name="Tracker",
        email="tracker@example.com",
        status="sent",
    )
    db.add(contact)
    db.commit()

    email = _make_email(db, cid, contact.id, user_id)

    resp = client.get(f"/api/v1/tracking/open/{email.tracking_pixel_id}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/gif"

    db.refresh(email)
    assert email.open_count == 1
    assert email.first_opened_at is not None
