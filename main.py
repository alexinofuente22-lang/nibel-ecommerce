# ==========================================================
# Proyecto : NIBEL - Tienda de chompas de lana y alpaca
# Archivo  : main.py
# Autor    : DAIT - David Alex Inofuente Trujillo
# Función  : API REST (FastAPI): CRUD de productos, subida de
#            imágenes a ImgBB y autenticación con JWT.
# ==========================================================

import os
from typing import List

import requests
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import get_db, engine, SessionLocal

app = FastAPI(
    title="NIBEL API - Chompas de Lana Auténtica",
    description="Backend con CRUD y autenticación JWT para NIBEL. Desarrollado por DAIT.",
    contact={"name": "DAIT - David Alex Inofuente Trujillo"},
)

# DAIT: crear las tablas en la base de datos si aún no existen
models.Base.metadata.create_all(bind=engine)


# ==========================================================
# DAIT - CREACIÓN AUTOMÁTICA DEL ADMINISTRADOR
# ==========================================================
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@nibel.pe")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def inicializar_admin():
    """DAIT: crea el usuario administrador si aún no existe en la base de datos."""
    if not ADMIN_PASSWORD:
        print("--> ADMIN_PASSWORD no configurada: se omite la creación del administrador.")
        return

    db = SessionLocal()
    try:
        query_check = text("SELECT id_usuario FROM usuarios WHERE email = :email")
        existe = db.execute(query_check, {"email": ADMIN_EMAIL}).fetchone()
        if not existe:
            query_insert = text("""
                INSERT INTO usuarios (nombre, email, password_hash, rol)
                VALUES ('Administrador NIBEL', :email, :password, 'admin')
            """)
            db.execute(query_insert, {
                "email": ADMIN_EMAIL,
                "password": auth.obtener_password_hash(ADMIN_PASSWORD),
            })
            db.commit()
            print(f"--> Usuario {ADMIN_EMAIL} creado con éxito.")
    except Exception as e:
        print(f"Error al inicializar admin: {e}")
    finally:
        db.close()


inicializar_admin()

# DAIT: permitir peticiones desde la página web (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DAIT: carpeta local de imágenes servida como archivos estáticos
os.makedirs("imagenes", exist_ok=True)
app.mount("/imagenes", StaticFiles(directory="imagenes"), name="imagenes")


# ==========================================================
# DAIT - RUTAS DE PRODUCTOS (CRUD)
# ==========================================================
EXTENSIONES_VALIDAS = [".jpg", ".jpeg", ".png", ".webp"]
URL_IMGBB = "https://api.imgbb.com/1/upload"


def buscar_producto(producto_id: int, db: Session):
    """DAIT: consulta base de un producto por su ID."""
    return db.query(models.Producto).filter(models.Producto.id_producto == producto_id)


# 1. Subir imagen de la chompa a ImgBB (almacenamiento permanente)
@app.post("/productos/subir-imagen")
def subir_imagen(archivo: UploadFile = File(...)):
    api_key = os.getenv("IMGBB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Falta configurar IMGBB_API_KEY en las variables de entorno")

    extension = os.path.splitext(archivo.filename)[1].lower()
    if extension not in EXTENSIONES_VALIDAS:
        raise HTTPException(status_code=400, detail="Formato de imagen no permitido. Usa JPG, PNG o WEBP.")

    try:
        archivos = {"image": (archivo.filename, archivo.file, archivo.content_type)}
        respuesta = requests.post(URL_IMGBB, data={"key": api_key}, files=archivos)
        datos_respuesta = respuesta.json()

        if respuesta.status_code == 200 and datos_respuesta.get("success"):
            return {"imagen_url": datos_respuesta["data"]["url"]}

        detalle_error = datos_respuesta.get("error", {}).get("message", "Fallo al subir a ImgBB")
        raise HTTPException(status_code=400, detail=detalle_error)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el servidor de imágenes: {str(e)}")


# 2. Listar todos los productos (catálogo)
@app.get("/productos", response_model=List[schemas.ProductoResponse])
def listar_productos(db: Session = Depends(get_db)):
    return db.query(models.Producto).all()


# 3. Obtener un producto por ID
@app.get("/productos/{producto_id}", response_model=schemas.ProductoResponse)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = buscar_producto(producto_id, db).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto NIBEL no encontrado")
    return producto


# 4. Crear producto
@app.post("/productos", response_model=schemas.ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    nuevo_producto = models.Producto(**producto.model_dump())
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto


# 5. Actualizar producto
@app.put("/productos/{producto_id}", response_model=schemas.ProductoResponse)
def actualizar_producto(producto_id: int, datos: schemas.ProductoCreate, db: Session = Depends(get_db)):
    query = buscar_producto(producto_id, db)
    if not query.first():
        raise HTTPException(status_code=404, detail="Producto NIBEL no encontrado")

    query.update(datos.model_dump(), synchronize_session=False)
    db.commit()
    return query.first()


# 6. Eliminar producto
@app.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    query = buscar_producto(producto_id, db)
    if not query.first():
        raise HTTPException(status_code=404, detail="Producto NIBEL no encontrado")

    query.delete(synchronize_session=False)
    db.commit()
    return None


# ==========================================================
# DAIT - RUTAS DE AUTENTICACIÓN Y USUARIOS
# ==========================================================

# Registrar un usuario administrador
@app.post("/usuarios/registro", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    query_check = text("SELECT id_usuario FROM usuarios WHERE email = :email")
    if db.execute(query_check, {"email": usuario.email}).fetchone():
        raise HTTPException(status_code=400, detail="El correo ya está registrado en NIBEL")

    query_insert = text("""
        INSERT INTO usuarios (nombre, email, password_hash, rol)
        VALUES (:nombre, :email, :password, 'admin')
        RETURNING id_usuario, nombre, email, rol
    """)
    nuevo = db.execute(query_insert, {
        "nombre": usuario.nombre,
        "email": usuario.email,
        "password": auth.obtener_password_hash(usuario.password),
    }).fetchone()
    db.commit()

    return {"id_usuario": nuevo[0], "nombre": nuevo[1], "email": nuevo[2], "rol": nuevo[3]}


# Login: devuelve un token JWT
@app.post("/token", response_model=schemas.Token)
def login_para_obtener_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    query = text("SELECT id_usuario, email, password_hash FROM usuarios WHERE email = :email")
    usuario = db.execute(query, {"email": form_data.username}).fetchone()

    if not usuario or not auth.verificar_password(form_data.password, usuario[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.crear_token_acceso(data={"sub": usuario[1], "id": usuario[0]})
    return {"access_token": access_token, "token_type": "bearer"}
