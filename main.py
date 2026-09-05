import os
import requests
import shutil
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text

import models, schemas, auth
from database import get_db, engine, SessionLocal

app = FastAPI(
    title="NIBEL API - Chompas de Lana Auténtica",
    description="Sistema Backend completo con CRUD y Autenticación JWT para NIBEL."
)

# Crear tablas en PostgreSQL si aún no existen
models.Base.metadata.create_all(bind=engine)

# ==========================================
# CREACIÓN AUTOMÁTICA DEL ADMINISTRADOR
# ==========================================
def inicializar_admin():
    db = SessionLocal()
    try:
        query_check = text("SELECT id_usuario FROM usuarios WHERE email = :email")
        existe = db.execute(query_check, {"email": "admin@nibel.pe"}).fetchone()
        if not existe:
            hashed_pwd = auth.obtener_password_hash("Nibel2026!")
            query_insert = text("""
                INSERT INTO usuarios (nombre, email, password_hash, rol) 
                VALUES ('Administrador NIBEL', 'admin@nibel.pe', :password, 'admin')
            """)
            db.execute(query_insert, {"password": hashed_pwd})
            db.commit()
            print("--> Usuario admin@nibel.pe creado con éxito.")
    except Exception as e:
        print(f"Error al inicializar admin: {e}")
    finally:
        db.close()

# Ejecutar la creación al arrancar
inicializar_admin()

# Permitir peticiones desde la página web (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear la carpeta de imágenes si no existe y montarla como estática
os.makedirs("imagenes", exist_ok=True)
app.mount("/imagenes", StaticFiles(directory="imagenes"), name="imagenes")

# ==========================================
# RUTAS DE PRODUCTOS (CRUD COMPLETO)
# ==========================================

# 1. Subir imagen de chompa a ImgBB (Almacenamiento permanente)
@app.post("/productos/subir-imagen")
def subir_imagen(archivo: UploadFile = File(...)):
    api_key = os.getenv("IMGBB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Falta configurar IMGBB_API_KEY en las variables de entorno")

    extensiones_validas = [".jpg", ".jpeg", ".png", ".webp"]
    extension = os.path.splitext(archivo.filename)[1].lower()

    if extension not in extensiones_validas:
        raise HTTPException(
            status_code=400, 
            detail="Formato de imagen no permitido. Usa JPG, PNG o WEBP."
        )

    try:
        # Enviar la imagen directamente a la API de ImgBB
        url_imgbb = "https://api.imgbb.com/1/upload"
        payload = {"key": api_key}
        archivos = {"image": (archivo.filename, archivo.file, archivo.content_type)}

        respuesta = requests.post(url_imgbb, data=payload, files=archivos)
        datos_respuesta = respuesta.json()

        if respuesta.status_code == 200 and datos_respuesta.get("success"):
            # Extraer la URL directa de la imagen
            url_permanente = datos_respuesta["data"]["url"]
            return {"imagen_url": url_permanente}
        else:
            detalle_error = datos_respuesta.get("error", {}).get("message", "Fallo al subir a ImgBB")
            raise HTTPException(status_code=400, detail=detalle_error)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el servidor de imágenes: {str(e)}")

# 2. Obtener todos los productos (Catálogo)
@app.get("/productos", response_model=List[schemas.ProductoResponse])
def listar_productos(db: Session = Depends(get_db)):
    return db.query(models.Producto).all()

# 3. Obtener un producto por ID
@app.get("/productos/{producto_id}", response_model=schemas.ProductoResponse)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id_producto == producto_id).first()
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
    query = db.query(models.Producto).filter(models.Producto.id_producto == producto_id)
    producto_existente = query.first()

    if not producto_existente:
        raise HTTPException(status_code=404, detail="Producto NIBEL no encontrado")

    query.update(datos.model_dump(), synchronize_session=False)
    db.commit()
    return query.first()

# 6. Eliminar producto
@app.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    query = db.query(models.Producto).filter(models.Producto.id_producto == producto_id)
    if not query.first():
        raise HTTPException(status_code=404, detail="Producto NIBEL no encontrado")

    query.delete(synchronize_session=False)
    db.commit()
    return None

# ==========================================
# RUTAS DE AUTENTICACIÓN Y USUARIOS
# ==========================================

# Registrar usuario/administrador manual
@app.post("/usuarios/registro", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    query_check = text("SELECT id_usuario FROM usuarios WHERE email = :email")
    existe = db.execute(query_check, {"email": usuario.email}).fetchone()
    if existe:
        raise HTTPException(status_code=400, detail="El correo ya está registrado en NIBEL")

    hashed_pwd = auth.obtener_password_hash(usuario.password)

    query_insert = text("""
        INSERT INTO usuarios (nombre, email, password_hash, rol) 
        VALUES (:nombre, :email, :password, 'admin') 
        RETURNING id_usuario, nombre, email, rol
    """)
    nuevo = db.execute(query_insert, {
        "nombre": usuario.nombre, 
        "email": usuario.email, 
        "password": hashed_pwd
    }).fetchone()
    db.commit()

    return {
        "id_usuario": nuevo[0],
        "nombre": nuevo[1],
        "email": nuevo[2],
        "rol": nuevo[3]
    }

# Login para obtener Token JWT
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