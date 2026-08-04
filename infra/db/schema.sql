-- Estrutura do Banco de Dados Rota Positiva (PostgreSQL)

-- ==========================================================
-- 1. TABELA: users (Contas de Usuários/Motoristas)
-- ==========================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(40) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    supabase_id VARCHAR(255) UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'driver',
    is_active_account BOOLEAN NOT NULL DEFAULT TRUE,
    must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_supabase_id ON users(supabase_id);

-- Segurança (RLS - Row Level Security)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários podem ver seu próprio perfil ou admins veem tudo" 
ON users FOR SELECT 
USING (
    supabase_id = auth.uid()::text 
    OR 
    (SELECT role FROM users WHERE supabase_id = auth.uid()::text) = 'admin'
);

CREATE POLICY "Usuários podem atualizar seu próprio perfil ou admins atualizam tudo" 
ON users FOR UPDATE 
USING (
    supabase_id = auth.uid()::text 
    OR 
    (SELECT role FROM users WHERE supabase_id = auth.uid()::text) = 'admin'
);

CREATE POLICY "Admins podem excluir usuários" 
ON users FOR DELETE 
USING (
    (SELECT role FROM users WHERE supabase_id = auth.uid()::text) = 'admin'
);



-- ==========================================================
-- 2. TABELA: categories (Categorias de Despesas)
-- ==========================================================

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(80) NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_categories_user_name UNIQUE (user_id, name)
);

CREATE INDEX idx_categories_user_id ON categories(user_id);
CREATE UNIQUE INDEX uq_categories_global_name ON categories(name) WHERE user_id IS NULL;

-- Segurança (RLS - Row Level Security)
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários podem ver suas próprias categorias ou globais" 
ON categories FOR SELECT 
USING (
    user_id IS NULL 
    OR 
    user_id IN (
        SELECT id FROM users WHERE supabase_id = auth.uid()::text
    )
);

CREATE POLICY "Usuários podem gerenciar suas próprias categorias" 
ON categories FOR ALL 
USING (
    user_id IN (
        SELECT id FROM users WHERE supabase_id = auth.uid()::text
    )
);


-- ==========================================================
-- 3. TABELA: daily_records (Registros de Faturamento Diário)
-- ==========================================================

CREATE TABLE daily_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    gross_revenue NUMERIC(12, 2) NOT NULL,
    kilometers NUMERIC(10, 2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_daily_records_user_date UNIQUE (user_id, date)
);

CREATE INDEX idx_daily_records_user_id ON daily_records(user_id);
CREATE INDEX idx_daily_records_date ON daily_records(date);

-- Segurança (RLS - Row Level Security)
ALTER TABLE daily_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários podem gerenciar seus próprios registros" 
ON daily_records FOR ALL 
USING (
    user_id IN (
        SELECT id FROM users WHERE supabase_id = auth.uid()::text
    )
);


-- ==========================================================
-- 4. TABELA: expenses (Despesas Diárias Detalhadas)
-- ==========================================================

CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL REFERENCES daily_records(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    description VARCHAR(180) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL
);

CREATE INDEX idx_expenses_record_id ON expenses(record_id);
CREATE INDEX idx_expenses_category_id ON expenses(category_id);

-- Segurança (RLS - Row Level Security)
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários podem gerenciar suas próprias despesas" 
ON expenses FOR ALL 
USING (
    record_id IN (
        SELECT id FROM daily_records 
        WHERE user_id IN (
            SELECT id FROM users WHERE supabase_id = auth.uid()::text
        )
    )
);
