# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.i18n_config import setup_i18n

from app.routers import (home,
                         questionnaire_options, user_collections, get_transletions,
                         collections_detail, generation, creating_sequels, display_stories)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    setup_i18n()


origins = [
    "http://127.0.0.1:8000",
    "https://fairytails-zrdj.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(home.router)
app.include_router(creating_sequels.router)
app.include_router(questionnaire_options.router)
app.include_router(user_collections.router)
app.include_router(collections_detail.router)
app.include_router(generation.router)
app.include_router(display_stories.router)
app.include_router(get_transletions.router)
