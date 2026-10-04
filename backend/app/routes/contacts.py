from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.entities import (
    ContactRequest, Property, User, UserRole, ViewingStatus
)
from backend.app.schemas.dtos import (
    ContactRequestCreate, ContactRequestStatusUpdate, ContactRequestResponse
)
from backend.app.security.auth_guard import get_current_user

router = APIRouter(prefix="/api/contact-requests", tags=["Contacts & Viewing Requests"])

def to_contact_response(req: ContactRequest) -> ContactRequestResponse:
    return ContactRequestResponse(
        id=req.id,
        property_id=req.property_id,
        property_title=req.property.title if req.property else "عقار",
        property_city=req.property.city if req.property else "",
        property_district=req.property.district if req.property else "",
        buyer_id=req.buyer_id,
        buyer_name=req.buyer.full_name if req.buyer else "",
        agent_id=req.agent_id,
        agent_name=req.agent.full_name if req.agent else "",
        status=req.status,
        buyer_message=req.buyer_message,
        agent_response=req.agent_response,
        proposed_date=req.proposed_date,
        created_at=req.created_at,
        updated_at=req.updated_at
    )

@router.post("", response_model=ContactRequestResponse, status_code=status.HTTP_201_CREATED)
def create_contact_request(
    payload: ContactRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prop = db.query(Property).filter(Property.id == payload.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="العقار غير موجود")

    if current_user.id == prop.agent_id:
        raise HTTPException(status_code=400, detail="لا يمكنك إرسال طلب معاينة لعقارك الخاص")

    # Check if existing active request exists
    existing = db.query(ContactRequest).filter(
        ContactRequest.property_id == prop.id,
        ContactRequest.buyer_id == current_user.id,
        ContactRequest.status.in_([ViewingStatus.VIEWING_REQUESTED, ViewingStatus.VIEWING_AGREED])
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="لديك طلب معاينة قائم بالفعل لهذا العقار"
        )

    req = ContactRequest(
        property_id=prop.id,
        buyer_id=current_user.id,
        agent_id=prop.agent_id,
        status=ViewingStatus.VIEWING_REQUESTED,
        buyer_message=payload.buyer_message,
        proposed_date=payload.proposed_date
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return to_contact_response(req)

@router.get("", response_model=List[ContactRequestResponse])
def get_my_contact_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Returns requests where current_user is buyer OR agent OR all if admin
    if current_user.role == UserRole.ADMIN:
        requests = db.query(ContactRequest).order_by(ContactRequest.created_at.desc()).all()
    elif current_user.role == UserRole.AGENT:
        requests = db.query(ContactRequest).filter(
            (ContactRequest.agent_id == current_user.id) | (ContactRequest.buyer_id == current_user.id)
        ).order_by(ContactRequest.created_at.desc()).all()
    else:
        requests = db.query(ContactRequest).filter(
            ContactRequest.buyer_id == current_user.id
        ).order_by(ContactRequest.created_at.desc()).all()

    return [to_contact_response(r) for r in requests]

@router.get("/{request_id}", response_model=ContactRequestResponse)
def get_contact_request_by_id(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = db.query(ContactRequest).filter(ContactRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")

    # Strict BOLA / IDOR Verification
    # Only buyer who created it, responsible agent, or admin can access
    if current_user.id != req.buyer_id and current_user.id != req.agent_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="غير مصرح لك باستعراض بيانات هذا الطلب"
        )

    return to_contact_response(req)

@router.patch("/{request_id}/status", response_model=ContactRequestResponse)
def update_contact_request_status(
    request_id: str,
    payload: ContactRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = db.query(ContactRequest).filter(ContactRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")

    # Strict BOLA / IDOR Verification
    is_agent = current_user.id == req.agent_id
    is_buyer = current_user.id == req.buyer_id
    is_admin = current_user.role == UserRole.ADMIN

    if not (is_agent or is_buyer or is_admin):
        raise HTTPException(status_code=403, detail="غير مصرح لك بتعديل حالة هذا الطلب")

    # Buyers can only cancel their own request
    if is_buyer and not (is_agent or is_admin):
        if payload.status != ViewingStatus.CANCELLED:
            raise HTTPException(status_code=403, detail="يمكن للمشتري فقط إلغاء طلبه")
        req.status = ViewingStatus.CANCELLED
    else:
        # Agent or Admin can Accept, Reject, or Cancel
        req.status = payload.status
        if payload.agent_response:
            req.agent_response = payload.agent_response

    db.commit()
    db.refresh(req)
    return to_contact_response(req)
