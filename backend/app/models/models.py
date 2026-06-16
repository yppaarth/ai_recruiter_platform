from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, Float,
    ForeignKey, JSON, Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"


class EmailStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    FAILED = "failed"
    BOUNCED = "bounced"


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    CAMPAIGN_CREATE = "campaign_create"
    CAMPAIGN_UPDATE = "campaign_update"
    CAMPAIGN_DELETE = "campaign_delete"
    EMAIL_SENT = "email_sent"
    FOLLOWUP_SENT = "followup_sent"
    REPLY_DETECTED = "reply_detected"
    CONTACTS_UPLOADED = "contacts_uploaded"
    EXPORT = "export"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # SMTP settings stored per user
    smtp_host = Column(String(255))
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String(255))
    smtp_password = Column(String(255))
    smtp_from_name = Column(String(255))
    smtp_use_tls = Column(Boolean, default=True)

    # IMAP settings
    imap_host = Column(String(255))
    imap_port = Column(Integer, default=993)
    imap_username = Column(String(255))
    imap_password = Column(String(255))

    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("EmailTemplate", back_populates="user", cascade="all, delete-orphan")




class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default=CampaignStatus.DRAFT.value, nullable=False)
    template_id = Column(String, ForeignKey("email_templates.id", ondelete="SET NULL"))
    resume_path = Column(String(500))
    sender_name = Column(String(255))
    sender_email = Column(String(255))

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Rate limiting overrides
    emails_per_hour = Column(Integer)
    emails_per_day = Column(Integer)

    # AI generated campaign summary
    ai_summary = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="campaigns")
    contacts = relationship("Contact", back_populates="campaign", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="campaign", cascade="all, delete-orphan")
    template = relationship("EmailTemplate", back_populates="campaigns")




class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=generate_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    company = Column(String(255))
    title = Column(String(255))
    extra_data = Column(JSON, default={})  # Custom columns stored here
    status = Column(String(50), default=EmailStatus.PENDING.value, nullable=False)

    # Tracking counts
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    has_replied = Column(Boolean, default=False)
    reply_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    campaign = relationship("Campaign", back_populates="contacts")
    emails = relationship("Email", back_populates="contact", cascade="all, delete-orphan")
    replies = relationship("Reply", back_populates="contact", cascade="all, delete-orphan")




class Email(Base):
    __tablename__ = "emails"

    id = Column(String, primary_key=True, default=generate_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    is_followup = Column(Boolean, default=False)
    followup_number = Column(Integer, default=0)  # 0=initial, 1=followup1, 2=followup2, etc.

    status = Column(String(50), default=EmailStatus.PENDING.value, nullable=False)
    sent_at = Column(DateTime(timezone=True))
    tracking_pixel_id = Column(String, unique=True, default=generate_uuid)

    # Counts
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    first_opened_at = Column(DateTime(timezone=True))
    last_opened_at = Column(DateTime(timezone=True))

    error_message = Column(Text)
    celery_task_id = Column(String(255))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    campaign = relationship("Campaign", back_populates="emails")
    contact = relationship("Contact", back_populates="emails")
    tracking_events = relationship("TrackingEvent", back_populates="email", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="original_email", foreign_keys="Followup.original_email_id", cascade="all, delete-orphan")




class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    email_id = Column(String, ForeignKey("emails.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # open, click
    url = Column(String(1000))  # For click events
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    email = relationship("Email", back_populates="tracking_events")




class Reply(Base):
    __tablename__ = "replies"

    id = Column(String, primary_key=True, default=generate_uuid)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    email_id = Column(String, ForeignKey("emails.id", ondelete="SET NULL"))

    subject = Column(String(500))
    body_preview = Column(Text)
    received_at = Column(DateTime(timezone=True))
    imap_message_id = Column(String(500))
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

    contact = relationship("Contact", back_populates="replies")

    __table_args__ = (
        UniqueConstraint("imap_message_id", name="uq_replies_imap_message_id"),
    )


class Followup(Base):
    __tablename__ = "followups"

    id = Column(String, primary_key=True, default=generate_uuid)
    original_email_id = Column(String, ForeignKey("emails.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)

    followup_number = Column(Integer, nullable=False)  # 1, 2, 3
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True))
    email_id = Column(String, ForeignKey("emails.id", ondelete="SET NULL"))  # The followup email sent
    status = Column(String(50), default="pending")  # pending, sent, cancelled

    original_email = relationship("Email", back_populates="followups", foreign_keys=[original_email_id])




class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    is_ai_generated = Column(Boolean, default=False)
    variables = Column(JSON, default=[])  # List of detected template variables

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="templates")
    campaigns = relationship("Campaign", back_populates="template")




class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    details = Column(JSON, default={})
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")


