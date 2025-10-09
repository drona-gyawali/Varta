from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.services.socket import SocketInit
from fastapi.staticfiles import StaticFiles
from app.api.v1 import auth
import os

app = FastAPI()


app.mount("/static", StaticFiles(directory="frontend", html=True), name="static")

varta = SocketInit.attachToServer(app)


app.include_router(auth.router)


@app.get("/")
def serve_frontend():
    index_path = os.path.join("frontend", "index.html")
    return FileResponse(index_path)