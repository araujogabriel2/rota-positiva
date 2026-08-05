import re
import secrets
import string
from functools import wraps

from flask import abort
from flask_login import current_user

from ..extensions import db
from ..models import Category, User


DEFAULT_CATEGORIES = [
    "Combustível",
    "Alimentação",
    "Manutenção",
    "Pedágio",
    "Lavagem",
    "Estacionamento",
    "Outros",
]
USERNAME_PATTERN = re.compile(r"^[a-z0-9._-]{3,40}$")


def normalize_username(value):
    return str(value or "").strip().lower()


def validate_username(value):
    username = normalize_username(value)
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError(
            "O usuário deve ter de 3 a 40 caracteres: letras minúsculas, "
            "números, ponto, traço ou sublinhado."
        )
    return username


def generate_temporary_password(length=16):
    alphabet = string.ascii_letters + string.digits + "-_%@"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and any(char.isdigit() for char in password)
            and any(not char.isalnum() for char in password)
        ):
            return password


def create_user(name, username, role="driver"):
    temporary_password = generate_temporary_password()
    user = User(
        name=name.strip(),
        username=validate_username(username),
        role=role,
        status="active",
        must_change_password=True,
        is_active_account=True,
    )
    user.set_password(temporary_password)
    db.session.add(user)
    return user, temporary_password


def create_oauth_user(name, email, supabase_id):
    normalized_email = str(email or "").strip().lower()
    normalized_supabase_id = str(supabase_id or "").strip()
    if not normalized_email or len(normalized_email) > 255:
        raise ValueError("O Google não forneceu um e-mail válido.")
    if not normalized_supabase_id or len(normalized_supabase_id) > 255:
        raise ValueError("O Supabase não forneceu uma identidade válida.")
    display_name = str(name or "").strip() or normalized_email
    user = User(
        name=display_name[:100],
        username=normalized_email,
        supabase_id=normalized_supabase_id,
        role="driver",
        status="pending",
        must_change_password=False,
        is_active_account=False,
    )
    user.set_password(generate_temporary_password(32))
    db.session.add(user)
    return user




def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped
