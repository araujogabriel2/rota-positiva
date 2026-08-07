from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Saúde da aplicação"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    application: str
    api_version: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Confirma que a API está pronta para receber requisições."""
    return HealthResponse(
        status="ok",
        application="Rota Positiva API",
        api_version="v1",
    )
