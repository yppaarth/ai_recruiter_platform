import uuid
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Campaign, Contact
from app.schemas.schemas import UploadResponse
from app.api.deps import get_current_user
from app.models.models import User
from app.services.upload_service import parse_contacts_file
from app.services.audit_service import log_action
from app.core.config import settings

router = APIRouter(prefix="/upload", tags=["Upload"])

ALLOWED_CONTACT_TYPES = {".csv", ".xlsx", ".xls"}
ALLOWED_RESUME_TYPES = {".pdf"}


def ensure_upload_dir() -> Path:
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def safe_upload_filename(filename: str, fallback: str) -> str:
    """Keep the uploaded basename while preventing path traversal."""
    safe_name = Path(filename.replace("\\", "/")).name.strip()
    return safe_name or fallback


@router.post("/contacts/{campaign_id}", response_model=UploadResponse)
async def upload_contacts(
    campaign_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    """Upload an Excel or CSV file of contacts for a campaign."""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_CONTACT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_CONTACT_TYPES)}",
        )

    # Check file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    try:
        contacts_data, all_columns, errors = parse_contacts_file(content, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    standard_cols = {"name", "email", "company", "title"}
    custom_columns = [col for col in all_columns if col not in standard_cols]

    imported = 0
    skipped = 0

    for contact_data in contacts_data:
        # Check if contact already exists in this campaign
        existing = db.query(Contact).filter(
            Contact.campaign_id == campaign_id,
            Contact.email == contact_data["email"],
        ).first()

        if existing:
            skipped += 1
            continue

        contact = Contact(
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            **contact_data,
        )
        db.add(contact)
        imported += 1

    db.commit()

    log_action(
        db,
        user_id=current_user.id,
        action="contacts_uploaded",
        resource_type="campaign",
        resource_id=campaign_id,
        details={
            "imported": imported,
            "skipped": skipped,
            "filename": filename,
        },
    )

    return UploadResponse(
        contacts_imported=imported,
        contacts_skipped=skipped,
        columns_detected=all_columns,
        custom_columns=custom_columns,
        errors=errors[:20],  # Limit error messages returned
    )


@router.post("/resume/{campaign_id}")
async def upload_resume(
    campaign_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload a PDF resume for a campaign."""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    filename = safe_upload_filename(file.filename or "resume.pdf", "resume.pdf")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_RESUME_TYPES:
        raise HTTPException(status_code=400, detail="Resume must be a PDF file")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    upload_dir = ensure_upload_dir() / "resumes" / current_user.id / campaign_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / filename

    # Delete old resume if exists
    if campaign.resume_path:
        old_path = Path(campaign.resume_path)
        if old_path.exists() and old_path != file_path:
            old_path.unlink()

    with open(file_path, "wb") as f:
        f.write(content)

    campaign.resume_path = str(file_path)
    db.commit()

    return {
        "message": "Resume uploaded successfully",
        "filename": filename,
        "path": str(file_path),
    }
