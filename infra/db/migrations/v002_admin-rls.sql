-- Migração v002: Atualiza as políticas de RLS da tabela 'users' para dar suporte ao papel de administrador.

-- 1. Remover políticas antigas da tabela 'users'
DROP POLICY IF EXISTS "Usuários podem ver seu próprio perfil" ON users;
DROP POLICY IF EXISTS "Usuários podem atualizar seu próprio perfil" ON users;

-- 2. Criar novas políticas de leitura e escrita com suporte a administradores (role = 'admin')
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
