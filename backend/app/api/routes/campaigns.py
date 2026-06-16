import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.models import Campaign, Contact, Email, EmailStatus, CampaignStatus
from app.schemas.schemas import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignStats,
    EmailGenerationRequest,
)
from app.api.deps import get_current_user
from app.models.models import User
from app.services.audit_service import log_action
from app.tasks.email_tasks import launch_campaign, generate_campaign_emails
from app.tasks.analytics_tasks import generate_campaign_ai_summary

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def compute_stats(campaign_id: str, db: Session) -> CampaignStats:
    contacts = db.query(Contact).filter(Contact.campaign_id == campaign_id).all()
    total = len(contacts)
    pending = sum(1 for c in contacts if c.status == "pending")
    sent = sum(1 for c in contacts if c.status not in ("pending", "failed"))
    opened = sum(1 for c in contacts if c.open_count > 0)
    clicked = sum(1 for c in contacts if c.click_count > 0)
    replied = sum(1 for c in contacts if c.has_replied)
    failed = sum(1 for c in contacts if c.status == "failed")
    return CampaignStats(
        total_contacts=total,
        pending=pending,
        sent=sent,
        opened=opened,
        clicked=clicked,
        replied=replied,
        failed=failed,
        open_rate=opened / max(sent, 1) * 100,
        click_rate=clicked / max(sent, 1) * 100,
        reply_rate=replied / max(sent, 1) * 100,
    )


@router.get("/", response_model=List[CampaignResponse])
def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CampaignResponse]:
    query = db.query(Campaign).filter(Campaign.user_id == current_user.id)
    if status:
        query = query.filter(Campaign.status == status)
    campaigns = query.order_by(Campaign.created_at.desc()).offset(skip).limit(limit).all()
    results = []
    for c in campaigns:
        resp = CampaignResponse.model_validate(c)
        resp.stats = compute_stats(c.id, db)
        results.append(resp)
    return results


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignResponse:
    campaign = Campaign(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        template_id=payload.template_id,
        sender_name=payload.sender_name,
        sender_email=payload.sender_email,
        emails_per_hour=payload.emails_per_hour,
        emails_per_day=payload.emails_per_day,
        scheduled_at=payload.scheduled_at,
        status=CampaignStatus.DRAFT.value,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    log_action(
        db, user_id=current_user.id, action="campaign_create",
        resource_type="campaign", resource_id=campaign.id,
        details={"name": campaign.name},
    )
    resp = CampaignResponse.model_validate(campaign)
    resp.stats = compute_stats(campaign.id, db)
    return resp


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignResponse:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    resp = CampaignResponse.model_validate(campaign)
    resp.stats = compute_stats(campaign.id, db)
    return resp


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: str,
    payload: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignResponse:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    db.commit()
    db.refresh(campaign)

    log_action(
        db, user_id=current_user.id, action="campaign_update",
        resource_type="campaign", resource_id=campaign.id,
    )
    resp = CampaignResponse.model_validate(campaign)
    resp.stats = compute_stats(campaign.id, db)
    return resp


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    log_action(
        db, user_id=current_user.id, action="campaign_delete",
        resource_type="campaign", resource_id=campaign.id,
    )
    db.delete(campaign)
    db.commit()


@router.post("/{campaign_id}/generate-emails")
def generate_emails(
    campaign_id: str,
    payload: EmailGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if not payload.subject.strip() or not payload.body.strip():
        raise HTTPException(status_code=400, detail="Subject and body are required")

    task = generate_campaign_emails.delay(
        campaign_id,
        current_user.id,
        payload.subject,
        payload.body,
    )
    return {"message": "Email generation started", "task_id": task.id}


@router.post("/{campaign_id}/launch")
def launch(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status not in ("draft", "scheduled", "paused"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot launch campaign with status: {campaign.status}",
        )

    # Check there are emails to send
    email_count = db.query(Email).filter(
        Email.campaign_id == campaign_id,
        Email.is_followup == False,
    ).count()
    if email_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No emails generated yet. Generate emails first.",
        )

    task = launch_campaign.delay(campaign_id, current_user.id)
    return {"message": "Campaign launched", "task_id": task.id}


@router.post("/{campaign_id}/pause")
def pause_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != "running":
        raise HTTPException(status_code=400, detail="Campaign is not running")
    campaign.status = CampaignStatus.PAUSED.value
    db.commit()
    return {"message": "Campaign paused"}


@router.post("/{campaign_id}/resume")
def resume_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != "paused":
        raise HTTPException(status_code=400, detail="Campaign is not paused")
    campaign.status = CampaignStatus.RUNNING.value
    db.commit()
    task = launch_campaign.delay(campaign_id, current_user.id)
    return {"message": "Campaign resumed", "task_id": task.id}


@router.post("/{campaign_id}/clone", response_model=CampaignResponse)
def clone_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignResponse:
    original = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not original:
        raise HTTPException(status_code=404, detail="Campaign not found")

    clone = Campaign(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=f"Copy of {original.name}",
        description=original.description,
        template_id=original.template_id,
        sender_name=original.sender_name,
        sender_email=original.sender_email,
        emails_per_hour=original.emails_per_hour,
        emails_per_day=original.emails_per_day,
        status=CampaignStatus.DRAFT.value,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)

    resp = CampaignResponse.model_validate(clone)
    resp.stats = compute_stats(clone.id, db)
    return resp


@router.post("/{campaign_id}/ai-summary")
def trigger_ai_summary(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    task = generate_campaign_ai_summary.delay(campaign_id)
    return {"message": "AI summary generation started", "task_id": task.id}
