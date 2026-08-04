from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from ..models import User
from ..services.finance import get_period, latest_record_date, records_between, summarize
from ..services.report_pdf import build_report

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/")
@login_required
def index():
    selected_user_id = request.args.get("driver", type=int) if current_user.is_admin else current_user.id
    drivers = User.query.order_by(User.name).all() if current_user.is_admin else []
    try:
        start, end, period = get_period(request.args, reference_date=latest_record_date(selected_user_id))
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("reports.index"))
    records = records_between(start, end, selected_user_id)
    return render_template(
        "reports.html", records=records, summary=summarize(records), start=start, end=end,
        period=period, selected_user_id=selected_user_id, drivers=drivers,
    )


@reports_bp.route("/pdf")
@login_required
def pdf():
    selected_user_id = request.args.get("driver", type=int) if current_user.is_admin else current_user.id
    try:
        start, end, _ = get_period(request.args, reference_date=latest_record_date(selected_user_id))
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("reports.index"))
    records = records_between(start, end, selected_user_id)
    stream = build_report(records, start, end)
    filename = f"relatorio-financeiro-{start.isoformat()}-a-{end.isoformat()}.pdf"
    return send_file(stream, mimetype="application/pdf", as_attachment=True, download_name=filename)
