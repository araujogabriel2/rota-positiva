from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import User
from ..services.auth import normalize_username


auth_bp = Blueprint("auth", __name__)


@auth_bp.before_app_request
def require_password_change():
    allowed = {"auth.login", "auth.logout", "auth.change_password", "static"}
    if (
        current_user.is_authenticated
        and current_user.must_change_password
        and request.endpoint not in allowed
    ):
        return redirect(url_for("auth.change_password"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        destination = "auth.change_password" if current_user.must_change_password else "main.dashboard"
        return redirect(url_for(destination))

    if request.method == "POST":
        username = normalize_username(request.form.get("username"))
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("Usuário ou senha incorretos.", "danger")
        elif not user.is_active:
            flash("Esta conta está desativada. Procure o administrador.", "danger")
        else:
            login_user(user)
            if user.must_change_password:
                flash("Crie sua senha pessoal para continuar.", "warning")
                return redirect(url_for("auth.change_password"))
            flash("Login realizado com sucesso.", "success")
            return redirect(url_for("main.dashboard"))
    return render_template("login.html")


@auth_bp.route("/alterar-senha", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        password = request.form.get("password", "")
        confirmation = request.form.get("password_confirmation", "")
        if len(password) < 12:
            flash("A nova senha deve ter pelo menos 12 caracteres.", "danger")
        elif password != confirmation:
            flash("A confirmação da senha não confere.", "danger")
        elif current_user.check_password(password):
            flash("Escolha uma senha diferente da senha temporária.", "danger")
        else:
            current_user.set_password(password)
            current_user.must_change_password = False
            db.session.commit()
            flash("Senha pessoal criada com sucesso.", "success")
            return redirect(url_for("main.dashboard"))
    return render_template("change_password.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada.", "success")
    return redirect(url_for("auth.login"))
