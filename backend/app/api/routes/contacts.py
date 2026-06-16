from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Campaign, Contact, Email
from app.schemas.schemas import ContactResponse, EmailResponse
from app.api.deps import get_current_user
from app.models.models import User

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("/{campaign_id}", response_model=List[ContactResponse])
def list_contacts(
    campaign_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    company: Optional[str] = None,
    status: Optional[str] = None,
    has_replied: Optional[bool] = None,
    opened: Optional[bool] = None,
    clicked: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ContactResponse]:
    # Verify campaign ownership
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    query = db.query(Contact).filter(Contact.campaign_id == campaign_id)

    if company:
        query = query.filter(Contact.company.ilike(f"%{company}%"))
    if status:
        query = query.filter(Contact.status == status)
    if has_replied is not None:
        query = query.filter(Contact.has_replied == has_replied)
    if opened is True:
        query = query.filter(Contact.open_count > 0)
    elif opened is False:
        query = query.filter(Contact.open_count == 0)
    if clicked is True:
        query = query.filter(Contact.click_count > 0)
    elif clicked is False:
        query = query.filter(Contact.click_count == 0)
    if search:
        query = query.filter(
            (Contact.name.ilike(f"%{search}%")) |
            (Contact.email.ilike(f"%{search}%")) |
            (Contact.company.ilike(f"%{search}%"))
        )

    contacts = query.order_by(Contact.created_at.desc()).offset(skip).limit(limit).all()
    return [ContactResponse.model_validate(c) for c in contacts]


@router.get("/{campaign_id}/{contact_id}", response_model=ContactResponse)
def get_contact(
    campaign_id: str,
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContactResponse:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.campaign_id == campaign_id,
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return ContactResponse.model_validate(contact)


@router.get("/{campaign_id}/{contact_id}/emails", response_model=List[EmailResponse])
def get_contact_emails(
    campaign_id: str,
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[EmailResponse]:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    emails = db.query(Email).filter(
        Email.contact_id == contact_id,
        Email.campaign_id == campaign_id,
    ).order_by(Email.created_at.asc()).all()

    return [EmailResponse.model_validate(e) for e in emails]


@router.delete("/{campaign_id}/{contact_id}", status_code=204)
def delete_contact(
    campaign_id: str,
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.campaign_id == campaign_id,
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()
