import uuid
import base64
from datetime import datetime, timezone
from urllib.parse import unquote
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Email, Contact, TrackingEvent, EmailStatus

router = APIRouter(prefix="/tracking", tags=["Tracking"])

# 1x1 transparent GIF pixel
TRACKING_PIXEL = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


@router.get("/open/{tracking_id}")
def track_open(
    tracking_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    """Return tracking pixel and record email open event."""
    email = db.query(Email).filter(Email.tracking_pixel_id == tracking_id).first()

    if email:
        now = datetime.now(timezone.utc)

        # Record tracking event
        event = TrackingEvent(
            id=str(uuid.uuid4()),
            email_id=email.id,
            event_type="open",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.add(event)

        # Update email stats
        email.open_count += 1
        if not email.first_opened_at:
            email.first_opened_at = now
        email.last_opened_at = now
        if email.status in ("sent", "delivered", "pending"):
            email.status = EmailStatus.OPENED.value

        # Update contact stats
        contact = db.query(Contact).filter(Contact.id == email.contact_id).first()
        if contact:
            contact.open_count += 1
            if contact.status in ("sent", "delivered", "pending"):
                contact.status = EmailStatus.OPENED.value

        db.commit()

    return Response(
        content=TRACKING_PIXEL,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/click/{email_id}")
def track_click(
    email_id: str,
    url: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Record click event and redirect to original URL."""
    decoded_url = unquote(url)

    email = db.query(Email).filter(Email.id == email_id).first()
    if email:
        event = TrackingEvent(
            id=str(uuid.uuid4()),
            email_id=email.id,
            event_type="click",
            url=decoded_url,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.add(event)

        email.click_count += 1
        if email.status in ("sent", "delivered", "opened", "pending"):
            email.status = EmailStatus.CLICKED.value

        contact = db.query(Contact).filter(Contact.id == email.contact_id).first()
        if contact:
            contact.click_count += 1
            if contact.status in ("sent", "delivered", "opened", "pending"):
                contact.status = EmailStatus.CLICKED.value

        db.commit()

    # Redirect to original URL
    if not decoded_url.startswith(("http://", "https://")):
        decoded_url = "https://" + decoded_url

    return RedirectResponse(url=decoded_url, status_code=302)
