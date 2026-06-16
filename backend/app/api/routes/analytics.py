from typing import List
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.db.session import get_db
from app.models.models import Campaign, Contact, Email, TrackingEvent, Reply
from app.schemas.schemas import OverallAnalytics, DailyStats
from app.api.deps import get_current_user
from app.models.models import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=OverallAnalytics)
def get_overview(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OverallAnalytics:
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Campaign counts
    total_campaigns = db.query(Campaign).filter(
        Campaign.user_id == current_user.id
    ).count()

    # Contact and email stats across all campaigns
    user_campaigns = db.query(Campaign.id).filter(
        Campaign.user_id == current_user.id
    ).subquery()

    contacts = (
        db.query(Contact)
        .filter(Contact.campaign_id.in_(user_campaigns))
        .all()
    )

    total_contacts = len(contacts)
    total_sent = sum(1 for c in contacts if c.status not in ("pending", "failed"))
    total_opened = sum(1 for c in contacts if c.open_count > 0)
    total_clicked = sum(1 for c in contacts if c.click_count > 0)
    total_replied = sum(1 for c in contacts if c.has_replied)

    # Daily stats
    daily_stats = []
    for i in range(days - 1, -1, -1):
        day = datetime.now(timezone.utc).date() - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        sent_count = (
            db.query(Email)
            .filter(
                Email.campaign_id.in_(user_campaigns),
                Email.sent_at >= day_start,
                Email.sent_at < day_end,
            )
            .count()
        )

        opened_count = (
            db.query(TrackingEvent)
            .join(Email, TrackingEvent.email_id == Email.id)
            .filter(
                Email.campaign_id.in_(user_campaigns),
                TrackingEvent.event_type == "open",
                TrackingEvent.timestamp >= day_start,
                TrackingEvent.timestamp < day_end,
            )
            .count()
        )

        clicked_count = (
            db.query(TrackingEvent)
            .join(Email, TrackingEvent.email_id == Email.id)
            .filter(
                Email.campaign_id.in_(user_campaigns),
                TrackingEvent.event_type == "click",
                TrackingEvent.timestamp >= day_start,
                TrackingEvent.timestamp < day_end,
            )
            .count()
        )

        replied_count = (
            db.query(Reply)
            .filter(
                Reply.campaign_id.in_(user_campaigns),
                Reply.received_at >= day_start,
                Reply.received_at < day_end,
            )
            .count()
        )

        daily_stats.append(DailyStats(
            date=day.isoformat(),
            sent=sent_count,
            opened=opened_count,
            clicked=clicked_count,
            replied=replied_count,
        ))

    # Top companies
    company_data: dict = {}
    for contact in contacts:
        company = contact.company or "Unknown"
        if company not in company_data:
            company_data[company] = {"total": 0, "replied": 0, "opened": 0}
        company_data[company]["total"] += 1
        if contact.has_replied:
            company_data[company]["replied"] += 1
        if contact.open_count > 0:
            company_data[company]["opened"] += 1

    top_companies = sorted(
        [
            {
                "company": k,
                "total": v["total"],
                "replied": v["replied"],
                "opened": v["opened"],
                "reply_rate": v["replied"] / max(v["total"], 1) * 100,
            }
            for k, v in company_data.items()
        ],
        key=lambda x: x["reply_rate"],
        reverse=True,
    )[:10]

    return OverallAnalytics(
        total_campaigns=total_campaigns,
        total_contacts=total_contacts,
        total_sent=total_sent,
        total_opened=total_opened,
        total_clicked=total_clicked,
        total_replied=total_replied,
        overall_open_rate=total_opened / max(total_sent, 1) * 100,
        overall_click_rate=total_clicked / max(total_sent, 1) * 100,
        overall_reply_rate=total_replied / max(total_sent, 1) * 100,
        daily_stats=daily_stats,
        top_companies=top_companies,
    )


@router.get("/campaign/{campaign_id}")
def get_campaign_analytics(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Campaign not found")

    contacts = db.query(Contact).filter(Contact.campaign_id == campaign_id).all()
    total = len(contacts)
    sent = sum(1 for c in contacts if c.status not in ("pending", "failed"))
    opened = sum(1 for c in contacts if c.open_count > 0)
    clicked = sum(1 for c in contacts if c.click_count > 0)
    replied = sum(1 for c in contacts if c.has_replied)

    # Events timeline
    events = (
        db.query(TrackingEvent)
        .join(Email, TrackingEvent.email_id == Email.id)
        .filter(Email.campaign_id == campaign_id)
        .order_by(TrackingEvent.timestamp.desc())
        .limit(100)
        .all()
    )

    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign.name,
        "status": campaign.status,
        "ai_summary": campaign.ai_summary,
        "stats": {
            "total": total,
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "replied": replied,
            "open_rate": opened / max(sent, 1) * 100,
            "click_rate": clicked / max(sent, 1) * 100,
            "reply_rate": replied / max(sent, 1) * 100,
        },
        "recent_events": [
            {
                "type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
                "url": e.url,
            }
            for e in events
        ],
    }
