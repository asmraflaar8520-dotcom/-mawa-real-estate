from datetime import datetime, timezone
from enum import Enum
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, ForeignKey,
    DateTime, Enum as SQLEnum, Text, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class UserRole(str, Enum):
    BUYER = "BUYER"
    AGENT = "AGENT"
    ADMIN = "ADMIN"

class IdentityStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ProfessionalStatus(str, Enum):
    NOT_APPLIED = "NOT_APPLIED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class ListingStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"

class ViewingStatus(str, Enum):
    VIEWING_REQUESTED = "VIEWING_REQUESTED"
    VIEWING_AGREED = "VIEWING_AGREED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class ReportReason(str, Enum):
    FAKE_PRICE = "FAKE_PRICE"
    NONEXISTENT = "NONEXISTENT"
    MISLEADING_INFO = "MISLEADING_INFO"
    STOLEN_IMAGES = "STOLEN_IMAGES"
    SCAM = "SCAM"
    INAPPROPRIATE = "INAPPROPRIATE"
    OTHER = "OTHER"

class DocumentType(str, Enum):
    NATIONAL_ID = "NATIONAL_ID"
    BROKER_LICENSE = "BROKER_LICENSE"
    COMMERCIAL_REGISTER = "COMMERCIAL_REGISTER"
    SYNDICATE_CARD = "SYNDICATE_CARD"

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    phone_number = Column(String(30), nullable=True)  # Sensitive - strictly private
    role = Column(SQLEnum(UserRole), default=UserRole.BUYER, nullable=False)

    # Independent Trust & Verification Model (Separate lifecycle per Master Prompt)
    identity_status = Column(SQLEnum(IdentityStatus), default=IdentityStatus.PENDING, nullable=False)
    professional_status = Column(SQLEnum(ProfessionalStatus), default=ProfessionalStatus.NOT_APPLIED, nullable=False)
    is_suspended = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    properties = relationship("Property", back_populates="agent", cascade="all, delete-orphan")
    contact_requests_sent = relationship("ContactRequest", back_populates="buyer", foreign_keys="ContactRequest.buyer_id")
    contact_requests_received = relationship("ContactRequest", back_populates="agent", foreign_keys="ContactRequest.agent_id")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("VerificationDocument", back_populates="user", cascade="all, delete-orphan")

class Property(Base):
    __tablename__ = "properties"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    property_type = Column(String(50), default="شقة سكني", nullable=False)
    governorate = Column(String(50), default="الغربية", nullable=False, index=True)
    city = Column(String(50), nullable=False, index=True)       # طنطا، المحلة الكبرى، زفتى
    district = Column(String(100), nullable=False, index=True)  # الاستاد، النحاس، شكري القوتلي

    # Location Privacy: Public approximate coords vs. Private exact physical address
    approx_lat = Column(Float, nullable=False)
    approx_lng = Column(Float, nullable=False)
    exact_address_private = Column(Text, nullable=True)  # Strictly hidden from public APIs

    price = Column(Float, nullable=False, index=True)
    area_sqm = Column(Float, nullable=False)
    bedrooms = Column(Integer, nullable=False, default=2)
    bathrooms = Column(Integer, nullable=False, default=1)
    floor = Column(Integer, nullable=False, default=1)
    total_floors = Column(Integer, nullable=False, default=5)
    elevator = Column(Boolean, default=True)
    parking = Column(Boolean, default=False)
    balcony = Column(Boolean, default=True)
    finishing = Column(String(50), default="سوبر لوكس", nullable=False)

    building_license_status = Column(String(150), default="مرخص بالكامل", nullable=False)
    land_share = Column(String(150), nullable=True)
    maintenance_deposit = Column(Float, nullable=True, default=0.0)
    negotiable = Column(Boolean, default=False)
    description = Column(Text, nullable=False)

    status = Column(SQLEnum(ListingStatus), default=ListingStatus.PENDING_REVIEW, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    agent = relationship("User", back_populates="properties")
    images = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")
    contact_requests = relationship("ContactRequest", back_populates="property", cascade="all, delete-orphan")
    reports = relationship("PropertyReport", back_populates="property", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="property", cascade="all, delete-orphan")

class PropertyImage(Base):
    __tablename__ = "property_images"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    property_id = Column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(255), nullable=False)  # Relative to public_media, metadata stripped
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    property = relationship("Property", back_populates="images")

class VerificationDocument(Base):
    __tablename__ = "verification_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(SQLEnum(DocumentType), nullable=False)
    file_path = Column(String(255), nullable=False)  # Random UUID in storage/private_docs
    status = Column(SQLEnum(IdentityStatus), default=IdentityStatus.PENDING, nullable=False)
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="documents")

class ContactRequest(Base):
    __tablename__ = "contact_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    property_id = Column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    buyer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(SQLEnum(ViewingStatus), default=ViewingStatus.VIEWING_REQUESTED, nullable=False)
    buyer_message = Column(Text, nullable=True)
    agent_response = Column(Text, nullable=True)
    proposed_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    property = relationship("Property", back_populates="contact_requests")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="contact_requests_sent")
    agent = relationship("User", foreign_keys=[agent_id], back_populates="contact_requests_received")

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="favorites")
    property = relationship("Property", back_populates="favorites")

    __table_args__ = (
        Index("idx_user_property_favorite", "user_id", "property_id", unique=True),
    )

class PropertyReport(Base):
    __tablename__ = "property_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    reporter_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(SQLEnum(ReportReason), nullable=False)
    details = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    property = relationship("Property", back_populates="reports")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
