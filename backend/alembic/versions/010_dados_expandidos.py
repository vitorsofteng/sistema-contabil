"""
Migration 010 - Dados Mensais Expandidos
Sistema Contábil Profissional

Expande a tabela de dados mensais para incluir TODOS os campos
extraídos dos balancetes reais.
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


revision = '010_dados_expandidos'
down_revision = '009_security_advanced'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # TABELA: dados_mensais_completos
    # Armazena TODOS os dados financeiros mensais extraídos dos balancetes
    # =========================================================================
    op.create_table(
        'dados_mensais_completos',
        # Identificação
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('competencia', sa.String(7), nullable=False),  # AAAA-MM
        sa.Column('periodo_inicio', sa.Date()),
        sa.Column('periodo_fim', sa.Date()),
        
        # =====================================================================
        # BALANÇO PATRIMONIAL - ATIVO
        # =====================================================================
        sa.Column('ativo_total', sa.Numeric(15, 2), default=0),
        sa.Column('ativo_circulante', sa.Numeric(15, 2), default=0),
        sa.Column('disponivel', sa.Numeric(15, 2), default=0),
        sa.Column('caixa', sa.Numeric(15, 2), default=0),
        sa.Column('bancos', sa.Numeric(15, 2), default=0),
        sa.Column('aplicacoes_financeiras', sa.Numeric(15, 2), default=0),
        sa.Column('clientes', sa.Numeric(15, 2), default=0),
        sa.Column('duplicatas_receber', sa.Numeric(15, 2), default=0),
        sa.Column('estoques', sa.Numeric(15, 2), default=0),
        sa.Column('adiantamentos', sa.Numeric(15, 2), default=0),
        sa.Column('impostos_recuperar', sa.Numeric(15, 2), default=0),
        sa.Column('outros_creditos', sa.Numeric(15, 2), default=0),
        
        sa.Column('ativo_nao_circulante', sa.Numeric(15, 2), default=0),
        sa.Column('realizavel_longo_prazo', sa.Numeric(15, 2), default=0),
        sa.Column('investimentos', sa.Numeric(15, 2), default=0),
        sa.Column('imobilizado', sa.Numeric(15, 2), default=0),
        sa.Column('intangivel', sa.Numeric(15, 2), default=0),
        sa.Column('depreciacao_acumulada', sa.Numeric(15, 2), default=0),
        
        # =====================================================================
        # BALANÇO PATRIMONIAL - PASSIVO
        # =====================================================================
        sa.Column('passivo_total', sa.Numeric(15, 2), default=0),
        sa.Column('passivo_circulante', sa.Numeric(15, 2), default=0),
        sa.Column('fornecedores', sa.Numeric(15, 2), default=0),
        sa.Column('emprestimos_cp', sa.Numeric(15, 2), default=0),
        sa.Column('financiamentos_cp', sa.Numeric(15, 2), default=0),
        sa.Column('obrigacoes_trabalhistas', sa.Numeric(15, 2), default=0),
        sa.Column('salarios_pagar', sa.Numeric(15, 2), default=0),
        sa.Column('ferias_pagar', sa.Numeric(15, 2), default=0),
        sa.Column('decimo_terceiro_pagar', sa.Numeric(15, 2), default=0),
        sa.Column('fgts_recolher', sa.Numeric(15, 2), default=0),
        sa.Column('inss_recolher', sa.Numeric(15, 2), default=0),
        sa.Column('obrigacoes_tributarias', sa.Numeric(15, 2), default=0),
        sa.Column('iss_recolher', sa.Numeric(15, 2), default=0),
        sa.Column('pis_recolher', sa.Numeric(15, 2), default=0),
        sa.Column('cofins_recolher', sa.Numeric(15, 2), default=0),
        sa.Column('irpj_recolher', sa.Numeric(15, 2), default=0),
        sa.Column('csll_recolher', sa.Numeric(15, 2), default=0),
        sa.Column('icms_recolher', sa.Numeric(15, 2), default=0),
        sa.Column('dividendos_pagar', sa.Numeric(15, 2), default=0),
        sa.Column('adiantamentos_clientes', sa.Numeric(15, 2), default=0),
        sa.Column('provisoes_cp', sa.Numeric(15, 2), default=0),
        
        sa.Column('passivo_nao_circulante', sa.Numeric(15, 2), default=0),
        sa.Column('emprestimos_lp', sa.Numeric(15, 2), default=0),
        sa.Column('financiamentos_lp', sa.Numeric(15, 2), default=0),
        sa.Column('provisoes_lp', sa.Numeric(15, 2), default=0),
        
        # =====================================================================
        # PATRIMÔNIO LÍQUIDO
        # =====================================================================
        sa.Column('patrimonio_liquido', sa.Numeric(15, 2), default=0),
        sa.Column('capital_social', sa.Numeric(15, 2), default=0),
        sa.Column('capital_subscrito', sa.Numeric(15, 2), default=0),
        sa.Column('capital_integralizar', sa.Numeric(15, 2), default=0),
        sa.Column('reservas_capital', sa.Numeric(15, 2), default=0),
        sa.Column('reservas_lucros', sa.Numeric(15, 2), default=0),
        sa.Column('reserva_legal', sa.Numeric(15, 2), default=0),
        sa.Column('lucros_acumulados', sa.Numeric(15, 2), default=0),
        sa.Column('prejuizos_acumulados', sa.Numeric(15, 2), default=0),
        sa.Column('lucro_exercicio', sa.Numeric(15, 2), default=0),
        sa.Column('ajustes_avaliacao', sa.Numeric(15, 2), default=0),
        
        # =====================================================================
        # DRE - RECEITAS
        # =====================================================================
        sa.Column('receita_bruta', sa.Numeric(15, 2), default=0),
        sa.Column('receita_vendas', sa.Numeric(15, 2), default=0),
        sa.Column('receita_servicos', sa.Numeric(15, 2), default=0),
        sa.Column('outras_receitas_operacionais', sa.Numeric(15, 2), default=0),
        
        # =====================================================================
        # DRE - DEDUÇÕES
        # =====================================================================
        sa.Column('deducoes_receita', sa.Numeric(15, 2), default=0),
        sa.Column('devolucoes', sa.Numeric(15, 2), default=0),
        sa.Column('abatimentos', sa.Numeric(15, 2), default=0),
        sa.Column('descontos_incondicionais', sa.Numeric(15, 2), default=0),
        sa.Column('impostos_sobre_vendas', sa.Numeric(15, 2), default=0),
        sa.Column('iss_deducao', sa.Numeric(15, 2), default=0),
        sa.Column('pis_deducao', sa.Numeric(15, 2), default=0),
        sa.Column('cofins_deducao', sa.Numeric(15, 2), default=0),
        sa.Column('icms_deducao', sa.Numeric(15, 2), default=0),
        sa.Column('irpj_deducao', sa.Numeric(15, 2), default=0),
        sa.Column('csll_deducao', sa.Numeric(15, 2), default=0),
        
        sa.Column('receita_liquida', sa.Numeric(15, 2), default=0),
        
        # =====================================================================
        # DRE - CUSTOS
        # =====================================================================
        sa.Column('custos_total', sa.Numeric(15, 2), default=0),
        sa.Column('cmv', sa.Numeric(15, 2), default=0),  # Custo Mercadorias Vendidas
        sa.Column('cpv', sa.Numeric(15, 2), default=0),  # Custo Produtos Vendidos
        sa.Column('csp', sa.Numeric(15, 2), default=0),  # Custo Serviços Prestados
        
        sa.Column('lucro_bruto', sa.Numeric(15, 2), default=0),
        
        # =====================================================================
        # DRE - DESPESAS OPERACIONAIS
        # =====================================================================
        sa.Column('despesas_operacionais', sa.Numeric(15, 2), default=0),
        sa.Column('despesas_administrativas', sa.Numeric(15, 2), default=0),
        sa.Column('despesas_pessoal', sa.Numeric(15, 2), default=0),
        sa.Column('folha_pagamento', sa.Numeric(15, 2), default=0),
        sa.Column('encargos_sociais', sa.Numeric(15, 2), default=0),
        sa.Column('beneficios', sa.Numeric(15, 2), default=0),
        sa.Column('despesas_comerciais', sa.Numeric(15, 2), default=0),
        sa.Column('despesas_marketing', sa.Numeric(15, 2), default=0),
        sa.Column('despesas_gerais', sa.Numeric(15, 2), default=0),
        sa.Column('alugueis', sa.Numeric(15, 2), default=0),
        sa.Column('energia_agua', sa.Numeric(15, 2), default=0),
        sa.Column('telefone_internet', sa.Numeric(15, 2), default=0),
        sa.Column('honorarios_contabeis', sa.Numeric(15, 2), default=0),
        sa.Column('honorarios_advocaticios', sa.Numeric(15, 2), default=0),
        sa.Column('depreciacao_amortizacao', sa.Numeric(15, 2), default=0),
        sa.Column('outras_despesas_operacionais', sa.Numeric(15, 2), default=0),
        
        # =====================================================================
        # DRE - RESULTADO FINANCEIRO
        # =====================================================================
        sa.Column('resultado_financeiro', sa.Numeric(15, 2), default=0),
        sa.Column('receitas_financeiras', sa.Numeric(15, 2), default=0),
        sa.Column('rendimentos_aplicacoes', sa.Numeric(15, 2), default=0),
        sa.Column('juros_ativos', sa.Numeric(15, 2), default=0),
        sa.Column('descontos_obtidos', sa.Numeric(15, 2), default=0),
        sa.Column('despesas_financeiras', sa.Numeric(15, 2), default=0),
        sa.Column('juros_passivos', sa.Numeric(15, 2), default=0),
        sa.Column('tarifas_bancarias', sa.Numeric(15, 2), default=0),
        sa.Column('descontos_concedidos', sa.Numeric(15, 2), default=0),
        sa.Column('variacao_cambial', sa.Numeric(15, 2), default=0),
        
        # =====================================================================
        # DRE - OUTRAS RECEITAS/DESPESAS
        # =====================================================================
        sa.Column('outras_receitas', sa.Numeric(15, 2), default=0),
        sa.Column('outras_despesas', sa.Numeric(15, 2), default=0),
        sa.Column('resultado_nao_operacional', sa.Numeric(15, 2), default=0),
        
        # =====================================================================
        # DRE - RESULTADO
        # =====================================================================
        sa.Column('resultado_antes_impostos', sa.Numeric(15, 2), default=0),
        sa.Column('irpj_devido', sa.Numeric(15, 2), default=0),
        sa.Column('csll_devido', sa.Numeric(15, 2), default=0),
        sa.Column('lucro_liquido', sa.Numeric(15, 2), default=0),
        
        # =====================================================================
        # INDICADORES CALCULADOS
        # =====================================================================
        sa.Column('margem_bruta', sa.Numeric(8, 2), default=0),
        sa.Column('margem_operacional', sa.Numeric(8, 2), default=0),
        sa.Column('margem_liquida', sa.Numeric(8, 2), default=0),
        sa.Column('margem_ebitda', sa.Numeric(8, 2), default=0),
        sa.Column('roe', sa.Numeric(10, 2), default=0),
        sa.Column('roa', sa.Numeric(8, 2), default=0),
        sa.Column('roic', sa.Numeric(8, 2), default=0),
        sa.Column('liquidez_corrente', sa.Numeric(8, 2), default=0),
        sa.Column('liquidez_seca', sa.Numeric(8, 2), default=0),
        sa.Column('liquidez_imediata', sa.Numeric(8, 4), default=0),
        sa.Column('liquidez_geral', sa.Numeric(8, 2), default=0),
        sa.Column('endividamento_geral', sa.Numeric(8, 2), default=0),
        sa.Column('endividamento_cp', sa.Numeric(8, 2), default=0),
        sa.Column('composicao_endividamento', sa.Numeric(8, 2), default=0),
        sa.Column('imobilizacao_pl', sa.Numeric(8, 2), default=0),
        sa.Column('carga_tributaria', sa.Numeric(8, 2), default=0),
        sa.Column('giro_ativo', sa.Numeric(8, 2), default=0),
        sa.Column('pme', sa.Numeric(8, 2), default=0),  # Prazo Médio Estocagem
        sa.Column('pmr', sa.Numeric(8, 2), default=0),  # Prazo Médio Recebimento
        sa.Column('pmp', sa.Numeric(8, 2), default=0),  # Prazo Médio Pagamento
        sa.Column('ciclo_financeiro', sa.Numeric(8, 2), default=0),
        sa.Column('ebitda', sa.Numeric(15, 2), default=0),
        sa.Column('nopat', sa.Numeric(15, 2), default=0),
        
        # =====================================================================
        # METADADOS
        # =====================================================================
        sa.Column('arquivo_origem', sa.String(255)),
        sa.Column('hash_arquivo', sa.String(64)),
        sa.Column('importado_em', sa.DateTime(), default=datetime.utcnow),
        sa.Column('importado_por', sa.Integer(), sa.ForeignKey('contadores.id')),
        sa.Column('observacoes', sa.Text()),
        
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        
        # Índices
        sa.Index('idx_dados_completos_empresa_comp', 'empresa_id', 'competencia'),
        sa.UniqueConstraint('empresa_id', 'competencia', name='uq_dados_completos_empresa_competencia')
    )
    
    # =========================================================================
    # TABELA: clientes_empresa
    # Clientes identificados nos balancetes
    # =========================================================================
    op.create_table(
        'clientes_empresa',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('cnpj_cpf', sa.String(20)),
        sa.Column('valor_total', sa.Numeric(15, 2), default=0),
        sa.Column('ultima_movimentacao', sa.Date()),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        
        sa.Index('idx_clientes_empresa', 'empresa_id')
    )
    
    # =========================================================================
    # TABELA: fornecedores_empresa
    # Fornecedores identificados nos balancetes
    # =========================================================================
    op.create_table(
        'fornecedores_empresa',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('cnpj_cpf', sa.String(20)),
        sa.Column('valor_total', sa.Numeric(15, 2), default=0),
        sa.Column('ultima_movimentacao', sa.Date()),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        
        sa.Index('idx_fornecedores_empresa', 'empresa_id')
    )
    
    # =========================================================================
    # TABELA: socios_empresa
    # Sócios identificados nos balancetes
    # =========================================================================
    op.create_table(
        'socios_empresa',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('cpf', sa.String(14)),
        sa.Column('valor_capital', sa.Numeric(15, 2), default=0),
        sa.Column('percentual', sa.Numeric(5, 2), default=0),
        sa.Column('data_entrada', sa.Date()),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        
        sa.Index('idx_socios_empresa', 'empresa_id')
    )
    
    # =========================================================================
    # ATUALIZAR TABELA empresas
    # Adicionar campos do contador e sistema
    # =========================================================================
    op.add_column('empresas', sa.Column('contador_nome', sa.String(255)))
    op.add_column('empresas', sa.Column('contador_crc', sa.String(20)))
    op.add_column('empresas', sa.Column('contador_cpf', sa.String(14)))
    op.add_column('empresas', sa.Column('sistema_contabil', sa.String(255)))
    

def downgrade():
    op.drop_column('empresas', 'sistema_contabil')
    op.drop_column('empresas', 'contador_cpf')
    op.drop_column('empresas', 'contador_crc')
    op.drop_column('empresas', 'contador_nome')
    
    op.drop_table('socios_empresa')
    op.drop_table('fornecedores_empresa')
    op.drop_table('clientes_empresa')
    op.drop_table('dados_mensais_completos')
