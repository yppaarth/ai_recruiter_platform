import uuid
from datetime import datetime, timezone, timedelta
from loguru import logger

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.models import Contact, Campaign, Reply, User, EmailStatus
from app.services.imap_service import IMAPService


@celery_app.task
def check_for_replies() -> dict:
    """Check all active campaigns for email replies via IMAP."""
    db = SessionLocal()
    total_detected = 0

    try:
        # Get all users with IMAP configured
        users = (
            db.query(User)
            .filter(
                User.imap_username != None,
                User.imap_password != None,
                User.is_active == True,
            )
            .all()
        )

        for user in users:
            imap = IMAPService(
                host=user.imap_host,
                port=user.imap_port,
                username=user.imap_username,
                password=user.imap_password,
            )

            since = datetime.now(timezone.utc) - timedelta(days=30)
            raw_replies = imap.fetch_replies(since_date=since)

            # Get all active campaign contacts for this user
            active_contacts = (
                db.query(Contact)
                .join(Campaign, Contact.campaign_id == Campaign.id)
                .filter(
                    Campaign.user_id == user.id,
                    Campaign.status.in_(["running", "completed"]),
                    Contact.has_replied == False,
                )
                .all()
            )

            contact_email_map = {c.email.lower(): c for c in active_contacts}

            for reply_data in raw_replies:
                sender_email = reply_data["from_email"].lower()
                if "<" in sender_email:
                    # Extract from "Name <email>" format
                    sender_email = sender_email.split("<")[1].rstrip(">").strip()

                matched_contact = contact_email_map.get(sender_email)
                if not matched_contact:
                    continue

                # Check if reply already recorded
                existing_reply = (
                    db.query(Reply)
                    .filter(Reply.imap_message_id == str(reply_data["message_id"]))
                    .first()
                )
                if existing_reply:
                    continue

                # Record the reply
                new_reply = Reply(
                    id=str(uuid.uuid4()),
                    contact_id=matched_contact.id,
                    campaign_id=matched_contact.campaign_id,
                    subject=reply_data["subject"],
                    body_preview=reply_data["body_preview"][:500],
                    received_at=reply_data["received_at"],
                    imap_message_id=str(reply_data["message_id"]),
                )
                db.add(new_reply)

                # Update contact
                matched_contact.has_replied = True
                matched_contact.reply_at = reply_data["received_at"]
                matched_contact.status = EmailStatus.REPLIED.value

                # Cancel pending follow-ups for this contact
                from app.models.models import Followup
                pending_followups = (
                    db.query(Followup)
                    .filter(
                        Followup.contact_id == matched_contact.id,
                        Followup.status == "pending",
                    )
                    .all()
                )
                for fu in pending_followups:
                    fu.status = "cancelled"

                total_detected += 1
                logger.info(f"Reply detected from {sender_email}")

            db.commit()

        return {"replies_detected": total_detected}

    except Exception as e:
        logger.error(f"Error checking replies: {e}")
        return {"error": str(e)}
    finally:
        db.close()
