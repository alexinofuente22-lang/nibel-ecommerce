# ==========================================================
# Proyecto : NIBEL - Tienda de chompas de lana y alpaca
# Archivo  : schemas.py
# Autor    : DAIT - David Alex Inofuente Trujillo
# Función  : Esquemas Pydantic de entrada y salida de la API.
# ==========================================================

from typing import Optional

from pydantic import BaseModel, ConfigDict


# DAIT - Esquemas de productos
class ProductoCreate(BaseModel):
    id_categoria: int
    codigo: str
    nombre: str
    descripcion_lana: str
    precio: float
    stock: int
    imagen_url: Optional[str] = None


class ProductoResponse(ProductoCreate):
    model_config = ConfigDict(from_attributes=True)

    id_producto: int
    estado: bool


# DAIT - Esquemas de usuarios y login
class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    password: str


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    nombre: str
    email: str
    rol: str


class Token(BaseModel):
    access_token: str
    token_type: str
