from fastapi import FastAPI
from app.api import upload

app = FastAPI()

app.include_router(upload.router)

@app.get("/api")
def hello():
    return {"message": "Hello World"}
