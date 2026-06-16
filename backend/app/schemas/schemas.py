from pydantic import BaseModel, EmailStr, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores/hyphens allowed)")
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be 3-50 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class SMTPSettings(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    smtp_from_name: str
    smtp_use_tls: bool = True
    imap_host: Optional[str] = None
    imap_port: int = 993
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None


# ─── Template Schemas ─────────────────────────────────────────────────────────

class TemplateCreate(BaseModel):
    name: str
    subject: str
    body: str


class EmailGenerationRequest(BaseModel):
    subject: str
    body: str


class TemplateResponse(BaseModel):
    id: str
    user_id: str
    name: str
    subject: str
    body: str
    is_ai_generated: bool
    variables: List[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Campaign Schemas ─────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    template_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    emails_per_hour: Optional[int] = None
    emails_per_day: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    emails_per_hour: Optional[int] = None
    emails_per_day: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class CampaignStats(BaseModel):
    total_contacts: int
    pending: int
    sent: int
    opened: int
    clicked: int
    replied: int
    failed: int
    open_rate: float
    click_rate: float
    reply_rate: float


class CampaignResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    status: str
    template_id: Optional[str]
    resume_path: Optional[str]
    sender_name: Optional[str]
    sender_email: Optional[str]
    emails_per_hour: Optional[int]
    emails_per_day: Optional[int]
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    ai_summary: Optional[str]
    created_at: datetime
    updated_at: datetime
    stats: Optional[CampaignStats] = None
    model_config = ConfigDict(from_attributes=True)


# ─── Contact Schemas ──────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    title: Optional[str] = None
    extra_data: Dict[str, Any] = {}


class ContactResponse(BaseModel):
    id: str
    campaign_id: str
    name: str
    email: str
    company: Optional[str]
    title: Optional[str]
    extra_data: Dict[str, Any]
    status: str
    open_count: int
    click_count: int
    has_replied: bool
    reply_at: Optional[datetime]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ContactFilter(BaseModel):
    company: Optional[str] = None
    status: Optional[str] = None
    has_replied: Optional[bool] = None
    opened: Optional[bool] = None
    clicked: Optional[bool] = None


# ─── Email Schemas ─────────────────────────────────────────────────────────────

class EmailResponse(BaseModel):
    id: str
    campaign_id: str
    contact_id: str
    subject: str
    body: str
    is_followup: bool
    followup_number: int
    status: str
    sent_at: Optional[datetime]
    open_count: int
    click_count: int
    first_opened_at: Optional[datetime]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GenerateEmailRequest(BaseModel):
    recruiter_name: str
    company: str
    title: str
    candidate_profile: str
    extra_context: Optional[Dict[str, Any]] = {}


class GeneratedEmail(BaseModel):
    subject: str
    body: str


# ─── Analytics Schemas ────────────────────────────────────────────────────────

class DailyStats(BaseModel):
    date: str
    sent: int
    opened: int
    clicked: int
    replied: int


class OverallAnalytics(BaseModel):
    total_campaigns: int
    total_contacts: int
    total_sent: int
    total_opened: int
    total_clicked: int
    total_replied: int
    overall_open_rate: float
    overall_click_rate: float
    overall_reply_rate: float
    daily_stats: List[DailyStats]
    top_companies: List[Dict[str, Any]]


class AIAnalyticsSummary(BaseModel):
    campaign_id: str
    summary: str
    generated_at: datetime


# ─── Upload Schemas ───────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    contacts_imported: int
    contacts_skipped: int
    columns_detected: List[str]
    custom_columns: List[str]
    errors: List[str]


# ─── Tracking Schemas ─────────────────────────────────────────────────────────

class TrackingEventResponse(BaseModel):
    id: str
    email_id: str
    event_type: str
    url: Optional[str]
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Audit Log Schemas ────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Export Schemas ───────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    campaign_id: str
    format: str  # csv, excel, pdf


# ─── Pagination ───────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int
