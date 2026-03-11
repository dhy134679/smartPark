
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import time
from uuid import uuid4

import cv2
import numpy as np

from app.config import settings
from ai.plate_recognition.detector import PlateDetector
from ai.plate_recognition.recognizer import PlateRecognizer


@dataclass
class PlateRecognitionResult:

    plate_number: str
    confidence: float
    bbox: list[int]
    is_resident: bool
    image_path: str
    plate_color: str = ""


class PlateRecognitionPipeline:

    def __init__(self, weights_dir: Path | None = None) -> None:
        weights_dir = weights_dir or (
            Path(__file__).resolve().parent / "weights"
        )
        detector_weights = weights_dir / "plate_detect.pt"
        recognizer_weights = weights_dir / "plate_rec_color.pth"

        self.detector = PlateDetector(detector_weights)
        self.recognizer = PlateRecognizer(recognizer_weights, is_color=True)

    def process(
        self, image_path: Path, fallback_plate: str | None = None
    ) -> PlateRecognitionResult:

        img = cv2.imdecode(
            np.fromfile(str(image_path), dtype=np.uint8), cv2.IMREAD_COLOR
        )
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")


        if img.shape[-1] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


        if self.detector.ready and self.recognizer.ready:
            detections = self.detector.detect(img)
            if not detections:
                raise ValueError("未检测到车牌")


            best = max(detections, key=lambda d: d["confidence"])
            recog = self.recognizer.recognize(best["roi_img"])

            return PlateRecognitionResult(
                plate_number=recog["plate_number"],
                confidence=recog["confidence"],
                bbox=best["bbox"],
                is_resident=False,
                image_path=str(image_path),
                plate_color=recog.get("plate_color", ""),
            )


        import re

        hint = fallback_plate
        if not hint:
            match = re.search(
                r"[京津沪渝冀晋蒙辽吉黑苏浙皖闽赣鲁豫鄂湘粤桂琼川贵云藏陕甘青宁新学警港澳挂使领民航危][A-Z][A-Z0-9]{5}",
                image_path.name,
            )
            hint = match.group(0) if match else None

        return PlateRecognitionResult(
            plate_number=hint or "未知",
            confidence=0.5 if hint else 0.0,
            bbox=[0, 0, 0, 0],
            is_resident=False,
            image_path=str(image_path),
        )


_pipeline_instance: PlateRecognitionPipeline | None = None


def get_pipeline() -> PlateRecognitionPipeline:

    global _pipeline_instance
    if not _pipeline_instance:
        _pipeline_instance = PlateRecognitionPipeline()
    return _pipeline_instance


def save_upload_file(upload_file, dest_dir: Path) -> Path:

    dest_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload_file.filename or "plate.jpg").suffix or ".jpg"
    file_path = dest_dir / f"plate_{int(time() * 1000)}_{uuid4().hex[:8]}{suffix}"
    content = upload_file.file.read()
    file_path.write_bytes(content)
    upload_file.file.close()
    return file_path
