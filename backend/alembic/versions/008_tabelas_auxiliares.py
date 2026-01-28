"""Tabelas auxiliares para relatórios e alertas

Revision ID: 008
Revises: 007
Create Date: 2026-01-26
"""
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Tabela de histórico de relatórios
    op.execute("""
        CREATE TABLE IF NOT EXISTS historico_relatorios (
            id SERIAL PRIMARY KEY,
            empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
            contador_id INTEGER NOT NULL REFERENCES contadores(id) ON DELETE CASCADE,
            analise_id INTEGER REFERENCES analises(id) ON DELETE SET NULL,
            tipo VARCHAR(20) NOT NULL DEFAULT 'pdf',
            template VARCHAR(50),
            arquivo_nome VARCHAR(255),
            arquivo_tamanho INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_historico_relatorios_empresa 
        ON historico_relatorios(empresa_id)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_historico_relatorios_contador 
        ON historico_relatorios(contador_id)
    """)
    
    # Tabela de configurações de relatório
    op.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes_relatorio (
            id SERIAL PRIMARY KEY,
            contador_id INTEGER NOT NULL UNIQUE REFERENCES contadores(id) ON DELETE CASCADE,
            logo_url TEXT,
            cor_primaria VARCHAR(20) DEFAULT '#1e40af',
            cor_secundaria VARCHAR(20) DEFAULT '#3b82f6',
            mostrar_logo BOOLEAN DEFAULT true,
            mostrar_marca_dagua BOOLEAN DEFAULT false,
            cabecalho_personalizado TEXT,
            rodape_personalizado TEXT,
            template_padrao VARCHAR(50) DEFAULT 'executivo',
            incluir_graficos BOOLEAN DEFAULT true,
            incluir_recomendacoes BOOLEAN DEFAULT true,
            formato_numeros VARCHAR(20) DEFAULT 'brasileiro',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de templates de relatório
    op.execute("""
        CREATE TABLE IF NOT EXISTS templates_relatorio (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            descricao TEXT,
            tipo VARCHAR(20) DEFAULT 'pdf',
            is_default BOOLEAN DEFAULT false,
            is_system BOOLEAN DEFAULT true,
            config_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Inserir templates padrão
    op.execute("""
        INSERT INTO templates_relatorio (nome, descricao, tipo, is_default, is_system)
        VALUES 
            ('Executivo', 'Relatório executivo com resumo e indicadores principais', 'pdf', true, true),
            ('Detalhado', 'Relatório completo com todas as análises e dados', 'pdf', false, true),
            ('Simplificado', 'Relatório resumido para visão rápida', 'pdf', false, true)
        ON CONFLICT DO NOTHING
    """)
    
    # Tabela de alertas
    op.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id SERIAL PRIMARY KEY,
            empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
            contador_id INTEGER NOT NULL REFERENCES contadores(id) ON DELETE CASCADE,
            tipo VARCHAR(50) NOT NULL,
            severidade VARCHAR(20) NOT NULL DEFAULT 'info',
            codigo VARCHAR(50) NOT NULL,
            titulo VARCHAR(255) NOT NULL,
            mensagem TEXT,
            valor_atual DECIMAL(15,2),
            valor_limite DECIMAL(15,2),
            valor_anterior DECIMAL(15,2),
            dados_json TEXT,
            periodo_referencia VARCHAR(20),
            lido BOOLEAN DEFAULT false,
            lido_em TIMESTAMP,
            resolvido BOOLEAN DEFAULT false,
            resolvido_em TIMESTAMP,
            resolvido_nota TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_alertas_empresa ON alertas(empresa_id)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_alertas_contador ON alertas(contador_id)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_alertas_severidade ON alertas(severidade)
    """)
    
    # Tabela de histórico de alertas (para evitar duplicados)
    op.execute("""
        CREATE TABLE IF NOT EXISTS alertas_historico (
            id SERIAL PRIMARY KEY,
            empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
            codigo VARCHAR(50) NOT NULL,
            periodo_referencia VARCHAR(20) NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(empresa_id, codigo, periodo_referencia)
        )
    """)
    
    # Tabela de configurações de alertas
    op.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes_alerta (
            id SERIAL PRIMARY KEY,
            empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
            contador_id INTEGER NOT NULL REFERENCES contadores(id) ON DELETE CASCADE,
            alerta_caixa_ativo BOOLEAN DEFAULT true,
            caixa_dias_critico INTEGER DEFAULT 30,
            caixa_dias_atencao INTEGER DEFAULT 60,
            alerta_margem_ativo BOOLEAN DEFAULT true,
            margem_minima DECIMAL(5,2) DEFAULT 5.0,
            margem_queda_pct DECIMAL(5,2) DEFAULT 20.0,
            alerta_tendencia_ativo BOOLEAN DEFAULT true,
            tendencia_meses_negativos INTEGER DEFAULT 3,
            queda_faturamento_pct DECIMAL(5,2) DEFAULT 15.0,
            alerta_anomalias_ativo BOOLEAN DEFAULT true,
            anomalia_desvio_padrao DECIMAL(5,2) DEFAULT 2.0,
            alerta_score_ativo BOOLEAN DEFAULT true,
            score_critico INTEGER DEFAULT 40,
            score_queda_pontos INTEGER DEFAULT 15,
            notificar_email BOOLEAN DEFAULT false,
            notificar_dashboard BOOLEAN DEFAULT true,
            frequencia_email VARCHAR(20) DEFAULT 'semanal',
            email_destino VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(empresa_id, contador_id)
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS configuracoes_alerta CASCADE")
    op.execute("DROP TABLE IF EXISTS alertas_historico CASCADE")
    op.execute("DROP TABLE IF EXISTS alertas CASCADE")
    op.execute("DROP TABLE IF EXISTS templates_relatorio CASCADE")
    op.execute("DROP TABLE IF EXISTS configuracoes_relatorio CASCADE")
    op.execute("DROP TABLE IF EXISTS historico_relatorios CASCADE")
