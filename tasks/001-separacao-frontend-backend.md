# Tarefa 001: Separação de Frontend e Backend (Migração para API + SPA)

Esta especificação técnica e pedagógica guia o processo de migração do **Rota Positiva** de um modelo monolítico (Flask + Jinja2) para uma arquitetura moderna desacoplada utilizando **FastAPI** no backend e **React** no frontend.

---

## 🎓 Conceitos Fundamentais (Para o Estagiário)

Antes de colocar a mão no código, é fundamental compreender a teoria por trás da mudança:

### 1. O que é um Monolito?
No modelo monolítico atual, o servidor Python (Flask) faz tudo: gerencia o banco de dados, processa as regras de negócio e renderiza o HTML final (telas) usando templates Jinja2.
* **O Problema**: Cada clique em um link ou botão de filtro faz o navegador solicitar uma página inteira de volta para o servidor. Isso gera um **refresh (recarga de tela)** perceptível e lento. Adicionalmente, se o banco estiver longe (ex: Supabase na nuvem), o acúmulo de consultas SQL executadas sequencialmente no servidor faz a página demorar muito para carregar na tela do usuário.

### 2. O que é uma API (Application Programming Interface)?
Uma API RESTful é um servidor que **não gera telas**. Ele apenas expõe "endpoints" (URLs) que recebem e respondem com dados puros, geralmente no formato **JSON (JavaScript Object Notation)**. 
* *Exemplo de resposta de uma API:*
  ```json
  {
    "id": 1,
    "name": "Combustível",
    "is_default": true
  }
  ```

### 3. O que é uma SPA (Single Page Application)?
Uma SPA é uma aplicação frontend executada inteiramente no navegador do usuário (usando **React**). O navegador baixa o código do frontend apenas uma vez.
* **Como funciona**: Quando o usuário clica em uma rota ou filtra uma busca, o React não recarrega a página. Ele faz uma chamada em segundo plano (AJAX/Fetch) para a API, obtém os dados em JSON e atualiza apenas os elementos necessários na tela. A experiência do usuário fica fluida, instantânea e sem piscadas de tela, idêntica a um aplicativo de celular.

---

## 📂 Nova Estrutura de Pastas Proposta

O repositório do Rota Positiva será dividido em duas pastas principais na raiz do projeto:

```text
rota-positiva/
├── backend/          # API FastAPI em Python
│   ├── app/          # Código fonte da API
│   ├── requirements.txt
│   └── main.py       # Ponto de entrada da API
│
└── frontend/         # Interface SPA em React
    ├── src/          # Código fonte em React
    ├── package.json
    └── index.html
```

---

## 🛠️ Roteiro de Implementação

Siga os passos abaixo na ordem descrita para realizar a transição:

### Fase 1: O Backend (`backend/`)

Você criará a API em **FastAPI**, que é o framework moderno de Python mais rápido e recomendado do mercado.

1. **Inicialização**:
   * Crie a pasta `backend/`.
   * Crie o arquivo virtualenv e instale as dependências: `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg` (para Postgres) e `supabase` (para manter o fluxo de autenticação social se necessário).

2. **Portabilidade de Modelos**:
   * Migre as definições de tabelas de `app/models.py` do SQLAlchemy do Flask para o SQLAlchemy padrão do FastAPI.

3. **CORS (Cross-Origin Resource Sharing)**:
   * **Muito Importante**: Como o React rodará em uma porta (ex: `http://localhost:5173`) e o FastAPI em outra (ex: `http://localhost:8000`), o navegador bloqueará as chamadas por segurança. Você deve habilitar o middleware de CORS no FastAPI para permitir requisições vindas da URL do frontend.

4. **Criação de Endpoints (Rotas da API)**:
   * Substitua as rotas antigas por endpoints JSON:
     * `GET /api/records` -> Retorna a lista de registros diários em JSON.
     * `POST /api/records` -> Recebe JSON com faturamento/km e cadastra um registro.
     * `GET /api/categories` -> Retorna a lista de categorias locais e globais.
     * `POST /api/categories` -> Cadastra uma categoria personalizada.

---

### Fase 2: O Frontend (`frontend/`)

Você criará a SPA em **React** utilizando a ferramenta de build rápida **Vite**.

1. **Inicialização**:
   * Crie a pasta `frontend/`.
   * Inicialize o projeto rodando: `npm create vite@latest . -- --template react` (ou react-ts se preferir TypeScript).
   * Instale o **React Router Dom** para gerenciar as rotas no navegador sem recarga de tela.

2. **Consumo de API**:
   * Utilize a API do navegador `fetch` ou instale a biblioteca `axios` para fazer requisições HTTP para a API FastAPI (ex: `http://localhost:8000/api/records`).

3. **Transição de Telas**:
   * Recrie o layout limpo e moderno da aplicação em componentes React.
   * Quando o formulário de "Novo Registro" for enviado, faça uma requisição `POST` com os dados em JSON para o backend e, se obtiver sucesso, redirecione o usuário usando o roteador do React (ex: `navigate('/historico')`) sem recarregar a página.

---

## 🎯 Critérios de Aceitação

A tarefa será considerada concluída quando:
* O backend e o frontend estiverem executando de forma independente.
* A navegação entre telas no React ocorrer de forma instantânea (sem reload visual).
* Os dados adicionados no formulário do frontend forem salvos no banco de dados através da chamada à API do backend.
* O fluxo de login e restrições RLS do Supabase continuarem operando de forma íntegra.
