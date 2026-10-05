from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.config import DATABASE_URL

connect_args = {}
engine_kwargs = {}

DB_INIT_ERROR = None

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    
    # Enforce foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL / Supabase cloud connection pooling with resilient fallback
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,      # Tests connection health before checkout to prevent disconnected SSL sockets
            pool_recycle=300,        # Recycles idle connections every 5 minutes
            pool_size=5,             # Optimized for serverless
            max_overflow=2,
            connect_args={"connect_timeout": 10}
        )
    except Exception as e:
        DB_INIT_ERROR = str(e)
        import logging
        from backend.app.config import BASE_DIR, IS_VERCEL
        from pathlib import Path
        logging.getLogger("uvicorn.error").warning(f"[DB Initialization Fallback] {e}")
        fallback_db = Path("/tmp") / "mawa.db" if IS_VERCEL else BASE_DIR / "mawa.db"
        engine = create_engine(f"sqlite:///{fallback_db.as_posix()}", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

_tables_checked = False

def ensure_db_ready():
    global _tables_checked
    if _tables_checked:
        return
    try:
        Base.metadata.create_all(bind=engine)
        if DATABASE_URL.startswith("sqlite"):
            db_check = SessionLocal()
            try:
                from backend.app.models.entities import Property
                if db_check.query(Property).count() == 0:
                    from backend.app.utils.seed_data import seed_database
                    seed_database()
            except Exception:
                pass
            finally:
                db_check.close()
        _tables_checked = True
    except Exception as e:
        import logging
        logging.getLogger("uvicorn.error").warning(f"[DB Auto-Init] {e}")

def get_db():
    if not _tables_checked:
        ensure_db_ready()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
