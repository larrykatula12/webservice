from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hola():
    return {"mensaje": "Hola Mundo desde Render 🚀"}
