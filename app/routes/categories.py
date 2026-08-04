from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ..extensions import db
from ..models import Category

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Informe o nome da categoria.", "danger")
        elif len(name) > 80:
            flash("O nome deve ter no máximo 80 caracteres.", "danger")
        elif Category.query.filter(
            (Category.user_id == current_user.id) | (Category.user_id.is_(None))
        ).filter(
            func.lower(Category.name) == name.lower()
        ).first():
            flash("Esta categoria já existe.", "danger")
        else:
            db.session.add(Category(name=name, user_id=current_user.id))
            db.session.commit()
            flash("Categoria criada com sucesso.", "success")
            return redirect(url_for("categories.index"))
    categories = Category.query.filter(
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).order_by(Category.name.asc()).all()
    return render_template("categories.html", categories=categories)



@categories_bp.route("/<int:category_id>/excluir", methods=["POST"])
@login_required
def delete(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    if category.is_default:
        flash("As categorias padrão não podem ser excluídas.", "danger")
    elif category.expenses.count():
        flash("Esta categoria possui despesas e não pode ser excluída.", "danger")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Categoria excluída com sucesso.", "success")
    return redirect(url_for("categories.index"))
