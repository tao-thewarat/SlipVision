from fastapi import FastAPI

from app.api.v1 import ocr
from app.core.logging import setup_logging

setup_logging()
app = FastAPI(title="SlipVision API")

app.include_router(
    ocr.router,
    prefix="/api/v1",
    tags=["OCR"],
)


@app.get("/")
def read_root():
    return {"status": "ok"}
