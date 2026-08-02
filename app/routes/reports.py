from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for

from ..services.finance import get_period, latest_record_date, records_between, summarize
from ..services.report_pdf import build_report

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/")
def index():
    try:
        start, end, period = get_period(request.args, reference_date=latest_record_date())
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("reports.index"))
    records = records_between(start, end)
    return render_template(
        "reports.html", records=records, summary=summarize(records), start=start, end=end,
        period=period,
    )


@reports_bp.route("/pdf")
def pdf():
    try:
        start, end, _ = get_period(request.args, reference_date=latest_record_date())
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("reports.index"))
    records = records_between(start, end)
    stream = build_report(records, start, end)
    filename = f"relatorio-financeiro-{start.isoformat()}-a-{end.isoformat()}.pdf"
    return send_file(stream, mimetype="application/pdf", as_attachment=True, download_name=filename)
