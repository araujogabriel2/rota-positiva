from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Category, DailyRecord, Expense, User
from ..services.finance import parse_date, records_between, validate_record_form

records_bp = Blueprint("records", __name__)


def _categories():
    return Category.query.filter(
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).order_by(Category.name.asc()).all()



def _expense_rows(record):
    if request.method == "POST":
        return list(zip(
            request.form.getlist("expense_category[]"),
            request.form.getlist("expense_description[]"),
            request.form.getlist("expense_amount[]"),
        ))
    return [(str(e.category_id), e.description, str(e.amount)) for e in record.expenses]


def _save_record(record):
    errors, data = validate_record_form(
        request.form, record.id if record.id else None, record.user_id
    )
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
@login_required
def create():
    record = DailyRecord(user_id=current_user.id)
    if request.method == "POST" and _save_record(record):
        flash("Registro salvo com sucesso.", "success")
        return redirect(url_for("records.detail", record_id=record.id))
    return render_template(
        "record_form.html", record=record, categories=_categories(),
        expense_rows=_expense_rows(record),
    )


@records_bp.route("/")
@login_required
def history():
    selected_user_id = request.args.get("driver", type=int) if current_user.is_admin else current_user.id
    drivers = User.query.order_by(User.name).all() if current_user.is_admin else []
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
        records = list(reversed(records_between(start, end, selected_user_id)))
    except ValueError as exc:
        flash(str(exc), "danger")
        records = []
    return render_template(
        "history.html", records=records, start=start_text, end=end_text, q=query_text,
        selected_user_id=selected_user_id, drivers=drivers,
    )


@records_bp.route("/<int:record_id>")
@login_required
def detail(record_id):
    query = DailyRecord.query
    if not current_user.is_admin:
        query = query.filter_by(user_id=current_user.id)
    return render_template("record_detail.html", record=query.filter_by(id=record_id).first_or_404())


@records_bp.route("/<int:record_id>/editar", methods=["GET", "POST"])
@login_required
def edit(record_id):
    record = DailyRecord.query.filter_by(id=record_id, user_id=current_user.id).first_or_404()
    if request.method == "POST" and _save_record(record):
        flash("Registro atualizado com sucesso.", "success")
        return redirect(url_for("records.detail", record_id=record.id))
    return render_template(
        "record_form.html", record=record, categories=_categories(),
        expense_rows=_expense_rows(record),
    )


@records_bp.route("/<int:record_id>/excluir", methods=["POST"])
@login_required
def delete(record_id):
    record = DailyRecord.query.filter_by(id=record_id, user_id=current_user.id).first_or_404()
    db.session.delete(record)
    db.session.commit()
    flash("Registro excluído com sucesso.", "success")
    return redirect(url_for("records.history"))
