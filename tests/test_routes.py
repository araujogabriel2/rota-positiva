from datetime import date, timedelta
from decimal import Decimal

from app.extensions import db
from app.models import Category, DailyRecord


def sample_payload(category_id, date_text="2026-08-01"):
    return {
        "date": date_text,
        "gross_revenue": "500,00",
        "kilometers": "200,00",
        "notes": "Dia de chuva e trânsito",
        "expense_category[]": [str(category_id), str(category_id)],
        "expense_description[]": ["Combustível", "Lanche"],
        "expense_amount[]": ["100,00", "20,00"],
    }


def test_dashboard_and_crud_flow(client, app):
    with app.app_context():
        category_id = Category.query.filter(
            (Category.user_id == app.config["TEST_DRIVER_ID"]) | (Category.user_id.is_(None))
        ).filter_by(name="Combustível").first().id

    response = client.post("/registros/novo", data=sample_payload(category_id), follow_redirects=True)
    assert "Registro salvo com sucesso" in response.get_data(as_text=True)
    with app.app_context():
        record = DailyRecord.query.one()
        record_id = record.id
        assert record.user_id == app.config["TEST_DRIVER_ID"]
        assert float(record.net_profit) == 380.0

    assert client.get(f"/registros/{record_id}").status_code == 200
    payload = sample_payload(category_id)
    payload["gross_revenue"] = "600,00"
    assert "Registro atualizado" in client.post(
        f"/registros/{record_id}/editar", data=payload, follow_redirects=True
    ).get_data(as_text=True)
    assert "Já existe um registro" in client.post(
        "/registros/novo", data=sample_payload(category_id), follow_redirects=True
    ).get_data(as_text=True)
    pdf = client.get("/relatorios/pdf?period=custom&start=2026-08-01&end=2026-08-01")
    assert pdf.status_code == 200 and pdf.data.startswith(b"%PDF")
    assert "Registro excluído" in client.post(
        f"/registros/{record_id}/excluir", follow_redirects=True
    ).get_data(as_text=True)


def test_validation_and_categories(client, app):
    with app.app_context():
        category_id = Category.query.filter(
            (Category.user_id == app.config["TEST_DRIVER_ID"]) | (Category.user_id.is_(None))
        ).first().id
    bad = sample_payload(category_id)
    bad["gross_revenue"] = "-2"
    bad["kilometers"] = "inválido"
    text = client.post("/registros/novo", data=bad, follow_redirects=True).get_data(as_text=True)
    assert "não pode ser negativo" in text
    assert "Quilometragem possui um valor inválido" in text
    assert "Categoria criada" in client.post(
        "/categorias/", data={"name": "Seguro"}, follow_redirects=True
    ).get_data(as_text=True)


def test_dashboard_period_filters_update_totals(client, app):
    today = date.today()
    with app.app_context():
        for record_date, revenue in [
            (today, "100.00"),
            (today - timedelta(days=3), "200.00"),
            (today - timedelta(days=10), "400.00"),
        ]:
            db.session.add(DailyRecord(
                user_id=app.config["TEST_DRIVER_ID"], date=record_date,
                gross_revenue=Decimal(revenue), kilometers=Decimal("50.00"),
            ))
        db.session.commit()
    assert "R$ 100,00" in client.get("/?period=today").get_data(as_text=True)
    assert "R$ 300,00" in client.get("/?period=7days").get_data(as_text=True)


def test_login_and_logout(anonymous_client):
    client = anonymous_client
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302 and "/login" in response.headers["Location"]
    assert "Usuário ou senha incorretos" in client.post(
        "/login", data={"username": "wrong", "password": "wrong"}, follow_redirects=True
    ).get_data(as_text=True)
    assert "Login realizado com sucesso" in client.post(
        "/login", data={"username": "admin", "password": "senha-admin-segura"}, follow_redirects=True
    ).get_data(as_text=True)
    assert "Sessão encerrada" in client.post("/logout", follow_redirects=True).get_data(as_text=True)


def test_driver_isolation_and_admin_visibility(client, admin_client, app):
    with app.app_context():
        other_record = DailyRecord(
            user_id=app.config["TEST_OTHER_ID"], date=date(2026, 8, 2),
            gross_revenue=Decimal("900.00"), kilometers=Decimal("100.00"),
        )
        db.session.add(other_record)
        db.session.commit()
        record_id = other_record.id
    assert client.get(f"/registros/{record_id}").status_code == 404
    assert client.get(f"/registros/{record_id}/editar").status_code == 404
    assert "R$ 900,00" not in client.get("/?period=custom&start=2026-08-02&end=2026-08-02").get_data(as_text=True)
    assert admin_client.get(f"/registros/{record_id}").status_code == 200
    assert admin_client.get(f"/registros/{record_id}/editar").status_code == 404
    assert admin_client.post(f"/registros/{record_id}/excluir").status_code == 404
    assert "R$ 900,00" in admin_client.get("/?period=custom&start=2026-08-02&end=2026-08-02").get_data(as_text=True)
