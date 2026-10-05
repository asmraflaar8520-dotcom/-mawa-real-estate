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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
