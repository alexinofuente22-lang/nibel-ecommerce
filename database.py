from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Reemplaza '1234' por la contraseña exacta de PostgreSQL
DATABASE_URL = "postgresql://postgres:alex1234@localhost:5432/nibel_db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"client_encoding": "utf8"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()