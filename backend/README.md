# Backend — Rota Positiva

API da nova arquitetura do Rota Positiva, construída com FastAPI.

## Execução local

No Windows, a partir da raiz do projeto:

```powershell
.\backend\.venv\Scripts\Activate.ps1
pip install -r .\backend\requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```

A API ficará disponível em `http://127.0.0.1:8000` e a documentação interativa em `http://127.0.0.1:8000/docs`.

## Testes

```powershell
pytest .\backend\tests
```
