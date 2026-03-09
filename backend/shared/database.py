from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models.base import Base, get_engine, get_session_factory

from .config.base import BaseServiceSettings

_settings = BaseServiceSettings()

engine = create_engine(
    _settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in _settings.database_url else {},
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print(f"Database initialized successfully at {_settings.database_url}")
    except Exception as e:
        print(f"Error initializing database: {e}")
