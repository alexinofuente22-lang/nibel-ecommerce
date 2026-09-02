from pydantic import BaseModel
from typing import Optional

class ProductoCreate(BaseModel):
    id_categoria: int
    codigo: str
    nombre: str
    descripcion_lana: str
    precio: float
    stock: int
    imagen_url: Optional[str] = None

class ProductoResponse(ProductoCreate):
    id_producto: int
    estado: bool

    class Config:
        from_attributes = True
# Esquemas para Usuarios y Login
class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    password: str

class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre: str
    email: str
    rol: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str