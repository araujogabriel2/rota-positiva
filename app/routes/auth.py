from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

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
        elif user.is_pending:
            flash("Seu cadastro está aguardando aprovação do administrador.", "warning")
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


@auth_bp.route("/login/google")
def login_google():
    from ..extensions import supabase
    if not supabase:
        flash("Configuração do Supabase (SUPABASE_URL e SUPABASE_KEY) ausente.", "danger")
        return redirect(url_for("auth.login"))
        
    redirect_url = url_for("auth.callback", _external=True)
    try:
        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url
            }
        })
        return redirect(res.url)
    except Exception:
        current_app.logger.exception("Falha ao iniciar o login Google")
        flash("Não foi possível iniciar o login com Google. Tente novamente.", "danger")
        return redirect(url_for("auth.login"))


@auth_bp.route("/auth/callback")
def callback():
    from ..extensions import supabase
    if not supabase:
        flash("Configuração do Supabase ausente.", "danger")
        return redirect(url_for("auth.login"))
        
    code = request.args.get("code")
    if not code:
        flash("Código de autenticação ausente.", "danger")
        return redirect(url_for("auth.login"))
        
    try:
        session_data = supabase.auth.exchange_code_for_session({"auth_code": code})
        supabase_user = session_data.user
        if not supabase_user:
            raise ValueError("O Supabase não retornou o usuário autenticado.")
        
        # Procura usuário pelo supabase_id
        user = User.query.filter_by(supabase_id=str(supabase_user.id)).first()
        if not user:
            # Tenta encontrar por email (caso seja uma conta local pré-existente)
            email = str(supabase_user.email or "").strip().lower()
            if not email:
                flash("Sua conta Google não forneceu um e-mail válido.", "danger")
                return redirect(url_for("auth.login"))
            user = User.query.filter(func.lower(User.username) == email).first()
            if user:
                if user.supabase_id and user.supabase_id != str(supabase_user.id):
                    flash("Este e-mail já está associado a outra identidade.", "danger")
                    return redirect(url_for("auth.login"))
                user.supabase_id = str(supabase_user.id)
                db.session.commit()
            else:
                from ..services.auth import create_oauth_user
                metadata = supabase_user.user_metadata or {}
                user = create_oauth_user(
                    name=metadata.get("full_name", email),
                    email=supabase_user.email,
                    supabase_id=str(supabase_user.id)
                )
                db.session.commit()

        if user.is_pending:
            flash("Cadastro recebido. Aguarde a aprovação do administrador.", "warning")
            return redirect(url_for("auth.login"))
        if not user.is_active:
            flash("Esta conta está desativada. Procure o administrador.", "danger")
            return redirect(url_for("auth.login"))
            
        login_user(user)
        flash("Login realizado com sucesso pelo Google!", "success")
        return redirect(url_for("main.dashboard"))
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Falha no retorno do login Google")
        flash("Não foi possível concluir o login com Google. Tente novamente.", "danger")
        return redirect(url_for("auth.login"))

