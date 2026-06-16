import time
import random
import uuid
from datetime import datetime, timezone
from typing import Optional
from loguru import logger
from celery import shared_task

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.models import Email, Contact, Campaign, EmailStatus, Followup, AuditLog
from app.services.email_service import get_email_service
from app.core.config import settings


def render_contact_template(template: str, contact: Contact) -> str:
    """Render simple contact placeholders in a subject or body."""
    values = {
        "name": contact.name or "",
        "email": contact.email or "",
        "company": contact.company or "",
        "title": contact.title or "",
    }
    if contact.extra_data:
        values.update({str(k): "" if v is None else str(v) for k, v in contact.extra_data.items()})

    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
    return rendered


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_campaign_email(
    self,
    email_id: str,
    campaign_id: str,
    contact_id: str,
    user_id: str,
) -> dict:
    """Send a single campaign email with retry logic."""
    db = SessionLocal()
    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not all([email, contact, campaign]):
            logger.error(f"Missing records for email_id={email_id}")
            return {"status": "error", "message": "Records not found"}

        if email.status == EmailStatus.SENT.value:
            return {"status": "skipped", "message": "Already sent"}

        # Get user for SMTP settings
        from app.models.models import User
        user = db.query(User).filter(User.id == user_id).first()
        email_service = get_email_service(user)

        # Send the email
        success = email_service.send_email(
            to_email=contact.email,
            to_name=contact.name,
            subject=email.subject,
            body=email.body,
            tracking_id=email.tracking_pixel_id,
            email_id=email.id,
            resume_path=campaign.resume_path,
        )

        now = datetime.now(timezone.utc)
        email.status = EmailStatus.SENT.value
        email.sent_at = now
        email.celery_task_id = self.request.id
        contact.status = EmailStatus.SENT.value
        db.commit()

        logger.info(f"Email sent to {contact.email} (email_id={email_id})")
        return {"status": "sent", "email_id": email_id}

    except Exception as e:
        logger.error(f"Error sending email {email_id}: {e}")
        db_email = db.query(Email).filter(Email.id == email_id).first()
        if db_email:
            db_email.status = EmailStatus.FAILED.value
            db_email.error_message = str(e)
            db.commit()
        raise self.retry(exc=e)
    finally:
        db.close()


@celery_app.task
def launch_campaign(campaign_id: str, user_id: str) -> dict:
    """Launch all emails for a campaign with rate limiting."""
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        if campaign.status not in ("draft", "scheduled", "paused"):
            return {"status": "error", "message": f"Cannot launch campaign in status: {campaign.status}"}

        campaign.status = "running"
        campaign.started_at = datetime.now(timezone.utc)
        db.commit()

        contacts = (
            db.query(Contact)
            .filter(
                Contact.campaign_id == campaign_id,
                Contact.status == "pending",
            )
            .all()
        )

        emails_per_hour = campaign.emails_per_hour or settings.EMAILS_PER_HOUR
        delay_min = settings.EMAIL_DELAY_MIN_SECONDS
        delay_max = settings.EMAIL_DELAY_MAX_SECONDS

        sent_count = 0
        for i, contact in enumerate(contacts):
            # Check if email already exists
            existing = (
                db.query(Email)
                .filter(
                    Email.contact_id == contact.id,
                    Email.campaign_id == campaign_id,
                    Email.is_followup == False,
                )
                .first()
            )
            if not existing:
                logger.warning(f"No email record for contact {contact.id}, skipping")
                continue

            # Calculate countdown delay for rate limiting
            countdown = int(i / emails_per_hour * 3600) + random.randint(delay_min, delay_max)

            send_campaign_email.apply_async(
                args=[existing.id, campaign_id, contact.id, user_id],
                countdown=countdown,
            )
            sent_count += 1

        logger.info(f"Launched {sent_count} emails for campaign {campaign_id}")
        return {"status": "launched", "emails_queued": sent_count}

    finally:
        db.close()


@celery_app.task
def generate_campaign_emails(
    campaign_id: str,
    user_id: str,
    subject_template: str,
    body_template: str,
) -> dict:
    """Generate personalized emails for all contacts from a manual template."""
    db = SessionLocal()
    try:
        contacts = (
            db.query(Contact)
            .filter(Contact.campaign_id == campaign_id)
            .all()
        )

        generated = 0
        failed = 0

        for contact in contacts:
            existing = (
                db.query(Email)
                .filter(
                    Email.contact_id == contact.id,
                    Email.is_followup == False,
                )
                .first()
            )

            try:
                subject = render_contact_template(subject_template, contact)
                body = render_contact_template(body_template, contact)

                if existing:
                    if existing.status != EmailStatus.PENDING.value:
                        continue
                    existing.subject = subject
                    existing.body = body
                    existing.error_message = None
                    email = existing
                else:
                    email = Email(
                        id=str(uuid.uuid4()),
                        campaign_id=campaign_id,
                        contact_id=contact.id,
                        user_id=user_id,
                        subject=subject,
                        body=body,
                        is_followup=False,
                        followup_number=0,
                        status=EmailStatus.PENDING.value,
                        tracking_pixel_id=str(uuid.uuid4()),
                    )
                    db.add(email)
                db.commit()
                generated += 1
            except Exception as e:
                logger.error(f"Failed to generate email for {contact.email}: {e}")
                failed += 1

        return {"generated": generated, "failed": failed}

    finally:
        db.close()
