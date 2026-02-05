"""Adiciona campos do escritório ao contador

Revision ID: 013_escritorio_contador
Revises: 012_sistema_contabil
Create Date: 2024-02-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013_escritorio_contador'
down_revision = '012_sistema_contabil'
branch_labels = None
depends_on = None


def upgrade():
    """Adiciona campos escritorio e cnpj à tabela contadores."""
    
    # Adicionar campo escritorio
    op.add_column('contadores', sa.Column('escritorio', sa.String(255), nullable=True))
    
    # Adicionar campo cnpj do escritório
    op.add_column('contadores', sa.Column('cnpj', sa.String(14), nullable=True))


def downgrade():
    """Remove campos escritorio e cnpj da tabela contadores."""
    
    op.drop_column('contadores', 'cnpj')
    op.drop_column('contadores', 'escritorio')
