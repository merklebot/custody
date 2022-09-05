from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from custody.core.config import settings

engine = create_engine(settings.DB.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
