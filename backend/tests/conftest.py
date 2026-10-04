import pytest
from pathlib import Path
from backend.app.config import STORAGE_PRIVATE_DIR
from backend.app.database import SessionLocal
from backend.app.models.entities import (
    User, VerificationDocument, AuditLog, ContactRequest, Property
)

@pytest.fixture(autouse=True, scope="session")
def auto_cleanup_test_artifacts():
    """
    Session-wide fixture that automatically cleans up all temporary test files
    and test database entries created during testing, preventing file duplication
    and database pollution.
    """
    yield

    # 1. Clean up mock private documents generated during tests
    if STORAGE_PRIVATE_DIR.exists():
        for doc_file in STORAGE_PRIVATE_DIR.glob("priv_doc_*"):
            try:
                doc_file.unlink(missing_ok=True)
            except Exception:
                pass

    # 2. Clean up test users and test entities from database
    db = SessionLocal()
    try:
        # Delete contact requests created during tests
        db.query(ContactRequest).delete()

        # Delete properties created during test runs
        test_props = db.query(Property).filter(Property.title.like("شقة تحت المراجعة الإدارية%")).all()
        for prop in test_props:
            db.delete(prop)

        # Delete test users
        test_users = db.query(User).filter(
            (User.email.like("test.%")) | (User.email == "intruder.user@mawa.eg")
        ).all()
        for user in test_users:
            db.delete(user)

        # Delete test verification records
        db.query(VerificationDocument).delete()

        # Delete test audit logs
        db.query(AuditLog).filter(AuditLog.action == "VIEW_SENSITIVE_DOCUMENT").delete()

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
