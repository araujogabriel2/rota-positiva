# Plano de Migração Incremental — Rota Positiva

Este documento orienta a migração do Rota Positiva, atualmente um monólito Flask + Jinja2, para uma arquitetura desacoplada com **FastAPI** no backend e **React SPA com Vite e TypeScript** no frontend.

A migração será incremental. Ao término de cada fase, o desenvolvimento será interrompido para execução dos testes automatizados, teste manual do usuário, revisão do código, commit, push, Pull Request e merge. A fase seguinte somente começará após a validação da fase atual.

O sistema Flask permanecerá disponível como referência durante toda a migração e só será arquivado ou removido na fase final.

---

## 1. Arquitetura definida

```text
React + TypeScript + PWA
            |
            | HTTPS / JSON
            v
       FastAPI (Python)
            |
            +---- Supabase Auth
            |       - autenticação por senha
            |       - login com Google
            |       - emissão e renovação de tokens
            |
            +---- PostgreSQL do Supabase
            |       - usuários da aplicação
            |       - categorias
            |       - registros diários
            |       - despesas
            |
            +---- Relatórios PDF
```

### Responsabilidades

- **Supabase Auth:** será o servidor de autenticação (Auth Server). Ele validará as credenciais e emitirá os tokens de acesso e renovação.
- **FastAPI:** disponibilizará os endpoints da aplicação, delegará o login ao Supabase, validará os tokens emitidos pelo Supabase e aplicará as regras de autorização.
- **React:** exibirá as telas, chamará a API FastAPI e apresentará os resultados ao usuário.
- **PostgreSQL:** armazenará os dados permanentes do sistema.
- **RLS:** continuará como uma camada adicional de proteção no banco. A API também verificará as permissões antes de consultar ou alterar dados.

O FastAPI **não emitirá um segundo JWT próprio**. Nas rotas protegidas, ele validará a assinatura e as claims do token do Supabase, incluindo emissor, público, validade e identificador do usuário.

O campo `sub` do token será relacionado ao `supabase_id` do usuário da aplicação. Depois dessa identificação, a API consultará o banco para verificar:

- papel `admin` ou `driver`;
- estado `pending`, `active` ou `disabled`;
- propriedade dos registros solicitados.

---

## 2. Estrutura de pastas planejada

```text
rota-positiva/
├── app/                         # Flask atual, mantido até a fase final
├── backend/
│   ├── app/
│   │   ├── api/                 # Endpoints FastAPI versionados
│   │   ├── core/                # Configuração, segurança e dependências
│   │   ├── models/              # Modelos SQLAlchemy
│   │   ├── schemas/             # Validações e contratos Pydantic
│   │   ├── services/            # Regras financeiras e relatórios
│   │   └── main.py              # Inicialização da API
│   ├── tests/                   # Testes pytest do backend
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Componentes reutilizáveis
│   │   ├── pages/               # Páginas da aplicação
│   │   ├── services/            # Comunicação HTTP com o FastAPI
│   │   ├── auth/                # Sessão e proteção de rotas
│   │   └── types/               # Tipos TypeScript
│   └── package.json
├── infra/
│   └── db/                      # Migrações, schema e políticas RLS
├── docs/                        # Decisões e documentação técnica
└── plano.md
```

Os ambientes virtuais, arquivos `.env`, dependências instaladas e chaves secretas não serão enviados ao GitHub.

---

## 3. Regras válidas para todas as fases

1. Toda alteração será feita em uma branch própria, nunca diretamente na `main`.
2. Cada fase terá escopo pequeno e critérios objetivos de conclusão.
3. Toda rota protegida deverá validar o token do Supabase.
4. Usuários pendentes ou desativados não poderão acessar dados financeiros.
5. Motoristas acessarão somente os próprios registros.
6. Administradores poderão acessar os registros de todos os motoristas quando a operação permitir.
7. Valores monetários usarão tipos decimais adequados, evitando cálculos com ponto flutuante impreciso.
8. Datas e períodos terão regras explícitas para o fuso horário brasileiro.
9. Migrações do banco serão controladas e repetíveis. O banco não será apagado para aplicar uma atualização.
10. Chaves `secret` ou `service_role` nunca serão usadas no React nem versionadas no Git.
11. A chave `publishable` poderá ser usada no frontend, acompanhada de políticas RLS revisadas.
12. Cada fase terá testes automatizados e um checkpoint de teste manual.
13. O assistente explicará cada comando antes de solicitar sua execução.

---

## 4. Fases do desenvolvimento

### Fase 1 — Fundação do FastAPI e do React

**Branch sugerida:** `estrutura-fastapi-react`

#### Implementação

- Criar as pastas `backend/` e `frontend/` sem remover o Flask atual.
- Criar o backend FastAPI com estrutura modular.
- Criar `backend/requirements.txt` e configuração por variáveis de ambiente.
- Criar o frontend React com Vite e TypeScript.
- Configurar Bootstrap e a base do tema responsivo.
- Criar o endpoint `GET /api/v1/health`.
- Fazer o React consultar o health check.
- Configurar CORS com uma lista explícita de endereços permitidos.
- Criar `.env.example` sem valores secretos e revisar o `.gitignore`.

#### Testes automatizados

- Teste do health check com resposta HTTP 200.
- Teste das configurações obrigatórias.
- Teste básico de renderização e comunicação do frontend.

#### Checkpoint manual

- Iniciar FastAPI e React em terminais separados.
- Abrir o frontend no navegador.
- Confirmar que o frontend exibe a resposta do FastAPI sem erro de CORS.
- Abrir a documentação automática da API.

#### Critério de conclusão

Frontend e backend iniciam separadamente e conseguem se comunicar.

---

### Fase 2 — Banco de dados e migrações

**Branch sugerida:** `banco-fastapi`

#### Implementação

- Conectar o FastAPI ao PostgreSQL do Supabase.
- Configurar SQLAlchemy, sessões e transações.
- Adotar uma ferramenta ou processo único de migrações controladas.
- Mapear os modelos `User`, `Category`, `DailyRecord` e `Expense`.
- Preparar uma migração-base compatível com o schema atual.
- Revisar índices, chaves estrangeiras, valores decimais e restrições.
- Revisar as políticas RLS existentes sem apagar dados automaticamente.
- Criar tratamento claro para falhas de conexão.

#### Testes automatizados

- Teste da configuração da URL do banco.
- Teste de abertura e encerramento de sessão.
- Teste dos relacionamentos entre os modelos.
- Teste das migrações em um banco isolado de teste.

#### Checkpoint manual

- Executar o teste de conexão.
- Consultar o endpoint de diagnóstico.
- Confirmar que as tabelas esperadas existem no Supabase.

#### Critério de conclusão

O FastAPI acessa o PostgreSQL de maneira controlada e as migrações podem ser executadas sem apagar o banco.

---

### Fase 3 — Autenticação, autorização e aprovação básica

**Branch sugerida:** `autenticacao-supabase`

#### Implementação

- Configurar o Supabase Auth como única autoridade emissora dos tokens.
- Criar `POST /api/v1/auth/login`, delegando a autenticação por senha ao Supabase.
- Criar o início e o callback do login com Google usando o fluxo recomendado pelo Supabase.
- Criar renovação de sessão, logout e `GET /api/v1/auth/me`.
- Validar tokens do Supabase no FastAPI por claims verificadas/JWKS.
- Relacionar o `sub` do token ao `supabase_id` do usuário.
- Exigir alteração da senha temporária no primeiro login manual.
- Criar contas Google como `pending`.
- Bloquear contas `pending` e `disabled` nas rotas privadas.
- Criar nesta fase a administração mínima para aprovar ou recusar uma conta pendente.
- Proteger páginas privadas no React.

#### Testes automatizados

- Token ausente, inválido e expirado.
- Token válido sem usuário correspondente.
- Usuário pendente, ativo e desativado.
- Motorista tentando acessar endpoint administrativo.
- Login por senha temporária e troca obrigatória.
- Criação e aprovação de conta Google com integrações simuladas nos testes.

#### Checkpoint manual

- Entrar com senha temporária e trocar a senha.
- Entrar com uma conta Google nova.
- Confirmar que a conta aparece como pendente.
- Aprovar a conta como administrador.
- Entrar novamente e confirmar a liberação.
- Desativar o usuário e confirmar o bloqueio.

#### Critério de conclusão

O Supabase emite as sessões e o FastAPI identifica e autoriza corretamente administradores e motoristas.

---

### Fase 4 — Categorias de despesas

**Branch sugerida:** `categorias-api-react`

#### Implementação

- Criar endpoints versionados para listar, criar, editar e remover categorias.
- Diferenciar categorias padrão globais de categorias personalizadas.
- Definir a propriedade das categorias personalizadas.
- Impedir exclusão de categoria padrão.
- Impedir ou tratar com segurança a exclusão de categoria associada a despesas.
- Criar a tela React de categorias com mensagens claras.

#### Testes automatizados

- CRUD de categoria personalizada.
- Bloqueio da exclusão de categoria padrão.
- Bloqueio ou tratamento de categoria em uso.
- Isolamento das categorias personalizadas entre motoristas.
- Acesso administrativo.

#### Checkpoint manual

- Criar, editar e excluir uma categoria personalizada.
- Tentar excluir uma categoria padrão e uma categoria em uso.
- Confirmar que um motorista não administra a categoria pessoal de outro.

#### Critério de conclusão

Categorias funcionam no React e respeitam propriedade, uso e permissões.

---

### Fase 5 — Registros diários e despesas

**Branch sugerida:** `registros-despesas-api-react`

#### Implementação

- Criar CRUD de registros diários com despesas na mesma operação.
- Usar transação para salvar o registro e todas as despesas de forma atômica.
- Validar campos obrigatórios, datas, valores negativos e categorias.
- Evitar divisão por zero quando os quilômetros forem iguais a zero.
- Calcular despesas, lucro e indicadores por quilômetro.
- Criar formulário React com linhas dinâmicas de despesas.
- Criar histórico com detalhes, edição, exclusão, paginação e filtros.
- Solicitar confirmação antes da exclusão.
- Formatar moeda e datas no padrão brasileiro.

#### Testes automatizados

- Cálculos financeiros e arredondamento.
- Quilometragem igual a zero.
- Criação com múltiplas despesas.
- Rollback quando uma despesa é inválida.
- Edição e exclusão.
- Filtros de hoje, últimos sete dias, mês atual e período personalizado.
- Motorista tentando visualizar, editar ou excluir registro de outro motorista.

#### Checkpoint manual

- Criar um dia com várias despesas.
- Conferir os cálculos manualmente.
- Editar e excluir o registro.
- Testar todos os filtros de período.
- Confirmar o isolamento usando dois motoristas.

#### Critério de conclusão

O fluxo financeiro diário completo funciona no React e está protegido por usuário.

---

### Fase 6 — Dashboard, gráficos e relatório PDF

**Branch sugerida:** `dashboard-relatorios-api-react`

#### Implementação

- Criar `GET /api/v1/dashboard/summary` com filtros de período.
- Retornar faturamento, despesas, lucro, quilômetros e médias.
- Retornar séries diárias e despesas agrupadas por categoria.
- Criar gráficos no React.
- Criar `GET /api/v1/reports/pdf`.
- Gerar PDF com resumo, categorias, registros, despesas e horário de geração.
- Aplicar as permissões de motorista e administrador nos indicadores e relatórios.

#### Testes automatizados

- Períodos vazios e com dados.
- Hoje, últimos sete dias, mês atual e período personalizado.
- Totais e médias com múltiplos registros.
- Isolamento dos dados por motorista.
- Conteúdo e tipo do arquivo PDF.

#### Checkpoint manual

- Comparar os indicadores com cálculos manuais.
- Alterar todos os períodos e observar os gráficos.
- Baixar e revisar visualmente o PDF.

#### Critério de conclusão

Dashboard e PDF apresentam valores corretos e somente dados autorizados.

---

### Fase 7 — Painel administrativo completo

**Branch sugerida:** `painel-administrativo-react`

#### Implementação

- Criar gerenciamento completo de usuários.
- Aprovar, recusar, ativar e desativar contas.
- Criar usuários manualmente com senha temporária.
- Redefinir acesso com nova senha temporária.
- Filtrar dashboard, histórico e PDF por motorista.
- Registrar ações administrativas relevantes.
- Garantir que endpoints administrativos validem o papel `admin` no backend.

#### Testes automatizados

- Motorista bloqueado em todas as rotas administrativas.
- Aprovação, recusa, ativação e desativação.
- Redefinição de senha.
- Filtro administrativo por motorista.
- Usuário desativado perdendo acesso mesmo com token ainda válido.

#### Checkpoint manual

- Administrar uma conta durante todo o ciclo de vida.
- Selecionar um motorista e conferir seus indicadores e registros.
- Confirmar que uma conta comum não abre o painel administrativo.

#### Critério de conclusão

O administrador controla os usuários e consulta os dados autorizados sem compartilhar credenciais.

---

### Fase 8 — PWA, responsividade e uso no celular

**Branch sugerida:** `pwa-responsividade`

#### Implementação

- Criar manifesto, ícones e configurações da PWA.
- Preparar instalação na tela inicial.
- Revisar navegação, formulários, tabelas e gráficos em telas pequenas.
- Criar estados de carregamento, erro, lista vazia e perda de conexão.
- Garantir áreas de toque e campos adequados ao celular.
- Definir comportamento seguro quando a sessão expirar.

#### Testes automatizados

- Build de produção do frontend.
- Validação do manifesto.
- Testes básicos dos fluxos principais em viewport móvel.

#### Checkpoint manual

- Abrir pelo celular.
- Instalar a PWA.
- Cadastrar um registro completo usando somente o telefone.
- Consultar dashboard, histórico e PDF.

#### Critério de conclusão

A aplicação é responsiva e instalável, com os fluxos principais utilizáveis no celular.

---

### Fase 9 — Qualidade, segurança e substituição do Flask

**Branch sugerida:** `finalizacao-nova-arquitetura`

#### Implementação

- Executar revisão completa de segurança e permissões.
- Revisar CORS, cookies ou armazenamento de sessão, logs e tratamento de erros.
- Revisar RLS e privilégios do banco.
- Comparar todos os cálculos com a versão Flask.
- Executar testes de regressão de backend e frontend.
- Atualizar README, documentação da API e instruções de execução.
- Registrar uma versão estável do Flask no Git antes de removê-lo ou arquivá-lo.
- Definir os comandos de build e preparação para hospedagem.
- Remover o Flask somente após a nova versão cumprir todos os critérios funcionais.

#### Checkpoint final

- Cadastrar, editar, consultar e excluir registros.
- Testar dois motoristas e um administrador.
- Testar aprovação, desativação e redefinição de acesso.
- Validar dashboard, filtros, gráficos e PDF.
- Testar a instalação e o uso pelo celular.
- Confirmar que nenhuma chave secreta está versionada.

#### Critério de conclusão

React e FastAPI substituem oficialmente o Flask sem perda das funcionalidades previstas para o Rota Positiva.

---

## 5. Fluxo de Git por fase

```text
Atualizar a main
      ↓
Criar uma branch da fase
      ↓
Implementar somente o escopo previsto
      ↓
Executar testes automatizados
      ↓
Realizar o checkpoint manual
      ↓
Revisar as alterações
      ↓
Criar commit e enviar a branch
      ↓
Abrir Pull Request e fazer o merge
      ↓
Atualizar a main antes da próxima fase
```

Cada commit deverá ter uma descrição objetiva do que foi concluído. Nenhuma fase será considerada pronta apenas porque o código foi escrito; os testes e o checkpoint manual fazem parte da conclusão.
