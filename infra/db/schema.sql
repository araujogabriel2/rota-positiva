-- Estrutura do Banco de Dados Rota Positiva (PostgreSQL)

-- ==========================================================
-- 1. TABELA: users (Contas de Usuários/Motoristas)
-- ==========================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    supabase_id VARCHAR(255) UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'driver',
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('pending', 'active', 'disabled')),
    is_active_account BOOLEAN NOT NULL DEFAULT TRUE,
    must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_supabase_id ON users(supabase_id);

-- Segurança (RLS - Row Level Security)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.current_app_user_id()
RETURNS INTEGER LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
    SELECT id FROM public.users
    WHERE supabase_id = auth.uid()::text
      AND status = 'active' AND is_active_account = TRUE
    LIMIT 1
$$;

CREATE OR REPLACE FUNCTION public.current_app_user_is_admin()
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.users
        WHERE supabase_id = auth.uid()::text
          AND status = 'active'
          AND is_active_account = TRUE AND role = 'admin'
    )
$$;

REVOKE ALL ON FUNCTION public.current_app_user_id() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_app_user_is_admin() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.current_app_user_id() TO authenticated;
GRANT EXECUTE ON FUNCTION public.current_app_user_is_admin() TO authenticated;

CREATE POLICY users_select_active ON users FOR SELECT TO authenticated
USING (id = public.current_app_user_id() OR public.current_app_user_is_admin());



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

CREATE POLICY categories_select_active ON categories FOR SELECT TO authenticated
USING (
    public.current_app_user_id() IS NOT NULL
    AND (
        user_id IS NULL
        OR user_id = public.current_app_user_id()
        OR public.current_app_user_is_admin()
    )
);

CREATE POLICY categories_insert_active ON categories FOR INSERT TO authenticated
WITH CHECK (user_id = public.current_app_user_id());
CREATE POLICY categories_update_active ON categories FOR UPDATE TO authenticated
USING (user_id = public.current_app_user_id())
WITH CHECK (user_id = public.current_app_user_id());
CREATE POLICY categories_delete_active ON categories FOR DELETE TO authenticated
USING (user_id = public.current_app_user_id());


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

CREATE POLICY daily_records_active ON daily_records FOR ALL TO authenticated
USING (
    user_id = public.current_app_user_id()
    OR public.current_app_user_is_admin()
)
WITH CHECK (
    user_id = public.current_app_user_id()
    OR public.current_app_user_is_admin()
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

CREATE POLICY expenses_active ON expenses FOR ALL TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM daily_records
        WHERE daily_records.id = expenses.record_id
          AND (
              daily_records.user_id = public.current_app_user_id()
              OR public.current_app_user_is_admin()
          )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM daily_records
        WHERE daily_records.id = expenses.record_id
          AND (
              daily_records.user_id = public.current_app_user_id()
              OR public.current_app_user_is_admin()
          )
    )
);
