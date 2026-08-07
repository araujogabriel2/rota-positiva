from fastapi.testclient import TestClient

from app.api.dependencies import get_auth_service
from app.core.config import Settings
from app.main import create_app
from app.schemas.auth import AuthenticatedUser, LoginResponse
from app.services.supabase_auth import InvalidCredentialsError
from app.services.supabase_auth import SupabaseAuthService


class SuccessfulAuthService:
    def sign_in_with_password(self, email: str, password: str) -> LoginResponse:
        assert email == "motorista@example.com"
        assert password == "senha-segura"
        return LoginResponse(
            access_token="access-token-do-supabase",
            refresh_token="refresh-token-do-supabase",
            expires_in=3600,
            user=AuthenticatedUser(
                id="3da4585d-0d72-4db5-b53f-cfbb231a722c",
                email=email,
            ),
        )


class RejectedAuthService:
    def sign_in_with_password(self, email: str, password: str) -> LoginResponse:
        raise InvalidCredentialsError("E-mail ou senha incorretos.")


def test_supabase_auth_client_can_be_created_with_current_sdk() -> None:
    service = SupabaseAuthService(
        Settings(
            supabase_url="https://projeto-de-teste.supabase.co",
            supabase_publishable_key="sb_publishable_chave_de_teste",
        )
    )

    assert service is not None


def test_login_returns_session_issued_by_auth_service() -> None:
    app = create_app(Settings())
    app.dependency_overrides[get_auth_service] = lambda: SuccessfulAuthService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "MOTORISTA@example.com", "password": "senha-segura"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "access-token-do-supabase",
        "refresh_token": "refresh-token-do-supabase",
        "expires_in": 3600,
        "token_type": "bearer",
        "user": {
            "id": "3da4585d-0d72-4db5-b53f-cfbb231a722c",
            "email": "motorista@example.com",
        },
    }


def test_login_rejects_invalid_credentials() -> None:
    app = create_app(Settings())
    app.dependency_overrides[get_auth_service] = lambda: RejectedAuthService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "motorista@example.com", "password": "senha-errada"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "E-mail ou senha incorretos."}


def test_login_validates_email_and_password_before_calling_supabase() -> None:
    app = create_app(Settings())
    app.dependency_overrides[get_auth_service] = lambda: SuccessfulAuthService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "email-invalido", "password": "123"},
    )

    assert response.status_code == 422


def test_login_explains_when_supabase_is_not_configured() -> None:
    client = TestClient(create_app(Settings(_env_file=None)))

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "motorista@example.com", "password": "senha-segura"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Defina SUPABASE_URL e SUPABASE_PUBLISHABLE_KEY no backend/.env."
    }
