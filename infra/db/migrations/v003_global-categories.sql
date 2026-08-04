-- Migração v003: Altera a tabela 'categories' para aceitar user_id NULL e atualizar políticas de RLS.

-- 1. Alterar a coluna user_id para aceitar NULL na tabela categories
ALTER TABLE categories ALTER COLUMN user_id DROP NOT NULL;

-- 2. Garantir que categorias globais tenham nomes únicos (índice único parcial)
CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_global_name ON categories(name) WHERE user_id IS NULL;

-- 3. Remover políticas antigas de categories
DROP POLICY IF EXISTS "Usuários podem gerenciar suas próprias categorias" ON categories;

-- 4. Criar novas políticas de RLS de categories para suportar categorias globais
CREATE POLICY "Usuários podem ver suas próprias categorias ou globais" 
ON categories FOR SELECT 
USING (
    user_id IS NULL 
    OR 
    user_id IN (SELECT id FROM users WHERE supabase_id = auth.uid()::text)
);

CREATE POLICY "Usuários podem gerenciar suas próprias categorias" 
ON categories FOR ALL 
USING (
    user_id IN (SELECT id FROM users WHERE supabase_id = auth.uid()::text)
);
