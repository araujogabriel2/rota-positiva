# Rota Positiva

Aplicação web responsiva para o controle financeiro diário de motoristas de aplicativo. Permite registrar faturamento, quilômetros e várias despesas, acompanha indicadores no dashboard e gera relatórios completos em PDF.

## Recursos

- Cadastro, edição, consulta e exclusão de registros diários.
- Múltiplas despesas por dia e categorias personalizadas.
- Cálculo automático de lucro, faturamento/custo/lucro por quilômetro.
- Histórico com filtro por período e pesquisa por data exata.
- Dashboard para hoje, últimos 7 dias, mês atual ou período personalizado.
- Gráficos de faturamento, lucro e despesas por categoria.
- Relatório PDF profissional com resumo e detalhamento.
- Banco SQLite local ou PostgreSQL hospedado no Supabase.
- Interface em português, responsiva e otimizada para celular.

## Pré-requisitos e instalação do Python

Instale o Python 3.11 ou mais recente pelo site [python.org](https://www.python.org/downloads/). No Windows, marque a opção **Add Python to PATH** durante a instalação. Confirme no terminal:

```powershell
python --version
```

No macOS ou Linux, o comando pode ser `python3 --version`.

## Criar o ambiente virtual

Abra um terminal na pasta do projeto.

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Se o PowerShell bloquear a ativação, execute uma vez na sessão atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Instalar e executar

Com o ambiente virtual ativo:

```powershell
python -m pip install -r requirements.txt
python run.py
```

Acesse [http://127.0.0.1:5000](http://127.0.0.1:5000) no navegador. Para abrir pelo celular na mesma rede Wi-Fi, descubra o IP local do computador com `ipconfig` (Windows) ou `ifconfig` (macOS/Linux) e acesse `http://SEU-IP:5000`.

O arquivo `instance/financeiro.db` será criado automaticamente. Para produção, defina uma chave secreta antes de iniciar:

```powershell
$env:SECRET_KEY = "uma-chave-longa-e-aleatoria"
python run.py
```

## Usar PostgreSQL no Supabase

O SQLite continua sendo o padrão quando `DATABASE_URL` não está definida. Para
usar o Supabase sem expor credenciais:

1. No painel do Supabase, abra **Connect > Direct > Session pooler > URI**.
2. Copie `.env.example` para um novo arquivo chamado `.env`.
3. Cole a URI em `DATABASE_URL`, mantendo `[YOUR-PASSWORD]` no endereço.
4. Informe a senha real separadamente em `DATABASE_PASSWORD`.
5. Gere valores privados para `SECRET_KEY` e `ADMIN_PASSWORD`.
6. Instale as dependências novamente.

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
notepad .env
python -m pip install -r requirements.txt
```

O arquivo `.env` está no `.gitignore` e nunca deve ser commitado. A aplicação
codifica a senha para uso seguro na URI e usa o driver Psycopg 3.

Teste a conexão antes de criar tabelas ou migrar dados:

```powershell
python scripts/check_database_connection.py
```

O teste executa apenas `SELECT 1` e não modifica o banco.

### Migrar os dados existentes do SQLite

Faça um backup de `instance/financeiro.db`, feche o servidor Flask e execute:

```powershell
python scripts/migrate_sqlite_to_postgres.py
```

A ferramenta cria as tabelas ausentes e copia categorias, registros e despesas
em uma única transação. Se o PostgreSQL já contiver registros ou despesas, a
migração é cancelada para evitar duplicação. O SQLite de origem não é alterado.

Depois da migração, inicie normalmente:

```powershell
python run.py
```

## Como usar

1. Abra **Novo registro**, informe data, faturamento e quilômetros.
2. Use **Adicionar** para incluir cada despesa; os totais são atualizados enquanto você digita.
3. Salve e confira os indicadores do dia.
4. Consulte **Histórico** para filtrar, visualizar, editar ou excluir registros.
5. Use **Categorias** para incluir tipos de despesas personalizados.
6. No **Dashboard**, selecione o período para atualizar cartões e gráficos.

## Gerar o relatório PDF

Abra **Relatórios**, escolha o período e clique em **Baixar PDF**. O arquivo inclui os totais, indicadores por quilômetro, despesas agrupadas por categoria, registros diários, despesas detalhadas, horário de geração e paginação.

## Testes automatizados

Com o ambiente virtual ativo:

```powershell
python -m pytest -q
```

Os testes usam um banco SQLite em memória e não alteram os dados reais.

## Estrutura

```text
app/
  routes/              # dashboard, registros, categorias e relatórios
  services/            # cálculos, validações e geração do PDF
  static/css/          # identidade visual responsiva
  static/js/           # despesas dinâmicas, cálculos e gráficos
  templates/           # páginas Jinja/Bootstrap
  config.py            # configuração
  extensions.py        # SQLAlchemy e proteção CSRF
  models.py             # entidades do banco
instance/              # banco SQLite local (criado automaticamente)
scripts/               # migração segura do SQLite para PostgreSQL
tests/                 # testes automatizados
requirements.txt       # dependências fixadas
run.py                 # ponto de entrada
```

## Modelo de dados

- `DailyRecord`: um dia de trabalho, com data única, faturamento, quilômetros e observações.
- `Expense`: despesa vinculada a um registro diário e a uma categoria.
- `Category`: categorias padrão ou criadas pelo usuário.

Ao excluir um registro diário, suas despesas são excluídas em conjunto. Categorias padrão e categorias que já possuem despesas são protegidas contra exclusão.
