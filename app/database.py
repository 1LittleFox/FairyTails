import os
from typing import Annotated
from app.config import settings

from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Session

load_dotenv()

#Получение из env url
DATABASE_URL = settings.database_url

#Создание асинхронного движка
engine = create_async_engine(DATABASE_URL, echo=False)

new_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with new_session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]