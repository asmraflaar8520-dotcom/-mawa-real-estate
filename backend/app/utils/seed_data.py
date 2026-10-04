from sqlalchemy.orm import Session
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
from backend.app.config import STORAGE_PUBLIC_DIR
from backend.app.database import SessionLocal, engine, Base
from backend.app.models.entities import (
    User, Property, PropertyImage, UserRole, IdentityStatus,
    ProfessionalStatus, ListingStatus
)
from backend.app.security.auth_guard import hash_password

def create_sample_property_image(filename: str, title: str, subtitle: str, bg_color: tuple):
    path = STORAGE_PUBLIC_DIR / filename
    if path.exists():
        return
    img = Image.new('RGB', (800, 500), color=bg_color)
    draw = ImageDraw.Draw(img)
    # Simple aesthetic pattern
    draw.rectangle([20, 20, 780, 480], outline=(255, 255, 255), width=3)
    draw.rectangle([40, 360, 760, 460], fill=(13, 59, 76))
    img.save(path, format="JPEG", quality=85)

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        # Create Sample Images
        create_sample_property_image("tanta_stadium.jpg", "طنطا - الاستاد", "شقة 185م² فاخرة", (20, 50, 80))
        create_sample_property_image("tanta_nahas.jpg", "طنطا - النحاس", "شقة 135م² كاملة التشطيب", (40, 60, 70))
        create_sample_property_image("mahalla_shoukry.jpg", "المحلة - شكري القوتلي", "شقة 150م² موقع استراتيجي", (30, 45, 65))
        create_sample_property_image("mahalla_bakry.jpg", "المحلة - منشية البكري", "شقة 120م² مرخصة", (25, 55, 75))
        create_sample_property_image("zefta_corniche.jpg", "زفتى - كورنيش النيل", "شقة 165م² فيو النيل", (15, 65, 85))

        # 1. Admin User
        admin = db.query(User).filter(User.email == "admin@mawa.eg").first()
        if not admin:
            admin = User(
                email="admin@mawa.eg",
                password_hash=hash_password("AdminMawa2026!Safe"),
                full_name="مشرف منصة مأوى",
                phone_number="01011112222",
                role=UserRole.ADMIN,
                identity_status=IdentityStatus.APPROVED,
                professional_status=ProfessionalStatus.VERIFIED
            )
            db.add(admin)

        # 2. Verified Agent in Tanta
        agent1 = db.query(User).filter(User.email == "tanta.broker@mawa.eg").first()
        if not agent1:
            agent1 = User(
                email="tanta.broker@mawa.eg",
                password_hash=hash_password("BrokerPass123!"),
                full_name="م. إبراهيم الدسوقي (الوسيط المعتمد)",
                phone_number="01223344556",
                role=UserRole.AGENT,
                identity_status=IdentityStatus.APPROVED,
                professional_status=ProfessionalStatus.VERIFIED
            )
            db.add(agent1)

        # 3. New Agent (Identity Approved, Professional Pending)
        agent2 = db.query(User).filter(User.email == "mahalla.broker@mawa.eg").first()
        if not agent2:
            agent2 = User(
                email="mahalla.broker@mawa.eg",
                password_hash=hash_password("BrokerPass123!"),
                full_name="أ. محمود السعدني (وسيط عقاري)",
                phone_number="01155443322",
                role=UserRole.AGENT,
                identity_status=IdentityStatus.APPROVED,
                professional_status=ProfessionalStatus.PENDING
            )
            db.add(agent2)

        # 4. Standard Buyer User
        buyer = db.query(User).filter(User.email == "buyer.ahmed@mawa.eg").first()
        if not buyer:
            buyer = User(
                email="buyer.ahmed@mawa.eg",
                password_hash=hash_password("BuyerPass123!"),
                full_name="أحمد حسن الشناوي",
                phone_number="01099887766",
                role=UserRole.BUYER,
                identity_status=IdentityStatus.APPROVED,
                professional_status=ProfessionalStatus.NOT_APPLIED
            )
            db.add(buyer)

        db.commit()

        # Seed Gharbia Properties
        if db.query(Property).count() == 0:
            p1 = Property(
                agent_id=agent1.id,
                title="شقة فاخرة للبيع بمنطقة الاستاد - طنطا",
                property_type="شقة سكني",
                governorate="الغربية",
                city="طنطا",
                district="الاستاد",
                approx_lat=30.795,
                approx_lng=31.002,
                exact_address_private="شارع معوض المتفرع من شارع الاستاد، عمارة الأندلس، الدور 4، شقة 8",
                price=3450000.0,
                area_sqm=185.0,
                bedrooms=3,
                bathrooms=2,
                floor=4,
                total_floors=9,
                elevator=True,
                parking=True,
                balcony=True,
                finishing="ألترا سوبر لوكس",
                building_license_status="مرخص بالكامل (حي ثان طنطا)",
                land_share="حصة مشاعة في الأرض بالعقد المسجل",
                maintenance_deposit=50000.0,
                negotiable=True,
                description="شقة استثنائية بواجهة بحرية صريحة غير مجروحة بالقرب من مجمع الكليات والاستاد، تشطيب حديث ومصعد مستورد وعدادات كاملة (كهرباء، مياه، غاز طبيعي).",
                status=ListingStatus.PUBLISHED
            )
            db.add(p1)
            db.flush()
            db.add(PropertyImage(property_id=p1.id, file_path="tanta_stadium.jpg", is_primary=True))

            p2 = Property(
                agent_id=agent1.id,
                title="شقة مميزة للبيع بشارع النحاس الرئيسي - طنطا",
                property_type="شقة سكني",
                governorate="الغربية",
                city="طنطا",
                district="النحاس",
                approx_lat=30.787,
                approx_lng=30.995,
                exact_address_private="تقاطع شارع النحاس مع الفاتح، برج النور، الدور 6",
                price=2150000.0,
                area_sqm=135.0,
                bedrooms=3,
                bathrooms=1,
                floor=6,
                total_floors=11,
                elevator=True,
                parking=False,
                balcony=True,
                finishing="سوبر لوكس",
                building_license_status="مرخص بالكامل (حي أول طنطا)",
                land_share="حصة في الأرض مسجلة",
                maintenance_deposit=25000.0,
                negotiable=False,
                description="موقع تجاري وحيوي ممتاز وسط طنطا، خطوات من محطة القطار والخدمات العامة، جاهزة للسكن الفوري والتسليم دون أي التزامات مالية.",
                status=ListingStatus.PUBLISHED
            )
            db.add(p2)
            db.flush()
            db.add(PropertyImage(property_id=p2.id, file_path="tanta_nahas.jpg", is_primary=True))

            p3 = Property(
                agent_id=agent2.id,
                title="شقة راقية بشارع شكري القوتلي - المحلة الكبرى",
                property_type="شقة سكني",
                governorate="الغربية",
                city="المحلة الكبرى",
                district="شكري القوتلي",
                approx_lat=30.973,
                approx_lng=31.164,
                exact_address_private="شارع شكري القوتلي الرئيسي، عمارة الصفوة، الدور 3، شقة 5",
                price=2600000.0,
                area_sqm=150.0,
                bedrooms=3,
                bathrooms=2,
                floor=3,
                total_floors=8,
                elevator=True,
                parking=True,
                balcony=True,
                finishing="سوبر لوكس",
                building_license_status="مرخص بالكامل (حي أول المحلة)",
                land_share="حصة مشاعة في أرض العقار مثبتة بالشهر العقاري",
                maintenance_deposit=30000.0,
                negotiable=True,
                description="أرقى مناطق المحلة الكبرى، إطلالة مفتوحة على الشارع الرئيسي، تقسيم داخلي ممتاز لغرف النوم ومجلس الضيوف، رخصة بناء سارية وكامل المرافق.",
                status=ListingStatus.PUBLISHED
            )
            db.add(p3)
            db.flush()
            db.add(PropertyImage(property_id=p3.id, file_path="mahalla_shoukry.jpg", is_primary=True))

            p4 = Property(
                agent_id=agent2.id,
                title="شقة عائلية هادئة بمنشية البكري - المحلة الكبرى",
                property_type="شقة سكني",
                governorate="الغربية",
                city="المحلة الكبرى",
                district="منشية البكري",
                approx_lat=30.985,
                approx_lng=31.178,
                exact_address_private="شارع العشرين المتفرع من شارع الترعة، منشية البكري، الدور 2",
                price=1850000.0,
                area_sqm=120.0,
                bedrooms=2,
                bathrooms=1,
                floor=2,
                total_floors=6,
                elevator=True,
                parking=False,
                balcony=True,
                finishing="تشطيب كامل لوكس",
                building_license_status="مرخص بالكامل (حي ثان المحلة)",
                land_share="حصة في الأرض",
                maintenance_deposit=15000.0,
                negotiable=True,
                description="قريبة من كافة المدارس والخدمات، واجهة بحرية، تشطيب نظيف، دور مميز مرغوب.",
                status=ListingStatus.PUBLISHED
            )
            db.add(p4)
            db.flush()
            db.add(PropertyImage(property_id=p4.id, file_path="mahalla_bakry.jpg", is_primary=True))

            p5 = Property(
                agent_id=agent1.id,
                title="شقة بإطلالة نيلية خلابة على كورنيش زفتى",
                property_type="شقة سكني",
                governorate="الغربية",
                city="زفتى",
                district="كورنيش النيل",
                approx_lat=30.718,
                approx_lng=31.242,
                exact_address_private="شارع الجيش / كورنيش النيل بزفتى، برج الكورنيش، الدور 5",
                price=2300000.0,
                area_sqm=165.0,
                bedrooms=3,
                bathrooms=2,
                floor=5,
                total_floors=10,
                elevator=True,
                parking=True,
                balcony=True,
                finishing="ألترا سوبر لوكس",
                building_license_status="مرخص بالكامل (مجلس مدينة زفتى)",
                land_share="حصة مشاعة في كامل أرض العقار",
                maintenance_deposit=20000.0,
                negotiable=True,
                description="فيو مباشر ومفتوح على فرع دمياط لنهر النيل في زفتى، موقع هادئ ونادر وراقٍ، واجهة بحرية وشرفة فسيحة، تشطيب راقٍ جداً.",
                status=ListingStatus.PUBLISHED
            )
            db.add(p5)
            db.flush()
            db.add(PropertyImage(property_id=p5.id, file_path="zefta_corniche.jpg", is_primary=True))

            db.commit()
            print("Successfully seeded MA'WA Gharbia initial data!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
