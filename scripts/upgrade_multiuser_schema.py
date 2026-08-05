"""Atualiza o PostgreSQL existente para o modelo multiusuário."""

import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Config  # noqa: E402
from app.models import User  # noqa: E402
from app.services.auth import generate_temporary_password  # noqa: E402


def quoted(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def main():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    if engine.dialect.name != "postgresql":
        print("Atualização cancelada: este script é exclusivo para PostgreSQL.")
        return 1

    temporary_password = None
    with engine.begin() as connection:
        User.__table__.create(bind=connection, checkfirst=True)
        inspector = inspect(connection)

        for table_name in ("daily_records", "categories"):
            columns = {column["name"] for column in inspector.get_columns(table_name)}
            if "user_id" not in columns:
                connection.execute(text(
                    f"ALTER TABLE {quoted(table_name)} ADD COLUMN user_id INTEGER"
                ))

        admin_row = connection.execute(text(
            "SELECT id FROM users WHERE role = 'admin' ORDER BY id LIMIT 1"
        )).first()
        if admin_row:
            admin_id = admin_row.id
        else:
            temporary_password = generate_temporary_password()
            admin = User(
                name="Administrador",
                username=Config.ADMIN_USERNAME.lower(),
                role="admin",
                status="active",
                is_active_account=True,
                must_change_password=True,
            )
            admin.set_password(temporary_password)
            result = connection.execute(
                User.__table__.insert().values(
                    name=admin.name,
                    username=admin.username,
                    password_hash=admin.password_hash,
                    role=admin.role,
                    status="active",
                    is_active_account=True,
                    must_change_password=True,
                ).returning(User.id)
            )
            admin_id = result.scalar_one()

        connection.execute(text(
            "UPDATE daily_records SET user_id = :admin_id WHERE user_id IS NULL"
        ), {"admin_id": admin_id})
        connection.execute(text(
            "UPDATE categories SET user_id = :admin_id WHERE user_id IS NULL"
        ), {"admin_id": admin_id})

        inspector = inspect(connection)
        for table_name, old_column, new_constraint in (
            ("daily_records", "date", "uq_daily_records_user_date"),
            ("categories", "name", "uq_categories_user_name"),
        ):
            unique_constraints = inspector.get_unique_constraints(table_name)
            for constraint in unique_constraints:
                if constraint.get("column_names") == [old_column] and constraint.get("name"):
                    connection.execute(text(
                        f"ALTER TABLE {quoted(table_name)} DROP CONSTRAINT {quoted(constraint['name'])}"
                    ))

            foreign_keys = inspector.get_foreign_keys(table_name)
            if not any(fk.get("constrained_columns") == ["user_id"] for fk in foreign_keys):
                connection.execute(text(
                    f"ALTER TABLE {quoted(table_name)} ADD CONSTRAINT "
                    f"{quoted('fk_' + table_name + '_user_id')} FOREIGN KEY (user_id) REFERENCES users(id)"
                ))

            connection.execute(text(
                f"ALTER TABLE {quoted(table_name)} ALTER COLUMN user_id SET NOT NULL"
            ))

            refreshed = inspect(connection).get_unique_constraints(table_name)
            if not any(item.get("name") == new_constraint for item in refreshed):
                connection.execute(text(
                    f"ALTER TABLE {quoted(table_name)} ADD CONSTRAINT {quoted(new_constraint)} "
                    f"UNIQUE (user_id, {quoted(old_column)})"
                ))

    print("Estrutura multiusuário atualizada com sucesso.")
    print(f"Usuário administrador: {Config.ADMIN_USERNAME.lower()}")
    if temporary_password:
        print(f"Senha temporária do administrador: {temporary_password}")
        print("Copie esta senha agora. Ela não será exibida novamente.")
    else:
        print("A conta administradora já existia; nenhuma senha foi alterada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
