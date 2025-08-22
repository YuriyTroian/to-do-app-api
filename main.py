from app.app import app


import uvicorn

from fastapi.middleware.cors import CORSMiddleware




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", log_level="info", reload=True)


