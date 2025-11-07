from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, message
from app.core.conf import origins
from app.services.socket import SocketInit
from app.utils.utils import starter


@asynccontextmanager
async def lifespan(app: FastAPI):
    await starter()
    yield


app = FastAPI(lifespan=lifespan)
varta = SocketInit.attachToServer(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "hello world"}


app.include_router(auth.router)
app.include_router(message.router)
