from pydantic import BaseModel

class UserLogin(BaseModel):
    username: str
    password: str

class UserData(BaseModel):
    id: int
    nombre_usuario: str
    rol: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
