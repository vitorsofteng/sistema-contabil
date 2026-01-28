"""Initial migration - Create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabela de contadores (usuários)
    op.create_table(
        'contadores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('senha_hash', sa.String(255), nullable=False),
        sa.Column('telefone', sa.String(50), nullable=True),
        sa.Column('crc', sa.String(50), nullable=True),
        sa.Column('ativo', sa.Boolean(), default=True, nullable=False),
        sa.Column('password_changed_at', sa.DateTime(), nullable=True),
        sa.Column('reset_token', sa.String(500), nullable=True),
        sa.Column('reset_token_expires', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_contadores_email', 'contadores', ['email'], unique=True)
    op.create_index('idx_contadores_email_ativo', 'contadores', ['email', 'ativo'])

    # Tabela de sessões
    op.create_table(
        'sessoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('contador_id', sa.Integer(), nullable=False),
        sa.Column('token_jti', sa.String(100), nullable=False),
        sa.Column('refresh_token_jti', sa.String(100), nullable=True),
        sa.Column('device_info', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('refresh_expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['contador_id'], ['contadores.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sessoes_token_jti', 'sessoes', ['token_jti'], unique=True)
    op.create_index('idx_sessoes_refresh_token_jti', 'sessoes', ['refresh_token_jti'], unique=True)
    op.create_index('idx_sessoes_contador_ativo', 'sessoes', ['contador_id', 'is_active'])

    # Tabela de empresas
    op.create_table(
        'empresas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('contador_id', sa.Integer(), nullable=False),
        sa.Column('razao_social', sa.String(255), nullable=False),
        sa.Column('nome_fantasia', sa.String(255), nullable=True),
        sa.Column('cnpj', sa.String(20), nullable=True),
        sa.Column('inscricao_estadual', sa.String(50), nullable=True),
        sa.Column('regime_tributario', sa.String(50), nullable=True),
        sa.Column('setor', sa.String(100), nullable=True),
        sa.Column('endereco', sa.String(500), nullable=True),
        sa.Column('cidade', sa.String(100), nullable=True),
        sa.Column('estado', sa.String(2), nullable=True),
        sa.Column('telefone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('contato_nome', sa.String(255), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('ativo', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['contador_id'], ['contadores.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_empresas_contador', 'empresas', ['contador_id'])
    op.create_index('idx_empresas_contador_ativo', 'empresas', ['contador_id', 'ativo'])
    op.create_index('idx_empresas_cnpj', 'empresas', ['cnpj'])

    # Tabela de dados mensais
    op.create_table(
        'dados_mensais',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('ano', sa.Integer(), nullable=False),
        sa.Column('mes', sa.Integer(), nullable=False),
        sa.Column('receita', sa.Float(), default=0),
        sa.Column('custos', sa.Float(), default=0),
        sa.Column('despesas', sa.Float(), default=0),
        sa.Column('impostos', sa.Float(), default=0),
        sa.Column('folha', sa.Float(), default=0),
        sa.Column('caixa', sa.Float(), default=0),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_dados_empresa', 'dados_mensais', ['empresa_id'])
    op.create_index('idx_dados_empresa_periodo', 'dados_mensais', ['empresa_id', 'ano', 'mes'])

    # Tabela de análises
    op.create_table(
        'analises',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('data_analise', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('periodo_inicio', sa.String(10), nullable=True),
        sa.Column('periodo_fim', sa.String(10), nullable=True),
        sa.Column('meses_analisados', sa.Integer(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('score_confianca', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('resultado_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_analises_empresa', 'analises', ['empresa_id'])
    op.create_index('idx_analises_empresa_data', 'analises', ['empresa_id', 'data_analise'])

    # Tabela de tentativas de login
    op.create_table(
        'login_attempts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('identifier', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('success', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_login_attempts_identifier', 'login_attempts', ['identifier'])
    op.create_index('idx_login_attempts_identifier_time', 'login_attempts', ['identifier', 'created_at'])

    # Tabela de blacklist de tokens
    op.create_table(
        'token_blacklist',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('jti', sa.String(100), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_token_blacklist_jti', 'token_blacklist', ['jti'], unique=True)
    op.create_index('idx_token_blacklist_expires', 'token_blacklist', ['expires_at'])


def downgrade() -> None:
    op.drop_table('token_blacklist')
    op.drop_table('login_attempts')
    op.drop_table('analises')
    op.drop_table('dados_mensais')
    op.drop_table('empresas')
    op.drop_table('sessoes')
    op.drop_table('contadores')
