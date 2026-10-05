from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from backend.app.models.entities import (
    UserRole, IdentityStatus, ProfessionalStatus, ListingStatus,
    ViewingStatus, ReportReason, DocumentType
)

# ----------------- Auth Schemas -----------------
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=3, max_length=150)
    phone_number: Optional[str] = Field(None, max_length=20)
    role: UserRole = UserRole.BUYER

    @field_validator("role")
    def validate_role(cls, v: UserRole):
        if v not in (UserRole.BUYER, UserRole.AGENT):
            raise ValueError("لا يمكن التسجيل بهذه الصلاحية")
        return v

    @field_validator("full_name")
    def validate_name(cls, v: str):
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("الاسم بالكامل مطلوب")
        return cleaned

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: UserRole
    identity_status: IdentityStatus
    professional_status: ProfessionalStatus

class UserPublicProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    role: UserRole
    identity_status: IdentityStatus
    professional_status: ProfessionalStatus
    created_at: datetime

# ----------------- Property Schemas -----------------
class PropertyImageDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_path: str
    is_primary: bool

class PropertyPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    property_type: str
    governorate: str
    city: str
    district: str
    approx_lat: float
    approx_lng: float
    price: float
    price_per_sqm: float
    area_sqm: float
    bedrooms: int
    bathrooms: int
    floor: int
    total_floors: int
    elevator: bool
    parking: bool
    balcony: bool
    finishing: str
    building_license_status: str
    land_share: Optional[str]
    maintenance_deposit: Optional[float]
    negotiable: bool
    description: str
    status: ListingStatus
    created_at: datetime

    # Trust & Verification Badges (Separated)
    agent_id: str
    agent_name: str
    agent_is_identity_verified: bool
    agent_is_professionally_verified: bool
    images: List[PropertyImageDto] = []

class PropertyDetailResponse(PropertyPublicResponse):
    # Private details revealed only if viewing is agreed or user is owner/admin
    exact_address_private: Optional[str] = None
    agent_phone_private: Optional[str] = None
    has_agreed_viewing: bool = False

class PropertyCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    property_type: str = Field("شقة سكني", max_length=50)
    city: str = Field(..., max_length=50)       # طنطا، المحلة الكبرى، زفتى
    district: str = Field(..., max_length=100)  # الاستاد، النحاس، شكري القوتلي
    approx_lat: float = Field(..., ge=20.0, le=35.0)
    approx_lng: float = Field(..., ge=25.0, le=37.0)
    exact_address_private: str = Field(..., min_length=5)
    price: float = Field(..., gt=10000)
    area_sqm: float = Field(..., gt=10)
    bedrooms: int = Field(2, ge=0, le=20)
    bathrooms: int = Field(1, ge=1, le=10)
    floor: int = Field(1, ge=0, le=100)
    total_floors: int = Field(5, ge=1, le=100)
    elevator: bool = True
    parking: bool = False
    balcony: bool = True
    finishing: str = Field("سوبر لوكس", max_length=50)
    building_license_status: str = Field(..., min_length=3, max_length=150)
    land_share: Optional[str] = None
    maintenance_deposit: Optional[float] = 0.0
    negotiable: bool = False
    description: str = Field(..., min_length=10)

class PropertyUpdateRequest(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = Field(None, gt=10000)
    area_sqm: Optional[float] = Field(None, gt=10)
    city: Optional[str] = None
    district: Optional[str] = None
    exact_address_private: Optional[str] = None
    approx_lat: Optional[float] = None
    approx_lng: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    elevator: Optional[bool] = None
    parking: Optional[bool] = None
    balcony: Optional[bool] = None
    finishing: Optional[str] = None
    building_license_status: Optional[str] = None
    land_share: Optional[str] = None
    maintenance_deposit: Optional[float] = None
    negotiable: Optional[bool] = None
    description: Optional[str] = None

# ----------------- Contact & Viewing Schemas -----------------
class ContactRequestCreate(BaseModel):
    property_id: str
    buyer_message: Optional[str] = Field(None, max_length=1000)
    proposed_date: Optional[datetime] = None

class ContactRequestStatusUpdate(BaseModel):
    status: ViewingStatus
    agent_response: Optional[str] = Field(None, max_length=1000)

class ContactRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    property_id: str
    property_title: str
    property_city: str
    property_district: str
    buyer_id: str
    buyer_name: str
    agent_id: str
    agent_name: str
    status: ViewingStatus
    buyer_message: Optional[str]
    agent_response: Optional[str]
    proposed_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

# ----------------- Verification Schemas -----------------
class DocumentReviewAction(BaseModel):
    document_id: str
    status: IdentityStatus
    reviewer_notes: Optional[str] = None

class AgentVerificationAction(BaseModel):
    user_id: str
    status: ProfessionalStatus
    reviewer_notes: Optional[str] = None

# ----------------- Report Schema -----------------
class ReportCreateRequest(BaseModel):
    property_id: str
    reason: ReportReason
    details: str = Field(..., min_length=10, max_length=2000)

class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reporter_id: str
    property_id: str
    property_title: str
    reason: ReportReason
    details: str
    is_resolved: bool
    created_at: datetime

# ----------------- Comparison DTO -----------------
class PropertyComparisonItem(BaseModel):
    id: str
    title: str
    city: str
    district: str
    price: float
    area_sqm: float
    price_per_sqm: float
    bedrooms: int
    bathrooms: int
    floor: int
    total_floors: int
    elevator: bool
    parking: bool
    finishing: str
    building_license_status: str
    land_share: Optional[str]
    maintenance_deposit: Optional[float]
    agent_is_identity_verified: bool
    agent_is_professionally_verified: bool
    primary_image: Optional[str]

# ----------------- Favorite DTO -----------------
class FavoriteResponse(BaseModel):
    property_id: str
    is_favorite: bool
    message: str
