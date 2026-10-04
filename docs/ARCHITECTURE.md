# مأوى | MA'WA — بنية النظام والأكواد المصدرية (Production Blueprint & Code)
**الشعار:** مكانك يبدأ بثقة  
**النطاق الجغرافي للمرحلة الأولى:** محافظة الغربية (طنطا، المحلة الكبرى، زفتى)

---

## 1. شجرة وهيكل مجلدات المشروع (Clean Modular Monolith)

```text
mawa/
├── frontend/
│   ├── index.html               # الشاشة الرئيسية وعقارات الغربية
│   ├── property.html            # تفاصيل العقار وفحص مأوى والخصوصية الجغرافية
│   ├── compare.html             # جدول المقارنة الفنية المحايدة (2-4 عقارات)
│   ├── css/
│   │   └── tailwind.css         # إعدادات RTL والخطوط والألوان المؤسسية
│   └── js/
│       ├── app.js               # إدارة التفاعل وحاسبة الرسوم والمقارنة
│       └── mawa-check.js        # تفاعل قائمة تدقيق فحص مأوى الذكية
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── auth.py          # التسجيل وتسجيل الدخول والجلسات
│   │   │   ├── properties.py    # عرض وتصفية وإضافة العقارات (مفصولة الصلاحيات)
│   │   │   ├── verifications.py # مسار التوثيق المستقل (هوية، اعتماد مهني، فحص)
│   │   │   ├── contacts.py      # طلبات التواصل والمعاينة بالتراضي (محمية BOLA/IDOR)
│   │   │   └── admin.py         # لوحة الإشراف ومراجعة التراخيص وسجلات التدقيق
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── models/
│   │   │   └── entities.py      # نماذج قاعدة البيانات (SQLAlchemy / Pydantic)
│   │   ├── schemas/
│   │   │   └── dtos.py          # كائنات الإدخال والإخراج مع قوائم السماح (Allowlist)
│   │   ├── security/
│   │   │   ├── auth_guard.py    # التحقق من الجلسات والصلاحيات Server-side
│   │   │   └── storage.py       # التخزين المعزول لبطاقات الرقم القومي
│   │   └── utils/
│   └── tests/
│       ├── test_auth.py
│       ├── test_idor_contacts.py # اختبار منع اختراق طلبات المعاينة
│       └── test_property_trust.py # اختبار عزل حالات التوثيق الخمس
├── storage/
│   ├── private_docs/            # وثائق الرقم القومي والتراخيص (تخزين معزول غير عام)
│   └── public_media/            # صور العقارات المعالجة والمحذوف منها الـ EXIF
└── .env.example
```

---

## 2. كود مخطط قاعدة البيانات (Database Schema - SQLAlchemy / PostgreSQL Ready)

```python
# backend/app/models/entities.py
from datetime import datetime
from enum import Enum
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, ForeignKey,
    DateTime, Enum as SQLEnum, Text, Index
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

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

class UserRole(str, Enum):
    BUYER = "BUYER"
    AGENT = "AGENT"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(30), nullable=True) # حساس ومحمي من العرض العام
    full_name = Column(String(150), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.BUYER, nullable=False)
    
    # نموذج التوثيق المستقل - البند 10 و 14
    identity_status = Column(SQLEnum(IdentityStatus), default=IdentityStatus.PENDING, nullable=False)
    professional_status = Column(SQLEnum(ProfessionalStatus), default=ProfessionalStatus.NOT_APPLIED, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    properties = relationship("Property", back_populates="agent")
    contact_requests_sent = relationship("ContactRequest", back_populates="buyer", foreign_keys="ContactRequest.buyer_id")

class Property(Base):
    __tablename__ = "properties"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    governorate = Column(String(50), default="الغربية", nullable=False, index=True)
    city = Column(String(50), nullable=False, index=True) # طنطا، المحلة الكبرى، زفتى
    district = Column(String(100), nullable=False)        # الاستاد، شكري القوتلي، كورنيش النيل
    
    # حماية الخصوصية الجغرافية - البند 16 (إحداثيات تقريبية عامة ودقيقة خاصة)
    approx_lat = Column(Float, nullable=False)
    approx_lng = Column(Float, nullable=False)
    exact_address_private = Column(Text, nullable=True)   # لا تظهر إلا بعد قبول المعاينة
    
    price = Column(Float, nullable=False, index=True)
    area_sqm = Column(Float, nullable=False)
    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Integer, nullable=False)
    floor = Column(Integer, nullable=False)
    total_floors = Column(Integer, nullable=False)
    elevator = Column(Boolean, default=True)
    parking = Column(Boolean, default=False)
    finishing = Column(String(50), nullable=False)        # ألترا سوبر لوكس، تشطيب كامل
    
    status = Column(SQLEnum(ListingStatus), default=ListingStatus.DRAFT, nullable=False, index=True)
    building_license_status = Column(String(100), nullable=False) # مرخص بالكامل (حي ثان طنطا)
    land_share = Column(String(100), nullable=True)               # حصة مشاعة بالعقد
    maintenance_deposit = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    agent = relationship("User", back_populates="properties")

class ContactRequest(Base):
    __tablename__ = "contact_requests"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String(36), ForeignKey("properties.id"), nullable=False, index=True)
    buyer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # حالة طلب المعاينة بالتراضي - البند 21 و 22
    status = Column(String(50), default="VIEWING_REQUESTED", nullable=False) # VIEWING_REQUESTED, VIEWING_AGREED, REJECTED
    buyer_message = Column(Text, nullable=True)
    proposed_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    buyer = relationship("User", foreign_keys=[buyer_id])
    agent = relationship("User", foreign_keys=[agent_id])
```

---

## 3. كود حماية الصلاحيات والـ DTOs ضد تسريب البيانات (Security & Privacy DTOs)

```python
# backend/app/schemas/dtos.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# استجابة عامة للعقار - محمي ضد تسريب الإحداثيات الحساسة وبيانات المالك
class PropertyPublicResponse(BaseModel):
    id: str
    title: str
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
    elevator: bool
    parking: bool
    finishing: str
    building_license_status: str
    land_share: Optional[str]
    
    # شارات التوثيق المستقلة فقط (بدون مستندات خام)
    agent_id: str
    agent_name: str
    agent_is_identity_verified: bool
    agent_is_professionally_verified: bool
    listing_is_field_inspected: bool

    class Config:
        orm_mode = True

# كود فحص الصلاحيات الصارم ومنع IDOR في طلبات التواصل
# backend/app/routes/contacts.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.security.auth_guard import get_current_user

router = APIRouter(prefix="/api/contact-requests", tags=["Contacts"])

@router.get("/{request_id}")
def get_contact_request(request_id: str, current_user = Depends(get_current_user)):
    req = fetch_request_from_db(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    # اختبار BOLA / IDOR الصارم (البند 21 و 33):
    # لا يمكن الوصول للطلب إلا للمشتري صاحب الطلب، أو الوسيط المسؤول، أو المشرف المعتمد
    if current_user.id != req.buyer_id and current_user.id != req.agent_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="غير مصرح لك باستعراض بيانات هذا الطلب"
        )
    return req
```

---

## 4. كود واجهة جدول المقارنة المحايد (HTML/CSS Snippet)

```html
<!-- snippet من frontend/compare.html لضمان الحيادية التامة (البند 19) -->
<div class="grid grid-cols-2 gap-3 bg-white p-4 rounded-2xl shadow-sm border border-slate-100">
  <!-- العقار الأول: الاستاد - طنطا -->
  <div class="space-y-3">
    <div class="text-xs font-bold text-slate-500">طنطا - الاستاد</div>
    <div class="text-lg font-bold text-[#0D3B4C]">3,450,000 ج.م</div>
    <div class="p-2 bg-slate-50 rounded-lg text-xs">
      <span class="block text-slate-400">سعر المتر الصافي:</span>
      <span class="font-bold text-slate-800">18,650 ج.م / م²</span>
    </div>
    <div class="text-xs text-slate-600">المساحة: 185 م² (الصافي: 162 م²)</div>
    <div class="text-xs font-semibold text-emerald-700 bg-emerald-50 p-2 rounded-lg">
      ✓ مرخص بالكامل (حي ثان طنطا)
    </div>
    <button onclick="requestViewing('prop_1')" class="w-full py-2 bg-[#0D3B4C] text-white text-xs font-bold rounded-xl">
      طلب معاينة بالتراضي
    </button>
  </div>

  <!-- العقار الثاني: شكري القوتلي - المحلة -->
  <div class="space-y-3 border-r pr-3 border-slate-100">
    <div class="text-xs font-bold text-slate-500">المحلة - شكري القوتلي</div>
    <div class="text-lg font-bold text-[#0D3B4C]">2,600,000 ج.م</div>
    <div class="p-2 bg-slate-50 rounded-lg text-xs">
      <span class="block text-slate-400">سعر المتر الصافي:</span>
      <span class="font-bold text-slate-800">17,330 ج.م / م²</span>
    </div>
    <div class="text-xs text-slate-600">المساحة: 150 م² (الصافي: 131 م²)</div>
    <div class="text-xs font-semibold text-emerald-700 bg-emerald-50 p-2 rounded-lg">
      ✓ مرخص بالكامل (حي أول المحلة)
    </div>
    <button onclick="requestViewing('prop_2')" class="w-full py-2 bg-[#0D3B4C] text-white text-xs font-bold rounded-xl">
      طلب معاينة بالتراضي
    </button>
  </div>
</div>
```
