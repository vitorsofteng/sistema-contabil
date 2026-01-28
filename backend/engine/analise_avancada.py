#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise Financeira Avançada - F12
==================================

Módulo completo para análise financeira com:
- DRE automático
- Índices financeiros 
- Ponto de equilíbrio (Break-even)
- Projeções em 3 cenários
- Benchmarks por setor
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
import statistics
import json


# =============================================================================
# BENCHMARKS POR SETOR (dados de mercado)
# =============================================================================

BENCHMARKS = {
    "comercio_varejo": {
        "nome": "Comércio Varejista",
        "margem_bruta": {"min": 20, "media": 35, "max": 50},
        "margem_liquida": {"min": 2, "media": 8, "max": 15},
        "liquidez_corrente": {"min": 0.8, "media": 1.3, "max": 2.0},
        "folha_pct": 15,
        "custo_fixo_pct": 25
    },
    "comercio_atacado": {
        "nome": "Comércio Atacadista", 
        "margem_bruta": {"min": 10, "media": 20, "max": 30},
        "margem_liquida": {"min": 1, "media": 5, "max": 10},
        "liquidez_corrente": {"min": 1.0, "media": 1.5, "max": 2.5},
        "folha_pct": 10,
        "custo_fixo_pct": 18
    },
    "servicos": {
        "nome": "Prestação de Serviços",
        "margem_bruta": {"min": 40, "media": 60, "max": 80},
        "margem_liquida": {"min": 5, "media": 18, "max": 35},
        "liquidez_corrente": {"min": 1.0, "media": 1.8, "max": 3.0},
        "folha_pct": 40,
        "custo_fixo_pct": 50
    },
    "industria": {
        "nome": "Indústria",
        "margem_bruta": {"min": 20, "media": 35, "max": 50},
        "margem_liquida": {"min": 3, "media": 10, "max": 18},
        "liquidez_corrente": {"min": 1.0, "media": 1.5, "max": 2.2},
        "folha_pct": 25,
        "custo_fixo_pct": 35
    },
    "tecnologia": {
        "nome": "Tecnologia/Software",
        "margem_bruta": {"min": 60, "media": 75, "max": 90},
        "margem_liquida": {"min": 10, "media": 25, "max": 40},
        "liquidez_corrente": {"min": 1.5, "media": 2.5, "max": 4.0},
        "folha_pct": 50,
        "custo_fixo_pct": 60
    },
    "restaurante": {
        "nome": "Restaurantes/Alimentação",
        "margem_bruta": {"min": 55, "media": 65, "max": 75},
        "margem_liquida": {"min": 3, "media": 10, "max": 18},
        "liquidez_corrente": {"min": 0.5, "media": 1.0, "max": 1.5},
        "folha_pct": 30,
        "custo_fixo_pct": 45
    },
    "saude": {
        "nome": "Saúde/Clínicas",
        "margem_bruta": {"min": 45, "media": 60, "max": 75},
        "margem_liquida": {"min": 8, "media": 20, "max": 35},
        "liquidez_corrente": {"min": 1.2, "media": 2.0, "max": 3.0},
        "folha_pct": 35,
        "custo_fixo_pct": 45
    },
    "construcao": {
        "nome": "Construção Civil",
        "margem_bruta": {"min": 15, "media": 25, "max": 40},
        "margem_liquida": {"min": 3, "media": 8, "max": 15},
        "liquidez_corrente": {"min": 1.0, "media": 1.4, "max": 2.0},
        "folha_pct": 20,
        "custo_fixo_pct": 25
    },
    "transporte": {
        "nome": "Transporte/Logística",
        "margem_bruta": {"min": 20, "media": 30, "max": 45},
        "margem_liquida": {"min": 2, "media": 7, "max": 12},
        "liquidez_corrente": {"min": 0.8, "media": 1.2, "max": 1.8},
        "folha_pct": 25,
        "custo_fixo_pct": 40
    },
    "educacao": {
        "nome": "Educação",
        "margem_bruta": {"min": 50, "media": 65, "max": 80},
        "margem_liquida": {"min": 8, "media": 18, "max": 30},
        "liquidez_corrente": {"min": 1.0, "media": 1.6, "max": 2.5},
        "folha_pct": 45,
        "custo_fixo_pct": 55
    },
    "geral": {
        "nome": "Média Geral",
        "margem_bruta": {"min": 25, "media": 40, "max": 60},
        "margem_liquida": {"min": 3, "media": 12, "max": 25},
        "liquidez_corrente": {"min": 1.0, "media": 1.5, "max": 2.5},
        "folha_pct": 25,
        "custo_fixo_pct": 35
    }
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DRE:
    """Demonstrativo de Resultado do Exercício."""
    periodo: str
    
    # Receitas
    receita_bruta: float = 0
    deducoes_receita: float = 0
    receita_liquida: float = 0
    
    # Custos
    custo_produtos_vendidos: float = 0
    lucro_bruto: float = 0
    margem_bruta_pct: float = 0
    
    # Despesas Operacionais
    despesas_pessoal: float = 0
    despesas_administrativas: float = 0
    despesas_comerciais: float = 0
    outras_despesas: float = 0
    total_despesas_operacionais: float = 0
    
    # Resultado
    lucro_operacional: float = 0
    margem_operacional_pct: float = 0
    
    # Impostos e Resultado Final
    impostos: float = 0
    lucro_liquido: float = 0
    margem_liquida_pct: float = 0


@dataclass
class IndicesFinanceiros:
    """Índices financeiros calculados."""
    periodo: str
    
    # ===== DADOS DO BALANÇO (para cálculos) =====
    ativo_circulante: float = 0
    passivo_circulante: float = 0
    ativo_nao_circulante: float = 0
    passivo_nao_circulante: float = 0
    ativo_total: float = 0
    passivo_total: float = 0
    patrimonio_liquido: float = 0
    
    # Componentes do Ativo Circulante
    disponibilidades: float = 0  # Caixa + Bancos + Aplicações
    caixa: float = 0
    contas_receber: float = 0  # Clientes/Duplicatas
    estoques: float = 0
    
    # Componentes do Passivo Circulante
    fornecedores: float = 0
    emprestimos_cp: float = 0
    
    # ===== ÍNDICES DE LIQUIDEZ (8 tipos) =====
    # 1. Liquidez Corrente = AC / PC
    liquidez_corrente: float = 0
    
    # 2. Liquidez Seca = (AC - Estoques) / PC
    liquidez_seca: float = 0
    
    # 3. Liquidez Imediata = Disponibilidades / PC
    liquidez_imediata: float = 0
    
    # 4. Liquidez Geral = (AC + ANC) / (PC + PNC)
    liquidez_geral: float = 0
    
    # 5. Liquidez Operacional = AC Operacional / PC Operacional
    liquidez_operacional: float = 0
    
    # 6. Liquidez de Caixa = (Caixa + Equivalentes) / PC
    liquidez_caixa: float = 0
    
    # 7. NCG - Necessidade de Capital de Giro
    ncg: float = 0  # AC Operacional - PC Operacional
    saldo_tesouraria: float = 0  # Disponibilidades - NCG
    
    # 8. Liquidez Ajustada = (Caixa + 70%CR + 30%Est) / PC
    liquidez_ajustada: float = 0
    
    # Capital de Giro
    capital_giro: float = 0  # AC - PC
    capital_giro_dias: float = 0  # Dias que o caixa cobre despesas
    
    # ===== RENTABILIDADE =====
    margem_bruta: float = 0
    margem_operacional: float = 0
    margem_liquida: float = 0
    retorno_sobre_receita: float = 0
    
    # ROE, ROA, Giro
    roe: float = 0  # Lucro Líquido / Patrimônio Líquido
    roa: float = 0  # Lucro Líquido / Ativo Total
    giro_ativo: float = 0  # Receita / Ativo Total
    
    # ===== EFICIÊNCIA =====
    giro_receita_caixa: float = 0  # Receita / Caixa
    produtividade_folha: float = 0  # Receita / Folha
    
    # Ciclos
    pmr: float = 0  # Prazo Médio de Recebimento
    pmp: float = 0  # Prazo Médio de Pagamento
    pme: float = 0  # Prazo Médio de Estoque
    ciclo_operacional: float = 0  # PMR + PME
    ciclo_financeiro: float = 0  # Ciclo Operacional - PMP
    
    # ===== ESTRUTURA =====
    peso_custos: float = 0  # Custos / Receita
    peso_despesas: float = 0  # Despesas / Receita
    peso_folha: float = 0  # Folha / Receita
    peso_impostos: float = 0  # Impostos / Receita
    
    # Endividamento
    endividamento_geral: float = 0  # Passivo / Ativo
    composicao_endividamento: float = 0  # PC / Passivo Total
    endividamento_pl: float = 0  # Passivo / PL
    
    # ===== EVOLUÇÃO =====
    variacao_receita: float = 0
    variacao_lucro: float = 0
    variacao_margem: float = 0
    
    # ===== SAÚDE FINANCEIRA =====
    saude_financeira: str = "N/A"  # Excelente, Boa, Regular, Crítica
    score_saude: int = 0  # 0-100


@dataclass
class BreakEven:
    """Análise de Ponto de Equilíbrio."""
    # Dados base
    receita_media_mensal: float = 0
    custo_fixo_mensal: float = 0
    custo_variavel_pct: float = 0
    
    # Margem de contribuição
    margem_contribuicao_pct: float = 0
    margem_contribuicao_valor: float = 0
    
    # Ponto de equilíbrio
    ponto_equilibrio_valor: float = 0
    ponto_equilibrio_pct_capacidade: float = 0
    
    # Situação atual
    folga_operacional: float = 0  # Receita atual - Break-even
    folga_pct: float = 0
    
    # Metas
    receita_para_lucro_10pct: float = 0
    receita_para_lucro_20pct: float = 0


@dataclass
class ProjecaoMensal:
    """Projeção de um mês específico."""
    ano: int
    mes: int
    
    receita: float = 0
    custos: float = 0
    despesas: float = 0
    impostos: float = 0
    lucro: float = 0
    margem: float = 0
    caixa_acumulado: float = 0


@dataclass
class Projecao:
    """Projeção financeira completa."""
    cenario: str  # otimista, realista, pessimista
    meses: int
    
    # Premissas
    taxa_crescimento_receita: float = 0
    taxa_variacao_custos: float = 0
    
    # Dados mensais
    dados_mensais: List[ProjecaoMensal] = field(default_factory=list)
    
    # Totais
    receita_total: float = 0
    lucro_total: float = 0
    caixa_final: float = 0
    margem_media: float = 0


@dataclass
class ComparacaoBenchmark:
    """Comparação com benchmark do setor."""
    indicador: str
    valor_empresa: float
    valor_setor_min: float
    valor_setor_media: float
    valor_setor_max: float
    
    posicao: str = ""  # acima, na_media, abaixo
    diferenca_vs_media: float = 0
    percentil_estimado: int = 50


@dataclass
class AnaliseAvancada:
    """Análise financeira avançada completa."""
    empresa_id: int
    empresa_nome: str
    setor: str
    periodo: str
    gerado_em: str
    
    # Componentes
    dre: Optional[DRE] = None
    indices: Optional[IndicesFinanceiros] = None
    break_even: Optional[BreakEven] = None
    projecoes: List[Projecao] = field(default_factory=list)
    benchmarks: List[ComparacaoBenchmark] = field(default_factory=list)
    
    # Resumo executivo
    pontos_fortes: List[str] = field(default_factory=list)
    pontos_fracos: List[str] = field(default_factory=list)
    oportunidades: List[str] = field(default_factory=list)
    riscos: List[str] = field(default_factory=list)
    recomendacoes: List[str] = field(default_factory=list)


# =============================================================================
# GERADORES
# =============================================================================

def gerar_dre(dados_mensais: List[Dict], periodo: str = None) -> DRE:
    """Gera DRE a partir dos dados mensais."""
    if not dados_mensais:
        return DRE(periodo=periodo or "N/A")
    
    # Agrupa por período se especificado
    if periodo and len(periodo) == 4:  # Ano
        dados = [d for d in dados_mensais if str(d.get('ano')) == periodo]
    elif periodo and len(periodo) == 7:  # YYYY-MM
        ano, mes = periodo.split('-')
        dados = [d for d in dados_mensais if str(d.get('ano')) == ano and d.get('mes') == int(mes)]
    else:
        dados = dados_mensais
    
    if not dados:
        return DRE(periodo=periodo or "N/A")
    
    # Soma valores
    receita = sum(d.get('receita', 0) or 0 for d in dados)
    custos = sum(d.get('custos', 0) or 0 for d in dados)
    despesas = sum(d.get('despesas', 0) or 0 for d in dados)
    impostos = sum(d.get('impostos', 0) or 0 for d in dados)
    folha = sum(d.get('folha', 0) or 0 for d in dados)
    
    dre = DRE(periodo=periodo or f"{dados[0].get('ano', 'N/A')}")
    
    # Receitas
    dre.receita_bruta = receita
    dre.deducoes_receita = impostos * 0.3  # Estimativa: 30% dos impostos são sobre receita
    dre.receita_liquida = receita - dre.deducoes_receita
    
    # Custos
    dre.custo_produtos_vendidos = custos
    dre.lucro_bruto = dre.receita_liquida - custos
    dre.margem_bruta_pct = (dre.lucro_bruto / receita * 100) if receita > 0 else 0
    
    # Despesas
    dre.despesas_pessoal = folha
    dre.despesas_administrativas = despesas * 0.6
    dre.despesas_comerciais = despesas * 0.3
    dre.outras_despesas = despesas * 0.1
    dre.total_despesas_operacionais = folha + despesas
    
    # Resultado operacional
    dre.lucro_operacional = dre.lucro_bruto - dre.total_despesas_operacionais
    dre.margem_operacional_pct = (dre.lucro_operacional / receita * 100) if receita > 0 else 0
    
    # Resultado final
    dre.impostos = impostos * 0.7  # 70% são impostos sobre lucro
    dre.lucro_liquido = dre.lucro_operacional - dre.impostos
    dre.margem_liquida_pct = (dre.lucro_liquido / receita * 100) if receita > 0 else 0
    
    return dre


def calcular_indices(dados_mensais: List[Dict]) -> IndicesFinanceiros:
    """Calcula índices financeiros completos incluindo 8 tipos de liquidez."""
    if not dados_mensais:
        return IndicesFinanceiros(periodo="N/A")
    
    # Ordena por data
    dados = sorted(dados_mensais, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))
    ultimo = dados[-1]
    n = len(dados)
    
    # ===== TOTAIS DO DRE =====
    receita_total = sum(d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados)
    custos_total = sum(d.get('custos', 0) or d.get('custos_total', 0) or d.get('custo_produtos_vendidos', 0) or 0 for d in dados)
    despesas_total = sum(d.get('despesas', 0) or d.get('despesas_operacionais', 0) or 0 for d in dados)
    impostos_total = sum(d.get('impostos', 0) or d.get('deducoes_receita', 0) or 0 for d in dados)
    folha_total = sum(d.get('folha', 0) or d.get('despesas_pessoal', 0) or 0 for d in dados)
    
    lucro_bruto = receita_total - custos_total
    lucro_operacional = lucro_bruto - despesas_total - folha_total
    lucro_liquido = sum(d.get('lucro_liquido', 0) or 0 for d in dados)
    if lucro_liquido == 0:
        lucro_liquido = receita_total - custos_total - despesas_total - impostos_total - folha_total
    
    receita_media = receita_total / n if n > 0 else 0
    gasto_medio_mensal = (custos_total + despesas_total + folha_total + impostos_total) / n if n > 0 else 1
    
    # ===== DADOS DO BALANÇO (último período) =====
    # Ativo Circulante e componentes
    ac = ultimo.get('ativo_circulante', 0) or 0
    disponibilidades = ultimo.get('disponivel', 0) or ultimo.get('disponibilidades', 0) or ultimo.get('caixa', 0) or 0
    caixa = ultimo.get('caixa', 0) or disponibilidades
    contas_receber = ultimo.get('clientes', 0) or ultimo.get('contas_receber', 0) or ultimo.get('duplicatas_receber', 0) or 0
    estoques = ultimo.get('estoques', 0) or ultimo.get('estoque', 0) or 0
    
    # Se AC não estiver explícito, calcular
    if ac == 0 and (disponibilidades > 0 or contas_receber > 0 or estoques > 0):
        ac = disponibilidades + contas_receber + estoques
    
    # Ativo Não Circulante
    anc = ultimo.get('ativo_nao_circulante', 0) or ultimo.get('imobilizado', 0) or 0
    
    # Ativo Total
    at = ultimo.get('ativo_total', 0) or (ac + anc) or 0
    
    # Passivo Circulante e componentes
    pc = ultimo.get('passivo_circulante', 0) or 0
    fornecedores = ultimo.get('fornecedores', 0) or 0
    emprestimos_cp = ultimo.get('emprestimos_cp', 0) or ultimo.get('emprestimos', 0) or 0
    
    # Se PC não estiver explícito, tentar estimar
    if pc == 0 and fornecedores > 0:
        pc = fornecedores + emprestimos_cp
    
    # Passivo Não Circulante
    pnc = ultimo.get('passivo_nao_circulante', 0) or ultimo.get('emprestimos_lp', 0) or 0
    
    # Passivo Total
    pt = pc + pnc
    
    # Patrimônio Líquido
    pl = ultimo.get('patrimonio_liquido', 0) or ultimo.get('capital_social', 0) or (at - pt) or 0
    if pl == 0 and at > 0:
        pl = at - pt
    
    # ===== CRIAR OBJETO DE ÍNDICES =====
    idx = IndicesFinanceiros(periodo=f"{dados[0].get('ano')}-{dados[-1].get('ano')}")
    
    # Armazenar dados do balanço
    idx.ativo_circulante = ac
    idx.passivo_circulante = pc
    idx.ativo_nao_circulante = anc
    idx.passivo_nao_circulante = pnc
    idx.ativo_total = at
    idx.passivo_total = pt
    idx.patrimonio_liquido = pl
    idx.disponibilidades = disponibilidades
    idx.caixa = caixa
    idx.contas_receber = contas_receber
    idx.estoques = estoques
    idx.fornecedores = fornecedores
    idx.emprestimos_cp = emprestimos_cp
    
    # ===== ÍNDICES DE LIQUIDEZ (8 tipos) =====
    
    # 1. Liquidez Corrente = AC / PC
    idx.liquidez_corrente = ac / pc if pc > 0 else 0
    
    # 2. Liquidez Seca = (AC - Estoques) / PC
    idx.liquidez_seca = (ac - estoques) / pc if pc > 0 else 0
    
    # 3. Liquidez Imediata = Disponibilidades / PC
    idx.liquidez_imediata = disponibilidades / pc if pc > 0 else 0
    
    # 4. Liquidez Geral = (AC + ANC) / (PC + PNC)
    idx.liquidez_geral = (ac + anc) / (pc + pnc) if (pc + pnc) > 0 else 0
    
    # 5. Liquidez Operacional = AC Operacional / PC Operacional
    ac_operacional = contas_receber + estoques
    pc_operacional = fornecedores
    idx.liquidez_operacional = ac_operacional / pc_operacional if pc_operacional > 0 else 0
    
    # 6. Liquidez de Caixa (Cash Ratio) = Caixa / PC
    idx.liquidez_caixa = caixa / pc if pc > 0 else 0
    
    # 7. NCG e Saldo de Tesouraria
    idx.ncg = ac_operacional - pc_operacional
    idx.saldo_tesouraria = disponibilidades - idx.ncg
    
    # 8. Liquidez Ajustada = (Caixa + 70%*CR + 30%*Estoques) / PC
    idx.liquidez_ajustada = (caixa + (contas_receber * 0.7) + (estoques * 0.3)) / pc if pc > 0 else 0
    
    # Capital de Giro
    idx.capital_giro = ac - pc
    idx.capital_giro_dias = (caixa / gasto_medio_mensal * 30) if gasto_medio_mensal > 0 else 0
    
    # ===== RENTABILIDADE =====
    idx.margem_bruta = (lucro_bruto / receita_total * 100) if receita_total > 0 else 0
    idx.margem_operacional = (lucro_operacional / receita_total * 100) if receita_total > 0 else 0
    idx.margem_liquida = (lucro_liquido / receita_total * 100) if receita_total > 0 else 0
    idx.retorno_sobre_receita = idx.margem_liquida
    
    # ROE = Lucro Líquido / Patrimônio Líquido
    idx.roe = (lucro_liquido / pl * 100) if pl > 0 else 0
    
    # ROA = Lucro Líquido / Ativo Total
    idx.roa = (lucro_liquido / at * 100) if at > 0 else 0
    
    # Giro do Ativo = Receita / Ativo Total
    idx.giro_ativo = receita_total / at if at > 0 else 0
    
    # ===== EFICIÊNCIA =====
    idx.giro_receita_caixa = receita_total / caixa if caixa > 0 else 0
    idx.produtividade_folha = receita_total / folha_total if folha_total > 0 else 0
    
    # Ciclos (em dias)
    idx.pmr = (contas_receber / receita_media * 30) if receita_media > 0 else 0
    idx.pmp = (fornecedores / (custos_total / n) * 30) if custos_total > 0 and n > 0 else 0
    idx.pme = (estoques / (custos_total / n) * 30) if custos_total > 0 and n > 0 else 0
    idx.ciclo_operacional = idx.pmr + idx.pme
    idx.ciclo_financeiro = idx.ciclo_operacional - idx.pmp
    
    # ===== ESTRUTURA =====
    idx.peso_custos = (custos_total / receita_total * 100) if receita_total > 0 else 0
    idx.peso_despesas = (despesas_total / receita_total * 100) if receita_total > 0 else 0
    idx.peso_folha = (folha_total / receita_total * 100) if receita_total > 0 else 0
    idx.peso_impostos = (impostos_total / receita_total * 100) if receita_total > 0 else 0
    
    # Endividamento
    idx.endividamento_geral = (pt / at * 100) if at > 0 else 0
    idx.composicao_endividamento = (pc / pt * 100) if pt > 0 else 0
    idx.endividamento_pl = (pt / pl * 100) if pl > 0 else 0
    
    # ===== EVOLUÇÃO (compara metades) =====
    if len(dados) >= 4:
        meio = len(dados) // 2
        receita_1 = sum(d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados[:meio])
        receita_2 = sum(d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados[meio:])
        
        lucro_1 = sum(
            (d.get('receita', 0) or d.get('receita_bruta', 0) or 0) - 
            (d.get('custos', 0) or d.get('custos_total', 0) or 0) - 
            (d.get('despesas', 0) or d.get('despesas_operacionais', 0) or 0) - 
            (d.get('impostos', 0) or 0) - 
            (d.get('folha', 0) or d.get('despesas_pessoal', 0) or 0) 
            for d in dados[:meio]
        )
        lucro_2 = sum(
            (d.get('receita', 0) or d.get('receita_bruta', 0) or 0) - 
            (d.get('custos', 0) or d.get('custos_total', 0) or 0) - 
            (d.get('despesas', 0) or d.get('despesas_operacionais', 0) or 0) - 
            (d.get('impostos', 0) or 0) - 
            (d.get('folha', 0) or d.get('despesas_pessoal', 0) or 0) 
            for d in dados[meio:]
        )
        
        idx.variacao_receita = ((receita_2 - receita_1) / receita_1 * 100) if receita_1 > 0 else 0
        idx.variacao_lucro = ((lucro_2 - lucro_1) / abs(lucro_1) * 100) if lucro_1 != 0 else 0
    
    # ===== SAÚDE FINANCEIRA (score 0-100) =====
    pontos = 0
    
    # Margem líquida (até 25 pontos)
    if idx.margem_liquida >= 20:
        pontos += 25
    elif idx.margem_liquida >= 10:
        pontos += 20
    elif idx.margem_liquida >= 5:
        pontos += 15
    elif idx.margem_liquida >= 0:
        pontos += 5
    
    # Liquidez corrente (até 25 pontos)
    if idx.liquidez_corrente >= 2.0:
        pontos += 25
    elif idx.liquidez_corrente >= 1.5:
        pontos += 20
    elif idx.liquidez_corrente >= 1.0:
        pontos += 15
    elif idx.liquidez_corrente >= 0.7:
        pontos += 5
    
    # Endividamento (até 25 pontos - quanto menor, melhor)
    if idx.endividamento_geral <= 30:
        pontos += 25
    elif idx.endividamento_geral <= 50:
        pontos += 20
    elif idx.endividamento_geral <= 70:
        pontos += 15
    elif idx.endividamento_geral <= 85:
        pontos += 5
    
    # Variação de receita (até 25 pontos)
    if idx.variacao_receita >= 20:
        pontos += 25
    elif idx.variacao_receita >= 10:
        pontos += 20
    elif idx.variacao_receita >= 0:
        pontos += 15
    elif idx.variacao_receita >= -10:
        pontos += 5
    
    idx.score_saude = pontos
    
    # Determinar status
    if pontos >= 80:
        idx.saude_financeira = "otima"
    elif pontos >= 60:
        idx.saude_financeira = "boa"
    elif pontos >= 40:
        idx.saude_financeira = "regular"
    else:
        idx.saude_financeira = "critica"
    
    return idx


def calcular_break_even(dados_mensais: List[Dict], custo_fixo_pct: float = None) -> BreakEven:
    """Calcula ponto de equilíbrio."""
    if not dados_mensais:
        return BreakEven()
    
    n = len(dados_mensais)
    
    # Médias mensais
    receita_media = sum(d.get('receita', 0) or 0 for d in dados_mensais) / n
    custos_media = sum(d.get('custos', 0) or 0 for d in dados_mensais) / n
    despesas_media = sum(d.get('despesas', 0) or 0 for d in dados_mensais) / n
    folha_media = sum(d.get('folha', 0) or 0 for d in dados_mensais) / n
    
    be = BreakEven()
    be.receita_media_mensal = receita_media
    
    # Estima custos fixos vs variáveis
    # Fixos: folha + parte das despesas
    # Variáveis: custos + parte das despesas
    be.custo_fixo_mensal = folha_media + (despesas_media * 0.7)
    custo_variavel = custos_media + (despesas_media * 0.3)
    
    be.custo_variavel_pct = (custo_variavel / receita_media * 100) if receita_media > 0 else 50
    
    # Margem de contribuição
    be.margem_contribuicao_pct = 100 - be.custo_variavel_pct
    be.margem_contribuicao_valor = receita_media * be.margem_contribuicao_pct / 100
    
    # Ponto de equilíbrio
    if be.margem_contribuicao_pct > 0:
        be.ponto_equilibrio_valor = be.custo_fixo_mensal / (be.margem_contribuicao_pct / 100)
        be.ponto_equilibrio_pct_capacidade = (be.ponto_equilibrio_valor / receita_media * 100) if receita_media > 0 else 100
    
    # Folga operacional
    be.folga_operacional = receita_media - be.ponto_equilibrio_valor
    be.folga_pct = (be.folga_operacional / be.ponto_equilibrio_valor * 100) if be.ponto_equilibrio_valor > 0 else 0
    
    # Metas
    if be.margem_contribuicao_pct > 0:
        # Para lucro de 10% da receita: MC * R - CF = 0.10 * R
        # R * (MC - 0.10) = CF
        mc_decimal = be.margem_contribuicao_pct / 100
        if mc_decimal > 0.10:
            be.receita_para_lucro_10pct = be.custo_fixo_mensal / (mc_decimal - 0.10)
        if mc_decimal > 0.20:
            be.receita_para_lucro_20pct = be.custo_fixo_mensal / (mc_decimal - 0.20)
    
    return be


def gerar_projecoes(dados_mensais: List[Dict], meses: int = 12) -> List[Projecao]:
    """Gera projeções em 3 cenários."""
    if len(dados_mensais) < 3:
        return []
    
    # Ordena e pega últimos dados
    dados = sorted(dados_mensais, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))
    ultimo = dados[-1]
    
    # Médias recentes (últimos 6 meses ou todos se menos)
    recentes = dados[-6:] if len(dados) >= 6 else dados
    n = len(recentes)
    
    receita_media = sum(d.get('receita', 0) or 0 for d in recentes) / n
    custos_media = sum(d.get('custos', 0) or 0 for d in recentes) / n
    despesas_media = sum(d.get('despesas', 0) or 0 for d in recentes) / n
    impostos_media = sum(d.get('impostos', 0) or 0 for d in recentes) / n
    folha_media = sum(d.get('folha', 0) or 0 for d in recentes) / n
    caixa_atual = ultimo.get('caixa', 0) or 0
    
    # Calcula tendência histórica
    if len(dados) >= 6:
        receita_inicio = sum(d.get('receita', 0) or 0 for d in dados[:3]) / 3
        receita_fim = sum(d.get('receita', 0) or 0 for d in dados[-3:]) / 3
        tendencia = ((receita_fim - receita_inicio) / receita_inicio) if receita_inicio > 0 else 0
        tendencia_mensal = tendencia / (len(dados) - 3) if len(dados) > 3 else 0
    else:
        tendencia_mensal = 0
    
    # Cenários
    cenarios = {
        'pessimista': {
            'taxa_receita': max(tendencia_mensal - 0.02, -0.05),
            'taxa_custos': 0.01
        },
        'realista': {
            'taxa_receita': tendencia_mensal,
            'taxa_custos': 0.005
        },
        'otimista': {
            'taxa_receita': min(tendencia_mensal + 0.02, 0.08),
            'taxa_custos': 0
        }
    }
    
    projecoes = []
    
    for cenario_nome, params in cenarios.items():
        proj = Projecao(
            cenario=cenario_nome,
            meses=meses,
            taxa_crescimento_receita=params['taxa_receita'] * 100,
            taxa_variacao_custos=params['taxa_custos'] * 100
        )
        
        ano = ultimo.get('ano', 2024)
        mes = ultimo.get('mes', 12)
        receita = receita_media
        custos = custos_media
        despesas = despesas_media + folha_media
        caixa = caixa_atual
        
        receita_total = 0
        lucro_total = 0
        
        for i in range(meses):
            # Avança mês
            mes += 1
            if mes > 12:
                mes = 1
                ano += 1
            
            # Aplica taxas
            receita *= (1 + params['taxa_receita'])
            custos *= (1 + params['taxa_custos'])
            despesas *= (1 + params['taxa_custos'] * 0.5)
            
            # Calcula
            impostos = receita * (impostos_media / receita_media) if receita_media > 0 else 0
            lucro = receita - custos - despesas - impostos
            margem = (lucro / receita * 100) if receita > 0 else 0
            caixa += lucro
            
            pm = ProjecaoMensal(
                ano=ano,
                mes=mes,
                receita=round(receita, 2),
                custos=round(custos, 2),
                despesas=round(despesas, 2),
                impostos=round(impostos, 2),
                lucro=round(lucro, 2),
                margem=round(margem, 1),
                caixa_acumulado=round(caixa, 2)
            )
            proj.dados_mensais.append(pm)
            
            receita_total += receita
            lucro_total += lucro
        
        proj.receita_total = round(receita_total, 2)
        proj.lucro_total = round(lucro_total, 2)
        proj.caixa_final = round(caixa, 2)
        proj.margem_media = round((lucro_total / receita_total * 100) if receita_total > 0 else 0, 1)
        
        projecoes.append(proj)
    
    return projecoes


def comparar_benchmarks(indices: IndicesFinanceiros, setor: str = "geral") -> List[ComparacaoBenchmark]:
    """Compara índices com benchmarks do setor."""
    bench = BENCHMARKS.get(setor, BENCHMARKS['geral'])
    comparacoes = []
    
    # Margem Bruta
    comp = ComparacaoBenchmark(
        indicador="Margem Bruta (%)",
        valor_empresa=round(indices.margem_bruta, 1),
        valor_setor_min=bench['margem_bruta']['min'],
        valor_setor_media=bench['margem_bruta']['media'],
        valor_setor_max=bench['margem_bruta']['max']
    )
    _classificar(comp)
    comparacoes.append(comp)
    
    # Margem Líquida
    comp = ComparacaoBenchmark(
        indicador="Margem Líquida (%)",
        valor_empresa=round(indices.margem_liquida, 1),
        valor_setor_min=bench['margem_liquida']['min'],
        valor_setor_media=bench['margem_liquida']['media'],
        valor_setor_max=bench['margem_liquida']['max']
    )
    _classificar(comp)
    comparacoes.append(comp)
    
    # Liquidez
    comp = ComparacaoBenchmark(
        indicador="Liquidez Corrente",
        valor_empresa=round(indices.liquidez_corrente, 2),
        valor_setor_min=bench['liquidez_corrente']['min'],
        valor_setor_media=bench['liquidez_corrente']['media'],
        valor_setor_max=bench['liquidez_corrente']['max']
    )
    _classificar(comp)
    comparacoes.append(comp)
    
    # Peso da Folha
    folha_bench = bench.get('folha_pct', 25)
    comp = ComparacaoBenchmark(
        indicador="Peso da Folha (%)",
        valor_empresa=round(indices.peso_folha, 1),
        valor_setor_min=folha_bench * 0.6,
        valor_setor_media=folha_bench,
        valor_setor_max=folha_bench * 1.4
    )
    _classificar(comp, inverso=True)  # Menor é melhor
    comparacoes.append(comp)
    
    return comparacoes


def _classificar(comp: ComparacaoBenchmark, inverso: bool = False):
    """Classifica posição em relação ao benchmark."""
    valor = comp.valor_empresa
    media = comp.valor_setor_media
    minimo = comp.valor_setor_min
    maximo = comp.valor_setor_max
    
    comp.diferenca_vs_media = round(valor - media, 1)
    
    if inverso:
        # Para métricas onde menor é melhor
        if valor <= minimo:
            comp.posicao = "acima"
            comp.percentil_estimado = 90
        elif valor >= maximo:
            comp.posicao = "abaixo"
            comp.percentil_estimado = 10
        else:
            comp.posicao = "na_media"
            comp.percentil_estimado = 50
    else:
        if valor >= maximo:
            comp.posicao = "acima"
            comp.percentil_estimado = 90
        elif valor <= minimo:
            comp.posicao = "abaixo"
            comp.percentil_estimado = 10
        else:
            comp.posicao = "na_media"
            # Interpola percentil
            if valor >= media:
                comp.percentil_estimado = int(50 + (valor - media) / (maximo - media) * 40) if maximo > media else 50
            else:
                comp.percentil_estimado = int(50 - (media - valor) / (media - minimo) * 40) if media > minimo else 50


def gerar_analise_avancada(empresa: Dict, dados_mensais: List[Dict], setor: str = None) -> AnaliseAvancada:
    """Gera análise financeira avançada completa."""
    
    setor = setor or empresa.get('setor') or 'geral'
    
    analise = AnaliseAvancada(
        empresa_id=empresa.get('id', 0),
        empresa_nome=empresa.get('razao_social', 'N/A'),
        setor=setor,
        periodo=_get_periodo(dados_mensais),
        gerado_em=datetime.now().isoformat()
    )
    
    if not dados_mensais or len(dados_mensais) < 3:
        analise.riscos.append("Dados insuficientes para análise completa (mínimo 3 meses)")
        return analise
    
    # Gera componentes
    analise.dre = gerar_dre(dados_mensais)
    analise.indices = calcular_indices(dados_mensais)
    analise.break_even = calcular_break_even(dados_mensais)
    analise.projecoes = gerar_projecoes(dados_mensais, 12)
    analise.benchmarks = comparar_benchmarks(analise.indices, setor)
    
    # Gera resumo executivo
    _gerar_resumo(analise)
    
    return analise


def _get_periodo(dados_mensais: List[Dict]) -> str:
    """Retorna período dos dados."""
    if not dados_mensais:
        return "N/A"
    dados = sorted(dados_mensais, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))
    inicio = f"{dados[0].get('mes', 1):02d}/{dados[0].get('ano', 0)}"
    fim = f"{dados[-1].get('mes', 1):02d}/{dados[-1].get('ano', 0)}"
    return f"{inicio} a {fim}"


def _gerar_resumo(analise: AnaliseAvancada):
    """Gera resumo executivo (SWOT + recomendações)."""
    idx = analise.indices
    be = analise.break_even
    dre = analise.dre
    
    if not idx:
        return
    
    # Pontos Fortes
    if idx.margem_liquida >= 15:
        analise.pontos_fortes.append(f"Margem líquida excelente de {idx.margem_liquida:.1f}%")
    elif idx.margem_liquida >= 10:
        analise.pontos_fortes.append(f"Boa margem líquida de {idx.margem_liquida:.1f}%")
    
    if idx.liquidez_corrente >= 2:
        analise.pontos_fortes.append(f"Alta liquidez ({idx.capital_giro_dias:.0f} dias de capital de giro)")
    
    if idx.variacao_receita > 10:
        analise.pontos_fortes.append(f"Receita em crescimento ({idx.variacao_receita:.1f}%)")
    
    if be and be.folga_pct > 30:
        analise.pontos_fortes.append(f"Operação {be.folga_pct:.0f}% acima do ponto de equilíbrio")
    
    # Pontos Fracos
    if idx.margem_liquida < 5:
        analise.pontos_fracos.append(f"Margem líquida baixa ({idx.margem_liquida:.1f}%)")
    
    if idx.margem_liquida < 0:
        analise.pontos_fracos.append(f"⚠️ Operação com prejuízo ({idx.margem_liquida:.1f}%)")
    
    if idx.liquidez_corrente < 1:
        analise.pontos_fracos.append(f"Liquidez crítica (apenas {idx.capital_giro_dias:.0f} dias de caixa)")
    
    if idx.peso_folha > 35:
        analise.pontos_fracos.append(f"Folha de pagamento elevada ({idx.peso_folha:.1f}% da receita)")
    
    # Oportunidades
    for bench in analise.benchmarks:
        if bench.posicao == "abaixo" and bench.indicador in ["Margem Bruta (%)", "Margem Líquida (%)"]:
            analise.oportunidades.append(f"Potencial de melhoria na {bench.indicador}: média do setor é {bench.valor_setor_media}%")
    
    if idx.produtividade_folha < 3:
        analise.oportunidades.append("Oportunidade de aumentar produtividade da equipe")
    
    # Riscos
    if idx.variacao_receita < -10:
        analise.riscos.append(f"Receita em queda ({idx.variacao_receita:.1f}%)")
    
    if be and be.folga_pct < 10:
        analise.riscos.append("Operação muito próxima do ponto de equilíbrio")
    
    if idx.liquidez_corrente < 0.5:
        analise.riscos.append("Risco alto de problemas de caixa no curto prazo")
    
    # Recomendações
    if idx.margem_liquida < 10:
        analise.recomendacoes.append("Revisar estrutura de custos para melhorar rentabilidade")
    
    if idx.liquidez_corrente < 1.5:
        analise.recomendacoes.append("Aumentar reserva de capital de giro para pelo menos 45 dias")
    
    if idx.peso_folha > 30:
        analise.recomendacoes.append("Avaliar produtividade da equipe e possíveis otimizações")
    
    if be and be.ponto_equilibrio_valor > 0:
        meta_segura = be.ponto_equilibrio_valor * 1.3
        if be.receita_media_mensal < meta_segura:
            aumento = (meta_segura - be.receita_media_mensal)
            analise.recomendacoes.append(f"Buscar aumento de receita de R$ {aumento:,.0f}/mês para margem de segurança de 30%")
    
    if idx.variacao_receita < 0:
        analise.recomendacoes.append("Desenvolver estratégias para retomar crescimento de receita")


# =============================================================================
# FUNÇÕES DE EXPORTAÇÃO
# =============================================================================

def analise_to_dict(analise: AnaliseAvancada) -> Dict:
    """Converte análise para dicionário."""
    return {
        'empresa_id': analise.empresa_id,
        'empresa_nome': analise.empresa_nome,
        'setor': analise.setor,
        'periodo': analise.periodo,
        'gerado_em': analise.gerado_em,
        
        'dre': asdict(analise.dre) if analise.dre else None,
        'indices': asdict(analise.indices) if analise.indices else None,
        'break_even': asdict(analise.break_even) if analise.break_even else None,
        
        'projecoes': [
            {
                'cenario': p.cenario,
                'meses': p.meses,
                'taxa_crescimento_receita': p.taxa_crescimento_receita,
                'taxa_variacao_custos': p.taxa_variacao_custos,
                'receita_total': p.receita_total,
                'lucro_total': p.lucro_total,
                'caixa_final': p.caixa_final,
                'margem_media': p.margem_media,
                'dados_mensais': [asdict(m) for m in p.dados_mensais]
            }
            for p in analise.projecoes
        ],
        
        'benchmarks': [asdict(b) for b in analise.benchmarks],
        
        'pontos_fortes': analise.pontos_fortes,
        'pontos_fracos': analise.pontos_fracos,
        'oportunidades': analise.oportunidades,
        'riscos': analise.riscos,
        'recomendacoes': analise.recomendacoes
    }


def get_setores_disponiveis() -> List[Dict]:
    """Retorna lista de setores disponíveis."""
    return [
        {'codigo': k, 'nome': v['nome']}
        for k, v in BENCHMARKS.items()
    ]


def get_benchmark_setor(setor: str) -> Dict:
    """Retorna benchmark de um setor específico."""
    return BENCHMARKS.get(setor, BENCHMARKS['geral'])
