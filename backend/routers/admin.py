from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuditLog, Role, User
from ..schemas import AuditOut
from ..security import require_roles

router = APIRouter(prefix="/api/v1", tags=["admin"])


@router.get("/audit-logs", response_model=list[AuditOut])
def audit_logs(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.admin)),
):
    return db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
