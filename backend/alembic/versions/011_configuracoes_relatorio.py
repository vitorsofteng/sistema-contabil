"""Adicionar colunas faltantes em configuracoes_relatorio

Revision ID: 011
Revises: 010
Create Date: 2025-01-28
"""
from alembic import op
import sqlalchemy as sa

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar tabela se não existir
    op.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes_relatorio (
            id SERIAL PRIMARY KEY,
            contador_id INTEGER NOT NULL UNIQUE,
            logo_base64 TEXT,
            logo_url TEXT,
            nome_escritorio TEXT,
            slogan TEXT,
            endereco TEXT,
            telefone TEXT,
            email_contato TEXT,
            website TEXT,
            cor_primaria TEXT DEFAULT '#1e40af',
            cor_secundaria TEXT DEFAULT '#3b82f6',
            cor_destaque TEXT DEFAULT '#059669',
            mostrar_logo BOOLEAN DEFAULT true,
            mostrar_marca_dagua BOOLEAN DEFAULT false,
            mostrar_graficos BOOLEAN DEFAULT true,
            mostrar_recomendacoes BOOLEAN DEFAULT true,
            cabecalho_personalizado TEXT,
            rodape_personalizado TEXT,
            texto_rodape TEXT,
            disclaimer TEXT,
            template_padrao TEXT DEFAULT 'executivo',
            incluir_graficos BOOLEAN DEFAULT true,
            incluir_recomendacoes BOOLEAN DEFAULT true,
            formato_numeros TEXT DEFAULT 'brasileiro',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Adicionar colunas que podem estar faltando
    colunas = [
        ("nome_escritorio", "TEXT"),
        ("slogan", "TEXT"),
        ("endereco", "TEXT"),
        ("telefone", "TEXT"),
        ("email_contato", "TEXT"),
        ("website", "TEXT"),
        ("cor_destaque", "TEXT DEFAULT '#059669'"),
        ("mostrar_graficos", "BOOLEAN DEFAULT true"),
        ("mostrar_recomendacoes", "BOOLEAN DEFAULT true"),
        ("texto_rodape", "TEXT"),
        ("disclaimer", "TEXT"),
        ("logo_base64", "TEXT"),
    ]
    
    for nome, tipo in colunas:
        try:
            op.execute(f"ALTER TABLE configuracoes_relatorio ADD COLUMN IF NOT EXISTS {nome} {tipo}")
        except Exception:
            pass


def downgrade() -> None:
    # Não remover colunas no downgrade para evitar perda de dados
    pass
