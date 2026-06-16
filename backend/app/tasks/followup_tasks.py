import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from loguru import logger

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.models import Email, Contact, Campaign, Followup, EmailStatus
from app.services.grok_client import grok_client
from app.services.email_service import get_email_service
from app.core.config import settings


FOLLOWUP_SCHEDULE = {
    1: 3,    # First follow-up after 3 days
    2: 7,    # Second follow-up after 7 days
    3: 14,   # Third follow-up after 14 days
}


@celery_app.task
def schedule_followups(
    email_id: str,
    campaign_id: str,
    contact_id: str,
    user_id: str,
) -> dict:
    """Schedule follow-up emails for a sent email."""
    db = SessionLocal()
    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email or not email.sent_at:
            return {"status": "error", "message": "Email not found or not sent"}

        sent_at = email.sent_at

        for followup_num, days_delay in FOLLOWUP_SCHEDULE.items():
            scheduled_at = sent_at + timedelta(days=days_delay)

            # Check if followup already scheduled
            existing = (
                db.query(Followup)
                .filter(
                    Followup.original_email_id == email_id,
                    Followup.followup_number == followup_num,
                )
                .first()
            )
            if existing:
                continue

            followup = Followup(
                id=str(uuid.uuid4()),
                original_email_id=email_id,
                contact_id=contact_id,
                campaign_id=campaign_id,
                followup_number=followup_num,
                scheduled_at=scheduled_at,
                status="pending",
            )
            db.add(followup)

        db.commit()
        logger.info(f"Scheduled {len(FOLLOWUP_SCHEDULE)} follow-ups for email {email_id}")
        return {"status": "scheduled", "followups": len(FOLLOWUP_SCHEDULE)}

    finally:
        db.close()


@celery_app.task
def process_pending_followups() -> dict:
    """Process all pending follow-ups that are due."""
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    processed = 0
    skipped = 0

    try:
        pending_followups = (
            db.query(Followup)
            .filter(
                Followup.status == "pending",
                Followup.scheduled_at <= now,
            )
            .all()
        )

        for followup in pending_followups:
            contact = db.query(Contact).filter(Contact.id == followup.contact_id).first()
            original_email = db.query(Email).filter(Email.id == followup.original_email_id).first()
            campaign = db.query(Campaign).filter(Campaign.id == followup.campaign_id).first()

            if not all([contact, original_email, campaign]):
                followup.status = "cancelled"
                db.commit()
                continue

            # Cancel if contact has already replied
            if contact.has_replied:
                followup.status = "cancelled"
                db.commit()
                skipped += 1
                continue

            # Cancel if campaign is not running
            if campaign.status not in ("running", "completed"):
                followup.status = "cancelled"
                db.commit()
                skipped += 1
                continue

            # Generate and send follow-up
            send_followup_email.delay(
                followup_id=followup.id,
                contact_id=contact.id,
                original_email_id=original_email.id,
                campaign_id=campaign.id,
                user_id=campaign.user_id,
            )
            processed += 1

        return {"processed": processed, "skipped": skipped}

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2)
def send_followup_email(
    self,
    followup_id: str,
    contact_id: str,
    original_email_id: str,
    campaign_id: str,
    user_id: str,
) -> dict:
    """Generate and send a specific follow-up email."""
    db = SessionLocal()
    try:
        followup = db.query(Followup).filter(Followup.id == followup_id).first()
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        original_email = db.query(Email).filter(Email.id == original_email_id).first()
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not all([followup, contact, original_email, campaign]):
            return {"status": "error", "message": "Missing records"}

        if followup.status != "pending":
            return {"status": "skipped", "reason": followup.status}

        if contact.has_replied:
            followup.status = "cancelled"
            db.commit()
            return {"status": "cancelled", "reason": "Contact replied"}

        days_since = (
            datetime.now(timezone.utc) - original_email.sent_at
        ).days if original_email.sent_at else followup.followup_number * 3

        # Get candidate profile from campaign description or a default
        candidate_profile = campaign.description or "An experienced software engineer and AI/ML specialist."

        # Generate follow-up content
        result = asyncio.run(
            grok_client.generate_followup_email(
                recruiter_name=contact.name,
                company=contact.company or "your company",
                original_subject=original_email.subject,
                followup_number=followup.followup_number,
                days_since_original=days_since,
                candidate_profile=candidate_profile,
            )
        )

        # Create email record
        from app.models.models import User
        user = db.query(User).filter(User.id == user_id).first()

        followup_email = Email(
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            contact_id=contact_id,
            user_id=user_id,
            subject=result["subject"],
            body=result["body"],
            is_followup=True,
            followup_number=followup.followup_number,
            status=EmailStatus.PENDING.value,
            tracking_pixel_id=str(uuid.uuid4()),
        )
        db.add(followup_email)
        db.flush()

        # Send it
        email_service = get_email_service(user)
        email_service.send_email(
            to_email=contact.email,
            to_name=contact.name,
            subject=result["subject"],
            body=result["body"],
            tracking_id=followup_email.tracking_pixel_id,
            email_id=followup_email.id,
            resume_path=campaign.resume_path,
        )

        now = datetime.now(timezone.utc)
        followup_email.status = EmailStatus.SENT.value
        followup_email.sent_at = now
        followup.status = "sent"
        followup.sent_at = now
        followup.email_id = followup_email.id
        db.commit()

        logger.info(
            f"Follow-up #{followup.followup_number} sent to {contact.email}"
        )
        return {"status": "sent", "followup_id": followup_id}

    except Exception as e:
        logger.error(f"Error sending follow-up {followup_id}: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()
