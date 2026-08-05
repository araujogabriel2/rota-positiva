-- Migração v005: aplica o status de aprovação às políticas RLS sem recursão.

BEGIN;

CREATE OR REPLACE FUNCTION public.current_app_user_id()
RETURNS INTEGER
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT id
    FROM public.users
    WHERE supabase_id = auth.uid()::text
      AND status = 'active'
      AND is_active_account = TRUE
    LIMIT 1
$$;

CREATE OR REPLACE FUNCTION public.current_app_user_is_admin()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.users
        WHERE supabase_id = auth.uid()::text
          AND status = 'active'
          AND is_active_account = TRUE
          AND role = 'admin'
    )
$$;

REVOKE ALL ON FUNCTION public.current_app_user_id() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_app_user_is_admin() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.current_app_user_id() TO authenticated;
GRANT EXECUTE ON FUNCTION public.current_app_user_is_admin() TO authenticated;

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Usuários podem ver seu próprio perfil" ON users;
DROP POLICY IF EXISTS "Usuários podem atualizar seu próprio perfil" ON users;
DROP POLICY IF EXISTS "Usuários podem ver seu próprio perfil ou admins veem tudo" ON users;
DROP POLICY IF EXISTS "Usuários podem atualizar seu próprio perfil ou admins atualizam tudo" ON users;
DROP POLICY IF EXISTS "Admins podem excluir usuários" ON users;
DROP POLICY IF EXISTS users_select_active ON users;
CREATE POLICY users_select_active
ON users FOR SELECT TO authenticated
USING (
    id = public.current_app_user_id()
    OR public.current_app_user_is_admin()
);

DROP POLICY IF EXISTS "Usuários podem gerenciar suas próprias categorias" ON categories;
DROP POLICY IF EXISTS "Usuários podem ver suas próprias categorias ou globais" ON categories;
DROP POLICY IF EXISTS categories_select_active ON categories;
DROP POLICY IF EXISTS categories_insert_active ON categories;
DROP POLICY IF EXISTS categories_update_active ON categories;
DROP POLICY IF EXISTS categories_delete_active ON categories;
CREATE POLICY categories_select_active
ON categories FOR SELECT TO authenticated
USING (
    public.current_app_user_id() IS NOT NULL
    AND (
        user_id IS NULL
        OR user_id = public.current_app_user_id()
        OR public.current_app_user_is_admin()
    )
);
CREATE POLICY categories_insert_active
ON categories FOR INSERT TO authenticated
WITH CHECK (user_id = public.current_app_user_id());
CREATE POLICY categories_update_active
ON categories FOR UPDATE TO authenticated
USING (user_id = public.current_app_user_id())
WITH CHECK (user_id = public.current_app_user_id());
CREATE POLICY categories_delete_active
ON categories FOR DELETE TO authenticated
USING (user_id = public.current_app_user_id());

DROP POLICY IF EXISTS "Usuários podem gerenciar seus próprios registros" ON daily_records;
DROP POLICY IF EXISTS daily_records_active ON daily_records;
CREATE POLICY daily_records_active
ON daily_records FOR ALL TO authenticated
USING (
    user_id = public.current_app_user_id()
    OR public.current_app_user_is_admin()
)
WITH CHECK (
    user_id = public.current_app_user_id()
    OR public.current_app_user_is_admin()
);

DROP POLICY IF EXISTS "Usuários podem gerenciar suas próprias despesas" ON expenses;
DROP POLICY IF EXISTS expenses_active ON expenses;
CREATE POLICY expenses_active
ON expenses FOR ALL TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM daily_records
        WHERE daily_records.id = expenses.record_id
          AND (
              daily_records.user_id = public.current_app_user_id()
              OR public.current_app_user_is_admin()
          )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM daily_records
        WHERE daily_records.id = expenses.record_id
          AND (
              daily_records.user_id = public.current_app_user_id()
              OR public.current_app_user_is_admin()
          )
    )
);

COMMIT;
