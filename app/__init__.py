import os

from flask import Flask

from .config import Config
from .extensions import csrf, db, login_manager


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, int(user_id))
        return user if user and user.is_active else None

    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    from .routes.categories import categories_bp
    from .routes.main import main_bp
    from .routes.records import records_bp
    from .routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(main_bp)
    app.register_blueprint(records_bp, url_prefix="/registros")
    app.register_blueprint(categories_bp, url_prefix="/categorias")
    app.register_blueprint(reports_bp, url_prefix="/relatorios")

    with app.app_context():
        db.create_all()

    return app
