import os
import sys
from pathlib import Path

# Force TESTING environment mode before any backend modules are imported
os.environ["TESTING"] = "1"

import pytest
from backend.app.config import STORAGE_PRIVATE_DIR, STORAGE_PUBLIC_DIR, BASE_DIR
from backend.app.database import engine, Base, SessionLocal
from backend.app.utils.seed_data import seed_database
from backend.app.models.entities import (
    User, VerificationDocument, AuditLog, ContactRequest, Property
)

@pytest.fixture(autouse=True, scope="session")
def setup_and_teardown_test_environment():
    """
    Session-wide fixture that initializes an isolated test database (test_mawa.db)
    and seeds test baseline entities, ensuring production mawa.db is NEVER touched or corrupted.
    """
    # 1. Clean build of test database schema & seed initial test accounts
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()

    yield

    # 2. Teardown: close DB sessions and engine
    try:
        from sqlalchemy.orm import close_all_sessions
        close_all_sessions()
    except Exception:
        pass
    engine.dispose()

    # 3. Clean up test private and public storage
    for test_dir in [STORAGE_PRIVATE_DIR, STORAGE_PUBLIC_DIR]:
        if test_dir.exists():
            for f in test_dir.glob("*"):
                try:
                    f.unlink(missing_ok=True)
                except Exception:
                    pass

    # 4. Remove isolated test database file
    test_db = BASE_DIR / "test_mawa.db"
    if test_db.exists():
        try:
            test_db.unlink(missing_ok=True)
        except Exception:
            pass
