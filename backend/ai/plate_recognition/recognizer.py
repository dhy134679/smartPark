"""车牌字符识别模块。

基于 we0091234/Chinese_license_plate_detection_recognition 项目，
使用 myNet_ocr_color 网络识别车牌字符及颜色。
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn  # noqa: F401

# 将克隆的仓库加入搜索路径
_LIB_DIR = Path(__file__).resolve().parent / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from plate_recognition.plateNet import myNet_ocr_color  # noqa: E402

# 车牌字符映射表
PLATE_CHARS = r"#京沪津渝冀晋蒙辽吉黑苏浙皖闽赣鲁豫鄂湘粤桂琼川贵云藏陕甘青宁新学警港澳挂使领民航危0123456789ABCDEFGHJKLMNPQRSTUVWXYZ险品"

# 颜色映射
COLOR_LIST = ["黑色", "蓝色", "绿色", "白色", "黄色"]

# 归一化参数
MEAN_VALUE = 0.588
STD_VALUE = 0.193


def _decode_plate(preds: list[int]) -> tuple[list[int], list[int]]:
    """CTC 解码：去除空白符和重复字符。"""
    pre = 0
    new_preds = []
    indices = []
    for i, p in enumerate(preds):
        if p != 0 and p != pre:
            new_preds.append(p)
            indices.append(i)
        pre = p
    return new_preds, indices


def _preprocess_plate_image(
    img: np.ndarray, device: torch.device
) -> torch.Tensor:
    """车牌图像预处理：resize → 归一化 → 转 Tensor。"""
    img = cv2.resize(img, (168, 48))
    img = np.reshape(img, (48, 168, 3))
    img = img.astype(np.float32)
    img = (img / 255.0 - MEAN_VALUE) / STD_VALUE
    img = img.transpose([2, 0, 1])
    img = torch.from_numpy(img)
    img = img.to(device)
    img = img.view(1, *img.size())
    return img


class PlateRecognizer:
    """车牌字符识别器。

    加载 OCR 权重（含颜色分支），对裁剪的车牌小图进行字符识别。
    """

    def __init__(
        self, weights_path: Path | None = None, is_color: bool = True
    ) -> None:
        self.weights_path = weights_path
        self.is_color = is_color
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.ready = False

        if weights_path and weights_path.exists():
            try:
                self._load_model(weights_path)
                self.ready = True
            except Exception as exc:
                print(f"[PlateRecognizer] 加载识别模型失败: {exc}")

    def _load_model(self, model_path: Path) -> None:
        """从 checkpoint 加载模型。"""
        check_point = torch.load(str(model_path), map_location=self.device, weights_only=False)
        model_state = check_point["state_dict"]
        cfg = check_point["cfg"]
        color_classes = 5 if self.is_color else 0
        self.model = myNet_ocr_color(
            num_classes=len(PLATE_CHARS),
            export=True,
            cfg=cfg,
            color_num=color_classes,
        )
        self.model.load_state_dict(model_state, strict=False)
        self.model.to(self.device)
        self.model.eval()

    def recognize(self, roi_img: np.ndarray) -> dict:
        """识别车牌小图中的字符。

        Args:
            roi_img: 透视变换后的车牌 BGR 小图。

        Returns:
            包含以下字段的字典：
            - plate_number: 识别出的车牌号
            - confidence: 平均字符置信度
            - plate_color: 车牌颜色（如果启用颜色识别）
            - color_confidence: 颜色置信度
        """
        if not self.ready or self.model is None:
            return {
                "plate_number": "未知",
                "confidence": 0.0,
                "plate_color": "",
                "color_confidence": 0.0,
            }

        input_tensor = _preprocess_plate_image(roi_img, self.device)

        plate_color = ""
        color_conf = 0.0

        with torch.no_grad():
            if self.is_color:
                preds, color_preds = self.model(input_tensor)
                color_preds = torch.softmax(color_preds, dim=-1)
                color_conf_t, color_index = torch.max(color_preds, dim=-1)
                color_conf = float(color_conf_t.item())
                plate_color = COLOR_LIST[int(color_index.item())]
            else:
                preds = self.model(input_tensor)

        # CTC 解码
        preds = torch.softmax(preds, dim=-1)
        prob, index = preds.max(dim=-1)
        index = index.view(-1).detach().cpu().numpy()
        prob = prob.view(-1).detach().cpu().numpy()

        decoded_chars, new_index = _decode_plate(index.tolist())
        char_probs = prob[new_index]

        # 拼接车牌号
        plate_number = "".join(PLATE_CHARS[i] for i in decoded_chars)
        avg_confidence = float(np.mean(char_probs)) if len(char_probs) > 0 else 0.0

        return {
            "plate_number": plate_number,
            "confidence": round(avg_confidence, 3),
            "plate_color": plate_color,
            "color_confidence": round(color_conf, 3),
        }
