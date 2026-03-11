
from pathlib import Path
from typing import List, Tuple

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_ignore_empty=True,
    )

    project_name: str = "智能停车场系统"
    api_prefix: str = "/api"
    database_url: str = (
        "mysql+aiomysql://root:password@127.0.0.1:3306/smart_parking?charset=utf8mb4"
    )
    jwt_secret_key: str = "change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    allowed_origins: list[str] = ["*"]
    upload_dir: Path = Path(__file__).resolve().parents[1] / "uploads"

    navigation_grid_width: int = 24
    navigation_grid_height: int = 18
    navigation_entry: Tuple[int, int] = (0, 0)
    navigation_blocked_cells: List[Tuple[int, int]] = []


settings = Settings()

