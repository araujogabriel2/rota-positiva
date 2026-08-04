from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..models import User
from ..services.finance import get_period, latest_record_date, records_between, summarize

main_bp = Blueprint("main", __name__)


@main_bp.app_template_filter("brl")
def brl(value):
    number = float(value or 0)
    formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


@main_bp.app_template_filter("brdate")
def brdate(value):
    return value.strftime("%d/%m/%Y") if value else "-"


@main_bp.route("/")
@login_required
def dashboard():
    selected_user_id = request.args.get("driver", type=int) if current_user.is_admin else current_user.id
    drivers = User.query.order_by(User.name).all() if current_user.is_admin else []
    try:
        start, end, period = get_period(
            request.args, reference_date=latest_record_date(selected_user_id)
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("main.dashboard"))
    records = records_between(start, end, selected_user_id)
    summary = summarize(records)
    chart_data = {
        "labels": [record.date.strftime("%d/%m") for record in records],
        "revenue": [float(record.gross_revenue) for record in records],
        "profit": [float(record.net_profit) for record in records],
        "category_labels": list(summary["by_category"].keys()),
        "category_values": [float(value) for value in summary["by_category"].values()],
    }
    return render_template(
        "dashboard.html", records=records, summary=summary, chart_data=chart_data,
        start=start, end=end, period=period, selected_user_id=selected_user_id,
        drivers=drivers,
    )
