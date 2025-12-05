from sqlalchemy.orm import Session
from api.models import Usuario, Rol, Alumno

def get_user_data(db: Session, user_id: int):
    user = db.query(Usuario).filter(Usuario.id == user_id).first()

    if not user:
        return None
    
    role = db.query(Rol).filter(Rol.id == user.rol_id).first()

    data = {
        "id": user.id,
        "usuario": user.nombre_usuario,
        "correo": user.correo,
        "rol": role.nombre if role else "N/A"
    }

    # Si es alumno, devolver datos extra
    alumno = db.query(Alumno).filter(Alumno.usuario_id == user.id).first()
    if alumno:
        data["nombre"] = alumno.nombre
        data["apellido_paterno"] = alumno.apellido_paterno

    return data
