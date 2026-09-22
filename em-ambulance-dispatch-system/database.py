from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings

DATABASE_URL = settings.database_url

# connect_args = {"check_same_thread": False}
# engine = create_engine(DATABASE_URL, connect_args=connect_args)
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
