from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.entities import (
    User, VerificationDocument, DocumentType, IdentityStatus, ProfessionalStatus, UserRole
)
from backend.app.security.auth_guard import get_current_user
from backend.app.security.storage import validate_and_save_private_document

router = APIRouter(prefix="/api/verifications", tags=["Verifications & Trust"])

@router.post("/identity")
def upload_identity_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Store in private isolated storage
    saved_filename = validate_and_save_private_document(file)

    doc = VerificationDocument(
        user_id=current_user.id,
        doc_type=DocumentType.NATIONAL_ID,
        file_path=saved_filename,
        status=IdentityStatus.PENDING
    )
    db.add(doc)
    current_user.identity_status = IdentityStatus.PENDING
    db.commit()

    # Never return the document URL or file path to frontend - only return the new status
    return {
        "message": "تم استلام وثيقة إثبات الهوية بنجاح وجارٍ مراجعتها بدقة وأمان من فريق مأوى",
        "identity_status": current_user.identity_status
    }

@router.post("/professional")
def upload_professional_license(
    doc_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.AGENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="التقديم على الاعتماد المهني متاح لحسابات الوسطاء العقاريين فقط"
        )

    saved_filename = validate_and_save_private_document(file)

    doc = VerificationDocument(
        user_id=current_user.id,
        doc_type=doc_type,
        file_path=saved_filename,
        status=IdentityStatus.PENDING
    )
    db.add(doc)
    current_user.professional_status = ProfessionalStatus.PENDING
    db.commit()

    return {
        "message": "تم استلام وثائق السجل التجاري / الترخيص المهني وجارٍ التدقيق الفني",
        "professional_status": current_user.professional_status
    }

@router.get("/status")
def get_verification_status(current_user: User = Depends(get_current_user)):
    return {
        "identity_status": current_user.identity_status,
        "professional_status": current_user.professional_status
    }
