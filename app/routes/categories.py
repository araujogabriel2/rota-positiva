from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from ..extensions import db
from ..models import Category

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Informe o nome da categoria.", "danger")
        elif len(name) > 80:
            flash("O nome deve ter no máximo 80 caracteres.", "danger")
        elif Category.query.filter(func.lower(Category.name) == name.lower()).first():
            flash("Esta categoria já existe.", "danger")
        else:
            db.session.add(Category(name=name))
            db.session.commit()
            flash("Categoria criada com sucesso.", "success")
            return redirect(url_for("categories.index"))
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template("categories.html", categories=categories)


@categories_bp.route("/<int:category_id>/excluir", methods=["POST"])
def delete(category_id):
    category = Category.query.get_or_404(category_id)
    if category.is_default:
        flash("As categorias padrão não podem ser excluídas.", "danger")
    elif category.expenses.count():
        flash("Esta categoria possui despesas e não pode ser excluída.", "danger")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Categoria excluída com sucesso.", "success")
    return redirect(url_for("categories.index"))

