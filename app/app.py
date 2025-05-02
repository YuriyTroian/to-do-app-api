from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.db import create_db_and_tables
from app.crud import router
# import app.crud

# from app.schemas import EXCreate, EXRead, EXUpdate
# from app.users import auth_backend, current_active_user, fastapi_users


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
#
# app.include_router(
#     fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
# )
# app.include_router(
#     fastapi_users.get_register_router(EXRead, EXCreate),
#     prefix="/auth",
#     tags=["auth"],
# )
# app.include_router(
#     fastapi_users.get_reset_password_router(),
#     prefix="/auth",
#     tags=["auth"],
# )
# app.include_router(
#     fastapi_users.get_verify_router(EXRead),
#     prefix="/auth",
#     tags=["auth"],
# )
# app.include_router(
#     fastapi_users.get_users_router(EXRead, EXUpdate),
#     prefix="/exercises",
#     tags=["exercises"],
# )
#
#
# @app.get("/authenticated-route")
# async def authenticated_route(exercise: Exercise = Depends(current_active_user)):
#     return {"message": f"Hello {user.email}!"}