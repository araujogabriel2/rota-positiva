import pytest

from app.config import build_database_url


def test_database_url_falls_back_to_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_PASSWORD", raising=False)

    assert build_database_url().startswith("sqlite:///")


def test_supabase_url_uses_psycopg_and_encodes_password(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://postgres.ref:[YOUR-PASSWORD]@host.example:5432/postgres",
    )
    monkeypatch.setenv("DATABASE_PASSWORD", "senha@com:/simbolos#")

    result = build_database_url()

    assert result.startswith("postgresql+psycopg://")
    assert "senha%40com%3A%2Fsimbolos%23" in result
    assert "[YOUR-PASSWORD]" not in result


def test_missing_database_password_has_clear_error(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://postgres.ref:[YOUR-PASSWORD]@host.example:5432/postgres",
    )
    monkeypatch.delenv("DATABASE_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_PASSWORD"):
        build_database_url()
