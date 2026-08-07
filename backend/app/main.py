from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Cria a aplicação permitindo substituir configurações nos testes."""
    app_settings = settings or get_settings()

    application = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        description="API financeira do Rota Positiva.",
    )

    if settings is not None:
        application.dependency_overrides[get_settings] = lambda: app_settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    application.include_router(api_router, prefix=app_settings.api_v1_prefix)
    return application


app = create_app()
