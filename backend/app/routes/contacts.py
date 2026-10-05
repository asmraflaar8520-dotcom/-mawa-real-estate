from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.entities import User
from backend.app.schemas.dtos import (
    ContactRequestCreate, ContactRequestStatusUpdate, ContactRequestResponse
)
from backend.app.security.auth_guard import get_current_user
from backend.app.services.contact_service import ContactService

router = APIRouter(tags=["Contacts & Viewing Requests"])

# Backward compatibility alias
to_contact_response = ContactService.to_contact_response

@router.post("", response_model=ContactRequestResponse, status_code=status.HTTP_201_CREATED)
def create_contact_request(
    payload: ContactRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ContactService.create_contact_request(db, payload, current_user)

@router.get("", response_model=List[ContactRequestResponse])
def get_my_contact_requests(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ContactService.get_my_contact_requests(db, current_user, limit=limit, offset=offset)

@router.get("/{request_id}", response_model=ContactRequestResponse)
def get_contact_request_by_id(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ContactService.get_contact_request_by_id(db, request_id, current_user)

@router.patch("/{request_id}/status", response_model=ContactRequestResponse)
def update_contact_request_status(
    request_id: str,
    payload: ContactRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ContactService.update_contact_request_status(db, request_id, payload, current_user)

