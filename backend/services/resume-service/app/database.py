
from shared.models.base import get_engine, get_session_factory
from shared.models.tables import Base
from .config import settings

engine = get_engine(settings.database_url)
SessionLocal = get_session_factory(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
