from typing import List, Optional
from pathlib import Path
from fastapi import HTTPException, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from backend.app.config import STORAGE_PRIVATE_DIR, USE_SUPABASE_STORAGE
from backend.app.security.storage import fetch_private_document_content
from backend.app.models.entities import (
    User, Property, VerificationDocument, PropertyReport, AuditLog,
    UserRole, IdentityStatus, ProfessionalStatus, ListingStatus, DocumentType
)
from backend.app.schemas.dtos import PropertyPublicResponse, ReportResponse
from backend.app.services.property_service import PropertyService

class AdminService:

    @staticmethod
    def log_admin_action(
        db: Session,
        admin: User,
        action: str,
        target_type: str,
        target_id: str,
        details: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        audit = AuditLog(
            actor_id=admin.id,
            actor_email=admin.email,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address
        )
        db.add(audit)
        db.commit()

    @classmethod
    def get_dashboard_stats(cls, db: Session) -> dict:
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

    @classmethod
    def list_users(cls, db: Session, role: Optional[UserRole] = None, limit: int = 50, offset: int = 0) -> list:
        q = db.query(User)
        if role:
            q = q.filter(User.role == role)
        users = q.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
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

    @classmethod
    def toggle_user_suspension(cls, db: Session, user_id: str, admin: User) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        if user.role == UserRole.ADMIN:
            raise HTTPException(status_code=400, detail="لا يمكن تعليق حساب المشرف")

        user.is_suspended = not user.is_suspended
        db.commit()

        action = "SUSPEND_USER" if user.is_suspended else "UNSUSPEND_USER"
        cls.log_admin_action(db, admin, action, "USER", user.id, f"Suspension toggled to {user.is_suspended}")

        return {"message": "تم تحديث حالة الحساب", "is_suspended": user.is_suspended}

    @classmethod
    def list_pending_verifications(cls, db: Session) -> list:
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

    @classmethod
    def view_sensitive_document(cls, db: Session, doc_id: str, admin: User):
        doc = db.query(VerificationDocument).filter(VerificationDocument.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="الوثيقة غير موجودة")

        # 1. Fetch from Supabase Cloud Storage if configured
        if USE_SUPABASE_STORAGE:
            doc_data = fetch_private_document_content(doc.file_path)
            if doc_data:
                content_bytes, ctype = doc_data
                cls.log_admin_action(
                    db, admin, "VIEW_SENSITIVE_DOCUMENT", "DOCUMENT", doc.id,
                    f"Admin viewed document {doc.doc_type} for user {doc.user_id}"
                )
                return Response(
                    content=content_bytes,
                    media_type=ctype,
                    headers={"Content-Disposition": f"inline; filename=doc_{doc.id[:8]}.pdf"}
                )

        # 2. Local filesystem fallback
        file_path = STORAGE_PRIVATE_DIR / doc.file_path
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="ملف الوثيقة غير موجود على الخادم")

        # Mandatory security rule: Log every sensitive document access to AuditLog
        cls.log_admin_action(
            db, admin, "VIEW_SENSITIVE_DOCUMENT", "DOCUMENT", doc.id,
            f"Admin viewed document {doc.doc_type} for user {doc.user_id}"
        )

        return FileResponse(
            path=str(file_path),
            headers={"Content-Disposition": f"inline; filename=doc_{doc.id[:8]}.pdf"}
        )

    @classmethod
    def decide_verification_document(
        cls,
        db: Session,
        doc_id: str,
        decision: IdentityStatus,
        notes: Optional[str],
        admin: User
    ) -> dict:
        doc = db.query(VerificationDocument).filter(VerificationDocument.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="الوثيقة غير موجودة")

        doc.status = decision
        doc.reviewer_notes = notes

        # Reflect decision in user profile
        user = doc.user
        if user:
            is_national_id = doc.doc_type in (DocumentType.NATIONAL_ID, "NATIONAL_ID")
            if is_national_id:
                user.identity_status = decision
            else:
                user.professional_status = ProfessionalStatus.VERIFIED if decision == IdentityStatus.APPROVED else ProfessionalStatus.REJECTED

        db.commit()

        cls.log_admin_action(
            db, admin, f"DECIDE_VERIFICATION_{decision.value}", "DOCUMENT", doc.id,
            f"Decision: {decision.value}, User: {user.email if user else ''}, Notes: {notes}"
        )

        return {"message": "تم اعتماد قرار التوثيق بنجاح", "status": decision}

    @classmethod
    def list_pending_properties(cls, db: Session) -> List[PropertyPublicResponse]:
        props = db.query(Property).filter(
            Property.status == ListingStatus.PENDING_REVIEW
        ).order_by(Property.created_at.asc()).all()
        return [PropertyService.to_public_response(p) for p in props]

    @classmethod
    def publish_property(cls, db: Session, property_id: str, admin: User) -> dict:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="العقار غير موجود")

        prop.status = ListingStatus.PUBLISHED
        db.commit()

        cls.log_admin_action(db, admin, "PUBLISH_PROPERTY", "PROPERTY", prop.id, f"Published listing: {prop.title}")
        return {"message": "تم اعتماد ونشر الإعلان بنجاح", "status": prop.status}

    @classmethod
    def reject_property(cls, db: Session, property_id: str, reason: Optional[str], admin: User) -> dict:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="العقار غير موجود")

        prop.status = ListingStatus.REJECTED
        db.commit()

        cls.log_admin_action(db, admin, "REJECT_PROPERTY", "PROPERTY", prop.id, f"Reason: {reason}")
        return {"message": "تم رفض الإعلان", "status": prop.status}

    @classmethod
    def list_reports(cls, db: Session, limit: int = 50, offset: int = 0) -> List[ReportResponse]:
        reports = db.query(PropertyReport).order_by(PropertyReport.created_at.desc()).offset(offset).limit(limit).all()
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

    @classmethod
    def resolve_report(cls, db: Session, report_id: str, admin: User) -> dict:
        report = db.query(PropertyReport).filter(PropertyReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="البلاغ غير موجود")

        report.is_resolved = True
        db.commit()

        cls.log_admin_action(
            db, admin, "RESOLVE_REPORT", "REPORT", report.id,
            f"Resolved report against property {report.property_id}"
        )
        return {"message": "تم إغلاق وحل البلاغ بنجاح", "is_resolved": True}

    @classmethod
    def list_audit_logs(cls, db: Session, limit: int = 100, offset: int = 0) -> list:
        logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
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
