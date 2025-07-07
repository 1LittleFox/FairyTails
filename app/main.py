from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import  home, connect_gpt, create_storyteller

app = FastAPI()

origins = [
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8000/create_storyteller",
    "http://127.0.0.1:8000/home",
    "http://127.0.0.1:8000/generate-tale"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(home.router)
app.include_router(connect_gpt.router)
app.include_router(create_storyteller.router)