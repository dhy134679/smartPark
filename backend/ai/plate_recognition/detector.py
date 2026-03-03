"""YOLOv5 车牌检测模块。

基于 we0091234/Chinese_license_plate_detection_recognition 项目，
使用自定义 YOLOv5 模型检测车牌区域及四角点坐标。
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import cv2
import numpy as np
import torch

# 将克隆的仓库加入搜索路径，以便导入 YOLOv5 自定义模块
_LIB_DIR = Path(__file__).resolve().parent / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from models.experimental import attempt_load  # noqa: E402
from utils.datasets import letterbox  # noqa: E402
from utils.general import (  # noqa: E402
    check_img_size,
    non_max_suppression_face,
    scale_coords,
)


def _scale_coords_landmarks(
    img1_shape: tuple, coords: torch.Tensor, img0_shape: tuple
) -> torch.Tensor:
    """将关键点坐标从推理尺寸缩放回原图尺寸。"""
    gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])
    pad = (
        (img1_shape[1] - img0_shape[1] * gain) / 2,
        (img1_shape[0] - img0_shape[0] * gain) / 2,
    )
    coords[:, [0, 2, 4, 6]] -= pad[0]
    coords[:, [1, 3, 5, 7]] -= pad[1]
    coords[:, :8] /= gain
    coords[:, 0].clamp_(0, img0_shape[1])
    coords[:, 1].clamp_(0, img0_shape[0])
    coords[:, 2].clamp_(0, img0_shape[1])
    coords[:, 3].clamp_(0, img0_shape[0])
    coords[:, 4].clamp_(0, img0_shape[1])
    coords[:, 5].clamp_(0, img0_shape[0])
    coords[:, 6].clamp_(0, img0_shape[1])
    coords[:, 7].clamp_(0, img0_shape[0])
    return coords


def _four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """透视变换：根据四角点坐标裁剪并矫正车牌区域。"""
    rect = pts.astype("float32")
    tl, tr, br, bl = rect
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))
    dst = np.array(
        [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]],
        dtype="float32",
    )
    m = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, m, (max_width, max_height))
    return warped


def _get_split_merge(img: np.ndarray) -> np.ndarray:
    """双层车牌拼接：将上下两部分水平拼接为单行。"""
    h, w, _ = img.shape
    img_upper = img[0 : int(5 / 12 * h), :]
    img_lower = img[int(1 / 3 * h) :, :]
    img_upper = cv2.resize(img_upper, (img_lower.shape[1], img_lower.shape[0]))
    return np.hstack((img_upper, img_lower))


class PlateDetector:
    """YOLOv5 车牌检测器。

    加载自定义 YOLOv5 权重，检测图片中的车牌区域，
    并通过四角点透视变换裁剪出矫正后的车牌小图。
    """

    def __init__(self, weights_path: Path | None = None, img_size: int = 640) -> None:
        self.weights_path = weights_path
        self.img_size = img_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.ready = False

        if weights_path and weights_path.exists():
            try:
                self.model = attempt_load(str(weights_path), map_location=self.device)
                self.ready = True
            except Exception as exc:
                print(f"[PlateDetector] 加载检测模型失败: {exc}")

    def detect(self, image: np.ndarray) -> list[dict]:
        """检测图片中的车牌。

        Args:
            image: BGR 格式的 OpenCV 图片。

        Returns:
            检测结果列表，每项包含：
            - bbox: [x1, y1, x2, y2]
            - confidence: 检测置信度
            - landmarks: 四角点坐标 [[x,y], ...]
            - plate_type: 0=单层, 1=双层
            - roi_img: 透视变换后的车牌小图
        """
        if not self.ready or self.model is None:
            return []

        conf_thres = 0.3
        iou_thres = 0.5
        results: list[dict] = []

        orgimg = copy.deepcopy(image)
        h0, w0 = orgimg.shape[:2]
        r = self.img_size / max(h0, w0)
        if r != 1:
            interp = cv2.INTER_AREA if r < 1 else cv2.INTER_LINEAR
            img0 = cv2.resize(orgimg, (int(w0 * r), int(h0 * r)), interpolation=interp)
        else:
            img0 = orgimg.copy()

        imgsz = check_img_size(self.img_size, s=self.model.stride.max())
        img = letterbox(img0, new_shape=imgsz)[0]
        img = img[:, :, ::-1].transpose(2, 0, 1).copy()  # BGR → RGB, HWC → CHW

        img_tensor = torch.from_numpy(img).to(self.device).float()
        img_tensor /= 255.0
        if img_tensor.ndimension() == 3:
            img_tensor = img_tensor.unsqueeze(0)

        # 推理
        pred = self.model(img_tensor)[0]
        pred = non_max_suppression_face(pred, conf_thres, iou_thres)

        for det in pred:
            if len(det):
                det[:, :4] = scale_coords(
                    img_tensor.shape[2:], det[:, :4], image.shape
                ).round()
                det[:, 5:13] = _scale_coords_landmarks(
                    img_tensor.shape[2:], det[:, 5:13], image.shape
                ).round()

                for j in range(det.size()[0]):
                    xyxy = det[j, :4].view(-1).tolist()
                    conf = float(det[j, 4].cpu().numpy())
                    landmarks = det[j, 5:13].view(-1).tolist()
                    class_num = int(det[j, 13].cpu().numpy())

                    # 构建四角点数组
                    landmarks_np = np.zeros((4, 2))
                    for k in range(4):
                        landmarks_np[k] = np.array(
                            [int(landmarks[2 * k]), int(landmarks[2 * k + 1])]
                        )

                    # 透视变换裁剪车牌
                    roi_img = _four_point_transform(image, landmarks_np)

                    # 双层车牌拼接处理
                    if class_num == 1:
                        roi_img = _get_split_merge(roi_img)

                    results.append(
                        {
                            "bbox": [int(x) for x in xyxy],
                            "confidence": round(conf, 3),
                            "landmarks": landmarks_np.tolist(),
                            "plate_type": class_num,
                            "roi_img": roi_img,
                        }
                    )

        return results
