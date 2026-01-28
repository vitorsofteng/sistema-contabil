"""007 - Análise Financeira Avançada

Revision ID: 007
Revises: 006
Create Date: 2024-01-26

DRE automático, índices financeiros, benchmarks, projeções e metas.
"""
from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Benchmarks por setor
    op.create_table(
        'benchmarks_setor',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('setor', sa.String(100), nullable=False),
        sa.Column('subsetor', sa.String(100), nullable=True),
        
        # Margens
        sa.Column('margem_bruta_min', sa.Float(), default=0),
        sa.Column('margem_bruta_media', sa.Float(), default=0),
        sa.Column('margem_bruta_max', sa.Float(), default=0),
        sa.Column('margem_liquida_min', sa.Float(), default=0),
        sa.Column('margem_liquida_media', sa.Float(), default=0),
        sa.Column('margem_liquida_max', sa.Float(), default=0),
        
        # Índices
        sa.Column('liquidez_corrente_min', sa.Float(), default=0),
        sa.Column('liquidez_corrente_media', sa.Float(), default=1),
        sa.Column('liquidez_corrente_max', sa.Float(), default=0),
        sa.Column('endividamento_medio', sa.Float(), default=0),
        
        # Operacionais
        sa.Column('custo_folha_pct_medio', sa.Float(), default=0),  # % da receita
        sa.Column('prazo_medio_recebimento', sa.Integer(), default=30),  # dias
        sa.Column('prazo_medio_pagamento', sa.Integer(), default=30),  # dias
        
        # Crescimento típico
        sa.Column('crescimento_anual_medio', sa.Float(), default=0),
        
        sa.Column('fonte', sa.String(255), nullable=True),
        sa.Column('ano_referencia', sa.Integer(), default=2024),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.UniqueConstraint('setor', 'subsetor', name='uq_benchmark_setor_subsetor')
    )
    
    # Metas da empresa
    op.create_table(
        'metas_empresa',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contador_id', sa.Integer(), sa.ForeignKey('contadores.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('ano', sa.Integer(), nullable=False),
        sa.Column('mes', sa.Integer(), nullable=True),  # NULL = meta anual
        
        # Metas financeiras
        sa.Column('receita_meta', sa.Float(), nullable=True),
        sa.Column('lucro_meta', sa.Float(), nullable=True),
        sa.Column('margem_meta', sa.Float(), nullable=True),
        sa.Column('custos_max', sa.Float(), nullable=True),
        sa.Column('despesas_max', sa.Float(), nullable=True),
        
        # Metas operacionais
        sa.Column('caixa_minimo', sa.Float(), nullable=True),
        sa.Column('score_minimo', sa.Integer(), nullable=True),
        
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.UniqueConstraint('empresa_id', 'ano', 'mes', name='uq_meta_empresa_periodo')
    )
    
    # Projeções salvas
    op.create_table(
        'projecoes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contador_id', sa.Integer(), sa.ForeignKey('contadores.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('cenario', sa.String(20), default='realista'),  # otimista, realista, pessimista
        
        # Parâmetros da projeção
        sa.Column('meses_projetados', sa.Integer(), default=12),
        sa.Column('taxa_crescimento_receita', sa.Float(), default=0),
        sa.Column('taxa_variacao_custos', sa.Float(), default=0),
        sa.Column('taxa_variacao_despesas', sa.Float(), default=0),
        sa.Column('sazonalidade_json', sa.Text(), nullable=True),  # Fatores por mês
        
        # Resultado da projeção (JSON com dados mensais)
        sa.Column('resultado_json', sa.Text(), nullable=True),
        
        # Resumo
        sa.Column('receita_total_projetada', sa.Float(), nullable=True),
        sa.Column('lucro_total_projetado', sa.Float(), nullable=True),
        sa.Column('caixa_final_projetado', sa.Float(), nullable=True),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Adicionar setor à empresa
    op.add_column('empresas', sa.Column('setor', sa.String(100), nullable=True))
    op.add_column('empresas', sa.Column('subsetor', sa.String(100), nullable=True))
    op.add_column('empresas', sa.Column('porte', sa.String(20), nullable=True))  # MEI, ME, EPP, Médio, Grande
    
    # Índice para busca de benchmarks
    op.create_index('ix_benchmarks_setor', 'benchmarks_setor', ['setor'])
    op.create_index('ix_metas_empresa', 'metas_empresa', ['empresa_id', 'ano'])
    op.create_index('ix_projecoes_empresa', 'projecoes', ['empresa_id'])


def downgrade():
    op.drop_index('ix_projecoes_empresa', 'projecoes')
    op.drop_index('ix_metas_empresa', 'metas_empresa')
    op.drop_index('ix_benchmarks_setor', 'benchmarks_setor')
    
    op.drop_column('empresas', 'porte')
    op.drop_column('empresas', 'subsetor')
    op.drop_column('empresas', 'setor')
    
    op.drop_table('projecoes')
    op.drop_table('metas_empresa')
    op.drop_table('benchmarks_setor')
