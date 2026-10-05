from typing import Optional, List
from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.entities import User, UserRole
from backend.app.schemas.dtos import (
    PropertyPublicResponse, PropertyDetailResponse, PropertyCreateRequest,
    PropertyUpdateRequest, PropertyImageDto, PropertyComparisonItem, FavoriteResponse
)
from backend.app.security.auth_guard import (
    get_current_user, get_current_user_optional, require_role
)
from backend.app.services.property_service import PropertyService

router = APIRouter(tags=["Properties"])

# Backward compatibility alias for other modules importing to_public_response
to_public_response = PropertyService.to_public_response

@router.get("", response_model=List[PropertyPublicResponse])
def get_properties(
    city: Optional[str] = Query(None, description="طنطا، المحلة الكبرى، زفتى"),
    district: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None,
    finishing: Optional[str] = None,
    elevator: Optional[bool] = None,
    parking: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = Query("newest", pattern="^(newest|price_asc|price_desc|area_desc)$"),
    limit: int = Query(50, ge=1, le=100, description="عدد النتائج في الصفحة"),
    offset: int = Query(0, ge=0, description="إزاحة البداية"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    return PropertyService.get_properties(
        db=db,
        city=city,
        district=district,
        min_price=min_price,
        max_price=max_price,
        min_area=min_area,
        max_area=max_area,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        finishing=finishing,
        elevator=elevator,
        parking=parking,
        search=search,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
        current_user=current_user
    )

@router.get("/compare", response_model=List[PropertyComparisonItem])
def compare_properties(
    ids: str = Query(..., description="معرفات العقارات مفصولة بفاصلة (2 إلى 4 عقارات)"),
    db: Session = Depends(get_db)
):
    return PropertyService.compare_properties(db, ids)

# ----------------- Favorites Endpoints -----------------
@router.get("/favorites", response_model=List[PropertyPublicResponse])
def list_my_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return PropertyService.list_favorites(db, current_user)

@router.post("/{property_id}/favorite", response_model=FavoriteResponse)
def toggle_favorite_property(
    property_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return PropertyService.toggle_favorite(db, property_id, current_user)

# ----------------- Property Detail & CRUD -----------------
@router.get("/{property_id}", response_model=PropertyDetailResponse)
def get_property_detail(
    property_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    return PropertyService.get_property_detail(db, property_id, current_user)

@router.post("", response_model=PropertyPublicResponse, status_code=status.HTTP_201_CREATED)
def create_property(
    payload: PropertyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.AGENT, UserRole.ADMIN))
):
    return PropertyService.create_property(db, payload, current_user)

@router.patch("/{property_id}", response_model=PropertyPublicResponse)
def update_property(
    property_id: str,
    payload: PropertyUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return PropertyService.update_property(db, property_id, payload, current_user)

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    property_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    PropertyService.delete_property(db, property_id, current_user)
    return None

# ----------------- Property Images -----------------
@router.post("/{property_id}/images", response_model=PropertyImageDto)
def upload_property_image(
    property_id: str,
    file: UploadFile = File(...),
    is_primary: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return PropertyService.upload_property_image(db, property_id, file, is_primary, current_user)

@router.delete("/{property_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property_image(
    property_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    PropertyService.delete_property_image(db, property_id, image_id, current_user)
    return None
