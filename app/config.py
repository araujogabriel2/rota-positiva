import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def build_database_url():
    """Monta a URL do banco sem expor a senha no código-fonte."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return f"sqlite:///{BASE_DIR / 'instance' / 'financeiro.db'}"

    if "[YOUR-PASSWORD]" in database_url:
        password = os.environ.get("DATABASE_PASSWORD")
        if not password:
            raise RuntimeError(
                "DATABASE_PASSWORD não foi definida no arquivo .env."
            )
        database_url = database_url.replace(
            "[YOUR-PASSWORD]", quote(password, safe="")
        )

    # A connection string do Supabase usa o esquema PostgreSQL padrão.
    # O sufixo +psycopg informa ao SQLAlchemy que usamos o Psycopg 3.
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://", "postgresql+psycopg://", 1
        )

    return database_url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
    SQLALCHEMY_DATABASE_URI = build_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    JSON_AS_ASCII = False
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
    LOGIN_REQUIRED = True

