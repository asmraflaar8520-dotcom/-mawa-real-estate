from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.entities import User, UserRole, IdentityStatus
from backend.app.schemas.dtos import PropertyPublicResponse, ReportResponse
from backend.app.security.auth_guard import require_admin
from backend.app.services.admin_service import AdminService

router = APIRouter(tags=["Admin Moderation & Audit"])

# Backward compatibility alias
log_admin_action = AdminService.log_admin_action

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return AdminService.get_dashboard_stats(db)

# ----------------- User Management -----------------
@router.get("/users")
def list_users(
    role: Optional[UserRole] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return AdminService.list_users(db, role=role, limit=limit, offset=offset)

@router.post("/users/{user_id}/toggle-suspend")
def toggle_user_suspension(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return AdminService.toggle_user_suspension(db, user_id, admin)

# ----------------- Verification Review -----------------
@router.get("/verifications/pending")
def list_pending_verifications(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return AdminService.list_pending_verifications(db)

@router.get("/verifications/{doc_id}/view-file")
def view_sensitive_document(
    doc_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return AdminService.view_sensitive_document(db, doc_id, admin)

@router.post("/verifications/{doc_id}/decide")
def decide_verification_document(
    doc_id: str,
    decision: IdentityStatus,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return AdminService.decide_verification_document(db, doc_id, decision, notes, admin)

# ----------------- Property Moderation -----------------
@router.get("/properties/pending", response_model=List[PropertyPublicResponse])
def list_pending_properties(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return AdminService.list_pending_properties(db)

@router.post("/properties/{property_id}/publish")
def publish_property(
    property_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return AdminService.publish_property(db, property_id, admin)

@router.post("/properties/{property_id}/reject")
def reject_property(
    property_id: str,
    reason: Optional[str] = "مخالفة معايير الدقة العقارية",
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return AdminService.reject_property(db, property_id, reason, admin)

# ----------------- Reports -----------------
@router.get("/reports", response_model=List[ReportResponse])
def list_reports(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return AdminService.list_reports(db, limit=limit, offset=offset)

@router.patch("/reports/{report_id}/resolve")
def resolve_report(
    report_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return AdminService.resolve_report(db, report_id, admin)

# ----------------- Audit Logs -----------------
@router.get("/audit-logs")
def list_audit_logs(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return AdminService.list_audit_logs(db, limit=limit, offset=offset)

