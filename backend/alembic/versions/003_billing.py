"""Sistema de Planos e Billing

Revision ID: 003_billing
Revises: 002_multi_tenancy
Create Date: 2025-01-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_billing'
down_revision: Union[str, None] = '002_multi_tenancy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabela de planos
    op.create_table(
        'planos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('codigo', sa.String(50), unique=True, nullable=False),  # free, starter, pro, enterprise
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('preco_mensal', sa.Float(), default=0),
        sa.Column('preco_anual', sa.Float(), default=0),
        sa.Column('moeda', sa.String(3), default='BRL'),
        
        # Limites
        sa.Column('max_usuarios', sa.Integer(), default=1),
        sa.Column('max_empresas', sa.Integer(), default=5),
        sa.Column('max_analises_mes', sa.Integer(), default=10),
        sa.Column('max_storage_mb', sa.Integer(), default=100),
        
        # Features
        sa.Column('permite_api', sa.Boolean(), default=False),
        sa.Column('permite_whitelabel', sa.Boolean(), default=False),
        sa.Column('permite_relatorios_pdf', sa.Boolean(), default=True),
        sa.Column('permite_exportar_excel', sa.Boolean(), default=False),
        sa.Column('suporte_prioritario', sa.Boolean(), default=False),
        
        # Stripe
        sa.Column('stripe_price_id_mensal', sa.String(100), nullable=True),
        sa.Column('stripe_price_id_anual', sa.String(100), nullable=True),
        
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.Column('ordem', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_planos_codigo', 'planos', ['codigo'], unique=True)
    
    # Planos padrão
    op.execute("""
        INSERT INTO planos (codigo, nome, descricao, preco_mensal, preco_anual, max_usuarios, max_empresas, max_analises_mes, max_storage_mb, permite_api, permite_whitelabel, permite_relatorios_pdf, permite_exportar_excel, suporte_prioritario, ordem) VALUES 
        ('free', 'Gratuito', 'Para começar a explorar', 0, 0, 1, 5, 10, 100, false, false, true, false, false, 1),
        ('starter', 'Starter', 'Para pequenos escritórios', 97, 970, 3, 20, 50, 500, false, false, true, true, false, 2),
        ('pro', 'Profissional', 'Para escritórios em crescimento', 297, 2970, 10, 100, 500, 2000, true, true, true, true, true, 3),
        ('enterprise', 'Enterprise', 'Para grandes operações', 997, 9970, 999, 9999, 99999, 50000, true, true, true, true, true, 4)
    """)
    
    # Tabela de assinaturas
    op.create_table(
        'assinaturas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organizacao_id', sa.Integer(), nullable=False),
        sa.Column('plano_id', sa.Integer(), nullable=False),
        
        # Status
        sa.Column('status', sa.String(30), default='active'),  # active, canceled, past_due, trialing, paused
        sa.Column('ciclo', sa.String(10), default='mensal'),  # mensal, anual
        
        # Período
        sa.Column('trial_start', sa.DateTime(), nullable=True),
        sa.Column('trial_end', sa.DateTime(), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), default=False),
        
        # Stripe
        sa.Column('stripe_customer_id', sa.String(100), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(100), nullable=True),
        sa.Column('stripe_payment_method_id', sa.String(100), nullable=True),
        
        # Desconto
        sa.Column('desconto_percentual', sa.Float(), default=0),
        sa.Column('cupom_codigo', sa.String(50), nullable=True),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['organizacao_id'], ['organizacoes.id']),
        sa.ForeignKeyConstraint(['plano_id'], ['planos.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_assinaturas_org', 'assinaturas', ['organizacao_id'])
    op.create_index('idx_assinaturas_stripe', 'assinaturas', ['stripe_subscription_id'], unique=True)
    
    # Tabela de faturas
    op.create_table(
        'faturas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('assinatura_id', sa.Integer(), nullable=False),
        sa.Column('organizacao_id', sa.Integer(), nullable=False),
        
        # Valores
        sa.Column('valor_bruto', sa.Float(), nullable=False),
        sa.Column('desconto', sa.Float(), default=0),
        sa.Column('valor_liquido', sa.Float(), nullable=False),
        sa.Column('moeda', sa.String(3), default='BRL'),
        
        # Status
        sa.Column('status', sa.String(30), default='pending'),  # pending, paid, failed, refunded, canceled
        sa.Column('data_vencimento', sa.DateTime(), nullable=False),
        sa.Column('data_pagamento', sa.DateTime(), nullable=True),
        
        # Stripe
        sa.Column('stripe_invoice_id', sa.String(100), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(100), nullable=True),
        sa.Column('stripe_charge_id', sa.String(100), nullable=True),
        
        # PDF
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('numero', sa.String(50), nullable=True),
        
        # Período de referência
        sa.Column('periodo_inicio', sa.DateTime(), nullable=True),
        sa.Column('periodo_fim', sa.DateTime(), nullable=True),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['assinatura_id'], ['assinaturas.id']),
        sa.ForeignKeyConstraint(['organizacao_id'], ['organizacoes.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_faturas_org', 'faturas', ['organizacao_id'])
    op.create_index('idx_faturas_assinatura', 'faturas', ['assinatura_id'])
    op.create_index('idx_faturas_stripe', 'faturas', ['stripe_invoice_id'], unique=True)
    
    # Tabela de uso mensal
    op.create_table(
        'uso_mensal',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organizacao_id', sa.Integer(), nullable=False),
        sa.Column('ano', sa.Integer(), nullable=False),
        sa.Column('mes', sa.Integer(), nullable=False),
        
        # Contadores
        sa.Column('usuarios_ativos', sa.Integer(), default=0),
        sa.Column('empresas_ativas', sa.Integer(), default=0),
        sa.Column('analises_realizadas', sa.Integer(), default=0),
        sa.Column('storage_usado_mb', sa.Float(), default=0),
        sa.Column('api_calls', sa.Integer(), default=0),
        sa.Column('relatorios_gerados', sa.Integer(), default=0),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['organizacao_id'], ['organizacoes.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organizacao_id', 'ano', 'mes', name='uq_uso_org_periodo')
    )
    op.create_index('idx_uso_org_periodo', 'uso_mensal', ['organizacao_id', 'ano', 'mes'])
    
    # Tabela de cupons
    op.create_table(
        'cupons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('codigo', sa.String(50), unique=True, nullable=False),
        sa.Column('descricao', sa.String(255), nullable=True),
        sa.Column('tipo', sa.String(20), default='percentual'),  # percentual, valor_fixo
        sa.Column('valor', sa.Float(), nullable=False),  # percentual ou valor em centavos
        sa.Column('max_usos', sa.Integer(), nullable=True),
        sa.Column('usos_atual', sa.Integer(), default=0),
        sa.Column('valido_ate', sa.DateTime(), nullable=True),
        sa.Column('planos_validos', sa.String(255), nullable=True),  # JSON array de códigos
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.Column('stripe_coupon_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_cupons_codigo', 'cupons', ['codigo'], unique=True)
    
    # Tabela de webhooks recebidos (para debug)
    op.create_table(
        'stripe_webhooks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(100), unique=True, nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('processado', sa.Boolean(), default=False),
        sa.Column('erro', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_webhooks_event', 'stripe_webhooks', ['event_id'], unique=True)


def downgrade() -> None:
    op.drop_table('stripe_webhooks')
    op.drop_table('cupons')
    op.drop_table('uso_mensal')
    op.drop_table('faturas')
    op.drop_table('assinaturas')
    op.drop_table('planos')
