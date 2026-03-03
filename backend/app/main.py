"""FastAPI 入口。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, navigation, parking, predict, recognize, spots, vehicles


def create_app() -> FastAPI:
    """创建应用实例。"""

    app = FastAPI(title=settings.project_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(spots.router, prefix=settings.api_prefix)
    app.include_router(vehicles.router, prefix=settings.api_prefix)
    app.include_router(parking.router, prefix=settings.api_prefix)
    app.include_router(recognize.router, prefix=settings.api_prefix)
    app.include_router(navigation.router, prefix=settings.api_prefix)
    app.include_router(predict.router, prefix=settings.api_prefix)

    @app.on_event("startup")
    async def prepare_directories() -> None:
        """启动时准备目录。"""

        settings.upload_dir.mkdir(parents=True, exist_ok=True)

    @app.get(f"{settings.api_prefix}/health")
    async def health_check() -> dict:
        """健康检查接口。"""

        return {"code": 200, "message": "success", "data": {"status": "ok"}}

    return app


app = create_app()

