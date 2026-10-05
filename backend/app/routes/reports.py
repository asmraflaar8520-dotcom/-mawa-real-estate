from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.entities import Property, PropertyReport, User
from backend.app.schemas.dtos import ReportCreateRequest, ReportResponse
from backend.app.security.auth_guard import get_current_user, rate_limit

router = APIRouter(tags=["Reporting & Anti-Fraud"])

@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))]
)
def submit_report(
    payload: ReportCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prop = db.query(Property).filter(Property.id == payload.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="العقار المطلوب الإبلاغ عنه غير موجود")

    report = PropertyReport(
        reporter_id=current_user.id,
        property_id=payload.property_id,
        reason=payload.reason,
        details=payload.details
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportResponse(
        id=report.id,
        reporter_id=report.reporter_id,
        property_id=report.property_id,
        property_title=prop.title,
        reason=report.reason,
        details=report.details,
        is_resolved=report.is_resolved,
        created_at=report.created_at
    )
