from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..extensions import db
from ..models import Category, DailyRecord, Expense
from ..services.finance import parse_date, records_between, validate_record_form

records_bp = Blueprint("records", __name__)


def _categories():
    return Category.query.order_by(Category.name.asc()).all()


def _expense_rows(record):
    if request.method == "POST":
        return list(zip(
            request.form.getlist("expense_category[]"),
            request.form.getlist("expense_description[]"),
            request.form.getlist("expense_amount[]"),
        ))
    return [(str(e.category_id), e.description, str(e.amount)) for e in record.expenses]


def _save_record(record):
    errors, data = validate_record_form(request.form, record.id if record.id else None)
    valid_ids = {category.id for category in _categories()}
    if any(category_id not in valid_ids for category_id, _, _ in data["expenses"]):
        errors.append("Uma das categorias selecionadas é inválida.")
    if errors:
        for error in errors:
            flash(error, "danger")
        return False

    record.date = data["date"]
    record.gross_revenue = data["gross_revenue"]
    record.kilometers = data["kilometers"]
    record.notes = data["notes"]
    record.expenses.clear()
    for category_id, description, amount in data["expenses"]:
        record.expenses.append(
            Expense(category_id=category_id, description=description, amount=amount)
        )
    db.session.add(record)
    db.session.commit()
    return True


@records_bp.route("/novo", methods=["GET", "POST"])
def create():
    record = DailyRecord()
    if request.method == "POST" and _save_record(record):
        flash("Registro salvo com sucesso.", "success")
        return redirect(url_for("records.detail", record_id=record.id))
    return render_template(
        "record_form.html", record=record, categories=_categories(),
        expense_rows=_expense_rows(record),
    )


@records_bp.route("/")
def history():
    start_text = request.args.get("start", "")
    end_text = request.args.get("end", "")
    query_text = request.args.get("q", "").strip()
    try:
        if query_text:
            searched = parse_date(query_text, "Data pesquisada")
            start, end = searched, searched
        elif start_text or end_text:
            start = parse_date(start_text or end_text, "Data inicial")
            end = parse_date(end_text or start_text, "Data final")
            if start > end:
                raise ValueError("A data inicial deve ser anterior à data final.")
        else:
            start, end = parse_date("1900-01-01"), parse_date("2999-12-31")
        records = list(reversed(records_between(start, end)))
    except ValueError as exc:
        flash(str(exc), "danger")
        records = []
    return render_template(
        "history.html", records=records, start=start_text, end=end_text, q=query_text
    )


@records_bp.route("/<int:record_id>")
def detail(record_id):
    return render_template("record_detail.html", record=DailyRecord.query.get_or_404(record_id))


@records_bp.route("/<int:record_id>/editar", methods=["GET", "POST"])
def edit(record_id):
    record = DailyRecord.query.get_or_404(record_id)
    if request.method == "POST" and _save_record(record):
        flash("Registro atualizado com sucesso.", "success")
        return redirect(url_for("records.detail", record_id=record.id))
    return render_template(
        "record_form.html", record=record, categories=_categories(),
        expense_rows=_expense_rows(record),
    )


@records_bp.route("/<int:record_id>/excluir", methods=["POST"])
def delete(record_id):
    record = DailyRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash("Registro excluído com sucesso.", "success")
    return redirect(url_for("records.history"))
