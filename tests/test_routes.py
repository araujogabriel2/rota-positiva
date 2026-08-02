from datetime import date, timedelta
from decimal import Decimal

from app.extensions import db
from app.models import Category, DailyRecord


def sample_payload(category_id, date="2026-08-01"):
    return {
        "date": date,
        "gross_revenue": "500,00",
        "kilometers": "200,00",
        "notes": "Dia de chuva & trânsito",
        "expense_category[]": [str(category_id), str(category_id)],
        "expense_description[]": ["Combustível", "Lanche"],
        "expense_amount[]": ["100,00", "20,00"],
    }


def test_dashboard_and_crud_flow(client, app):
    assert client.get("/").status_code == 200
    with app.app_context():
        category_id = Category.query.filter_by(name="Combustível").first().id

    response = client.post("/registros/novo", data=sample_payload(category_id), follow_redirects=True)
    assert response.status_code == 200
    assert "Registro salvo com sucesso" in response.get_data(as_text=True)
    with app.app_context():
        record = DailyRecord.query.one()
        record_id = record.id
        assert len(record.expenses) == 2
        assert float(record.net_profit) == 380.0

    assert client.get("/registros/").status_code == 200
    assert client.get(f"/registros/{record_id}").status_code == 200
    payload = sample_payload(category_id)
    payload["gross_revenue"] = "600,00"
    response = client.post(f"/registros/{record_id}/editar", data=payload, follow_redirects=True)
    assert "Registro atualizado com sucesso" in response.get_data(as_text=True)

    duplicate = client.post("/registros/novo", data=sample_payload(category_id), follow_redirects=True)
    assert "Já existe um registro para esta data" in duplicate.get_data(as_text=True)

    pdf = client.get("/relatorios/pdf?period=custom&start=2026-08-01&end=2026-08-01")
    assert pdf.status_code == 200
    assert pdf.mimetype == "application/pdf"
    assert pdf.data.startswith(b"%PDF")
    assert len(pdf.data) > 2000

    deleted = client.post(f"/registros/{record_id}/excluir", follow_redirects=True)
    assert "Registro excluído com sucesso" in deleted.get_data(as_text=True)
    with app.app_context():
        assert DailyRecord.query.count() == 0


def test_validation_and_categories(client, app):
    with app.app_context():
        category_id = Category.query.first().id
    bad = sample_payload(category_id)
    bad["gross_revenue"] = "-2"
    bad["kilometers"] = "inválido"
    response = client.post("/registros/novo", data=bad, follow_redirects=True)
    text = response.get_data(as_text=True)
    assert "não pode ser negativo" in text
    assert "Quilometragem possui um valor inválido" in text

    created = client.post("/categorias/", data={"name": "Seguro"}, follow_redirects=True)
    assert "Categoria criada com sucesso" in created.get_data(as_text=True)
    duplicate = client.post("/categorias/", data={"name": "seguro"}, follow_redirects=True)
    assert "Esta categoria já existe" in duplicate.get_data(as_text=True)


def test_dashboard_period_filters_update_totals(client, app):
    today = date.today()
    with app.app_context():
        for record_date, revenue in [
            (today, "100.00"),
            (today - timedelta(days=3), "200.00"),
            (today - timedelta(days=10), "400.00"),
        ]:
            db.session.add(DailyRecord(
                date=record_date,
                gross_revenue=Decimal(revenue),
                kilometers=Decimal("50.00"),
            ))
        db.session.commit()

    today_page = client.get("/?period=today").get_data(as_text=True)
    seven_days_page = client.get("/?period=7days").get_data(as_text=True)
    old_day = today - timedelta(days=10)
    custom_page = client.get(
        f"/?period=custom&start={old_day.isoformat()}&end={old_day.isoformat()}"
    ).get_data(as_text=True)

    assert "R$ 100,00" in today_page
    assert "R$ 300,00" in seven_days_page
    assert "R$ 400,00" in custom_page
    assert 'name="period" value="custom"' in custom_page
    assert 'name="period" value="custom" disabled' not in custom_page


def test_login_flow(client, app):
    # Ativa temporariamente a obrigatoriedade de login
    app.config["LOGIN_REQUIRED"] = True
    try:
        # 1. Tentar acessar o dashboard deslogado -> deve redirecionar para /login
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]
        
        # 2. Tentar logar com credenciais inválidas
        response = client.post("/login", data={"username": "wrong", "password": "wrong"}, follow_redirects=True)
        assert "Usuário ou senha incorretos." in response.get_data(as_text=True)
        
        # 3. Logar com credenciais válidas (admin/admin)
        response = client.post("/login", data={"username": "admin", "password": "admin"}, follow_redirects=True)
        assert "Login realizado com sucesso!" in response.get_data(as_text=True)
        
        # 4. Acessar o dashboard agora que está logado -> deve retornar 200
        response = client.get("/")
        assert response.status_code == 200
        
        # 5. Fazer logout
        response = client.get("/logout", follow_redirects=True)
        assert "Sessão encerrada." in response.get_data(as_text=True)
        
        # 6. Tentar acessar novamente o dashboard deslogado -> deve redirecionar
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
    finally:
        # Restaura configuração original
        app.config["LOGIN_REQUIRED"] = False

