# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import  (home, connect_gpt,
                          create_storyteller, questionnaire_options, fairytales_section, user_collections, collections_detail)

app = FastAPI()

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
app.include_router(connect_gpt.router)
app.include_router(create_storyteller.router)
app.include_router(questionnaire_options.router)
app.include_router(fairytales_section.router)
app.include_router(user_collections.router)
app.include_router(collections_detail.router)