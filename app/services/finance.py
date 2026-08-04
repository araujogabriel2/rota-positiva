from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from itertools import zip_longest

from sqlalchemy import func
from sqlalchemy.orm import selectinload

from ..extensions import db
from ..models import DailyRecord, Expense


def parse_decimal(value, field_name):
    text = str(value or "").strip().replace("R$", "").replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field_name} possui um valor inválido.")
    if number < 0:
        raise ValueError(f"{field_name} não pode ser negativo.")
    return number.quantize(Decimal("0.01"))


def parse_date(value, field_name="Data"):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} inválida.")


def latest_record_date(user_id=None):
    query = db.session.query(func.max(DailyRecord.date))
    if user_id is not None:
        query = query.filter(DailyRecord.user_id == user_id)
    return query.scalar()


def get_period(args, default="month", reference_date=None):
    today = date.today()
    period = args.get("period", default)
    if period == "today":
        return today, today, period
    if period == "7days":
        end = max(today, reference_date) if reference_date else today
        return end - timedelta(days=6), end, period
    if period == "custom":
        start = parse_date(args.get("start"), "Data inicial")
        end = parse_date(args.get("end"), "Data final")
        if start > end:
            raise ValueError("A data inicial deve ser anterior à data final.")
        return start, end, period
    next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = next_month - timedelta(days=1)
    return today.replace(day=1), month_end, "month"


def records_between(start, end, user_id=None):
    query = (
        DailyRecord.query.options(
            selectinload(DailyRecord.expenses).selectinload(Expense.category)
        )
        .filter(DailyRecord.date.between(start, end))
    )
    if user_id is not None:
        query = query.filter(DailyRecord.user_id == user_id)
    return query.order_by(DailyRecord.date.asc()).all()


def summarize(records):
    revenue = sum((r.gross_revenue for r in records), Decimal("0.00"))
    expenses = sum((r.total_expenses for r in records), Decimal("0.00"))
    kilometers = sum((r.kilometers for r in records), Decimal("0.00"))
    profit = revenue - expenses
    days = len(records)
    by_category = defaultdict(lambda: Decimal("0.00"))
    for record in records:
        for expense in record.expenses:
            by_category[expense.category.name] += expense.amount
    return {
        "revenue": revenue,
        "expenses": expenses,
        "profit": profit,
        "kilometers": kilometers,
        "average_revenue": revenue / days if days else Decimal("0.00"),
        "average_profit": profit / days if days else Decimal("0.00"),
        "gross_per_km": revenue / kilometers if kilometers else Decimal("0.00"),
        "cost_per_km": expenses / kilometers if kilometers else Decimal("0.00"),
        "by_category": dict(sorted(by_category.items())),
    }


def validate_record_form(form, editing_id=None, user_id=None):
    errors = []
    try:
        record_date = parse_date(form.get("date"))
    except ValueError as exc:
        errors.append(str(exc))
        record_date = None
    try:
        revenue = parse_decimal(form.get("gross_revenue"), "Faturamento")
    except ValueError as exc:
        errors.append(str(exc))
        revenue = None
    try:
        kilometers = parse_decimal(form.get("kilometers"), "Quilometragem")
    except ValueError as exc:
        errors.append(str(exc))
        kilometers = None

    if record_date:
        query = DailyRecord.query.filter_by(date=record_date)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        if editing_id:
            query = query.filter(DailyRecord.id != editing_id)
        if query.first():
            errors.append("Já existe um registro para esta data.")

    categories = form.getlist("expense_category[]")
    descriptions = form.getlist("expense_description[]")
    amounts = form.getlist("expense_amount[]")
    expenses = []
    for index, (category, description, amount) in enumerate(
        zip_longest(categories, descriptions, amounts, fillvalue=""), start=1
    ):
        if not any([category.strip(), description.strip(), amount.strip()]):
            continue
        if not category:
            errors.append(f"Selecione a categoria da despesa {index}.")
            continue
        if not description.strip():
            errors.append(f"Informe a descrição da despesa {index}.")
            continue
        if len(description.strip()) > 180:
            errors.append(f"A descrição da despesa {index} deve ter no máximo 180 caracteres.")
            continue
        try:
            parsed_amount = parse_decimal(amount, f"Valor da despesa {index}")
            if parsed_amount == 0:
                errors.append(f"O valor da despesa {index} deve ser maior que zero.")
            else:
                expenses.append((int(category), description.strip(), parsed_amount))
        except (ValueError, TypeError):
            errors.append(f"Valor da despesa {index} inválido.")

    notes = form.get("notes", "").strip()
    if len(notes) > 2000:
        errors.append("As observações devem ter no máximo 2.000 caracteres.")
    return errors, {
        "date": record_date,
        "gross_revenue": revenue,
        "kilometers": kilometers,
        "notes": notes,
        "expenses": expenses,
    }
