from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.db import create_db_and_tables
from app.crud import router



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
