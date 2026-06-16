import uuid
import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import EmailTemplate
from app.schemas.schemas import TemplateCreate, TemplateResponse
from app.api.deps import get_current_user
from app.models.models import User

router = APIRouter(prefix="/templates", tags=["Email Templates"])


def detect_variables(body: str, subject: str) -> List[str]:
    """Detect Jinja2-style variables in template."""
    pattern = r"\{\{(\w+)\}\}"
    vars_in_body = re.findall(pattern, body)
    vars_in_subject = re.findall(pattern, subject)
    return list(set(vars_in_body + vars_in_subject))


@router.get("/", response_model=List[TemplateResponse])
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TemplateResponse]:
    templates = (
        db.query(EmailTemplate)
        .filter(EmailTemplate.user_id == current_user.id)
        .order_by(EmailTemplate.created_at.desc())
        .all()
    )
    return [TemplateResponse.model_validate(t) for t in templates]


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    variables = detect_variables(payload.body, payload.subject)
    template = EmailTemplate(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=payload.name,
        subject=payload.subject,
        body=payload.body,
        variables=variables,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return TemplateResponse.model_validate(template)


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.user_id == current_user.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: str,
    payload: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.user_id == current_user.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.name = payload.name
    template.subject = payload.subject
    template.body = payload.body
    template.variables = detect_variables(payload.body, payload.subject)
    db.commit()
    db.refresh(template)
    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.user_id == current_user.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
