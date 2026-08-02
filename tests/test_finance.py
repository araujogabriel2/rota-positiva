from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models import Category, DailyRecord, Expense
from app.services.finance import get_period, parse_decimal, summarize


def test_parse_decimal_accepts_brazilian_format_and_rejects_negative():
    assert parse_decimal("1.234,56", "Valor") == Decimal("1234.56")
    assert parse_decimal("42.10", "Valor") == Decimal("42.10")
    with pytest.raises(ValueError, match="não pode ser negativo"):
        parse_decimal("-1", "Valor")


def test_financial_calculations_and_zero_kilometers(app):
    with app.app_context():
        category = Category.query.filter_by(name="Combustível").first()
        record = DailyRecord(
            date=date(2026, 8, 1), gross_revenue=Decimal("300.00"),
            kilometers=Decimal("100.00"),
        )
        record.expenses.append(Expense(category=category, description="Gasolina", amount=Decimal("80.00")))
        assert record.total_expenses == Decimal("80.00")
        assert record.net_profit == Decimal("220.00")
        assert record.gross_per_km == Decimal("3")
        assert record.cost_per_km == Decimal("0.8")
        assert record.net_per_km == Decimal("2.2")

        zero = DailyRecord(date=date(2026, 8, 2), gross_revenue=Decimal("10"), kilometers=Decimal("0"))
        assert zero.gross_per_km == Decimal("0.00")
        assert zero.cost_per_km == Decimal("0.00")
        assert zero.net_per_km == Decimal("0.00")

        total = summarize([record])
        assert total["profit"] == Decimal("220.00")
        assert total["by_category"]["Combustível"] == Decimal("80.00")


def test_automatic_periods_cover_full_month_and_latest_record():
    today = date.today()
    future_reference = today + timedelta(days=10)
    start, end, period = get_period(
        {"period": "7days"}, reference_date=future_reference
    )
    assert period == "7days"
    assert end == future_reference
    assert start == future_reference - timedelta(days=6)

    month_start, month_end, period = get_period({"period": "month"})
    assert period == "month"
    assert month_start == today.replace(day=1)
    assert month_end.month == today.month
    assert (month_end + timedelta(days=1)).day == 1
