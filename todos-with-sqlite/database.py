from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import settings

# DATABASE_URL = "sqlite:///./sqlite_todos_db.db"
# DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/todos"
# DATABASE_URL = "mysql+pymysql://root:mysql@localhost:3306/todos"
DATABASE_URL = settings.database_url

# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

Base = declarative_base()
