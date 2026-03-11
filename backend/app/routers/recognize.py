
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.recognize import RecognizeResponse
from app.schemas.response import success_response
from app.services import parking_service


router = APIRouter(prefix="/recognize", tags=["识别"])


def _load_pipeline_tools():

    try:
        from ai.plate_recognition.pipeline import get_pipeline, save_upload_file
    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail=f"识别服务依赖未就绪（OpenCV/模型环境异常）: {exc}",
        ) from exc

    return get_pipeline, save_upload_file


@router.post("/")
async def recognize_plate(
    file: UploadFile = File(...),
    hint_plate: str | None = Form(None),
    session: AsyncSession = Depends(get_db),
) -> dict:

    get_pipeline, save_upload_file = _load_pipeline_tools()
    saved_path = save_upload_file(file, settings.upload_dir)
    pipeline = get_pipeline()
    try:
        result = pipeline.process(saved_path, fallback_plate=hint_plate)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    vehicle = await parking_service.get_vehicle_by_plate(session, result.plate_number)
    response = RecognizeResponse(
        plate_number=result.plate_number,
        confidence=result.confidence,
        bbox=result.bbox,
        is_resident=bool(vehicle and vehicle.is_resident),
        image_path=result.image_path,
    )
    return success_response(response.model_dump())
