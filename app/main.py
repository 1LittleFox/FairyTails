# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.i18n_config import setup_i18n

from app.routers import (home, all_users,
                         questionnaire_options, delete_story, delete_collection, all_collection,
                         collections_detail, generation, creating_sequels, display_stories)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_i18n()
    yield
    # Shutdown (если нужно что-то выполнить при завершении)

app = FastAPI(lifespan=lifespan)


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
app.include_router(collections_detail.router)
app.include_router(generation.router)
app.include_router(display_stories.router)
app.include_router(all_users.router)
app.include_router(delete_story.router)
app.include_router(delete_collection.router)
app.include_router(all_collection.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)