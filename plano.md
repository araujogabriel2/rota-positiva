# Plano de Migração Incremental - Rota Positiva

Este documento guiará a migração do Rota Positiva do modelo monolítico Flask + Jinja2 para uma arquitetura desacoplada utilizando **FastAPI** (backend) e **React SPA com Vite** (frontend).

O desenvolvimento será feito de forma estritamente incremental, fase por fase. **Ao término de cada fase, o assistente parará a execução e solicitará que você realize testes locais para validar o funcionamento antes de prosseguirmos.**

---

## 📂 Estrutura de Pastas Inicial
```text
rota-positiva/
├── backend/          # API FastAPI em Python
└── frontend/         # Interface SPA em React
```

---

## 🗺️ Fases do Desenvolvimento e Checkpoints de Testes

### 🚀 Fase 1: Setup Inicial de Infraestrutura
* **O que será feito:**
  * Criação das pastas `backend/` e `frontend/`.
  * Inicialização do projeto React usando Vite com JavaScript/TypeScript na pasta `frontend/`.
  * Criação do ambiente virtual do backend (`backend/.venv`), dependências no `backend/requirements.txt` e arquivo principal `backend/main.py`.
  * Configuração básica do FastAPI com um endpoint `/api/health` e configuração de CORS para aceitar requisições do frontend.
* **🛑 Checkpoint de Teste (Usuário):**
  * Você iniciará o backend (`uvicorn`) e o frontend (`npm run dev`) e verificará se o navegador consegue acessar a rota do frontend e se o frontend consegue puxar dados do endpoint de health check do backend sem erros de CORS.

### 🔐 Fase 2: Login e Autenticação (Fluxo Auth Completo)
* **O que será feito:**
  * **Backend (FastAPI):**
    * Migração do modelo `User` para SQLAlchemy do FastAPI.
    * Implementação do endpoint de autenticação local (`POST /api/auth/login`) com retorno de Token JWT.
    * Implementação do fluxo de integração do Google OAuth via Supabase Auth.
    * Lógica de verificação da flag `must_change_password` e alteração de senha obrigatória no primeiro login.
  * **Frontend (React):**
    * Criação da tela de Login.
    * Configuração de contexto de autenticação global e proteção de rotas privadas.
    * Tela obrigatória de alteração de senha temporária.
* **🛑 Checkpoint de Teste (Usuário):**
  * Você validará se consegue realizar o login com senha temporária, se o sistema exige a alteração da senha, se o login social via Google está cadastrando o usuário pendente e se as rotas privadas estão devidamente protegidas contra acessos não autenticados.

### 🏷️ Fase 3: Categorias de Despesas
* **O que será feito:**
  * **Backend (FastAPI):**
    * Migração do modelo `Category`.
    * Endpoints de CRUD de categorias: listagem (`GET /api/categories`), criação (`POST /api/categories`) e remoção (`DELETE /api/categories/{id}`).
    * Validações de exclusão de categoria padrão e de categoria que possui despesas associadas.
  * **Frontend (React):**
    * Interface para gerenciamento de categorias.
    * Validação visual e tratamento de erros ao tentar remover categorias restritas.
* **🛑 Checkpoint de Teste (Usuário):**
  * Você tentará criar categorias personalizadas, deletá-las e verificará se a API e a tela bloqueiam a exclusão das categorias padrão pré-cadastradas no seed.

### 📝 Fase 4: Lançamentos Diários (Registros e Despesas)
* **O que será feito:**
  * **Backend (FastAPI):**
    * Migração dos modelos `DailyRecord` e `Expense`.
    * Endpoints de CRUD de registros diários com inclusão dinâmica de despesas na mesma requisição.
    * Lógica de validações numéricas e cálculo automático de médias por quilômetro rodado e lucro líquido.
  * **Frontend (React):**
    * Formulário dinâmico de lançamento diário (com possibilidade de adicionar/remover linhas de despesa em tempo real).
    * Tela de histórico de lançamentos com paginação, filtros de período e barra de busca por data.
* **🛑 Checkpoint de Teste (Usuário):**
  * Você fará lançamentos de dias completos (faturamento, km rodada e múltiplas despesas com categorias diferentes), editará os lançamentos inseridos e validará se todos os cálculos de médias no histórico estão correspondendo aos dados de entrada.

### 📊 Fase 5: Dashboard, Gráficos e Exportação de PDF
* **O que será feito:**
  * **Backend (FastAPI):**
    * Endpoint consolidado de estatísticas (`GET /api/dashboard/summary`).
    * Endpoint de exportação de relatório financeiro em PDF usando reportlab (`GET /api/reports/pdf`).
  * **Frontend (React):**
    * Painel principal contendo os cartões de indicadores (faturamento total, lucro, kms, custo/km, ganho/km).
    * Gráficos interativos diários (linha/barra) e distribuição de despesa por categoria (pizza/rosca).
    * Botão de exportação que baixa o PDF consolidado do período selecionado.
* **🛑 Checkpoint de Teste (Usuário):**
  * Você testará a reatividade dos gráficos ao alterar os filtros de período e fará o download do PDF para atestar se a renderização das tabelas e estatísticas está funcionando.

### 👑 Fase 6: Painel Administrativo
* **O que será feito:**
  * **Backend (FastAPI):**
    * Endpoints administrativos com validação do perfil `is_admin`.
    * Gerenciamento de usuários: aprovação de contas pendentes, desativação de contas e redefinição de senha com senha temporária.
  * **Frontend (React):**
    * Telas de controle do administrador para aprovação e gestão de motoristas.
    * Habilitação da seleção de motoristas específicos no dashboard/histórico/PDF do admin.
* **🛑 Checkpoint de Teste (Usuário):**
  * Você usará a conta de Administrador para aprovar um novo usuário que se cadastrou via Google OAuth e simulará a visualização das métricas deste usuário no seu dashboard de administrador.
