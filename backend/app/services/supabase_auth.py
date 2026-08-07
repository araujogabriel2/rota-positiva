from typing import Protocol

from supabase import Client, create_client
from supabase.client import ClientOptions

from app.core.config import Settings
from app.schemas.auth import AuthenticatedUser, LoginResponse


class AuthConfigurationError(RuntimeError):
    """Configuração necessária para autenticação não foi fornecida."""


class InvalidCredentialsError(ValueError):
    """O Supabase recusou as credenciais enviadas."""


class AuthProviderError(RuntimeError):
    """O servidor de autenticação não conseguiu concluir a operação."""


class AuthService(Protocol):
    def sign_in_with_password(self, email: str, password: str) -> LoginResponse: ...


class SupabaseAuthService:
    def __init__(self, settings: Settings):
        if not settings.is_supabase_auth_configured:
            raise AuthConfigurationError(
                "Defina SUPABASE_URL e SUPABASE_PUBLISHABLE_KEY no backend/.env."
            )

        self._client: Client = create_client(
            settings.supabase_url,
            settings.supabase_publishable_key,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False,
            ),
        )

    def sign_in_with_password(self, email: str, password: str) -> LoginResponse:
        try:
            response = self._client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
        except Exception as exc:
            status = getattr(exc, "status", None)
            if status in {400, 401}:
                raise InvalidCredentialsError("E-mail ou senha incorretos.") from exc
            raise AuthProviderError(
                "Não foi possível consultar o Supabase Auth. Tente novamente."
            ) from exc

        if not response.session or not response.user or not response.user.email:
            raise AuthProviderError("O Supabase não retornou uma sessão válida.")

        return LoginResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            expires_in=response.session.expires_in,
            user=AuthenticatedUser(
                id=str(response.user.id),
                email=response.user.email,
            ),
        )
