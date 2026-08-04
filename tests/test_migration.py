from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, insert, select

from app.extensions import db
from app.models import Category, DailyRecord, Expense, User
from scripts.migrate_sqlite_to_postgres import copy_data


def test_copy_data_preserves_financial_records(tmp_path):
    source_engine = create_engine(f"sqlite:///{tmp_path / 'source.db'}")
    target_engine = create_engine(f"sqlite:///{tmp_path / 'target.db'}")
    db.metadata.create_all(source_engine)
    now = datetime.now(timezone.utc)

    with source_engine.begin() as source:
        source.execute(
            insert(User.__table__).values(
                id=1, name="Motorista", username="motorista",
                password_hash="hash-de-teste", role="driver",
                is_active_account=True, must_change_password=False, created_at=now,
            )
        )
        source.execute(
            insert(Category.__table__).values(
                id=1, user_id=1, name="Combustível", is_default=True, created_at=now
            )
        )
        source.execute(
            insert(DailyRecord.__table__).values(
                id=1,
                user_id=1,
                date=date(2026, 8, 1),
                gross_revenue=Decimal("500.00"),
                kilometers=Decimal("200.00"),
                notes="Teste",
                created_at=now,
                updated_at=now,
            )
        )
        source.execute(
            insert(Expense.__table__).values(
                id=1,
                record_id=1,
                category_id=1,
                description="Abastecimento",
                amount=Decimal("100.00"),
            )
        )

    totals = copy_data(source_engine, target_engine)

    assert totals == {"users": 1, "categories": 1, "records": 1, "expenses": 1}
    with target_engine.connect() as target:
        assert target.scalar(select(func.count()).select_from(Category.__table__)) == 1
        assert target.scalar(select(func.count()).select_from(DailyRecord.__table__)) == 1
        assert target.scalar(select(func.count()).select_from(Expense.__table__)) == 1

    with pytest.raises(RuntimeError, match="evitar dados duplicados"):
        copy_data(source_engine, target_engine)
