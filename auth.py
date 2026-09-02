import hashlib
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "NIBEL_JULIACA_CLAVE_SUPER_SECRETA_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def obtener_password_hash(password: str) -> str:
    # Genera un hash SHA-256 seguro
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    return obtener_password_hash(plain_password) == hashed_password

def crear_token_acceso(data: dict):
    para_codificar = data.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    para_codificar.update({"exp": expiracion})
    return jwt.encode(para_codificar, SECRET_KEY, algorithm=ALGORITHM)