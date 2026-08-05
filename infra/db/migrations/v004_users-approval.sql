-- Migração v004: completa o esquema de autenticação e adiciona aprovação de contas.
-- Pode ser executada novamente com segurança no PostgreSQL do Supabase.

BEGIN;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS supabase_id VARCHAR(255);

ALTER TABLE users
    ALTER COLUMN username TYPE VARCHAR(255);

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_supabase_id
    ON users (supabase_id)
    WHERE supabase_id IS NOT NULL;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS status VARCHAR(20);

UPDATE users
SET status = CASE
    WHEN is_active_account THEN 'active'
    ELSE 'disabled'
END
WHERE status IS NULL;

ALTER TABLE users
    ALTER COLUMN status SET DEFAULT 'active',
    ALTER COLUMN status SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_users_status'
          AND conrelid = 'users'::regclass
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT ck_users_status
            CHECK (status IN ('pending', 'active', 'disabled'));
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS ix_users_status ON users (status);

-- Necessário para as categorias padrão compartilhadas entre todos os usuários.
ALTER TABLE categories
    ALTER COLUMN user_id DROP NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_global_name
    ON categories (LOWER(name))
    WHERE user_id IS NULL;

COMMIT;
