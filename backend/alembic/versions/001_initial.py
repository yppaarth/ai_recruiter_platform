"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("smtp_host", sa.String(255), nullable=True),
        sa.Column("smtp_port", sa.Integer(), nullable=True, server_default="587"),
        sa.Column("smtp_username", sa.String(255), nullable=True),
        sa.Column("smtp_password", sa.String(255), nullable=True),
        sa.Column("smtp_from_name", sa.String(255), nullable=True),
        sa.Column("smtp_use_tls", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("imap_host", sa.String(255), nullable=True),
        sa.Column("imap_port", sa.Integer(), nullable=True, server_default="993"),
        sa.Column("imap_username", sa.String(255), nullable=True),
        sa.Column("imap_password", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # email_templates
    op.create_table(
        "email_templates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_ai_generated", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("variables", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_templates_user_id", "email_templates", ["user_id"])

    # campaigns
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("template_id", sa.String(), nullable=True),
        sa.Column("resume_path", sa.String(500), nullable=True),
        sa.Column("sender_name", sa.String(255), nullable=True),
        sa.Column("sender_email", sa.String(255), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("emails_per_hour", sa.Integer(), nullable=True),
        sa.Column("emails_per_day", sa.Integer(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["email_templates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_campaigns_user_id", "campaigns", ["user_id"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])

    # contacts
    op.create_table(
        "contacts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("campaign_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("open_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("click_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("has_replied", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("reply_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_campaign_id", "contacts", ["campaign_id"])
    op.create_index("ix_contacts_email", "contacts", ["email"])
    op.create_index("ix_contacts_status", "contacts", ["status"])

    # emails
    op.create_table(
        "emails",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("campaign_id", sa.String(), nullable=False),
        sa.Column("contact_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_followup", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("followup_number", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tracking_pixel_id", sa.String(), nullable=True),
        sa.Column("open_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("click_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("first_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tracking_pixel_id"),
    )
    op.create_index("ix_emails_campaign_id", "emails", ["campaign_id"])
    op.create_index("ix_emails_contact_id", "emails", ["contact_id"])
    op.create_index("ix_emails_tracking_pixel_id", "emails", ["tracking_pixel_id"])
    op.create_index("ix_emails_status", "emails", ["status"])

    # tracking_events
    op.create_table(
        "tracking_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("url", sa.String(1000), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tracking_events_email_id", "tracking_events", ["email_id"])
    op.create_index("ix_tracking_events_event_type", "tracking_events", ["event_type"])
    op.create_index("ix_tracking_events_timestamp", "tracking_events", ["timestamp"])

    # replies
    op.create_table(
        "replies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("contact_id", sa.String(), nullable=False),
        sa.Column("campaign_id", sa.String(), nullable=False),
        sa.Column("email_id", sa.String(), nullable=True),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("body_preview", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("imap_message_id", sa.String(500), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("imap_message_id", name="uq_replies_imap_message_id"),
    )
    op.create_index("ix_replies_contact_id", "replies", ["contact_id"])
    op.create_index("ix_replies_campaign_id", "replies", ["campaign_id"])

    # followups
    op.create_table(
        "followups",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("original_email_id", sa.String(), nullable=False),
        sa.Column("contact_id", sa.String(), nullable=False),
        sa.Column("campaign_id", sa.String(), nullable=False),
        sa.Column("followup_number", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(50), nullable=True, server_default="pending"),
        sa.ForeignKeyConstraint(["original_email_id"], ["emails.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_followups_original_email_id", "followups", ["original_email_id"])
    op.create_index("ix_followups_scheduled_at", "followups", ["scheduled_at"])
    op.create_index("ix_followups_status", "followups", ["status"])

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("followups")
    op.drop_table("replies")
    op.drop_table("tracking_events")
    op.drop_table("emails")
    op.drop_table("contacts")
    op.drop_table("campaigns")
    op.drop_table("email_templates")
    op.drop_table("users")
