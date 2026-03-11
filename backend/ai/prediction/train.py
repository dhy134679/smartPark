
from __future__ import annotations

from pathlib import Path

try:
    import torch
    from torch import nn, optim
except ImportError:
    torch = None

from .data_generator import generate_samples
from .lstm_model import ParkingAvailabilityLSTM


def train(output_dir: Path, epochs: int = 5) -> None:

    if torch is None:
        raise RuntimeError("需要安装 PyTorch 才能训练")

    samples = generate_samples(days=30)
    features = []
    targets = []
    window = 24
    horizon = 12
    for idx in range(len(samples) - window - horizon):
        seq = samples[idx : idx + window]
        next_seq = samples[idx + window : idx + window + horizon]
        features.append(
            [
                [item.occupancy_rate, item.hour / 23, item.day_of_week / 6, int(item.is_weekend), 0]
                for item in seq
            ]
        )
        targets.append([item.occupancy_rate for item in next_seq])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ParkingAvailabilityLSTM().to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    x = torch.tensor(features, dtype=torch.float32).to(device)
    y = torch.tensor(targets, dtype=torch.float32).to(device)

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(x)
        loss = criterion(output, y)
        loss.backward()
        optimizer.step()
        print(f"epoch={epoch+1}, loss={loss.item():.4f}")

    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_dir / "lstm.pt")


if __name__ == "__main__":
    train(Path(__file__).resolve().parent / "weights")

