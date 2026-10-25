# ==========================================================
# Proyecto : NIBEL - Tienda de chompas de lana y alpaca
# Archivo  : auth.py
# Autor    : DAIT - David Alex Inofuente Trujillo
# Función  : Hash de contraseñas y generación de tokens JWT.
# ==========================================================

import hashlib
import os
from datetime import datetime, timedelta, timezone

from jose import jwt

# DAIT: la clave se lee de la variable de entorno SECRET_KEY (configurar en Render)
SECRET_KEY = os.getenv("SECRET_KEY", "NIBEL_JULIACA_CLAVE_SUPER_SECRETA_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def obtener_password_hash(password: str) -> str:
    """DAIT: genera el hash SHA-256 de la contraseña."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """DAIT: compara una contraseña en texto plano con su hash guardado."""
    return obtener_password_hash(plain_password) == hashed_password


def crear_token_acceso(data: dict) -> str:
    """DAIT: crea un token JWT con vencimiento de ACCESS_TOKEN_EXPIRE_MINUTES."""
    para_codificar = data.copy()
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    para_codificar.update({"exp": expiracion})
    return jwt.encode(para_codificar, SECRET_KEY, algorithm=ALGORITHM)
