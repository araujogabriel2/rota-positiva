from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import case, func

from ..extensions import db
from ..models import User
from ..services.auth import admin_required, create_user, generate_temporary_password


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/usuarios")
@login_required
@admin_required
def users():
    status_order = case(
        (User.status == "pending", 0),
        (User.status == "active", 1),
        else_=2,
    )
    return render_template(
        "admin/users.html",
        users=User.query.order_by(status_order, User.name).all(),
    )


@admin_bp.route("/usuarios/novo", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        if not name or len(name) > 100:
            flash("Informe um nome com até 100 caracteres.", "danger")
        elif User.query.filter(func.lower(User.username) == username.lower()).first():
            flash("Esse nome de usuário já está em uso.", "danger")
        else:
            try:
                user, temporary_password = create_user(name, username)
                db.session.commit()
                return render_template(
                    "admin/temporary_password.html",
                    managed_user=user,
                    temporary_password=temporary_password,
                    action="criada",
                )
            except ValueError as exc:
                db.session.rollback()
                flash(str(exc), "danger")
    return render_template("admin/user_form.html")


@admin_bp.route("/usuarios/<int:user_id>/alternar-status", methods=["POST"])
@login_required
@admin_required
def toggle_status(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Você não pode desativar a própria conta.", "danger")
    elif user.is_active:
        user.disable()
        db.session.commit()
        flash("Conta desativada. O usuário perdeu o acesso.", "success")
    else:
        user.activate()
        db.session.commit()
        flash("Conta ativada com sucesso.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/usuarios/<int:user_id>/aprovar", methods=["POST"])
@login_required
@admin_required
def approve(user_id):
    user = db.get_or_404(User, user_id)
    if not user.is_pending:
        flash("Esta conta não está aguardando aprovação.", "warning")
    else:
        user.activate()
        db.session.commit()
        flash(f"Acesso de {user.name} aprovado com sucesso.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/usuarios/<int:user_id>/recusar", methods=["POST"])
@login_required
@admin_required
def reject(user_id):
    user = db.get_or_404(User, user_id)
    if not user.is_pending:
        flash("Esta conta não está aguardando aprovação.", "warning")
    else:
        user.disable()
        db.session.commit()
        flash(f"Solicitação de {user.name} recusada.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/usuarios/<int:user_id>/redefinir-senha", methods=["POST"])
@login_required
@admin_required
def reset_password(user_id):
    user = db.get_or_404(User, user_id)
    temporary_password = generate_temporary_password()
    user.set_password(temporary_password)
    user.must_change_password = True
    db.session.commit()
    return render_template(
        "admin/temporary_password.html",
        managed_user=user,
        temporary_password=temporary_password,
        action="redefinida",
    )
