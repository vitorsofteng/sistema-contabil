"""Importação Avançada de Dados

Revision ID: 004_importacao_avancada
Revises: 003_billing
Create Date: 2025-01-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_importacao_avancada'
down_revision: Union[str, None] = '003_billing'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabela de histórico de importações
    op.create_table(
        'importacoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organizacao_id', sa.Integer(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=True),
        sa.Column('contador_id', sa.Integer(), nullable=False),
        
        # Arquivo
        sa.Column('nome_arquivo', sa.String(255), nullable=False),
        sa.Column('tipo_arquivo', sa.String(20), nullable=False),  # csv, xlsx, ofx, xml_nfe
        sa.Column('tamanho_bytes', sa.Integer(), nullable=True),
        sa.Column('hash_arquivo', sa.String(64), nullable=True),  # SHA256 para detectar duplicatas
        
        # Status
        sa.Column('status', sa.String(30), default='pending'),  # pending, processing, completed, failed, partial
        sa.Column('total_registros', sa.Integer(), default=0),
        sa.Column('registros_importados', sa.Integer(), default=0),
        sa.Column('registros_duplicados', sa.Integer(), default=0),
        sa.Column('registros_erro', sa.Integer(), default=0),
        
        # Mapeamento usado
        sa.Column('mapeamento_id', sa.Integer(), nullable=True),
        sa.Column('mapeamento_json', sa.Text(), nullable=True),  # Snapshot do mapeamento usado
        
        # Erros e log
        sa.Column('erros_json', sa.Text(), nullable=True),  # Lista de erros por linha
        sa.Column('resumo', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('iniciado_em', sa.DateTime(), nullable=True),
        sa.Column('finalizado_em', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.ForeignKeyConstraint(['organizacao_id'], ['organizacoes.id']),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id']),
        sa.ForeignKeyConstraint(['contador_id'], ['contadores.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_importacoes_org', 'importacoes', ['organizacao_id'])
    op.create_index('idx_importacoes_empresa', 'importacoes', ['empresa_id'])
    op.create_index('idx_importacoes_hash', 'importacoes', ['hash_arquivo'])
    
    # Tabela de mapeamentos salvos
    op.create_table(
        'mapeamentos_importacao',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organizacao_id', sa.Integer(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=True),
        sa.Column('contador_id', sa.Integer(), nullable=False),
        
        # Identificação
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('descricao', sa.String(255), nullable=True),
        sa.Column('tipo_arquivo', sa.String(20), nullable=False),  # csv, xlsx
        
        # Configuração
        sa.Column('delimitador', sa.String(5), default=','),
        sa.Column('encoding', sa.String(20), default='utf-8'),
        sa.Column('linha_cabecalho', sa.Integer(), default=1),
        sa.Column('pular_linhas', sa.Integer(), default=0),
        
        # Mapeamento de colunas (JSON)
        # {
        #   "data": {"coluna": "A", "formato": "DD/MM/YYYY"},
        #   "receita": {"coluna": "B", "tipo": "moeda"},
        #   "custos": {"coluna": "C", "tipo": "moeda"},
        #   ...
        # }
        sa.Column('colunas_json', sa.Text(), nullable=False),
        
        # Transformações (JSON)
        # [
        #   {"campo": "receita", "operacao": "multiplicar", "valor": 100},
        #   {"campo": "data", "operacao": "formato", "de": "MM/DD/YYYY", "para": "YYYY-MM-DD"}
        # ]
        sa.Column('transformacoes_json', sa.Text(), nullable=True),
        
        # Flags
        sa.Column('is_padrao', sa.Boolean(), default=False),
        sa.Column('ativo', sa.Boolean(), default=True),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.ForeignKeyConstraint(['organizacao_id'], ['organizacoes.id']),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id']),
        sa.ForeignKeyConstraint(['contador_id'], ['contadores.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mapeamentos_org', 'mapeamentos_importacao', ['organizacao_id'])
    op.create_index('idx_mapeamentos_empresa', 'mapeamentos_importacao', ['empresa_id'])
    
    # Tabela de registros importados (para rastreabilidade)
    op.create_table(
        'registros_importados',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('importacao_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('dados_mensal_id', sa.Integer(), nullable=True),
        
        # Dados originais
        sa.Column('linha_arquivo', sa.Integer(), nullable=True),
        sa.Column('dados_originais_json', sa.Text(), nullable=True),
        
        # Hash para detectar duplicatas
        sa.Column('hash_registro', sa.String(64), nullable=True),  # Hash dos dados para detectar duplicata
        
        # Status
        sa.Column('status', sa.String(20), default='imported'),  # imported, duplicate, error
        sa.Column('mensagem_erro', sa.String(500), nullable=True),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.ForeignKeyConstraint(['importacao_id'], ['importacoes.id']),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id']),
        sa.ForeignKeyConstraint(['dados_mensal_id'], ['dados_mensais.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_registros_import', 'registros_importados', ['importacao_id'])
    op.create_index('idx_registros_hash', 'registros_importados', ['hash_registro'])
    
    # Adicionar referência de importação na tabela dados_mensais
    op.add_column('dados_mensais', sa.Column('importacao_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_dados_importacao', 'dados_mensais', 'importacoes', ['importacao_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_dados_importacao', 'dados_mensais', type_='foreignkey')
    op.drop_column('dados_mensais', 'importacao_id')
    op.drop_table('registros_importados')
    op.drop_table('mapeamentos_importacao')
    op.drop_table('importacoes')
