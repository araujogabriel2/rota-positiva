from app.extensions import db
from app.models import User
from app.services.auth import create_user, generate_temporary_password


def test_temporary_password_has_required_character_groups():
    password = generate_temporary_password()
    assert len(password) == 16
    assert any(char.islower() for char in password)
    assert any(char.isupper() for char in password)
    assert any(char.isdigit() for char in password)
    assert any(not char.isalnum() for char in password)


def test_first_login_requires_personal_password(anonymous_client, app):
    with app.app_context():
        user, temporary_password = create_user("Novo Motorista", "novo")
        db.session.commit()
        user_id = user.id

    response = anonymous_client.post(
        "/login",
        data={"username": "novo", "password": temporary_password},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/alterar-senha" in response.headers["Location"]
    assert "/alterar-senha" in anonymous_client.get("/", follow_redirects=False).headers["Location"]

    response = anonymous_client.post(
        "/alterar-senha",
        data={"password": "minha-senha-pessoal-123", "password_confirmation": "minha-senha-pessoal-123"},
        follow_redirects=True,
    )
    assert "Senha pessoal criada com sucesso" in response.get_data(as_text=True)
    with app.app_context():
        user = db.session.get(User, user_id)
        assert not user.must_change_password
        assert user.check_password("minha-senha-pessoal-123")
        assert not user.check_password(temporary_password)


def test_admin_can_create_reset_and_disable_driver(admin_client, anonymous_client, app):
    response = admin_client.post(
        "/admin/usuarios/novo",
        data={"name": "Quarto Motorista", "username": "quarto"},
        follow_redirects=True,
    )
    assert "Senha temporária de Quarto Motorista" in response.get_data(as_text=True)
    with app.app_context():
        user = User.query.filter_by(username="quarto").one()
        user.set_password("senha-conhecida-segura")
        user.must_change_password = False
        db.session.commit()
        user_id = user.id

    admin_client.post(f"/admin/usuarios/{user_id}/alternar-status")
    with app.app_context():
        assert not db.session.get(User, user_id).is_active
    response = anonymous_client.post(
        "/login",
        data={"username": "quarto", "password": "senha-conhecida-segura"},
        follow_redirects=True,
    )
    assert "Esta conta está desativada" in response.get_data(as_text=True)


def test_deactivated_driver_loses_an_existing_session(client, admin_client, app):
    admin_client.post(
        f"/admin/usuarios/{app.config['TEST_DRIVER_ID']}/alternar-status",
        follow_redirects=True,
    )
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_driver_cannot_access_user_administration(client):
    assert client.get("/admin/usuarios").status_code == 403
