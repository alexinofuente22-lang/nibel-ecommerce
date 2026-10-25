# ==========================================================
# Proyecto : NIBEL - Tienda de chompas de lana y alpaca
# Archivo  : database.py
# Autor    : DAIT - David Alex Inofuente Trujillo
# Función  : Conexión a la base de datos (PostgreSQL en Render,
#            SQLite en desarrollo local).
# ==========================================================

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# DAIT: URL de conexión configurada como variable de entorno en Render
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test.db"
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """DAIT: abre una sesión por petición y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
