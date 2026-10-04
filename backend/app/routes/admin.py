from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.config import STORAGE_PRIVATE_DIR
from backend.app.database import get_db
from backend.app.models.entities import (
    User, Property, VerificationDocument, PropertyReport, AuditLog,
    UserRole, IdentityStatus, ProfessionalStatus, ListingStatus
)
from backend.app.schemas.dtos import (
    PropertyPublicResponse, ReportResponse
)
from backend.app.security.auth_guard import require_admin
from backend.app.routes.properties import to_public_response

router = APIRouter(tags=["Admin Moderation & Audit"])

def log_admin_action(
    db: Session,
    admin: User,
    action: str,
    target_type: str,
    target_id: str,
    details: Optional[str] = None
):
    audit = AuditLog(
        actor_id=admin.id,
        actor_email=admin.email,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    db.add(audit)
    db.commit()

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    total_users = db.query(User).count()
    total_agents = db.query(User).filter(User.role == UserRole.AGENT).count()
    pending_verifications = db.query(VerificationDocument).filter(VerificationDocument.status == IdentityStatus.PENDING).count()
    pending_properties = db.query(Property).filter(Property.status == ListingStatus.PENDING_REVIEW).count()
    total_published = db.query(Property).filter(Property.status == ListingStatus.PUBLISHED).count()
    total_reports = db.query(PropertyReport).filter(PropertyReport.is_resolved == False).count()

    return {
        "total_users": total_users,
        "total_agents": total_agents,
        "pending_verifications": pending_verifications,
        "pending_properties": pending_properties,
        "total_published": total_published,
        "unresolved_reports": total_reports
    }

# ----------------- User Management -----------------
@router.get("/users")
def list_users(
    role: Optional[UserRole] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    users = q.order_by(User.created_at.desc()).limit(limit).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "identity_status": u.identity_status,
            "professional_status": u.professional_status,
            "is_suspended": u.is_suspended,
            "created_at": u.created_at
        }
        for u in users
    ]

@router.post("/users/{user_id}/toggle-suspend")
def toggle_user_suspension(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="لا يمكن تعليق حساب المشرف")

    user.is_suspended = not user.is_suspended
    db.commit()

    action = "SUSPEND_USER" if user.is_suspended else "UNSUSPEND_USER"
    log_admin_action(db, admin, action, "USER", user.id, f"Suspension toggled to {user.is_suspended}")

    return {"message": "تم تحديث حالة الحساب", "is_suspended": user.is_suspended}

# ----------------- Verification Review -----------------
@router.get("/verifications/pending")
def list_pending_verifications(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    docs = db.query(VerificationDocument).filter(
        VerificationDocument.status == IdentityStatus.PENDING
    ).order_by(VerificationDocument.created_at.asc()).all()

    return [
        {
            "id": d.id,
            "user_id": d.user_id,
            "user_email": d.user.email if d.user else "",
            "user_name": d.user.full_name if d.user else "",
            "user_role": d.user.role if d.user else "",
            "doc_type": d.doc_type,
            "status": d.status,
            "created_at": d.created_at
        }
        for d in docs
    ]

@router.get("/verifications/{doc_id}/view-file")
def view_sensitive_document(
    doc_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    doc = db.query(VerificationDocument).filter(VerificationDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="الوثيقة غير موجودة")

    file_path = STORAGE_PRIVATE_DIR / doc.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="ملف الوثيقة غير موجود على الخادم")

    # Mandatory security rule: Log every sensitive document access to AuditLog
    log_admin_action(
        db, admin, "VIEW_SENSITIVE_DOCUMENT", "DOCUMENT", doc.id,
        f"Admin viewed document {doc.doc_type} for user {doc.user_id}"
    )

    return FileResponse(file_path)

@router.post("/verifications/{doc_id}/decide")
def decide_verification_document(
    doc_id: str,
    decision: IdentityStatus,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    doc = db.query(VerificationDocument).filter(VerificationDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="الوثيقة غير موجودة")

    doc.status = decision
    doc.reviewer_notes = notes

    # Reflect decision in user's profile depending on doc type
    user = doc.user
    if user:
        if doc.doc_type == "NATIONAL_ID":
            user.identity_status = decision
        else:
            user.professional_status = ProfessionalStatus.VERIFIED if decision == IdentityStatus.APPROVED else ProfessionalStatus.REJECTED

    db.commit()

    log_admin_action(
        db, admin, f"DECIDE_VERIFICATION_{decision.value}", "DOCUMENT", doc.id,
        f"Decision: {decision.value}, User: {user.email if user else ''}, Notes: {notes}"
    )

    return {"message": "تم اعتماد قرار التوثيق بنجاح", "status": decision}

# ----------------- Property Moderation -----------------
@router.get("/properties/pending", response_model=List[PropertyPublicResponse])
def list_pending_properties(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    props = db.query(Property).filter(
        Property.status == ListingStatus.PENDING_REVIEW
    ).order_by(Property.created_at.asc()).all()
    return [to_public_response(p) for p in props]

@router.post("/properties/{property_id}/publish")
def publish_property(
    property_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="العقار غير موجود")

    prop.status = ListingStatus.PUBLISHED
    db.commit()

    log_admin_action(db, admin, "PUBLISH_PROPERTY", "PROPERTY", prop.id, f"Published listing: {prop.title}")
    return {"message": "تم اعتماد ونشر الإعلان بنجاح", "status": prop.status}

@router.post("/properties/{property_id}/reject")
def reject_property(
    property_id: str,
    reason: Optional[str] = "مخالفة معايير الدقة العقارية",
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="العقار غير موجود")

    prop.status = ListingStatus.REJECTED
    db.commit()

    log_admin_action(db, admin, "REJECT_PROPERTY", "PROPERTY", prop.id, f"Reason: {reason}")
    return {"message": "تم رفض الإعلان", "status": prop.status}

# ----------------- Reports -----------------
@router.get("/reports", response_model=List[ReportResponse])
def list_reports(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    reports = db.query(PropertyReport).order_by(PropertyReport.created_at.desc()).all()
    return [
        ReportResponse(
            id=r.id,
            reporter_id=r.reporter_id,
            property_id=r.property_id,
            property_title=r.property.title if r.property else "عقار",
            reason=r.reason,
            details=r.details,
            is_resolved=r.is_resolved,
            created_at=r.created_at
        )
        for r in reports
    ]

# ----------------- Audit Logs -----------------
@router.get("/audit-logs")
def list_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "actor_email": l.actor_email,
            "action": l.action,
            "target_type": l.target_type,
            "target_id": l.target_id,
            "details": l.details,
            "created_at": l.created_at
        }
        for l in logs
    ]
