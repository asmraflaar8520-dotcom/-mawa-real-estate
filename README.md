# 🏛️ مأوى | MA'WA — المنصة العقارية الموثوقة

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Vercel](https://img.shields.io/badge/Deployed_on-Vercel-000000.svg?style=for-the-badge&logo=vercel&logoColor=white)](https://mawa-real-estate.vercel.app)
[![Security Hardened](https://img.shields.io/badge/Security-Hardened%20(BOLA%20%26%20RBAC)-4CAF50.svg?style=for-the-badge&logo=shield)](https://github.com/asmraflaar8520-dotcom/-mawa-real-estate)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg?style=for-the-badge)](LICENSE)

### **"مكانك يبدأ بثقة"**
**النطاق الجغرافي للمرحلة الأولى:** محافظة الغربية، جمهورية مصر العربية (طنطا، المحلة الكبرى، زفتى).

</div>

---

## 🌐 تجربة المنصة مباشرة (Live Production Platform)

<div align="center">
  <img src="qr_code.png" width="200" alt="MAWA QR Code" style="border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" />
  <br><br>
  <p><strong>امسح الكود بكاميرا هاتفك لفتح المنصة مباشرة على الهاتف 📱</strong></p>
  
  <p>
    🚀 <strong>رابط المنصة المباشر:</strong> <br>
    <a href="https://mawa-real-estate.vercel.app" target="_blank" style="font-size: 1.2rem; font-weight: bold; color: #0d6efd;">https://mawa-real-estate.vercel.app</a>
  </p>

  <p>
    📑 <strong>التوثيق التفاعلي للـ API (Swagger Documentation):</strong> <br>
    <a href="https://mawa-real-estate.vercel.app/docs" target="_blank">https://mawa-real-estate.vercel.app/docs</a>
  </p>
</div>

---

## 🏛️ عن المنظومة (Project Vision & Core Principles)

**مأوى (MA'WA)** هي منصة عقارية تقنية متطورة مبنية وفق أحدث معايير هندسة البرمجيات والأمن السيبراني المتقدم (**Clean Modular Monolith Architecture**). صُممت لإعادة الانضباط والشفافية لسوق العقارات بمحافظة الغربية وحماية حقوق المشترين والوسطاء على حدٍ سواء من خلال المبادئ التالية:

### 1. 🛡️ فصل نماذج التوثيق (Separated Verification Model)
- استقلالية كاملة وغير قابلة للتلاعب بين:
  1. توثيق هوية المستخدم الشخصية (`IdentityStatus`).
  2. الاعتماد المهني للوسيط العقاري (`ProfessionalStatus`).
  3. الموقف القانوني وترخيص البناء للعقار (`BuildingLicenseStatus`).
- التسجيل في المنصة لا يمنح الوسيط شارة الاعتماد تلقائياً؛ بل يخضع لمراجعة وتدقيق مستندي صارم من قِبل إدارة المنصة.

### 2. 📍 حماية الخصوصية الجغرافية (Location Privacy-by-Design)
- حجب العنوان التفصيلي الدقيق (`exact_address_private`) والإحداثيات الجغرافية الحساسة عن الواجهات العامة ومنع تسريبها في الـ APIs.
- الاكتفاء بعرض الحي والإحداثيات التقريبية للموقع العام، ولا يُكشف العنوان الدقيق إلا بعد **قبول طلب المعاينة بالتراضي** بين الطرفين.

### 3. 🔒 عزل المستندات والتحقق الثنائي (Zero Public Access & Magic Bytes)
- حفظ بطاقات الرقم القومي والتراخيص في مسار محمي ومحجوب عن الوصول المباشر (`storage/private_docs/`) بأسماء عشوائية مشفرة (`UUID`).
- فحص البصمة الثنائية (`Magic Bytes`) للملفات المرفوعة لمنع حقن الملفات الضارة.
- تسجيل كل عملية استعراض إدارية في سجل تدقيق محكم (`AuditLog`) لضمان الامتثال القانوني والمساءلة.

### 4. ⚖️ المقارنة الفنية المحايدة (Neutral Fact-Based Comparison)
- أداة متطورة للمقارنة الفنية بين (2 إلى 4 عقارات) تعتمد على البيانات المجردة وسعر المتر الصافي والمواصفات الفنية ونسب الأرض وتراخيص المباني دون انحياز أو إعلانات ممولة موجهة.

### 5. 📋 فحص مأوى الإرشادي الذكي (MA'WA Check)
- قائمة فحص تفاعلية مدمجة للمشتري تشمل أهم 7 استفسارات قانونية وهندسية يجب التأكد منها قبل توقيع أي عقد أو دفع أي مقدمات.

### 6. 🛑 الحماية الشاملة من ثغرات BOLA / IDOR و RBAC
- تطبيق حماية برمجية متقدمة على مستوى الخادم تمنع أي مستخدم من الوصول إلى بيانات أو تعديل طلبات أو استعراض وثائق مستخدمين آخرين.

---

## 📂 الهيكلية البرمجية للمشروع (Architecture Overview)

```text
mawa/
├── frontend/                     # واجهات المستخدم التفاعلية (HTML5 / Vanilla JS / Modern CSS)
│   ├── index.html                # البوابة الرئيسية، محرك البحث، والتصفية الجغرافية
│   ├── property.html             # بطاقة العقار التفصيلية، الخصوصية، وقائمة فحص مأوى
│   ├── compare.html              # نظام المقارنة الهندسية المحايدة
│   ├── login.html                # تسجيل الدخول الموحد
│   ├── register.html             # فتح حسابات المشترين والوسطاء
│   ├── dashboard.html            # لوحة إدارة العقارات والطلبات والرقابة الإدارية
│   ├── css/
│   │   └── design-system.css     # لغة التصميم الموحدة ودعم RTL الكامل
│   └── js/
│       ├── app.js                # إدارة الجلسات والاتصال الآمن بـ API وعربة المقارنة
│       └── mawa-check.js         # محرك قائمة فحص مأوى التفاعلية
├── backend/                      # خادم النظام (FastAPI Core)
│   ├── app/
│   │   ├── routes/               # نقاط النهاية المنظمة (Modular Endpoints)
│   │   │   ├── auth.py           # المصادقة، التحقق من الصلاحيات، وإصدار JWT
│   │   │   ├── properties.py     # إدارة العقارات، الفلاتر، والمقارنات
│   │   │   ├── contacts.py       # طلبات المعاينة المحمية بنظام التراضي
│   │   │   ├── verifications.py  # مسار رفع وتوثيق الهويات والرخص
│   │   │   ├── reports.py        # منظومة مكافحة الاحتيال والبلاغات
│   │   │   └── admin.py          # لوحة التحكم المركزية وسجلات التدقيق (Audit Logs)
│   │   ├── models/
│   │   │   └── entities.py       # نماذج البيانات والعلاقات (SQLAlchemy ORM)
│   │   ├── schemas/
│   │   │   └── dtos.py           # كائنات تبادل البيانات الصارمة (Pydantic DTOs)
│   │   ├── security/
│   │   │   ├── auth_guard.py     # تشفير كلمات المرور (Bcrypt) وإدارة التوكنز
│   │   │   └── storage.py        # فحص Magic Bytes وتجريد EXIF وحفظ الملفات
│   │   ├── utils/
│   │   │   └── seed_data.py      # بذر البيانات التجريبية لعقارات الغربية
│   │   ├── config.py             # إدارة البيئات (Local, Vercel, Production)
│   │   ├── database.py           # إدارة الاتصال بقواعد البيانات (SQLite & PostgreSQL)
│   │   └── main.py               # التطبيق الرئيسي والترويسات الأمنية (Security Headers)
│   └── tests/                    # مصفوفة الاختبارات الآلية (Pytest Suite)
│       ├── test_auth.py          # فحص المصادقة ومنع تصعيد الصلاحيات
│       ├── test_security_idor.py # اختبارات الحماية من BOLA و IDOR
│       ├── test_property_trust.py# فحص استقلالية التوثيق والحيادية
│       └── test_privacy_leakage.py# فحص منع تسريب العناوين والوثائق
├── storage/                      # التخزين المحلي المعزول (Development Only)
│   ├── private_docs/             # مسار الوثائق الحساسة المعزول
│   └── public_media/             # صور العقارات المعالجة
├── api/                          # مدخل تشغيل Serverless على Vercel
├── requirements.txt              # حزم واعتمادات Python للإنتاج
├── vercel.json                   # إعدادات الاستضافة والتوجيه والأمان
└── README.md                     # التوثيق الشامل
```

---

## 🚀 التثبيت والتشغيل المحلي (Local Development Setup)

### 1. استنساخ المستودع وتثبيت الاعتمادات:
```bash
git clone https://github.com/asmraflaar8520-dotcom/-mawa-real-estate.git
cd -mawa-real-estate
pip install -r requirements.txt
```

### 2. إعداد المتغيرات البيئية:
```bash
cp .env.example .env
```

### 3. بذر البيانات الأولية التجريبية (مدن محافظة الغربية):
```bash
python -m backend.app.utils.seed_data
```

### 4. تشغيل خادم التطوير:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- المنصة الرئيسية: `http://127.0.0.1:8000/`
- توثيق الـ API التفاعلي: `http://127.0.0.1:8000/docs`

---

## 🧪 الاختبارات الآلية ومراقبة الجودة (Quality Assurance)

تتضمن المنصة مصفوفة اختبارات متكاملة تغطي الجوانب الأمنية والمنطقية:
```bash
pytest backend/tests -v
```

---

## 🔐 الأمان وحماية البيانات (DevSecOps & Security Posture)

تم تصميم وتطوير المنصة مع الالتزام بأعلى معايير الأمن السيبراني:
* **حماية الرؤوس الأمنية (Security Headers):** تطبيق سياسات صارمة لـ `Content-Security-Policy`، `X-Frame-Options: DENY`، و `X-Content-Type-Options: nosniff`.
* **الحماية من هجمات حقن الصلاحيات:** فحص صارم للأدوار المسموح بها في واجهات التسجيل لمنع أي تصعيد غير مشروع لصلاحيات الإدارة.
* **حماية قواعد البيانات:** عزل كامل لملفات قواعد البيانات وسجلات النظام من مستودع الكود المصدري.
* **جاهزية السحابة (Cloud Database Ready):** دعم فوري للاتصال بقواعد بيانات **PostgreSQL** المدارة (Supabase / Neon / Vercel Postgres) عبر متغير `DATABASE_URL`.

---

<div align="center">
  <p>© 2026 مأوى (MA'WA) — جميع الحقوق محفوظة لفرق التطوير والعمليات.</p>
</div>
