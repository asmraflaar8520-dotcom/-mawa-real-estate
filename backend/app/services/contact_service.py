from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from backend.app.models.entities import (
    ContactRequest, Property, User, UserRole, ViewingStatus
)
from backend.app.schemas.dtos import (
    ContactRequestCreate, ContactRequestStatusUpdate, ContactRequestResponse
)

class ContactService:

    @staticmethod
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

    @classmethod
    def create_contact_request(
        cls,
        db: Session,
        payload: ContactRequestCreate,
        current_user: User
    ) -> ContactRequestResponse:
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

        # Reload with relationships for clean DTO formatting
        reloaded = db.query(ContactRequest).options(
            joinedload(ContactRequest.property),
            joinedload(ContactRequest.buyer),
            joinedload(ContactRequest.agent)
        ).filter(ContactRequest.id == req.id).first()

        return cls.to_contact_response(reloaded or req)

    @classmethod
    def get_my_contact_requests(
        cls,
        db: Session,
        current_user: User,
        limit: int = 50,
        offset: int = 0
    ) -> List[ContactRequestResponse]:
        query = db.query(ContactRequest).options(
            joinedload(ContactRequest.property),
            joinedload(ContactRequest.buyer),
            joinedload(ContactRequest.agent)
        )

        if current_user.role == UserRole.ADMIN:
            requests = query.order_by(ContactRequest.created_at.desc()).offset(offset).limit(limit).all()
        elif current_user.role == UserRole.AGENT:
            requests = query.filter(
                (ContactRequest.agent_id == current_user.id) | (ContactRequest.buyer_id == current_user.id)
            ).order_by(ContactRequest.created_at.desc()).offset(offset).limit(limit).all()
        else:
            requests = query.filter(
                ContactRequest.buyer_id == current_user.id
            ).order_by(ContactRequest.created_at.desc()).offset(offset).limit(limit).all()

        return [cls.to_contact_response(r) for r in requests]

    @classmethod
    def get_contact_request_by_id(
        cls,
        db: Session,
        request_id: str,
        current_user: User
    ) -> ContactRequestResponse:
        req = db.query(ContactRequest).options(
            joinedload(ContactRequest.property),
            joinedload(ContactRequest.buyer),
            joinedload(ContactRequest.agent)
        ).filter(ContactRequest.id == request_id).first()

        if not req:
            raise HTTPException(status_code=404, detail="الطلب غير موجود")

        # Strict BOLA / IDOR Verification
        if current_user.id != req.buyer_id and current_user.id != req.agent_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح لك باستعراض بيانات هذا الطلب"
            )

        return cls.to_contact_response(req)

    @classmethod
    def update_contact_request_status(
        cls,
        db: Session,
        request_id: str,
        payload: ContactRequestStatusUpdate,
        current_user: User
    ) -> ContactRequestResponse:
        req = db.query(ContactRequest).options(
            joinedload(ContactRequest.property),
            joinedload(ContactRequest.buyer),
            joinedload(ContactRequest.agent)
        ).filter(ContactRequest.id == request_id).first()

        if not req:
            raise HTTPException(status_code=404, detail="الطلب غير موجود")

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
            req.status = payload.status
            if payload.agent_response:
                req.agent_response = payload.agent_response

        db.commit()
        db.refresh(req)
        return cls.to_contact_response(req)
