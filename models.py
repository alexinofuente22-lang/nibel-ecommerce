from sqlalchemy import Column, Integer, String, Numeric, Boolean, Text
from database import Base

class Producto(Base):
    __tablename__ = "productos"

    id_producto = Column(Integer, primary_key=True, index=True)
    id_categoria = Column(Integer, nullable=False)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion_lana = Column(Text, nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    imagen_url = Column(String(255))
    estado = Column(Boolean, default=True)

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), default="admin")