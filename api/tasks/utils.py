from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.config import settings

sync_engine = create_engine(settings.DATABASE_URL_SYNC)
_SessionLocal = sessionmaker(bind=sync_engine)


def get_sync_session():
    return _SessionLocal()
