from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from api.database import SessionLocal
import api.auth as auth, api.crud as crud
from api.schemas import Token
from fastapi import Depends
from api.auth import get_current_user

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# LOGIN
@app.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = auth.create_token({"sub": str(user.id)})
    return {"access_token": token}

# DATOS GENERALES DEL USUARIO
@app.get("/usuario/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user