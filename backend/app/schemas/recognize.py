
from pydantic import BaseModel


class RecognizeResponse(BaseModel):

    plate_number: str
    confidence: float
    bbox: list[int]
    is_resident: bool
    image_path: str

