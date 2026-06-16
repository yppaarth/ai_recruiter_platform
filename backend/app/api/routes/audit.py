from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import AuditLog
from app.schemas.schemas import AuditLogResponse
from app.api.deps import get_current_user
from app.models.models import User

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/", response_model=List[AuditLogResponse])
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AuditLogResponse]:
    query = db.query(AuditLog).filter(AuditLog.user_id == current_user.id)
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return [AuditLogResponse.model_validate(log) for log in logs]
