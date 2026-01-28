-- Script para corrigir tabela configuracoes_relatorio
-- Execute este script diretamente no banco PostgreSQL se estiver tendo erros de colunas

-- Adicionar colunas faltantes (IF NOT EXISTS evita erros se já existirem)
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS nome_escritorio TEXT;
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS slogan TEXT;
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS endereco TEXT;
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS telefone TEXT;
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS email_contato TEXT;
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS website TEXT;
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS cor_destaque TEXT DEFAULT '#059669';
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS mostrar_graficos BOOLEAN DEFAULT true;
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS mostrar_recomendacoes BOOLEAN DEFAULT true;
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS texto_rodape TEXT;
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS disclaimer TEXT;
ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS logo_base64 TEXT;

-- Verificar se as colunas foram adicionadas
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'configuracoes_relatorio'
ORDER BY ordinal_position;
