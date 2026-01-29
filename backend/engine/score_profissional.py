#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Score Profissional Kontabil v2.0
================================

Sistema de pontuação financeira profissional com:
- Ajuste por setor (benchmarks)
- Z-Score de Altman (modelo validado academicamente)
- Análise de tendência
- Múltiplas dimensões ponderadas
- Confiança estatística

Autor: Kontabil
Versão: 2.0
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy import stats


# =============================================================================
# BENCHMARKS POR SETOR
# =============================================================================

BENCHMARKS = {
    "comercio_varejo": {
        "nome": "Comércio Varejista",
        "margem_bruta": {"min": 20, "media": 35, "max": 50},
        "margem_liquida": {"min": 2, "media": 8, "max": 15},
        "liquidez_corrente": {"min": 0.8, "media": 1.3, "max": 2.0},
        "endividamento": {"min": 30, "media": 55, "max": 75},
        "pesos": {"rentabilidade": 0.30, "liquidez": 0.25, "endividamento": 0.20, "eficiencia": 0.25}
    },
    "comercio_atacado": {
        "nome": "Comércio Atacadista",
        "margem_bruta": {"min": 10, "media": 20, "max": 30},
        "margem_liquida": {"min": 1, "media": 5, "max": 10},
        "liquidez_corrente": {"min": 1.0, "media": 1.5, "max": 2.5},
        "endividamento": {"min": 35, "media": 55, "max": 70},
        "pesos": {"rentabilidade": 0.25, "liquidez": 0.30, "endividamento": 0.25, "eficiencia": 0.20}
    },
    "servicos": {
        "nome": "Prestação de Serviços",
        "margem_bruta": {"min": 40, "media": 60, "max": 80},
        "margem_liquida": {"min": 5, "media": 18, "max": 35},
        "liquidez_corrente": {"min": 1.0, "media": 1.8, "max": 3.0},
        "endividamento": {"min": 20, "media": 40, "max": 60},
        "pesos": {"rentabilidade": 0.35, "liquidez": 0.20, "endividamento": 0.20, "eficiencia": 0.25}
    },
    "industria": {
        "nome": "Indústria",
        "margem_bruta": {"min": 20, "media": 35, "max": 50},
        "margem_liquida": {"min": 3, "media": 10, "max": 18},
        "liquidez_corrente": {"min": 1.0, "media": 1.5, "max": 2.2},
        "endividamento": {"min": 35, "media": 55, "max": 75},
        "pesos": {"rentabilidade": 0.25, "liquidez": 0.25, "endividamento": 0.25, "eficiencia": 0.25}
    },
    "tecnologia": {
        "nome": "Tecnologia/Software",
        "margem_bruta": {"min": 60, "media": 75, "max": 90},
        "margem_liquida": {"min": 10, "media": 25, "max": 40},
        "liquidez_corrente": {"min": 1.5, "media": 2.5, "max": 4.0},
        "endividamento": {"min": 15, "media": 35, "max": 55},
        "pesos": {"rentabilidade": 0.35, "liquidez": 0.15, "endividamento": 0.15, "eficiencia": 0.35}
    },
    "restaurante": {
        "nome": "Restaurantes/Alimentação",
        "margem_bruta": {"min": 55, "media": 65, "max": 75},
        "margem_liquida": {"min": 3, "media": 10, "max": 18},
        "liquidez_corrente": {"min": 0.5, "media": 1.0, "max": 1.5},
        "endividamento": {"min": 40, "media": 60, "max": 80},
        "pesos": {"rentabilidade": 0.30, "liquidez": 0.30, "endividamento": 0.20, "eficiencia": 0.20}
    },
    "saude": {
        "nome": "Saúde/Clínicas",
        "margem_bruta": {"min": 45, "media": 60, "max": 75},
        "margem_liquida": {"min": 8, "media": 20, "max": 35},
        "liquidez_corrente": {"min": 1.2, "media": 2.0, "max": 3.0},
        "endividamento": {"min": 25, "media": 45, "max": 65},
        "pesos": {"rentabilidade": 0.30, "liquidez": 0.25, "endividamento": 0.20, "eficiencia": 0.25}
    },
    "construcao": {
        "nome": "Construção Civil",
        "margem_bruta": {"min": 15, "media": 25, "max": 40},
        "margem_liquida": {"min": 3, "media": 8, "max": 15},
        "liquidez_corrente": {"min": 1.0, "media": 1.4, "max": 2.0},
        "endividamento": {"min": 45, "media": 65, "max": 85},
        "pesos": {"rentabilidade": 0.20, "liquidez": 0.30, "endividamento": 0.30, "eficiencia": 0.20}
    },
    "transporte": {
        "nome": "Transporte/Logística",
        "margem_bruta": {"min": 20, "media": 30, "max": 45},
        "margem_liquida": {"min": 2, "media": 7, "max": 12},
        "liquidez_corrente": {"min": 0.8, "media": 1.2, "max": 1.8},
        "endividamento": {"min": 50, "media": 70, "max": 85},
        "pesos": {"rentabilidade": 0.25, "liquidez": 0.30, "endividamento": 0.25, "eficiencia": 0.20}
    },
    "geral": {
        "nome": "Média Geral",
        "margem_bruta": {"min": 25, "media": 40, "max": 60},
        "margem_liquida": {"min": 3, "media": 12, "max": 25},
        "liquidez_corrente": {"min": 1.0, "media": 1.5, "max": 2.5},
        "endividamento": {"min": 30, "media": 50, "max": 70},
        "pesos": {"rentabilidade": 0.25, "liquidez": 0.25, "endividamento": 0.25, "eficiencia": 0.25}
    }
}


@dataclass
class ScoreProfissional:
    """Resultado do score profissional."""
    # Score final
    score_final: int = 0
    classificacao: str = ""  # A, B, C, D, E
    status: str = ""  # Excelente, Bom, Regular, Atenção, Crítico
    
    # Scores por dimensão (0-100)
    score_rentabilidade: int = 0
    score_liquidez: int = 0
    score_endividamento: int = 0
    score_eficiencia: int = 0
    score_tendencia: int = 0
    
    # Z-Score de Altman
    zscore_altman: float = 0
    risco_falencia: str = ""  # Baixo, Moderado, Alto
    
    # Comparação com setor
    setor: str = ""
    posicao_setor: str = ""  # Acima da média, Na média, Abaixo da média
    percentil_setor: int = 0
    
    # Confiança
    confianca: int = 0  # 0-100
    meses_analisados: int = 0
    
    # Detalhes
    pontos_fortes: List[str] = field(default_factory=list)
    pontos_atencao: List[str] = field(default_factory=list)
    recomendacoes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


def calcular_score_relativo(valor: float, benchmark: Dict) -> int:
    """
    Calcula score relativo ao benchmark do setor.
    
    Retorna 0-100 onde:
    - 0-30: Abaixo do mínimo (crítico)
    - 30-50: Entre mínimo e média (atenção)
    - 50-70: Na média (ok)
    - 70-90: Entre média e máximo (bom)
    - 90-100: Acima do máximo (excelente)
    """
    minimo = benchmark.get('min', 0)
    media = benchmark.get('media', 50)
    maximo = benchmark.get('max', 100)
    
    if valor <= minimo:
        # Proporcional de 0 a 30
        return max(0, int(30 * valor / minimo)) if minimo > 0 else 0
    elif valor <= media:
        # Proporcional de 30 a 50
        return 30 + int(20 * (valor - minimo) / (media - minimo))
    elif valor <= maximo:
        # Proporcional de 50 a 90
        return 50 + int(40 * (valor - media) / (maximo - media))
    else:
        # Acima do máximo: 90-100
        excesso = (valor - maximo) / maximo
        return min(100, 90 + int(10 * excesso))


def calcular_score_inverso(valor: float, benchmark: Dict) -> int:
    """
    Para métricas onde MENOR é MELHOR (ex: endividamento).
    """
    minimo = benchmark.get('min', 0)
    media = benchmark.get('media', 50)
    maximo = benchmark.get('max', 100)
    
    if valor >= maximo:
        return max(0, int(30 * (100 - valor) / (100 - maximo))) if maximo < 100 else 0
    elif valor >= media:
        return 30 + int(20 * (maximo - valor) / (maximo - media))
    elif valor >= minimo:
        return 50 + int(40 * (media - valor) / (media - minimo))
    else:
        return min(100, 90 + int(10 * (minimo - valor) / minimo)) if minimo > 0 else 100


def calcular_zscore_altman(dados: Dict) -> Tuple[float, str]:
    """
    Calcula Z-Score de Altman para empresas privadas.
    
    Fórmula (empresas privadas):
    Z = 0.717×X1 + 0.847×X2 + 3.107×X3 + 0.420×X4 + 0.998×X5
    
    Onde:
    X1 = Capital de Giro / Ativo Total
    X2 = Lucros Retidos / Ativo Total
    X3 = EBIT / Ativo Total
    X4 = Patrimônio Líquido / Passivo Total
    X5 = Receita / Ativo Total
    
    Interpretação:
    Z > 2.9: Zona segura (baixo risco)
    1.23 < Z < 2.9: Zona cinza (moderado)
    Z < 1.23: Zona de perigo (alto risco)
    """
    at = dados.get('ativo_total', 0) or 1  # Evita divisão por zero
    pt = dados.get('passivo_total', 0) or 1
    
    # X1: Capital de Giro / Ativo Total
    ac = dados.get('ativo_circulante', 0) or 0
    pc = dados.get('passivo_circulante', 0) or 0
    capital_giro = ac - pc
    x1 = capital_giro / at
    
    # X2: Lucros Retidos / Ativo Total
    lucros_retidos = dados.get('lucros_acumulados', 0) or dados.get('lucro_liquido', 0) or 0
    x2 = lucros_retidos / at
    
    # X3: EBIT / Ativo Total (aproximamos com Lucro Operacional)
    ebit = dados.get('lucro_operacional', 0) or dados.get('lucro_liquido', 0) or 0
    x3 = ebit / at
    
    # X4: Patrimônio Líquido / Passivo Total
    pl = dados.get('patrimonio_liquido', 0) or 0
    x4 = pl / pt if pt > 0 else 0
    
    # X5: Receita / Ativo Total
    receita = dados.get('receita', 0) or dados.get('receita_bruta', 0) or 0
    x5 = receita / at
    
    # Z-Score
    z = 0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5
    
    # Classificação
    if z > 2.9:
        risco = "Baixo"
    elif z > 1.23:
        risco = "Moderado"
    else:
        risco = "Alto"
    
    return round(z, 2), risco


def calcular_tendencia(valores: List[float]) -> Tuple[float, float, str]:
    """
    Calcula tendência usando regressão linear.
    
    Retorna:
    - taxa_mensal: variação percentual média por mês
    - r_squared: coeficiente de determinação (confiança)
    - direcao: 'crescente', 'estavel', 'decrescente'
    """
    if len(valores) < 3:
        return 0, 0, 'indefinida'
    
    n = len(valores)
    x = np.arange(n)
    y = np.array(valores)
    
    # Regressão linear
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Taxa mensal (%)
    media = np.mean(y)
    taxa_mensal = (slope / media * 100) if media > 0 else 0
    
    # Direção
    if taxa_mensal > 1:
        direcao = 'crescente'
    elif taxa_mensal < -1:
        direcao = 'decrescente'
    else:
        direcao = 'estavel'
    
    return round(taxa_mensal, 2), round(r_value ** 2, 2), direcao


def calcular_score_profissional(
    dados_mensais: List[Dict],
    setor: str = "geral",
    dados_balanco: Dict = None
) -> ScoreProfissional:
    """
    Calcula score profissional completo.
    
    Args:
        dados_mensais: Lista de dicionários com dados mensais
        setor: Código do setor (ex: 'comercio_varejo', 'servicos')
        dados_balanco: Dados do balanço patrimonial (opcional)
    
    Returns:
        ScoreProfissional com todas as métricas
    """
    if not dados_mensais:
        return ScoreProfissional(
            score_final=0,
            classificacao="E",
            status="Sem dados",
            confianca=0
        )
    
    # Benchmark do setor
    bench = BENCHMARKS.get(setor, BENCHMARKS['geral'])
    pesos = bench.get('pesos', {"rentabilidade": 0.25, "liquidez": 0.25, "endividamento": 0.25, "eficiencia": 0.25})
    
    # Ordenar dados
    dados = sorted(dados_mensais, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))
    n = len(dados)
    ultimo = dados[-1]
    
    # Criar resultado
    resultado = ScoreProfissional(
        setor=bench.get('nome', 'Geral'),
        meses_analisados=n
    )
    
    pontos_fortes = []
    pontos_atencao = []
    recomendacoes = []
    
    # =========================================================================
    # 1. SCORE DE RENTABILIDADE
    # =========================================================================
    receitas = [d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados]
    custos = [d.get('custos', 0) or 0 for d in dados]
    despesas = [d.get('despesas', 0) or 0 for d in dados]
    impostos = [d.get('impostos', 0) or 0 for d in dados]
    folhas = [d.get('folha', 0) or 0 for d in dados]
    
    receita_total = sum(receitas)
    custo_total = sum(custos)
    despesa_total = sum(despesas)
    imposto_total = sum(impostos)
    folha_total = sum(folhas)
    
    lucro_bruto = receita_total - custo_total
    lucro_liquido = receita_total - custo_total - despesa_total - imposto_total - folha_total
    
    margem_bruta = (lucro_bruto / receita_total * 100) if receita_total > 0 else 0
    margem_liquida = (lucro_liquido / receita_total * 100) if receita_total > 0 else 0
    
    # Score de rentabilidade usando benchmark
    score_margem_bruta = calcular_score_relativo(margem_bruta, bench['margem_bruta'])
    score_margem_liquida = calcular_score_relativo(margem_liquida, bench['margem_liquida'])
    resultado.score_rentabilidade = int((score_margem_bruta + score_margem_liquida) / 2)
    
    if margem_liquida >= bench['margem_liquida']['media']:
        pontos_fortes.append(f"Margem líquida de {margem_liquida:.1f}% está acima da média do setor")
    elif margem_liquida < bench['margem_liquida']['min']:
        pontos_atencao.append(f"Margem líquida de {margem_liquida:.1f}% está abaixo do mínimo saudável para o setor")
        recomendacoes.append("Analisar estrutura de custos e precificação")
    
    # =========================================================================
    # 2. SCORE DE LIQUIDEZ
    # =========================================================================
    # Usar dados do balanço se disponíveis, senão estimar
    if dados_balanco:
        ac = dados_balanco.get('ativo_circulante', 0)
        pc = dados_balanco.get('passivo_circulante', 0)
    else:
        ac = ultimo.get('ativo_circulante', 0) or ultimo.get('caixa', 0)
        pc = ultimo.get('passivo_circulante', 0)
    
    liquidez_corrente = ac / pc if pc > 0 else 0
    
    resultado.score_liquidez = calcular_score_relativo(liquidez_corrente, bench['liquidez_corrente'])
    
    if liquidez_corrente >= bench['liquidez_corrente']['media']:
        pontos_fortes.append(f"Liquidez corrente de {liquidez_corrente:.2f} está adequada para o setor")
    elif liquidez_corrente < bench['liquidez_corrente']['min']:
        pontos_atencao.append(f"Liquidez corrente de {liquidez_corrente:.2f} está crítica")
        recomendacoes.append("Priorizar gestão de capital de giro e negociação com fornecedores")
    
    # =========================================================================
    # 3. SCORE DE ENDIVIDAMENTO
    # =========================================================================
    if dados_balanco:
        at = dados_balanco.get('ativo_total', 0)
        pt = dados_balanco.get('passivo_total', 0)
        pl = dados_balanco.get('patrimonio_liquido', 0)
    else:
        at = ultimo.get('ativo_total', 0)
        pt = ultimo.get('passivo_total', 0)
        pl = ultimo.get('patrimonio_liquido', 0)
    
    endividamento = (pt / at * 100) if at > 0 else 0
    
    resultado.score_endividamento = calcular_score_inverso(endividamento, bench['endividamento'])
    
    if endividamento <= bench['endividamento']['media']:
        pontos_fortes.append(f"Endividamento de {endividamento:.1f}% está controlado")
    elif endividamento > bench['endividamento']['max']:
        pontos_atencao.append(f"Endividamento de {endividamento:.1f}% está muito elevado")
        recomendacoes.append("Avaliar renegociação de dívidas ou aporte de capital")
    
    # =========================================================================
    # 4. SCORE DE EFICIÊNCIA
    # =========================================================================
    # Giro do ativo
    giro_ativo = receita_total / at if at > 0 else 0
    
    # Produtividade da folha
    prod_folha = receita_total / folha_total if folha_total > 0 else 0
    
    # Score de eficiência (normalizado)
    score_giro = min(100, int(giro_ativo * 20))  # Giro de 5x = 100 pontos
    score_prod = min(100, int(prod_folha / 5 * 100))  # R$5 receita por R$1 folha = 100 pontos
    resultado.score_eficiencia = int((score_giro + score_prod) / 2)
    
    if giro_ativo >= 2:
        pontos_fortes.append(f"Boa eficiência operacional com giro do ativo de {giro_ativo:.1f}x")
    elif giro_ativo < 1:
        pontos_atencao.append("Baixa eficiência no uso dos ativos")
        recomendacoes.append("Avaliar ativos ociosos ou subutilizados")
    
    # =========================================================================
    # 5. SCORE DE TENDÊNCIA
    # =========================================================================
    taxa_receita, r2_receita, dir_receita = calcular_tendencia(receitas)
    
    lucros = []
    for d in dados:
        rec = d.get('receita', 0) or 0
        cus = d.get('custos', 0) or 0
        des = d.get('despesas', 0) or 0
        imp = d.get('impostos', 0) or 0
        fol = d.get('folha', 0) or 0
        lucros.append(rec - cus - des - imp - fol)
    
    taxa_lucro, r2_lucro, dir_lucro = calcular_tendencia(lucros)
    
    # Score de tendência
    if dir_receita == 'crescente' and dir_lucro == 'crescente':
        resultado.score_tendencia = 90
        pontos_fortes.append(f"Receita e lucro em crescimento ({taxa_receita:+.1f}%/mês)")
    elif dir_receita == 'crescente':
        resultado.score_tendencia = 70
        pontos_fortes.append(f"Receita crescendo {taxa_receita:+.1f}%/mês")
    elif dir_receita == 'estavel' and dir_lucro != 'decrescente':
        resultado.score_tendencia = 50
    elif dir_receita == 'decrescente' or dir_lucro == 'decrescente':
        resultado.score_tendencia = 30
        pontos_atencao.append(f"Tendência de queda na receita ({taxa_receita:+.1f}%/mês)")
        recomendacoes.append("Investigar causas da queda e desenvolver plano de ação")
    else:
        resultado.score_tendencia = 50
    
    # =========================================================================
    # 6. Z-SCORE DE ALTMAN
    # =========================================================================
    dados_zscore = {
        'ativo_total': at,
        'passivo_total': pt,
        'ativo_circulante': ac,
        'passivo_circulante': pc,
        'patrimonio_liquido': pl,
        'lucro_liquido': lucro_liquido / n if n > 0 else 0,  # Anualizado
        'lucro_operacional': (lucro_liquido + imposto_total) / n if n > 0 else 0,
        'lucros_acumulados': pl * 0.3 if pl > 0 else 0,  # Estimativa
        'receita': receita_total / n * 12 if n > 0 else 0  # Anualizado
    }
    
    resultado.zscore_altman, resultado.risco_falencia = calcular_zscore_altman(dados_zscore)
    
    if resultado.risco_falencia == "Alto":
        pontos_atencao.append(f"Z-Score de Altman ({resultado.zscore_altman}) indica risco elevado de insolvência")
        recomendacoes.append("URGENTE: Avaliar reestruturação financeira")
    elif resultado.risco_falencia == "Baixo":
        pontos_fortes.append(f"Z-Score de Altman ({resultado.zscore_altman}) indica baixo risco de insolvência")
    
    # =========================================================================
    # SCORE FINAL PONDERADO
    # =========================================================================
    score_base = (
        resultado.score_rentabilidade * pesos['rentabilidade'] +
        resultado.score_liquidez * pesos['liquidez'] +
        resultado.score_endividamento * pesos['endividamento'] +
        resultado.score_eficiencia * pesos['eficiencia']
    )
    
    # Ajuste por tendência (±15%)
    ajuste_tendencia = (resultado.score_tendencia - 50) / 50 * 15
    
    # Ajuste por Z-Score (±10%)
    if resultado.risco_falencia == "Baixo":
        ajuste_zscore = 10
    elif resultado.risco_falencia == "Alto":
        ajuste_zscore = -10
    else:
        ajuste_zscore = 0
    
    resultado.score_final = int(max(0, min(100, score_base + ajuste_tendencia + ajuste_zscore)))
    
    # =========================================================================
    # CLASSIFICAÇÃO
    # =========================================================================
    if resultado.score_final >= 85:
        resultado.classificacao = "A"
        resultado.status = "Excelente"
        resultado.posicao_setor = "Acima da média"
    elif resultado.score_final >= 70:
        resultado.classificacao = "B"
        resultado.status = "Bom"
        resultado.posicao_setor = "Acima da média"
    elif resultado.score_final >= 55:
        resultado.classificacao = "C"
        resultado.status = "Regular"
        resultado.posicao_setor = "Na média"
    elif resultado.score_final >= 40:
        resultado.classificacao = "D"
        resultado.status = "Atenção"
        resultado.posicao_setor = "Abaixo da média"
    else:
        resultado.classificacao = "E"
        resultado.status = "Crítico"
        resultado.posicao_setor = "Muito abaixo da média"
    
    # Percentil estimado (simplificado)
    resultado.percentil_setor = min(99, max(1, resultado.score_final))
    
    # =========================================================================
    # CONFIANÇA
    # =========================================================================
    # Baseado em: quantidade de dados, R² das tendências, completude dos dados
    confianca_qtd = min(100, n * 8)  # 12+ meses = 100%
    confianca_r2 = int((r2_receita + r2_lucro) / 2 * 100)
    confianca_dados = 100 if at > 0 and pt > 0 and pl != 0 else 60
    
    resultado.confianca = int((confianca_qtd + confianca_r2 + confianca_dados) / 3)
    
    # =========================================================================
    # RECOMENDAÇÕES FINAIS
    # =========================================================================
    if resultado.score_final >= 70 and not recomendacoes:
        recomendacoes.append("Manter práticas atuais de gestão financeira")
        recomendacoes.append("Considerar investimentos para crescimento")
    
    resultado.pontos_fortes = pontos_fortes
    resultado.pontos_atencao = pontos_atencao
    resultado.recomendacoes = recomendacoes
    
    return resultado


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def detectar_setor(dados_empresa: Dict) -> str:
    """Detecta setor baseado em palavras-chave."""
    setor_texto = (dados_empresa.get('setor', '') or '').lower()
    regime = (dados_empresa.get('regime_tributario', '') or '').lower()
    
    mapeamento = {
        'varejo': 'comercio_varejo',
        'loja': 'comercio_varejo',
        'atacado': 'comercio_atacado',
        'distribuidor': 'comercio_atacado',
        'serviço': 'servicos',
        'consultoria': 'servicos',
        'indústria': 'industria',
        'fábrica': 'industria',
        'manufatura': 'industria',
        'software': 'tecnologia',
        'tech': 'tecnologia',
        'ti': 'tecnologia',
        'restaurante': 'restaurante',
        'alimenta': 'restaurante',
        'bar': 'restaurante',
        'saúde': 'saude',
        'clínica': 'saude',
        'médic': 'saude',
        'constru': 'construcao',
        'obra': 'construcao',
        'transport': 'transporte',
        'logística': 'transporte',
        'frete': 'transporte',
        'escola': 'educacao',
        'educa': 'educacao',
        'curso': 'educacao',
    }
    
    for palavra, setor in mapeamento.items():
        if palavra in setor_texto:
            return setor
    
    return 'geral'


# =============================================================================
# TESTE
# =============================================================================

if __name__ == '__main__':
    # Dados de teste
    dados_teste = [
        {'ano': 2024, 'mes': 1, 'receita': 100000, 'custos': 45000, 'despesas': 20000, 'impostos': 10000, 'folha': 18000, 'caixa': 50000},
        {'ano': 2024, 'mes': 2, 'receita': 105000, 'custos': 47000, 'despesas': 21000, 'impostos': 10500, 'folha': 18000, 'caixa': 55000},
        {'ano': 2024, 'mes': 3, 'receita': 110000, 'custos': 49000, 'despesas': 22000, 'impostos': 11000, 'folha': 18500, 'caixa': 60000},
        {'ano': 2024, 'mes': 4, 'receita': 108000, 'custos': 48000, 'despesas': 21500, 'impostos': 10800, 'folha': 18500, 'caixa': 58000},
        {'ano': 2024, 'mes': 5, 'receita': 115000, 'custos': 51000, 'despesas': 23000, 'impostos': 11500, 'folha': 19000, 'caixa': 62000},
        {'ano': 2024, 'mes': 6, 'receita': 120000, 'custos': 54000, 'despesas': 24000, 'impostos': 12000, 'folha': 19000, 'caixa': 65000},
    ]
    
    balanco = {
        'ativo_total': 500000,
        'ativo_circulante': 200000,
        'passivo_total': 280000,
        'passivo_circulante': 150000,
        'patrimonio_liquido': 220000,
    }
    
    resultado = calcular_score_profissional(dados_teste, 'servicos', balanco)
    
    print(f"\n{'='*60}")
    print(f"SCORE PROFISSIONAL KONTABIL v2.0")
    print(f"{'='*60}")
    print(f"\nSCORE FINAL: {resultado.score_final}/100 ({resultado.classificacao})")
    print(f"Status: {resultado.status}")
    print(f"Posição no setor ({resultado.setor}): {resultado.posicao_setor}")
    print(f"\n--- Scores por Dimensão ---")
    print(f"Rentabilidade: {resultado.score_rentabilidade}/100")
    print(f"Liquidez: {resultado.score_liquidez}/100")
    print(f"Endividamento: {resultado.score_endividamento}/100")
    print(f"Eficiência: {resultado.score_eficiencia}/100")
    print(f"Tendência: {resultado.score_tendencia}/100")
    print(f"\n--- Z-Score de Altman ---")
    print(f"Z-Score: {resultado.zscore_altman}")
    print(f"Risco de Falência: {resultado.risco_falencia}")
    print(f"\n--- Confiança ---")
    print(f"Nível de Confiança: {resultado.confianca}%")
    print(f"Meses Analisados: {resultado.meses_analisados}")
    print(f"\n--- Pontos Fortes ---")
    for p in resultado.pontos_fortes:
        print(f"  ✓ {p}")
    print(f"\n--- Pontos de Atenção ---")
    for p in resultado.pontos_atencao:
        print(f"  ⚠ {p}")
    print(f"\n--- Recomendações ---")
    for r in resultado.recomendacoes:
        print(f"  → {r}")
