from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from api.database import Base

class Usuario(Base):
    __tablename__ = "Usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(50), unique=True)
    contraseña = Column(String(255))
    correo = Column(String(100))
    rol_id = Column(Integer, ForeignKey("Roles.id"))
    activo = Column(Boolean)

    rol = relationship("Rol")

class Rol(Base):
    __tablename__ = "Roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50))

class Alumno(Base):
    __tablename__ = "Alumnos"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100))
    apellido_paterno = Column(String(100))
    apellido_materno = Column(String(100))
    usuario_id = Column(Integer, ForeignKey("Usuarios.id"))
