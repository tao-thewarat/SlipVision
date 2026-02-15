import logging

from fastapi import APIRouter, File, UploadFile

from app.services.ocr.google_engine import OCRService

router = APIRouter()
_logger = logging.getLogger(__name__)


ocr_service = OCRService()


@router.post("/ocr/slip")
async def ocr(file: UploadFile = File(...)):  # noqa: B008
    try:
        ocr_service.validate_image(file.content_type)
        file_bytes = await file.read()
        result = ocr_service.process(file_bytes)

        _logger.info(f"OCR slip success: {result}")

        return result
        # return {
        #     "message": "success",
        #     "code": 200,
        # }
    except Exception as e:
        _logger.error(f"OCR slip failed: {e}")
        return {
            "message": "error",
            "code": 500,
            "error": str(e),
        }
