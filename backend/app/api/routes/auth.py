from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_auth_service
from app.schemas.auth import ApiError, LoginRequest, LoginResponse
from app.services.supabase_auth import (
    AuthConfigurationError,
    AuthProviderError,
    AuthService,
    InvalidCredentialsError,
)

router = APIRouter(tags=["Autenticação"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": ApiError, "description": "Credenciais inválidas"},
        503: {"model": ApiError, "description": "Supabase indisponível ou não configurado"},
    },
)
def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Delega o login ao Supabase Auth e devolve a sessão emitida por ele."""
    try:
        return auth_service.sign_in_with_password(
            email=str(credentials.email).lower(),
            password=credentials.password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except (AuthConfigurationError, AuthProviderError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
