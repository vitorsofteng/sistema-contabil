"""Multi-tenancy and permissions tables

Revision ID: 002_multi_tenancy
Revises: 001_initial
Create Date: 2025-01-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_multi_tenancy'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabela de organizações (escritórios contábeis)
    op.create_table(
        'organizacoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('cnpj', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('telefone', sa.String(50), nullable=True),
        sa.Column('endereco', sa.String(500), nullable=True),
        sa.Column('cidade', sa.String(100), nullable=True),
        sa.Column('estado', sa.String(2), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('cor_primaria', sa.String(7), default='#3B82F6'),
        sa.Column('plano', sa.String(50), default='free'),
        sa.Column('max_usuarios', sa.Integer(), default=1),
        sa.Column('max_empresas', sa.Integer(), default=5),
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_organizacoes_slug', 'organizacoes', ['slug'], unique=True)
    
    # Tabela de papéis
    op.create_table(
        'papeis',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(50), nullable=False),
        sa.Column('descricao', sa.String(255), nullable=True),
        sa.Column('nivel', sa.Integer(), default=0),  # 0=cliente, 10=assistente, 20=contador, 30=admin, 99=owner
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Papéis padrão do sistema
    op.execute("""
        INSERT INTO papeis (nome, descricao, nivel, is_system) VALUES 
        ('owner', 'Proprietário da organização', 99, true),
        ('admin', 'Administrador com acesso total', 30, true),
        ('contador', 'Contador com acesso às empresas', 20, true),
        ('assistente', 'Assistente com acesso limitado', 10, true),
        ('cliente', 'Cliente visualiza apenas sua empresa', 0, true)
    """)
    
    # Tabela de membros da organização
    op.create_table(
        'membros_organizacao',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organizacao_id', sa.Integer(), nullable=False),
        sa.Column('contador_id', sa.Integer(), nullable=False),
        sa.Column('papel_id', sa.Integer(), nullable=False),
        sa.Column('is_default', sa.Boolean(), default=False),  # Organização padrão do usuário
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['organizacao_id'], ['organizacoes.id']),
        sa.ForeignKeyConstraint(['contador_id'], ['contadores.id']),
        sa.ForeignKeyConstraint(['papel_id'], ['papeis.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organizacao_id', 'contador_id', name='uq_membro_org_contador')
    )
    op.create_index('idx_membros_org', 'membros_organizacao', ['organizacao_id'])
    op.create_index('idx_membros_contador', 'membros_organizacao', ['contador_id'])
    
    # Tabela de permissões por papel
    op.create_table(
        'permissoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('papel_id', sa.Integer(), nullable=False),
        sa.Column('recurso', sa.String(50), nullable=False),  # empresas, dados, analises, usuarios, etc
        sa.Column('acao', sa.String(20), nullable=False),  # create, read, update, delete
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['papel_id'], ['papeis.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('papel_id', 'recurso', 'acao', name='uq_permissao')
    )
    
    # Permissões padrão
    op.execute("""
        INSERT INTO permissoes (papel_id, recurso, acao) VALUES 
        -- Owner (tudo)
        (1, 'organizacao', 'create'), (1, 'organizacao', 'read'), (1, 'organizacao', 'update'), (1, 'organizacao', 'delete'),
        (1, 'usuarios', 'create'), (1, 'usuarios', 'read'), (1, 'usuarios', 'update'), (1, 'usuarios', 'delete'),
        (1, 'empresas', 'create'), (1, 'empresas', 'read'), (1, 'empresas', 'update'), (1, 'empresas', 'delete'),
        (1, 'dados', 'create'), (1, 'dados', 'read'), (1, 'dados', 'update'), (1, 'dados', 'delete'),
        (1, 'analises', 'create'), (1, 'analises', 'read'), (1, 'analises', 'update'), (1, 'analises', 'delete'),
        (1, 'relatorios', 'create'), (1, 'relatorios', 'read'),
        (1, 'convites', 'create'), (1, 'convites', 'read'), (1, 'convites', 'delete'),
        (1, 'audit', 'read'),
        -- Admin (quase tudo, exceto deletar org)
        (2, 'organizacao', 'read'), (2, 'organizacao', 'update'),
        (2, 'usuarios', 'create'), (2, 'usuarios', 'read'), (2, 'usuarios', 'update'), (2, 'usuarios', 'delete'),
        (2, 'empresas', 'create'), (2, 'empresas', 'read'), (2, 'empresas', 'update'), (2, 'empresas', 'delete'),
        (2, 'dados', 'create'), (2, 'dados', 'read'), (2, 'dados', 'update'), (2, 'dados', 'delete'),
        (2, 'analises', 'create'), (2, 'analises', 'read'), (2, 'analises', 'update'), (2, 'analises', 'delete'),
        (2, 'relatorios', 'create'), (2, 'relatorios', 'read'),
        (2, 'convites', 'create'), (2, 'convites', 'read'), (2, 'convites', 'delete'),
        (2, 'audit', 'read'),
        -- Contador (empresas e dados)
        (3, 'organizacao', 'read'),
        (3, 'empresas', 'create'), (3, 'empresas', 'read'), (3, 'empresas', 'update'),
        (3, 'dados', 'create'), (3, 'dados', 'read'), (3, 'dados', 'update'), (3, 'dados', 'delete'),
        (3, 'analises', 'create'), (3, 'analises', 'read'),
        (3, 'relatorios', 'create'), (3, 'relatorios', 'read'),
        -- Assistente (leitura + dados)
        (4, 'organizacao', 'read'),
        (4, 'empresas', 'read'),
        (4, 'dados', 'create'), (4, 'dados', 'read'), (4, 'dados', 'update'),
        (4, 'analises', 'read'),
        (4, 'relatorios', 'read'),
        -- Cliente (só leitura da própria empresa)
        (5, 'empresas', 'read'),
        (5, 'dados', 'read'),
        (5, 'analises', 'read'),
        (5, 'relatorios', 'read')
    """)
    
    # Tabela de convites
    op.create_table(
        'convites',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organizacao_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('papel_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(100), unique=True, nullable=False),
        sa.Column('convidado_por', sa.Integer(), nullable=False),
        sa.Column('mensagem', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='pendente'),  # pendente, aceito, expirado, cancelado
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organizacao_id'], ['organizacoes.id']),
        sa.ForeignKeyConstraint(['papel_id'], ['papeis.id']),
        sa.ForeignKeyConstraint(['convidado_por'], ['contadores.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_convites_token', 'convites', ['token'], unique=True)
    op.create_index('idx_convites_email', 'convites', ['email'])
    op.create_index('idx_convites_org', 'convites', ['organizacao_id'])
    
    # Tabela de audit log
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organizacao_id', sa.Integer(), nullable=True),
        sa.Column('contador_id', sa.Integer(), nullable=True),
        sa.Column('acao', sa.String(50), nullable=False),  # create, update, delete, login, logout, etc
        sa.Column('recurso', sa.String(50), nullable=False),  # empresa, dados, analise, usuario, etc
        sa.Column('recurso_id', sa.Integer(), nullable=True),
        sa.Column('detalhes', sa.Text(), nullable=True),  # JSON com detalhes
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organizacao_id'], ['organizacoes.id']),
        sa.ForeignKeyConstraint(['contador_id'], ['contadores.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_org', 'audit_logs', ['organizacao_id'])
    op.create_index('idx_audit_contador', 'audit_logs', ['contador_id'])
    op.create_index('idx_audit_acao', 'audit_logs', ['acao'])
    op.create_index('idx_audit_recurso', 'audit_logs', ['recurso', 'recurso_id'])
    op.create_index('idx_audit_created', 'audit_logs', ['created_at'])
    
    # Adicionar organizacao_id na tabela empresas
    op.add_column('empresas', sa.Column('organizacao_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_empresas_org', 'empresas', 'organizacoes', ['organizacao_id'], ['id'])
    op.create_index('idx_empresas_org', 'empresas', ['organizacao_id'])


def downgrade() -> None:
    op.drop_index('idx_empresas_org', 'empresas')
    op.drop_constraint('fk_empresas_org', 'empresas', type_='foreignkey')
    op.drop_column('empresas', 'organizacao_id')
    
    op.drop_table('audit_logs')
    op.drop_table('convites')
    op.drop_table('permissoes')
    op.drop_table('membros_organizacao')
    op.drop_table('papeis')
    op.drop_table('organizacoes')
