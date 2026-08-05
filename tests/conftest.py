import pytest

from app import create_app
from app.extensions import db
from app.services.auth import create_user


class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        admin, _ = create_user("Administrador", "admin", role="admin")
        admin.set_password("senha-admin-segura")
        admin.must_change_password = False
        driver, _ = create_user("Motorista Teste", "motorista")
        driver.set_password("senha-motorista-segura")
        driver.must_change_password = False
        other, _ = create_user("Outro Motorista", "outro")
        other.set_password("senha-outro-segura")
        other.must_change_password = False
        db.session.commit()
        application.config.update(
            TEST_ADMIN_ID=admin.id,
            TEST_DRIVER_ID=driver.id,
            TEST_OTHER_ID=other.id,
        )
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    client = app.test_client()
    client.post("/login", data={"username": "motorista", "password": "senha-motorista-segura"})
    return client


@pytest.fixture()
def anonymous_client(app):
    return app.test_client()


@pytest.fixture()
def admin_client(app):
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "senha-admin-segura"})
    return client
