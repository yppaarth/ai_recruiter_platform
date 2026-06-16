from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.db.session import get_db
from app.models.models import Campaign
from app.api.deps import get_current_user
from app.models.models import User
from app.services.export_service import (
    export_campaign_csv,
    export_campaign_excel,
    export_campaign_pdf,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/campaign/{campaign_id}/csv")
def export_csv(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    content = export_campaign_csv(campaign_id, db)
    log_action(db, user_id=current_user.id, action="export",
               resource_type="campaign", resource_id=campaign_id,
               details={"format": "csv"})

    return StreamingResponse(
        io.BytesIO(content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=campaign_{campaign_id}.csv"
        },
    )


@router.get("/campaign/{campaign_id}/excel")
def export_excel(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    content = export_campaign_excel(campaign_id, db)
    log_action(db, user_id=current_user.id, action="export",
               resource_type="campaign", resource_id=campaign_id,
               details={"format": "excel"})

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=campaign_{campaign_id}.xlsx"
        },
    )


@router.get("/campaign/{campaign_id}/pdf")
def export_pdf(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    content = export_campaign_pdf(campaign_id, db)
    log_action(db, user_id=current_user.id, action="export",
               resource_type="campaign", resource_id=campaign_id,
               details={"format": "pdf"})

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=campaign_report_{campaign_id}.pdf"
        },
    )
