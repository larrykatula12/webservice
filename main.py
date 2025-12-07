from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import pyodbc
import os
from passlib.context import CryptContext
import jwt

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "tu-secret-key-super-segura-cambiar-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Configuración de la base de datos
DB_SERVER = os.getenv("dbsistemapos.database.windows.net", "localhost")
DB_NAME = os.getenv("db_escuela", "escuela_db")
DB_USER = os.getenv("honorio.haro", "sa")
DB_PASSWORD = os.getenv("As123456*", "password")

app = FastAPI(title="Sistema Escolar API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# Modelos Pydantic
class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

class UserInfo(BaseModel):
    id: int
    nombre_usuario: str
    correo: Optional[str]
    rol_id: int
    rol_nombre: str

class DashboardStats(BaseModel):
    total_alumnos: int
    total_maestros: int
    total_grupos: int
    total_materias: int
    total_aulas: int

class Alumno(BaseModel):
    id: int
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str]
    fecha_nacimiento: Optional[str]
    direccion: Optional[str]
    telefono: Optional[str]

class Maestro(BaseModel):
    id: int
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str]
    especialidad: Optional[str]
    correo: Optional[str]
    telefono: Optional[str]

class Grupo(BaseModel):
    id: int
    grado: int
    letra: str
    turno: str
    cupo_maximo: int
    activo: bool

# Funciones de utilidad
def get_db_connection():
    try:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD}"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión a BD: {str(e)}")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except jwt.PyJWTError:
        raise credentials_exception

# API Endpoints
@app.get("/api/health")
def health_check():
    return {"message": "API Sistema Escolar", "status": "active"}

@app.post("/api/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT u.id, u.nombre_usuario, u.contraseña, u.correo, u.rol_id, u.activo, r.nombre as rol_nombre
            FROM Usuarios u
            LEFT JOIN Roles r ON u.rol_id = r.id
            WHERE u.nombre_usuario = ? AND u.activo = 1
        """, form_data.username)
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos"
            )
        
        if not verify_password(form_data.password, user.contraseña):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos"
            )
        
        access_token = create_access_token(data={"sub": user.nombre_usuario})
        
        user_info = {
            "id": user.id,
            "nombre_usuario": user.nombre_usuario,
            "correo": user.correo,
            "rol_id": user.rol_id,
            "rol_nombre": user.rol_nombre or "Sin rol"
        }
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_info": user_info
        }
    
    finally:
        cursor.close()
        conn.close()

@app.get("/api/me", response_model=UserInfo)
async def get_me(current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT u.id, u.nombre_usuario, u.correo, u.rol_id, r.nombre as rol_nombre
            FROM Usuarios u
            LEFT JOIN Roles r ON u.rol_id = r.id
            WHERE u.nombre_usuario = ?
        """, current_user)
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return UserInfo(
            id=user.id,
            nombre_usuario=user.nombre_usuario,
            correo=user.correo,
            rol_id=user.rol_id,
            rol_nombre=user.rol_nombre or "Sin rol"
        )
    
    finally:
        cursor.close()
        conn.close()

@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM Alumnos")
        total_alumnos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Maestros")
        total_maestros = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM grupos WHERE activo = 1")
        total_grupos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Materias WHERE Estado = 1")
        total_materias = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Aulas WHERE Estado = 1")
        total_aulas = cursor.fetchone()[0]
        
        return DashboardStats(
            total_alumnos=total_alumnos,
            total_maestros=total_maestros,
            total_grupos=total_grupos,
            total_materias=total_materias,
            total_aulas=total_aulas
        )
    
    finally:
        cursor.close()
        conn.close()

@app.get("/api/alumnos", response_model=List[Alumno])
async def get_alumnos(current_user: str = Depends(get_current_user), limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"""
            SELECT TOP {limit} id, nombre, apellido_paterno, apellido_materno, 
                   fecha_nacimiento, direccion, telefono
            FROM Alumnos
            ORDER BY apellido_paterno, apellido_materno, nombre
        """)
        
        alumnos = []
        for row in cursor.fetchall():
            alumnos.append(Alumno(
                id=row.id,
                nombre=row.nombre,
                apellido_paterno=row.apellido_paterno,
                apellido_materno=row.apellido_materno,
                fecha_nacimiento=str(row.fecha_nacimiento) if row.fecha_nacimiento else None,
                direccion=row.direccion,
                telefono=row.telefono
            ))
        
        return alumnos
    
    finally:
        cursor.close()
        conn.close()

@app.get("/api/maestros", response_model=List[Maestro])
async def get_maestros(current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, nombre, apellido_paterno, apellido_materno, 
                   especialidad, correo, telefono
            FROM Maestros
            ORDER BY apellido_paterno, apellido_materno, nombre
        """)
        
        maestros = []
        for row in cursor.fetchall():
            maestros.append(Maestro(
                id=row.id,
                nombre=row.nombre,
                apellido_paterno=row.apellido_paterno,
                apellido_materno=row.apellido_materno,
                especialidad=row.especialidad,
                correo=row.correo,
                telefono=row.telefono
            ))
        
        return maestros
    
    finally:
        cursor.close()
        conn.close()

@app.get("/api/grupos", response_model=List[Grupo])
async def get_grupos(current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, grado, letra, turno, cupo_maximo, activo
            FROM grupos
            WHERE activo = 1
            ORDER BY grado, letra
        """)
        
        grupos = []
        for row in cursor.fetchall():
            grupos.append(Grupo(
                id=row.id,
                grado=row.grado,
                letra=row.letra,
                turno=row.turno,
                cupo_maximo=row.cupo_maximo,
                activo=row.activo
            ))
        
        return grupos
    
    finally:
        cursor.close()
        conn.close()

# Servir archivos estáticos (Frontend)
# Si existe la carpeta static, la sirve
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Ruta raíz sirve el index.html
@app.get("/")
async def read_root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "API Sistema Escolar - Frontend no encontrado", "status": "active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)