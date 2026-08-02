import os

from flask import Flask

from .config import Config
from .extensions import csrf, db


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    from .routes.categories import categories_bp
    from .routes.main import main_bp
    from .routes.records import records_bp
    from .routes.reports import reports_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(records_bp, url_prefix="/registros")
    app.register_blueprint(categories_bp, url_prefix="/categorias")
    app.register_blueprint(reports_bp, url_prefix="/relatorios")

    with app.app_context():
        db.create_all()
        _seed_categories()

    return app


def _seed_categories():
    from .models import Category

    defaults = [
        "Combustível", "Alimentação", "Manutenção", "Pedágio",
        "Lavagem", "Estacionamento", "Outros",
    ]
    existing = {name for (name,) in db.session.query(Category.name).all()}
    for name in defaults:
        if name not in existing:
            db.session.add(Category(name=name, is_default=True))
    db.session.commit()

