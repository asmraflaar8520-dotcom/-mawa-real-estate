"""
MA'WA (مأوى) — Data Migration Tool: Local SQLite -> Cloud Supabase PostgreSQL
Usage:
    python -m backend.scripts.migrate_to_supabase [TARGET_DATABASE_URL]
    
Or set DATABASE_URL in your environment / .env file.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models.entities import (
    User, Property, PropertyImage, VerificationDocument,
    ContactRequest, PropertyReport, AuditLog, Favorite
)

def run_migration():
    print("==================================================")
    print("   منصة مأوى | أداة نقل وترقية البيانات السحابية    ")
    print("      SQLite Local  --->  Supabase PostgreSQL     ")
    print("==================================================\n")

    sqlite_path = PROJECT_ROOT / "mawa.db"
    if not sqlite_path.exists():
        print(f"[-] لم يتم العثور على قاعدة البيانات المحلية: {sqlite_path}")
        return

    sqlite_url = f"sqlite:///{sqlite_path.as_posix()}"
    
    # Target PostgreSQL URL
    target_url = None
    if len(sys.argv) > 1 and sys.argv[1].startswith(("postgres://", "postgresql://")):
        target_url = sys.argv[1]
    else:
        target_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("SUPABASE_DB_URL")

    if not target_url or target_url.startswith("sqlite"):
        print("[-] تنبيه: لم يتم تمرير رابط اتصال PostgreSQL سحابي صالح.")
        print("    الاستخدام: python -m backend.scripts.migrate_to_supabase \"postgresql://user:pass@db.xyz.supabase.co:5432/postgres\"")
        print("    أو ضع المتغير DATABASE_URL في ملف .env")
        return

    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)

    print(f"[+] مصدر البيانات المحلي: {sqlite_url}")
    print(f"[+] وجهة البيانات السحابية (Supabase): {target_url.split('@')[-1] if '@' in target_url else 'PostgreSQL'}")

    # Initialize engines
    src_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    dst_engine = create_engine(target_url, pool_pre_ping=True)

    SrcSession = sessionmaker(bind=src_engine)
    DstSession = sessionmaker(bind=dst_engine)

    print("\n[1] إنشاء الجداول وتهيئتها على قاعدة بيانات Supabase...")
    Base.metadata.create_all(bind=dst_engine)
    print("    [✓] تم إنشاء وتأكيد وجود كافة الجداول بنجاح.")

    src_db = SrcSession()
    dst_db = DstSession()

    try:
        tables_to_migrate = [
            ("المستخدمين (Users)", User),
            ("العقارات (Properties)", Property),
            ("صور العقارات (Images)", PropertyImage),
            ("وثائق التوثيق (Documents)", VerificationDocument),
            ("طلبات التواصل (Contacts)", ContactRequest),
            ("البلاغات (Reports)", PropertyReport),
            ("سجلات التدقيق (Audit Logs)", AuditLog),
            ("المفضلة (Favorites)", Favorite),
        ]

        print("\n[2] بدء نقل السجلات...")
        for name, model in tables_to_migrate:
            records = src_db.query(model).all()
            migrated_count = 0
            for record in records:
                # Merge into destination if not already present
                dst_db.merge(record)
                migrated_count += 1
            dst_db.commit()
            print(f"    [✓] تم نقل {migrated_count} سجل من جدول {name}")

        print("\n==================================================")
        print("    تهانينا! اكتملت عملية الترحيل إلى Supabase بنجاح!   ")
        print("==================================================")

    except Exception as e:
        dst_db.rollback()
        print(f"\n[!] حدث خطأ أثناء النقل: {e}")
        raise
    finally:
        src_db.close()
        dst_db.close()

if __name__ == "__main__":
    run_migration()
