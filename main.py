from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def hola():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hola Mundo</title>
        <style>
            body {
                background-color: white;
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            h1 {
                font-size: 3em;
                color: #222;
            }
        </style>
    </head>
    <body>
        <h1> Javier Gabriel López Acosta - 22031006</h1>
    </body>
    </html>
    """
