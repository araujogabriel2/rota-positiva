"""Migra os dados locais do SQLite para o PostgreSQL configurado no .env."""

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine, func, insert, select


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Config  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Category, DailyRecord, Expense  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(
        description="Copia categorias, registros e despesas do SQLite para o PostgreSQL."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=PROJECT_ROOT / "instance" / "financeiro.db",
        help="Caminho do banco SQLite de origem.",
    )
    return parser.parse_args()


def migrate(source_path):
    source_path = source_path.resolve()
    if not source_path.is_file():
        raise RuntimeError(f"Banco SQLite não encontrado: {source_path}")

    target_url = Config.SQLALCHEMY_DATABASE_URI
    if target_url.startswith("sqlite"):
        raise RuntimeError(
            "DATABASE_URL não aponta para PostgreSQL. Confira o arquivo .env."
        )

    source_engine = create_engine(f"sqlite:///{source_path.as_posix()}")
    target_engine = create_engine(target_url, pool_pre_ping=True)

    return copy_data(source_engine, target_engine)


def copy_data(source_engine, target_engine):
    """Copia os dados entre engines; separada para permitir teste isolado."""

    category_table = Category.__table__
    record_table = DailyRecord.__table__
    expense_table = Expense.__table__

    # Cria somente tabelas ausentes. Nenhuma tabela existente é apagada.
    db.metadata.create_all(target_engine)

    with source_engine.connect() as source:
        source_categories = source.execute(
            select(category_table).order_by(category_table.c.id)
        ).mappings().all()
        source_records = source.execute(
            select(record_table).order_by(record_table.c.id)
        ).mappings().all()
        source_expenses = source.execute(
            select(expense_table).order_by(expense_table.c.id)
        ).mappings().all()

    with target_engine.begin() as target:
        target_record_count = target.scalar(
            select(func.count()).select_from(record_table)
        )
        target_expense_count = target.scalar(
            select(func.count()).select_from(expense_table)
        )
        if target_record_count or target_expense_count:
            raise RuntimeError(
                "O banco de destino já possui registros ou despesas. "
                "A migração foi cancelada para evitar dados duplicados."
            )

        existing_categories = {
            row["name"]: row["id"]
            for row in target.execute(
                select(category_table.c.id, category_table.c.name)
            ).mappings()
        }
        category_ids = {}
        for category in source_categories:
            category_id = existing_categories.get(category["name"])
            if category_id is None:
                category_id = target.execute(
                    insert(category_table)
                    .values(
                        name=category["name"],
                        is_default=category["is_default"],
                        created_at=category["created_at"],
                    )
                    .returning(category_table.c.id)
                ).scalar_one()
            category_ids[category["id"]] = category_id

        record_ids = {}
        for record in source_records:
            record_id = target.execute(
                insert(record_table)
                .values(
                    date=record["date"],
                    gross_revenue=record["gross_revenue"],
                    kilometers=record["kilometers"],
                    notes=record["notes"],
                    created_at=record["created_at"],
                    updated_at=record["updated_at"],
                )
                .returning(record_table.c.id)
            ).scalar_one()
            record_ids[record["id"]] = record_id

        for expense in source_expenses:
            target.execute(
                insert(expense_table).values(
                    record_id=record_ids[expense["record_id"]],
                    category_id=category_ids[expense["category_id"]],
                    description=expense["description"],
                    amount=expense["amount"],
                )
            )

    return {
        "categories": len(source_categories),
        "records": len(source_records),
        "expenses": len(source_expenses),
    }


def main():
    args = parse_args()
    try:
        totals = migrate(args.source)
    except Exception as exc:
        print(f"Migração cancelada: {exc}", file=sys.stderr)
        return 1

    print("Migração concluída com sucesso.")
    print(f"Categorias: {totals['categories']}")
    print(f"Registros diários: {totals['records']}")
    print(f"Despesas: {totals['expenses']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
