"""Aplica, em ordem, somente as migrações da fase de aprovação de usuários."""

import sys
from pathlib import Path

from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Config  # noqa: E402


MIGRATIONS = (
    PROJECT_ROOT / "infra" / "db" / "migrations" / "v004_users-approval.sql",
    PROJECT_ROOT / "infra" / "db" / "migrations" / "v005_approval-rls.sql",
)


def migration_body(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(
        line for line in lines if line.strip().upper() not in {"BEGIN;", "COMMIT;"}
    ).strip()


def main():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    if engine.dialect.name != "postgresql":
        print("Aplicação cancelada: DATABASE_URL não aponta para PostgreSQL.")
        return 1

    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))

    for path in MIGRATIONS:
        with engine.begin() as connection:
            already_applied = connection.scalar(
                text("SELECT 1 FROM schema_migrations WHERE name = :name"),
                {"name": path.name},
            )
            if already_applied:
                print(f"Já aplicada: {path.name}")
                continue
            connection.exec_driver_sql(migration_body(path))
            connection.execute(
                text("INSERT INTO schema_migrations (name) VALUES (:name)"),
                {"name": path.name},
            )
            print(f"Aplicada com sucesso: {path.name}")

    print("Estrutura de aprovação de usuários atualizada com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
