"""Verifica a conexão configurada sem criar ou modificar tabelas."""

import sys
from pathlib import Path

from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Config  # noqa: E402


def main():
    database_url = Config.SQLALCHEMY_DATABASE_URI
    if database_url.startswith("sqlite"):
        print("Conexão cancelada: DATABASE_URL ainda aponta para SQLite.")
        return 1

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            result = connection.scalar(text("SELECT 1"))
    except Exception as exc:
        print(f"Falha na conexão: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    if result != 1:
        print("Falha na conexão: resposta inesperada do banco.", file=sys.stderr)
        return 1

    print("Conexão com o PostgreSQL do Supabase: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
