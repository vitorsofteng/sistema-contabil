"""Adiciona campo sistema_contabil na tabela empresas

Revision ID: 012_sistema_contabil
Revises: 011_configuracoes_relatorio
Create Date: 2025-01-30
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '012_sistema_contabil'
down_revision = '011_configuracoes_relatorio'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Adiciona coluna sistema_contabil."""
    op.add_column(
        'empresas',
        sa.Column('sistema_contabil', sa.Integer(), nullable=False, server_default='0')
    )
    
    # Remove o server_default após criar a coluna
    op.alter_column('empresas', 'sistema_contabil', server_default=None)


def downgrade() -> None:
    """Remove coluna sistema_contabil."""
    op.drop_column('empresas', 'sistema_contabil')
