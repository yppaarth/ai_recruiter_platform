import asyncio
from loguru import logger

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.models import Campaign, Contact, Email
from app.services.grok_client import grok_client
from sqlalchemy import func


@celery_app.task
def generate_campaign_ai_summary(campaign_id: str) -> dict:
    """Generate an AI-powered analytics summary for a campaign."""
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        contacts = db.query(Contact).filter(Contact.campaign_id == campaign_id).all()
        total = len(contacts)
        if total == 0:
            return {"status": "error", "message": "No contacts"}

        sent = sum(1 for c in contacts if c.status not in ("pending", "failed"))
        opened = sum(1 for c in contacts if c.open_count > 0)
        clicked = sum(1 for c in contacts if c.click_count > 0)
        replied = sum(1 for c in contacts if c.has_replied)

        stats = {
            "sent": sent,
            "open_rate": opened / max(sent, 1) * 100,
            "click_rate": clicked / max(sent, 1) * 100,
            "reply_rate": replied / max(sent, 1) * 100,
        }

        # Company breakdown
        company_data = {}
        for contact in contacts:
            company = contact.company or "Unknown"
            if company not in company_data:
                company_data[company] = {"count": 0, "replied": 0, "opened": 0}
            company_data[company]["count"] += 1
            if contact.has_replied:
                company_data[company]["replied"] += 1
            if contact.open_count > 0:
                company_data[company]["opened"] += 1

        company_breakdown = [
            {
                "company": company,
                "count": data["count"],
                "reply_rate": data["replied"] / max(data["count"], 1) * 100,
                "open_rate": data["opened"] / max(data["count"], 1) * 100,
            }
            for company, data in company_data.items()
        ]
        company_breakdown.sort(key=lambda x: x["reply_rate"], reverse=True)

        summary = asyncio.run(
            grok_client.generate_campaign_analytics_summary(
                campaign_name=campaign.name,
                stats=stats,
                company_breakdown=company_breakdown,
            )
        )

        campaign.ai_summary = summary
        db.commit()

        return {"status": "generated", "summary": summary}

    except Exception as e:
        logger.error(f"Failed to generate AI summary for campaign {campaign_id}: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
