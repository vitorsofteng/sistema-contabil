"""006 - Alertas Inteligentes

Revision ID: 006
Revises: 005
Create Date: 2024-01-25

Sistema de alertas automáticos para contadores.
"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Configurações de alertas por empresa
    op.create_table(
        'configuracoes_alerta',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contador_id', sa.Integer(), sa.ForeignKey('contadores.id', ondelete='CASCADE'), nullable=False),
        
        # Alertas de Caixa
        sa.Column('alerta_caixa_ativo', sa.Boolean(), default=True),
        sa.Column('caixa_dias_critico', sa.Integer(), default=30),  # Alerta se runway < X dias
        sa.Column('caixa_dias_atencao', sa.Integer(), default=60),
        
        # Alertas de Margem
        sa.Column('alerta_margem_ativo', sa.Boolean(), default=True),
        sa.Column('margem_minima', sa.Float(), default=5.0),  # Alerta se margem < X%
        sa.Column('margem_queda_pct', sa.Float(), default=20.0),  # Alerta se margem caiu X% vs período anterior
        
        # Alertas de Tendência
        sa.Column('alerta_tendencia_ativo', sa.Boolean(), default=True),
        sa.Column('tendencia_meses_negativos', sa.Integer(), default=3),  # Alerta se X meses consecutivos negativos
        sa.Column('queda_faturamento_pct', sa.Float(), default=15.0),  # Alerta se faturamento caiu X%
        
        # Alertas de Anomalias
        sa.Column('alerta_anomalias_ativo', sa.Boolean(), default=True),
        sa.Column('anomalia_desvio_padrao', sa.Float(), default=2.0),  # Alerta se valor > X desvios padrão
        
        # Alertas de Score
        sa.Column('alerta_score_ativo', sa.Boolean(), default=True),
        sa.Column('score_critico', sa.Integer(), default=40),  # Alerta se score < X
        sa.Column('score_queda_pontos', sa.Integer(), default=15),  # Alerta se score caiu X pontos
        
        # Notificações
        sa.Column('notificar_email', sa.Boolean(), default=False),
        sa.Column('notificar_dashboard', sa.Boolean(), default=True),
        sa.Column('frequencia_email', sa.String(20), default='semanal'),  # diario, semanal, mensal
        sa.Column('email_destino', sa.String(255), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.UniqueConstraint('empresa_id', 'contador_id', name='uq_config_alerta_empresa_contador')
    )
    
    # Alertas gerados
    op.create_table(
        'alertas',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contador_id', sa.Integer(), sa.ForeignKey('contadores.id', ondelete='CASCADE'), nullable=False),
        
        # Tipo e severidade
        sa.Column('tipo', sa.String(50), nullable=False),  # caixa_critico, margem_baixa, tendencia_negativa, anomalia, score_baixo
        sa.Column('severidade', sa.String(20), nullable=False),  # critico, atencao, info
        sa.Column('codigo', sa.String(50), nullable=False),  # Código único do tipo de alerta
        
        # Conteúdo
        sa.Column('titulo', sa.String(255), nullable=False),
        sa.Column('mensagem', sa.Text(), nullable=False),
        sa.Column('valor_atual', sa.Float(), nullable=True),  # Valor que disparou o alerta
        sa.Column('valor_limite', sa.Float(), nullable=True),  # Limite configurado
        sa.Column('valor_anterior', sa.Float(), nullable=True),  # Valor anterior (para comparação)
        
        # Dados adicionais
        sa.Column('dados_json', sa.Text(), nullable=True),  # Dados extras em JSON
        sa.Column('periodo_referencia', sa.String(20), nullable=True),  # Ex: "01/2024"
        
        # Status
        sa.Column('lido', sa.Boolean(), default=False),
        sa.Column('lido_em', sa.DateTime(), nullable=True),
        sa.Column('resolvido', sa.Boolean(), default=False),
        sa.Column('resolvido_em', sa.DateTime(), nullable=True),
        sa.Column('resolvido_por', sa.Integer(), sa.ForeignKey('contadores.id'), nullable=True),
        sa.Column('resolucao_nota', sa.Text(), nullable=True),
        
        # Notificação
        sa.Column('notificado_email', sa.Boolean(), default=False),
        sa.Column('notificado_email_em', sa.DateTime(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Índices para alertas
    op.create_index('ix_alertas_contador_id', 'alertas', ['contador_id'])
    op.create_index('ix_alertas_empresa_id', 'alertas', ['empresa_id'])
    op.create_index('ix_alertas_tipo', 'alertas', ['tipo'])
    op.create_index('ix_alertas_severidade', 'alertas', ['severidade'])
    op.create_index('ix_alertas_lido', 'alertas', ['lido'])
    op.create_index('ix_alertas_resolvido', 'alertas', ['resolvido'])
    op.create_index('ix_alertas_created_at', 'alertas', ['created_at'])
    
    # Histórico de alertas (para não gerar duplicados)
    op.create_table(
        'alertas_historico',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('codigo', sa.String(50), nullable=False),
        sa.Column('periodo_referencia', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.UniqueConstraint('empresa_id', 'codigo', 'periodo_referencia', name='uq_alerta_hist_empresa_codigo_periodo')
    )
    
    # Configuração global de alertas do contador
    op.create_table(
        'configuracoes_alerta_global',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('contador_id', sa.Integer(), sa.ForeignKey('contadores.id', ondelete='CASCADE'), nullable=False, unique=True),
        
        # Horário preferido para notificações
        sa.Column('horario_notificacao', sa.String(5), default='09:00'),
        sa.Column('dias_notificacao', sa.String(50), default='1,2,3,4,5'),  # 1=seg, 7=dom
        
        # Resumo
        sa.Column('enviar_resumo_semanal', sa.Boolean(), default=True),
        sa.Column('dia_resumo_semanal', sa.Integer(), default=1),  # 1=segunda
        
        # Limites
        sa.Column('max_alertas_email_dia', sa.Integer(), default=10),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade():
    op.drop_table('configuracoes_alerta_global')
    op.drop_table('alertas_historico')
    op.drop_index('ix_alertas_created_at', 'alertas')
    op.drop_index('ix_alertas_resolvido', 'alertas')
    op.drop_index('ix_alertas_lido', 'alertas')
    op.drop_index('ix_alertas_severidade', 'alertas')
    op.drop_index('ix_alertas_tipo', 'alertas')
    op.drop_index('ix_alertas_empresa_id', 'alertas')
    op.drop_index('ix_alertas_contador_id', 'alertas')
    op.drop_table('alertas')
    op.drop_table('configuracoes_alerta')
