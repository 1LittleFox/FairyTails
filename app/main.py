# main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, validate_all_settings
from app.i18n_config import setup_i18n

from app.routers import (home, all_users,
                         questionnaire_options, delete_story, delete_collection, all_collection,
                         collections_detail, generation, creating_sequels, display_stories)

if not validate_all_settings():
    exit(1)

settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting application in {settings.environment} mode...")
    setup_i18n()
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    lifespan=lifespan,
    debug=settings.debug
)


cors_config = settings.get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)


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