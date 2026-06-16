from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Campaign, Reply
from app.api.deps import get_current_user
from app.models.models import User
from app.tasks.reply_tasks import check_for_replies

router = APIRouter(prefix="/replies", tags=["Replies"])


@router.get("/{campaign_id}")
def list_replies(
    campaign_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    from fastapi import HTTPException
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    replies = (
        db.query(Reply)
        .filter(Reply.campaign_id == campaign_id)
        .order_by(Reply.received_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "contact_id": r.contact_id,
            "subject": r.subject,
            "body_preview": r.body_preview,
            "received_at": r.received_at.isoformat() if r.received_at else None,
            "detected_at": r.detected_at.isoformat() if r.detected_at else None,
        }
        for r in replies
    ]


@router.post("/check")
def trigger_reply_check(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Manually trigger reply detection."""
    task = check_for_replies.delay()
    return {"message": "Reply check started", "task_id": task.id}
