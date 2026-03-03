"""车牌识别数据模型。"""

from pydantic import BaseModel


class RecognizeResponse(BaseModel):
    """识别返回。"""

    plate_number: str
    confidence: float
    bbox: list[int]
    is_resident: bool
    image_path: str

