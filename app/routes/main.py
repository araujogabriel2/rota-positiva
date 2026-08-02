from flask import Blueprint, flash, redirect, render_template, request, url_for, session, current_app

from ..services.finance import get_period, latest_record_date, records_between, summarize

main_bp = Blueprint("main", __name__)


@main_bp.before_app_request
def check_login():
    if not current_app.config.get("LOGIN_REQUIRED", True):
        return
        
    if request.endpoint in ("main.login", "static") or not request.endpoint:
        return
        
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("main.dashboard"))
        
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        admin_user = current_app.config.get("ADMIN_USERNAME", "admin")
        admin_pass = current_app.config.get("ADMIN_PASSWORD", "admin")
        
        if username == admin_user and password == admin_pass:
            session["logged_in"] = True
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Usuário ou senha incorretos.", "danger")
            
    return render_template("login.html")


@main_bp.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Sessão encerrada.", "success")
    return redirect(url_for("main.login"))



@main_bp.app_template_filter("brl")
def brl(value):
    number = float(value or 0)
    formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


@main_bp.app_template_filter("brdate")
def brdate(value):
    return value.strftime("%d/%m/%Y") if value else "-"


@main_bp.route("/")
def dashboard():
    try:
        start, end, period = get_period(request.args, reference_date=latest_record_date())
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("main.dashboard"))
    records = records_between(start, end)
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
        start=start, end=end, period=period,
    )
