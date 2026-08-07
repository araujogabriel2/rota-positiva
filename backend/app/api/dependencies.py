from fastapi import Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.services.supabase_auth import (
    AuthConfigurationError,
    AuthService,
    SupabaseAuthService,
)


def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthService:
    try:
        return SupabaseAuthService(settings)
    except AuthConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
