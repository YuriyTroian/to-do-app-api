from app.app import app
# import app.crud
# import app.crud


import uvicorn


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", log_level="info")

