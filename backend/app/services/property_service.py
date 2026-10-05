import os
from typing import Optional, List
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from backend.app.models.entities import (
    Property, PropertyImage, User, UserRole, ListingStatus,
    ContactRequest, ViewingStatus, Favorite, IdentityStatus, ProfessionalStatus
)
from backend.app.schemas.dtos import (
    PropertyPublicResponse, PropertyDetailResponse, PropertyCreateRequest,
    PropertyUpdateRequest, PropertyImageDto, PropertyComparisonItem, FavoriteResponse
)
from backend.app.security.storage import validate_and_save_public_image, delete_from_storage, STORAGE_PUBLIC_DIR

MAX_IMAGES_PER_PROPERTY = 10

def _resolve_image_url(path_or_url: str) -> str:
    if not path_or_url:
        return "/media/tanta_stadium.jpg"
    if path_or_url.startswith("http://") or path_or_url.startswith("https://") or path_or_url.startswith("/"):
        return path_or_url
    return f"/media/{path_or_url}"

class PropertyService:

    @staticmethod
    def to_public_response(prop: Property) -> PropertyPublicResponse:
        price_per_sqm = round(prop.price / prop.area_sqm, 2) if prop.area_sqm > 0 else 0.0
        images = [
            PropertyImageDto(id=img.id, file_path=_resolve_image_url(img.file_path), is_primary=img.is_primary)
            for img in prop.images
        ]
        return PropertyPublicResponse(
            id=prop.id,
            title=prop.title,
            property_type=prop.property_type,
            governorate=prop.governorate,
            city=prop.city,
            district=prop.district,
            approx_lat=prop.approx_lat,
            approx_lng=prop.approx_lng,
            price=prop.price,
            price_per_sqm=price_per_sqm,
            area_sqm=prop.area_sqm,
            bedrooms=prop.bedrooms,
            bathrooms=prop.bathrooms,
            floor=prop.floor,
            total_floors=prop.total_floors,
            elevator=prop.elevator,
            parking=prop.parking,
            balcony=prop.balcony,
            finishing=prop.finishing,
            building_license_status=prop.building_license_status,
            land_share=prop.land_share,
            maintenance_deposit=prop.maintenance_deposit,
            negotiable=prop.negotiable,
            description=prop.description,
            status=prop.status,
            created_at=prop.created_at,
            agent_id=prop.agent_id,
            agent_name=prop.agent.full_name if prop.agent else "وسيط معتمد",
            agent_is_identity_verified=prop.agent.identity_status == IdentityStatus.APPROVED if prop.agent else False,
            agent_is_professionally_verified=prop.agent.professional_status == ProfessionalStatus.VERIFIED if prop.agent else False,
            images=images
        )

    @classmethod
    def get_properties(
        cls,
        db: Session,
        city: Optional[str] = None,
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
        sort_by: Optional[str] = "newest",
        limit: int = 50,
        offset: int = 0,
        current_user: Optional[User] = None
    ) -> List[PropertyPublicResponse]:
        # Eager load images and agent to solve N+1 query problem completely
        query = db.query(Property).options(
            joinedload(Property.images),
            joinedload(Property.agent)
        )

        # Status visibility: Only PUBLISHED to public, unless admin or viewing own properties
        if not current_user or current_user.role != UserRole.ADMIN:
            if current_user and current_user.role == UserRole.AGENT:
                query = query.filter(or_(Property.status == ListingStatus.PUBLISHED, Property.agent_id == current_user.id))
            else:
                query = query.filter(Property.status == ListingStatus.PUBLISHED)

        # Filters
        if city:
            query = query.filter(Property.city == city)
        if district:
            query = query.filter(Property.district.ilike(f"%{district}%"))
        if min_price is not None:
            query = query.filter(Property.price >= min_price)
        if max_price is not None:
            query = query.filter(Property.price <= max_price)
        if min_area is not None:
            query = query.filter(Property.area_sqm >= min_area)
        if max_area is not None:
            query = query.filter(Property.area_sqm <= max_area)
        if bedrooms is not None:
            query = query.filter(Property.bedrooms >= bedrooms)
        if bathrooms is not None:
            query = query.filter(Property.bathrooms >= bathrooms)
        if finishing:
            query = query.filter(Property.finishing == finishing)
        if elevator is not None:
            query = query.filter(Property.elevator == elevator)
        if parking is not None:
            query = query.filter(Property.parking == parking)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(or_(
                Property.title.ilike(search_term),
                Property.district.ilike(search_term),
                Property.city.ilike(search_term),
                Property.description.ilike(search_term)
            ))

        # Safe Allowlist Sorting
        if sort_by == "price_asc":
            query = query.order_by(Property.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Property.price.desc())
        elif sort_by == "area_desc":
            query = query.order_by(Property.area_sqm.desc())
        else:
            query = query.order_by(Property.created_at.desc())

        # Pagination
        results = query.offset(offset).limit(limit).all()
        return [cls.to_public_response(p) for p in results]

    @classmethod
    def get_property_detail(
        cls,
        db: Session,
        property_id: str,
        current_user: Optional[User] = None
    ) -> PropertyDetailResponse:
        prop = db.query(Property).options(
            joinedload(Property.images),
            joinedload(Property.agent)
        ).filter(Property.id == property_id).first()

        if not prop:
            raise HTTPException(status_code=404, detail="العقار غير موجود")

        is_owner = current_user and current_user.id == prop.agent_id
        is_admin = current_user and current_user.role == UserRole.ADMIN

        if prop.status != ListingStatus.PUBLISHED and not (is_owner or is_admin):
            raise HTTPException(status_code=404, detail="العقار غير متاح حالياً للعرض")

        # Location Privacy Model: Check if mutual viewing has been agreed
        has_agreed_viewing = False
        if current_user:
            if is_owner or is_admin:
                has_agreed_viewing = True
            else:
                viewing = db.query(ContactRequest).filter(
                    ContactRequest.property_id == prop.id,
                    ContactRequest.buyer_id == current_user.id,
                    ContactRequest.status == ViewingStatus.VIEWING_AGREED
                ).first()
                if viewing:
                    has_agreed_viewing = True

        pub = cls.to_public_response(prop)
        return PropertyDetailResponse(
            **pub.model_dump(),
            exact_address_private=prop.exact_address_private if has_agreed_viewing else None,
            agent_phone_private=prop.agent.phone_number if (has_agreed_viewing and prop.agent) else None,
            has_agreed_viewing=has_agreed_viewing
        )

    @classmethod
    def create_property(
        cls,
        db: Session,
        payload: PropertyCreateRequest,
        current_user: User
    ) -> PropertyPublicResponse:
        new_prop = Property(
            agent_id=current_user.id,
            title=payload.title,
            property_type=payload.property_type,
            governorate="الغربية",
            city=payload.city,
            district=payload.district,
            approx_lat=payload.approx_lat,
            approx_lng=payload.approx_lng,
            exact_address_private=payload.exact_address_private,
            price=payload.price,
            area_sqm=payload.area_sqm,
            bedrooms=payload.bedrooms,
            bathrooms=payload.bathrooms,
            floor=payload.floor,
            total_floors=payload.total_floors,
            elevator=payload.elevator,
            parking=payload.parking,
            balcony=payload.balcony,
            finishing=payload.finishing,
            building_license_status=payload.building_license_status,
            land_share=payload.land_share,
            maintenance_deposit=payload.maintenance_deposit,
            negotiable=payload.negotiable,
            description=payload.description,
            status=ListingStatus.PENDING_REVIEW  # Moderation: Requires admin approval
        )
        db.add(new_prop)
        db.commit()
        db.refresh(new_prop)
        return cls.to_public_response(new_prop)

    @classmethod
    def update_property(
        cls,
        db: Session,
        property_id: str,
        payload: PropertyUpdateRequest,
        current_user: User
    ) -> PropertyPublicResponse:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="العقار غير موجود")

        # BOLA / IDOR Protection
        if current_user.id != prop.agent_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="غير مصرح لك بتعديل هذا العقار")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prop, field, value)

        # Moderation rule: Non-admin updates return listing to PENDING_REVIEW
        if current_user.role != UserRole.ADMIN and prop.status == ListingStatus.PUBLISHED:
            prop.status = ListingStatus.PENDING_REVIEW

        db.commit()
        db.refresh(prop)
        return cls.to_public_response(prop)

    @classmethod
    def delete_property(
        cls,
        db: Session,
        property_id: str,
        current_user: User
    ) -> None:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="العقار غير موجود")

        # BOLA / IDOR Protection
        if current_user.id != prop.agent_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="غير مصرح لك بحذف هذا العقار")

        db.delete(prop)
        db.commit()

    @classmethod
    def upload_property_image(
        cls,
        db: Session,
        property_id: str,
        file: UploadFile,
        is_primary: bool,
        current_user: User
    ) -> PropertyImageDto:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="العقار غير موجود")

        # BOLA Protection
        if current_user.id != prop.agent_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="غير مصرح لك برفع صور لهذا العقار")

        # Enforce maximum images limit per listing
        existing_count = db.query(PropertyImage).filter(PropertyImage.property_id == prop.id).count()
        if existing_count >= MAX_IMAGES_PER_PROPERTY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"تم الوصول للحد الأقصى لعدد الصور المسموح بها لهذا العقار ({MAX_IMAGES_PER_PROPERTY} صور)"
            )

        filename = validate_and_save_public_image(file)

        if is_primary:
            db.query(PropertyImage).filter(PropertyImage.property_id == prop.id).update({"is_primary": False})

        new_img = PropertyImage(
            property_id=prop.id,
            file_path=filename,
            is_primary=is_primary
        )
        db.add(new_img)
        db.commit()
        db.refresh(new_img)

        return PropertyImageDto(id=new_img.id, file_path=_resolve_image_url(new_img.file_path), is_primary=new_img.is_primary)

    @classmethod
    def delete_property_image(
        cls,
        db: Session,
        property_id: str,
        image_id: str,
        current_user: User
    ) -> None:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="العقار غير موجود")

        # BOLA Protection
        if current_user.id != prop.agent_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="غير مصرح لك بحذف صور هذا العقار")

        img = db.query(PropertyImage).filter(
            PropertyImage.id == image_id,
            PropertyImage.property_id == prop.id
        ).first()
        if not img:
            raise HTTPException(status_code=404, detail="الصورة غير موجودة")

        # Delete physical file from cloud storage or local disk
        delete_from_storage(img.file_path)

        db.delete(img)
        db.commit()

    @classmethod
    def compare_properties(cls, db: Session, ids: str) -> List[PropertyComparisonItem]:
        property_ids = [pid.strip() for pid in ids.split(",") if pid.strip()]
        if len(property_ids) < 2 or len(property_ids) > 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="جدول المقارنة الفنية المحايدة يدعم مقارنة ما بين عقارين إلى 4 عقارات كحد أقصى"
            )

        properties = db.query(Property).options(
            joinedload(Property.images),
            joinedload(Property.agent)
        ).filter(
            Property.id.in_(property_ids),
            Property.status == ListingStatus.PUBLISHED
        ).all()

        comparison_items = []
        for prop in properties:
            primary_img = next((_resolve_image_url(img.file_path) for img in prop.images if img.is_primary), None)
            if not primary_img and prop.images:
                primary_img = _resolve_image_url(prop.images[0].file_path)

            comparison_items.append(PropertyComparisonItem(
                id=prop.id,
                title=prop.title,
                city=prop.city,
                district=prop.district,
                price=prop.price,
                area_sqm=prop.area_sqm,
                price_per_sqm=round(prop.price / prop.area_sqm, 2) if prop.area_sqm > 0 else 0.0,
                bedrooms=prop.bedrooms,
                bathrooms=prop.bathrooms,
                floor=prop.floor,
                total_floors=prop.total_floors,
                elevator=prop.elevator,
                parking=prop.parking,
                finishing=prop.finishing,
                building_license_status=prop.building_license_status,
                land_share=prop.land_share,
                maintenance_deposit=prop.maintenance_deposit,
                agent_is_identity_verified=prop.agent.identity_status == IdentityStatus.APPROVED if prop.agent else False,
                agent_is_professionally_verified=prop.agent.professional_status == ProfessionalStatus.VERIFIED if prop.agent else False,
                primary_image=primary_img
            ))

        return comparison_items

    @classmethod
    def toggle_favorite(cls, db: Session, property_id: str, current_user: User) -> FavoriteResponse:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="العقار غير موجود")

        fav = db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.property_id == prop.id
        ).first()

        if fav:
            db.delete(fav)
            db.commit()
            return FavoriteResponse(property_id=prop.id, is_favorite=False, message="تمت إزالة العقار من المفضلة")
        else:
            new_fav = Favorite(user_id=current_user.id, property_id=prop.id)
            db.add(new_fav)
            db.commit()
            return FavoriteResponse(property_id=prop.id, is_favorite=True, message="تمت إضافة العقار إلى المفضلة")

    @classmethod
    def list_favorites(cls, db: Session, current_user: User) -> List[PropertyPublicResponse]:
        favorites = db.query(Favorite).options(
            joinedload(Favorite.property).joinedload(Property.images),
            joinedload(Favorite.property).joinedload(Property.agent)
        ).filter(Favorite.user_id == current_user.id).all()

        return [cls.to_public_response(f.property) for f in favorites if f.property and f.property.status == ListingStatus.PUBLISHED]
