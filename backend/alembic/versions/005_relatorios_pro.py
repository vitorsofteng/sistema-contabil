"""F09: Relatórios Pro - Configurações e Links Compartilháveis

Revision ID: 005
Revises: 004
Create Date: 2025-01-25

"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Configurações de relatório por organização (white-label)
    op.create_table(
        'configuracoes_relatorio',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('organizacao_id', sa.Integer(), sa.ForeignKey('organizacoes.id'), nullable=True),
        sa.Column('contador_id', sa.Integer(), sa.ForeignKey('contadores.id'), nullable=False),
        
        # White-label
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('logo_base64', sa.Text(), nullable=True),
        sa.Column('nome_escritorio', sa.String(255), nullable=True),
        sa.Column('slogan', sa.String(255), nullable=True),
        sa.Column('endereco', sa.String(500), nullable=True),
        sa.Column('telefone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        
        # Cores personalizadas
        sa.Column('cor_primaria', sa.String(7), default='#1e40af'),
        sa.Column('cor_secundaria', sa.String(7), default='#3b82f6'),
        sa.Column('cor_destaque', sa.String(7), default='#059669'),
        
        # Configurações de conteúdo
        sa.Column('mostrar_logo', sa.Boolean(), default=True),
        sa.Column('mostrar_graficos', sa.Boolean(), default=True),
        sa.Column('mostrar_recomendacoes', sa.Boolean(), default=True),
        sa.Column('mostrar_benchmarks', sa.Boolean(), default=False),
        sa.Column('template_padrao', sa.String(50), default='executivo'),
        
        # Rodapé personalizado
        sa.Column('texto_rodape', sa.Text(), nullable=True),
        sa.Column('disclaimer', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.Index('idx_config_rel_org', 'organizacao_id'),
        sa.Index('idx_config_rel_contador', 'contador_id'),
    )
    
    # Templates de relatório
    op.create_table(
        'templates_relatorio',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('tipo', sa.String(50), nullable=False),  # executivo, detalhado, resumido, comparativo
        sa.Column('configuracao_json', sa.Text(), nullable=True),  # Configurações específicas do template
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('is_system', sa.Boolean(), default=True),  # Template do sistema vs customizado
        sa.Column('organizacao_id', sa.Integer(), sa.ForeignKey('organizacoes.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    # Links compartilháveis
    op.create_table(
        'links_compartilhados',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('token', sa.String(64), unique=True, nullable=False),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id'), nullable=False),
        sa.Column('contador_id', sa.Integer(), sa.ForeignKey('contadores.id'), nullable=False),
        sa.Column('analise_id', sa.Integer(), sa.ForeignKey('analises.id'), nullable=True),
        
        # Configurações do link
        sa.Column('tipo_relatorio', sa.String(50), default='pdf'),  # pdf, excel, dashboard
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('templates_relatorio.id'), nullable=True),
        sa.Column('permite_download', sa.Boolean(), default=True),
        sa.Column('requer_senha', sa.Boolean(), default=False),
        sa.Column('senha_hash', sa.String(255), nullable=True),
        
        # Validade
        sa.Column('expira_em', sa.DateTime(), nullable=True),
        sa.Column('max_acessos', sa.Integer(), nullable=True),
        sa.Column('acessos', sa.Integer(), default=0),
        
        # Tracking
        sa.Column('ultimo_acesso', sa.DateTime(), nullable=True),
        sa.Column('ativo', sa.Boolean(), default=True),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.Index('idx_link_token', 'token'),
        sa.Index('idx_link_empresa', 'empresa_id'),
    )
    
    # Histórico de relatórios gerados
    op.create_table(
        'historico_relatorios',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id'), nullable=False),
        sa.Column('contador_id', sa.Integer(), sa.ForeignKey('contadores.id'), nullable=False),
        sa.Column('analise_id', sa.Integer(), sa.ForeignKey('analises.id'), nullable=True),
        
        sa.Column('tipo', sa.String(20), nullable=False),  # pdf, excel, pptx
        sa.Column('template', sa.String(50), nullable=True),
        sa.Column('periodo_inicio', sa.String(10), nullable=True),
        sa.Column('periodo_fim', sa.String(10), nullable=True),
        
        # Arquivo gerado
        sa.Column('arquivo_nome', sa.String(255), nullable=True),
        sa.Column('arquivo_tamanho', sa.Integer(), nullable=True),
        sa.Column('arquivo_url', sa.String(500), nullable=True),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.Index('idx_hist_rel_empresa', 'empresa_id'),
        sa.Index('idx_hist_rel_contador', 'contador_id'),
    )
    
    # Agendamentos de relatório
    op.create_table(
        'agendamentos_relatorio',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id'), nullable=False),
        sa.Column('contador_id', sa.Integer(), sa.ForeignKey('contadores.id'), nullable=False),
        
        sa.Column('frequencia', sa.String(20), nullable=False),  # mensal, semanal, diario
        sa.Column('dia_execucao', sa.Integer(), nullable=True),  # dia do mês ou da semana
        sa.Column('hora_execucao', sa.Integer(), default=8),  # hora do dia
        
        sa.Column('tipo_relatorio', sa.String(20), default='pdf'),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('templates_relatorio.id'), nullable=True),
        
        # Destinatários
        sa.Column('emails_destino', sa.Text(), nullable=True),  # JSON array de emails
        sa.Column('enviar_cliente', sa.Boolean(), default=False),
        
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.Column('ultima_execucao', sa.DateTime(), nullable=True),
        sa.Column('proxima_execucao', sa.DateTime(), nullable=True),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.Index('idx_agend_empresa', 'empresa_id'),
    )
    
    # Inserir templates padrão do sistema
    op.execute("""
        INSERT INTO templates_relatorio (nome, descricao, tipo, is_default, is_system, configuracao_json) VALUES
        ('Executivo', 'Relatório resumido para apresentação executiva', 'executivo', true, true, 
         '{"paginas": ["capa", "resumo", "graficos", "recomendacoes"], "graficos": true, "tabelas_detalhadas": false}'),
        ('Detalhado', 'Relatório completo com todas as análises', 'detalhado', false, true,
         '{"paginas": ["capa", "resumo", "indicadores", "graficos", "evolucao", "benchmarks", "recomendacoes", "anexos"], "graficos": true, "tabelas_detalhadas": true}'),
        ('Resumido', 'Relatório de uma página com principais indicadores', 'resumido', false, true,
         '{"paginas": ["resumo_compacto"], "graficos": true, "tabelas_detalhadas": false}'),
        ('Comparativo', 'Relatório comparando períodos diferentes', 'comparativo', false, true,
         '{"paginas": ["capa", "comparativo", "evolucao", "graficos"], "graficos": true, "tabelas_detalhadas": true}')
    """)


def downgrade():
    op.drop_table('agendamentos_relatorio')
    op.drop_table('historico_relatorios')
    op.drop_table('links_compartilhados')
    op.drop_table('templates_relatorio')
    op.drop_table('configuracoes_relatorio')
