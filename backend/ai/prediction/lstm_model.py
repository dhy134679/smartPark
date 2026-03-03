"""LSTM 预测模型定义（可选训练使用）。"""

from __future__ import annotations

try:
    import torch
    from torch import nn
except ImportError:  # pragma: no cover - 未安装 PyTorch 时跳过
    torch = None
    nn = object  # type: ignore


class ParkingAvailabilityLSTM(nn.Module):  # type: ignore[misc]
    """两层 LSTM 网络，输入 24×5，输出 12 步预测。"""

    def __init__(self, input_size: int = 5, hidden_sizes: tuple[int, int] = (128, 64)) -> None:
        if torch is None:
            raise RuntimeError("未安装 PyTorch，无法初始化 LSTM 模型")
        super().__init__()
        self.lstm1 = nn.LSTM(input_size, hidden_sizes[0], batch_first=True)
        self.dropout1 = nn.Dropout(0.2)
        self.lstm2 = nn.LSTM(hidden_sizes[0], hidden_sizes[1], batch_first=True)
        self.dropout2 = nn.Dropout(0.2)
        self.fc = nn.Linear(hidden_sizes[1], 12)

    def forward(self, x):  # type: ignore[override]
        out, _ = self.lstm1(x)
        out = self.dropout1(out)
        out, _ = self.lstm2(out)
        out = self.dropout2(out[:, -1, :])
        return self.fc(out)

