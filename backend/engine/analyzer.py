#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Engine de Análise Contábil com Machine Learning

4 Pilares de Análise:
1. Tendência de Faturamento (Crescimento / Estagnação / Queda)
2. Risco de Caixa (Burn rate, Runway, Meses até aperto)
3. Anomalias Financeiras (Custos, Margem, Impostos)
4. Probabilidade de Problemas (Prejuízo, Quebra, Imposto inesperado)
"""

import numpy as np
from scipy import stats
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

from data.csv_importer import CompanyData, MonthlyRecord


class TendenciaFaturamento(str, Enum):
    CRESCIMENTO_FORTE = "Crescimento Forte"
    CRESCIMENTO_MODERADO = "Crescimento Moderado"
    ESTAGNACAO = "Estagnação"
    QUEDA_MODERADA = "Queda Moderada"
    QUEDA_FORTE = "Queda Forte"


class NivelRisco(str, Enum):
    CRITICO = "Crítico"
    ALTO = "Alto"
    MODERADO = "Moderado"
    BAIXO = "Baixo"
    MINIMO = "Mínimo"


class TipoAnomalia(str, Enum):
    CUSTO_ELEVADO = "Custos acima do padrão"
    MARGEM_COMPRIMIDA = "Margem em queda"
    IMPOSTO_DESCOLADO = "Impostos descolados do faturamento"
    DESPESA_ATIPICA = "Despesa atípica"


@dataclass
class AnaliseTendencia:
    """Resultado da análise de tendência."""
    tendencia: str
    direcao: str  # 'up', 'down', 'stable'
    taxa_mensal: float
    taxa_anual_projetada: float
    r_squared: float
    confianca: float
    faturamento_atual: float
    faturamento_projetado_12m: float
    variacao_6m: float
    variacao_3m: float
    meses_analisados: int
    descricao: str
    recomendacao: str


@dataclass
class AnaliseRiscoCaixa:
    """Resultado da análise de risco de caixa."""
    nivel: str
    saldo_atual: float
    burn_rate: float
    runway_meses: int
    meses_ate_aperto: int
    tendencia_caixa: str
    liquidez_corrente: float
    capital_giro: float
    confianca: float
    descricao: str
    recomendacao: str


@dataclass
class Anomalia:
    """Uma anomalia detectada."""
    tipo: str
    severidade: str
    mes: str
    valor_detectado: float
    valor_esperado: float
    desvio_percentual: float
    descricao: str
    impacto: float


@dataclass
class AnaliseAnomalias:
    """Resultado da análise de anomalias."""
    total: int
    anomalias: List[Dict]
    impacto_total: float
    tendencia_custos: str
    tendencia_margem: str
    comportamento_impostos: str
    descricao: str


@dataclass
class AnaliseProbabilidades:
    """Probabilidades de problemas."""
    prob_prejuizo: float
    prob_quebra: float
    prob_imposto: float
    risco_prejuizo: str
    risco_quebra: str
    risco_imposto: str
    score_saude: float
    fatores_risco: List[str]
    fatores_positivos: List[str]
    descricao: str
    recomendacao: str


@dataclass
class ResultadoAnalise:
    """Resultado completo da análise."""
    # Metadata
    empresa: str
    cnpj: str
    periodo_inicio: str
    periodo_fim: str
    data_analise: str
    meses_analisados: int
    
    # Score geral
    score: int
    status: str  # 'saudavel', 'atencao', 'critico'
    
    # 4 Pilares
    tendencia: Dict
    risco_caixa: Dict
    anomalias: Dict
    probabilidades: Dict
    
    # Resumo financeiro
    faturamento_total: float
    faturamento_medio: float
    lucro_total: float
    margem_media: float
    
    # Dados para gráficos
    dados_mensais: List[Dict]
    
    # Recomendação principal
    recomendacao_principal: str


class ContabilAnalyzer:
    """Engine principal de análise."""
    
    def __init__(self):
        self.anomalia_threshold = 2.0  # Desvios padrão
        self.caixa_critico_meses = 3
    
    def analyze(self, data: CompanyData) -> ResultadoAnalise:
        """Executa análise completa."""
        
        if len(data.records) < 3:
            raise ValueError("Necessário pelo menos 3 meses de dados")
        
        # Executa os 4 pilares
        tendencia = self._analyze_tendencia(data)
        risco_caixa = self._analyze_risco_caixa(data)
        anomalias = self._analyze_anomalias(data)
        probabilidades = self._analyze_probabilidades(data, tendencia, risco_caixa, anomalias)
        
        # Calcula score geral
        score = int(probabilidades.score_saude)
        if score >= 70:
            status = 'saudavel'
        elif score >= 40:
            status = 'atencao'
        else:
            status = 'critico'
        
        # Dados mensais para gráficos
        dados_mensais = []
        for r in data.records:
            dados_mensais.append({
                'periodo': r.periodo,
                'receita': r.receita,
                'lucro': r.lucro_liquido,
                'margem': r.margem_liquida,
                'caixa': r.caixa,
                'custos_pct': (r.custos / r.receita * 100) if r.receita > 0 else 0,
                'impostos_pct': r.carga_tributaria,
            })
        
        # Margem média
        margens = [r.margem_liquida for r in data.records]
        margem_media = np.mean(margens) if margens else 0
        
        return ResultadoAnalise(
            empresa=data.empresa,
            cnpj=data.cnpj,
            periodo_inicio=data.periodo_inicio.strftime('%Y-%m') if data.periodo_inicio else '',
            periodo_fim=data.periodo_fim.strftime('%Y-%m') if data.periodo_fim else '',
            data_analise=datetime.now().strftime('%Y-%m-%d %H:%M'),
            meses_analisados=len(data.records),
            score=score,
            status=status,
            tendencia=asdict(tendencia),
            risco_caixa=asdict(risco_caixa),
            anomalias=asdict(anomalias),
            probabilidades=asdict(probabilidades),
            faturamento_total=data.faturamento_total,
            faturamento_medio=data.faturamento_medio,
            lucro_total=data.lucro_total,
            margem_media=margem_media,
            dados_mensais=dados_mensais,
            recomendacao_principal=probabilidades.recomendacao,
        )
    
    def _analyze_tendencia(self, data: CompanyData) -> AnaliseTendencia:
        """Análise de tendência de faturamento com regressão linear."""
        records = data.records
        n = len(records)
        
        receitas = np.array([r.receita for r in records])
        x = np.arange(n)
        
        # Regressão linear
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, receitas)
        
        # Taxa mensal
        media = np.mean(receitas)
        taxa_mensal = (slope / media * 100) if media > 0 else 0
        
        # Taxa anual projetada
        taxa_anual = ((1 + taxa_mensal/100) ** 12 - 1) * 100
        
        # Variações recentes
        var_6m = ((receitas[-1] / receitas[-min(6, n)]) - 1) * 100 if n > 1 else 0
        var_3m = ((receitas[-1] / receitas[-min(3, n)]) - 1) * 100 if n > 1 else 0
        
        # Classificação
        if taxa_mensal > 3:
            tendencia = TendenciaFaturamento.CRESCIMENTO_FORTE
            direcao = 'up'
        elif taxa_mensal > 0.5:
            tendencia = TendenciaFaturamento.CRESCIMENTO_MODERADO
            direcao = 'up'
        elif taxa_mensal > -0.5:
            tendencia = TendenciaFaturamento.ESTAGNACAO
            direcao = 'stable'
        elif taxa_mensal > -3:
            tendencia = TendenciaFaturamento.QUEDA_MODERADA
            direcao = 'down'
        else:
            tendencia = TendenciaFaturamento.QUEDA_FORTE
            direcao = 'down'
        
        # Projeção 12 meses
        fat_projetado = receitas[-1] * ((1 + taxa_mensal/100) ** 12)
        
        # Confiança
        confianca = min(95, max(30, r_value**2 * 100))
        
        # Descrição
        if direcao == 'up':
            descricao = f"Faturamento em crescimento de {taxa_mensal:+.1f}% ao mês. Variação de {var_6m:+.1f}% nos últimos 6 meses."
            recomendacao = "Manter estratégia atual. Preparar estrutura para suportar crescimento."
        elif direcao == 'stable':
            descricao = f"Faturamento estagnado ({taxa_mensal:+.1f}% ao mês). Pode indicar saturação de mercado."
            recomendacao = "Revisar estratégia comercial e mix de produtos."
        else:
            descricao = f"Faturamento em queda de {abs(taxa_mensal):.1f}% ao mês. Variação de {var_6m:.1f}% nos últimos 6 meses."
            recomendacao = "AÇÃO URGENTE: Identificar causas da queda. Adequar custos ao novo patamar."
        
        return AnaliseTendencia(
            tendencia=tendencia.value,
            direcao=direcao,
            taxa_mensal=round(taxa_mensal, 2),
            taxa_anual_projetada=round(taxa_anual, 2),
            r_squared=round(r_value**2, 3),
            confianca=round(confianca, 1),
            faturamento_atual=round(receitas[-1], 2),
            faturamento_projetado_12m=round(fat_projetado, 2),
            variacao_6m=round(var_6m, 2),
            variacao_3m=round(var_3m, 2),
            meses_analisados=n,
            descricao=descricao,
            recomendacao=recomendacao,
        )
    
    def _analyze_risco_caixa(self, data: CompanyData) -> AnaliseRiscoCaixa:
        """Análise de risco de caixa."""
        records = data.records
        n = len(records)
        
        saldo_atual = records[-1].caixa
        
        # Burn rate
        variacoes = []
        for i in range(1, n):
            variacoes.append(records[i].caixa - records[i-1].caixa)
        
        burn_rate = np.mean(variacoes) if variacoes else 0
        
        # Runway
        if burn_rate < 0 and saldo_atual > 0:
            runway = int(saldo_atual / abs(burn_rate))
            despesa_media = np.mean([r.despesas_totais + r.custos for r in records])
            caixa_critico = despesa_media * self.caixa_critico_meses
            meses_ate_aperto = max(0, int((saldo_atual - caixa_critico) / abs(burn_rate)))
            tendencia_caixa = "caindo"
        else:
            runway = 999
            meses_ate_aperto = 999
            tendencia_caixa = "crescendo" if burn_rate > 0 else "estavel"
        
        # Liquidez
        r = records[-1]
        ativo_circ = r.caixa
        passivo_circ = r.custos * 0.3  # Estimativa
        liquidez = ativo_circ / passivo_circ if passivo_circ > 0 else 999
        capital_giro = ativo_circ - passivo_circ
        
        # Nível de risco
        if runway < 3 or meses_ate_aperto < 1:
            nivel = NivelRisco.CRITICO
        elif runway < 6 or meses_ate_aperto < 3:
            nivel = NivelRisco.ALTO
        elif runway < 12 or meses_ate_aperto < 6:
            nivel = NivelRisco.MODERADO
        elif burn_rate < 0:
            nivel = NivelRisco.BAIXO
        else:
            nivel = NivelRisco.MINIMO
        
        # Descrição
        if nivel in [NivelRisco.CRITICO, NivelRisco.ALTO]:
            descricao = f"Consumindo R$ {abs(burn_rate):,.0f}/mês. Runway de {min(runway, 99)} meses."
            recomendacao = "AÇÃO IMEDIATA: Buscar capital, renegociar prazos, cortar custos."
        elif burn_rate < 0:
            descricao = f"Consumo de R$ {abs(burn_rate):,.0f}/mês, mas com margem de {min(runway, 99)} meses."
            recomendacao = "Monitorar evolução e buscar reverter queima de caixa."
        else:
            descricao = f"Caixa saudável com saldo de R$ {saldo_atual:,.0f} e geração positiva."
            recomendacao = "Manter política atual. Avaliar aplicação de excedentes."
        
        return AnaliseRiscoCaixa(
            nivel=nivel.value,
            saldo_atual=round(saldo_atual, 2),
            burn_rate=round(burn_rate, 2),
            runway_meses=min(runway, 999),
            meses_ate_aperto=min(meses_ate_aperto, 999),
            tendencia_caixa=tendencia_caixa,
            liquidez_corrente=round(liquidez, 2),
            capital_giro=round(capital_giro, 2),
            confianca=85 if n >= 12 else 70,
            descricao=descricao,
            recomendacao=recomendacao,
        )
    
    def _analyze_anomalias(self, data: CompanyData) -> AnaliseAnomalias:
        """Detecta anomalias financeiras."""
        records = data.records
        n = len(records)
        anomalias = []
        
        # Arrays
        custos_pct = np.array([(r.custos/r.receita*100) if r.receita > 0 else 0 for r in records])
        margens = np.array([r.margem_liquida for r in records])
        impostos_pct = np.array([r.carga_tributaria for r in records])
        
        # Detecta custos anormais
        custo_mean, custo_std = np.mean(custos_pct), np.std(custos_pct)
        for i, (r, c) in enumerate(zip(records, custos_pct)):
            if custo_std > 0 and c > custo_mean + self.anomalia_threshold * custo_std:
                desvio = ((c - custo_mean) / custo_mean * 100) if custo_mean > 0 else 0
                impacto = r.receita * (c - custo_mean) / 100
                anomalias.append(Anomalia(
                    tipo=TipoAnomalia.CUSTO_ELEVADO.value,
                    severidade=NivelRisco.ALTO.value if desvio > 20 else NivelRisco.MODERADO.value,
                    mes=r.periodo,
                    valor_detectado=round(c, 1),
                    valor_esperado=round(custo_mean, 1),
                    desvio_percentual=round(desvio, 1),
                    descricao=f"Custos em {r.periodo}: {c:.1f}% vs média {custo_mean:.1f}%",
                    impacto=round(impacto, 2),
                ))
        
        # Detecta margens anormais
        marg_mean, marg_std = np.mean(margens), np.std(margens)
        for i, (r, m) in enumerate(zip(records, margens)):
            if marg_std > 0 and m < marg_mean - self.anomalia_threshold * marg_std:
                desvio = ((m - marg_mean) / abs(marg_mean) * 100) if marg_mean != 0 else 0
                impacto = r.receita * abs(m - marg_mean) / 100
                anomalias.append(Anomalia(
                    tipo=TipoAnomalia.MARGEM_COMPRIMIDA.value,
                    severidade=NivelRisco.ALTO.value if m < 0 else NivelRisco.MODERADO.value,
                    mes=r.periodo,
                    valor_detectado=round(m, 1),
                    valor_esperado=round(marg_mean, 1),
                    desvio_percentual=round(desvio, 1),
                    descricao=f"Margem em {r.periodo}: {m:.1f}% vs média {marg_mean:.1f}%",
                    impacto=round(impacto, 2),
                ))
        
        # Detecta impostos anormais
        imp_mean, imp_std = np.mean(impostos_pct), np.std(impostos_pct)
        for i, (r, imp) in enumerate(zip(records, impostos_pct)):
            if imp_std > 0 and imp > imp_mean + self.anomalia_threshold * imp_std:
                desvio = ((imp - imp_mean) / imp_mean * 100) if imp_mean > 0 else 0
                impacto = r.receita * (imp - imp_mean) / 100
                anomalias.append(Anomalia(
                    tipo=TipoAnomalia.IMPOSTO_DESCOLADO.value,
                    severidade=NivelRisco.ALTO.value if desvio > 30 else NivelRisco.MODERADO.value,
                    mes=r.periodo,
                    valor_detectado=round(imp, 1),
                    valor_esperado=round(imp_mean, 1),
                    desvio_percentual=round(desvio, 1),
                    descricao=f"Impostos em {r.periodo}: {imp:.1f}% vs média {imp_mean:.1f}%",
                    impacto=round(impacto, 2),
                ))
        
        # Tendências (últimos 6 meses)
        if n >= 6:
            x = np.arange(6)
            slope_custo, _, r_c, _, _ = stats.linregress(x, custos_pct[-6:])
            slope_marg, _, r_m, _, _ = stats.linregress(x, margens[-6:])
            
            if slope_custo > 0.3 and r_c**2 > 0.3:
                tendencia_custos = f"ALERTA: Custos subindo {slope_custo:.2f}pp/mês"
            elif slope_custo < -0.3:
                tendencia_custos = f"Custos caindo {abs(slope_custo):.2f}pp/mês"
            else:
                tendencia_custos = "Custos estáveis"
            
            if slope_marg < -0.3 and r_m**2 > 0.3:
                tendencia_margem = f"ALERTA: Margem caindo {abs(slope_marg):.2f}pp/mês"
            elif slope_marg > 0.3:
                tendencia_margem = f"Margem subindo {slope_marg:.2f}pp/mês"
            else:
                tendencia_margem = "Margem estável"
        else:
            tendencia_custos = "Dados insuficientes"
            tendencia_margem = "Dados insuficientes"
        
        # Impostos
        cv_imp = (imp_std / imp_mean * 100) if imp_mean > 0 else 0
        if cv_imp > 20:
            comportamento_impostos = f"ATENÇÃO: Alta variabilidade (CV={cv_imp:.0f}%)"
        else:
            comportamento_impostos = f"Regular (CV={cv_imp:.0f}%)"
        
        # Impacto total
        impacto_total = sum(a.impacto for a in anomalias)
        
        # Descrição
        if not anomalias:
            descricao = "Nenhuma anomalia significativa detectada."
        else:
            descricao = f"{len(anomalias)} anomalia(s) com impacto de R$ {impacto_total:,.0f}"
        
        return AnaliseAnomalias(
            total=len(anomalias),
            anomalias=[asdict(a) for a in anomalias],
            impacto_total=round(impacto_total, 2),
            tendencia_custos=tendencia_custos,
            tendencia_margem=tendencia_margem,
            comportamento_impostos=comportamento_impostos,
            descricao=descricao,
        )
    
    def _analyze_probabilidades(
        self,
        data: CompanyData,
        tendencia: AnaliseTendencia,
        risco_caixa: AnaliseRiscoCaixa,
        anomalias: AnaliseAnomalias
    ) -> AnaliseProbabilidades:
        """Calcula probabilidades de problemas."""
        records = data.records
        n = len(records)
        fatores_risco = []
        fatores_positivos = []
        
        # Dados
        lucros = [r.lucro_liquido for r in records]
        meses_prejuizo = sum(1 for l in lucros[-6:] if l < 0)
        margem_atual = records[-1].margem_liquida
        
        # PROB PREJUÍZO
        prob_prejuizo = 10
        if meses_prejuizo >= 3:
            prob_prejuizo += 40
            fatores_risco.append(f"{meses_prejuizo} meses com prejuízo recente")
        elif meses_prejuizo >= 1:
            prob_prejuizo += 20
            fatores_risco.append(f"{meses_prejuizo} mês(es) com prejuízo")
        
        if tendencia.direcao == 'down':
            prob_prejuizo += 25 if 'Forte' in tendencia.tendencia else 15
            fatores_risco.append("Faturamento em queda")
        
        if margem_atual < 0:
            prob_prejuizo += 20
            fatores_risco.append("Margem negativa no último mês")
        elif margem_atual < 5:
            prob_prejuizo += 10
            fatores_risco.append("Margem muito baixa")
        
        if tendencia.direcao == 'up':
            prob_prejuizo -= 15
            fatores_positivos.append("Faturamento em crescimento")
        
        if margem_atual > 10:
            fatores_positivos.append("Margem líquida saudável")
        
        prob_prejuizo = max(5, min(95, prob_prejuizo))
        
        # PROB QUEBRA
        prob_quebra = 5
        if risco_caixa.nivel == NivelRisco.CRITICO.value:
            prob_quebra += 50
            fatores_risco.append("Risco de caixa crítico")
        elif risco_caixa.nivel == NivelRisco.ALTO.value:
            prob_quebra += 30
            fatores_risco.append("Risco de caixa alto")
        elif risco_caixa.nivel == NivelRisco.MODERADO.value:
            prob_quebra += 15
        
        if risco_caixa.runway_meses < 6:
            prob_quebra += 20
            fatores_risco.append(f"Runway de apenas {risco_caixa.runway_meses} meses")
        
        if risco_caixa.liquidez_corrente < 1:
            prob_quebra += 15
            fatores_risco.append("Liquidez abaixo de 1")
        
        if risco_caixa.tendencia_caixa == "crescendo":
            prob_quebra -= 20
            fatores_positivos.append("Caixa em crescimento")
        
        if risco_caixa.liquidez_corrente > 2:
            fatores_positivos.append("Boa liquidez corrente")
        
        prob_quebra = max(2, min(90, prob_quebra))
        
        # PROB IMPOSTO
        impostos = [r.carga_tributaria for r in records]
        cv = (np.std(impostos) / np.mean(impostos) * 100) if np.mean(impostos) > 0 else 0
        
        prob_imposto = 10
        if cv > 30:
            prob_imposto += 30
            fatores_risco.append("Alta variabilidade tributária")
        elif cv > 20:
            prob_imposto += 15
        
        anomalias_imp = [a for a in anomalias.anomalias if 'Imposto' in a.get('tipo', '')]
        if len(anomalias_imp) >= 2:
            prob_imposto += 25
            fatores_risco.append("Múltiplas anomalias de impostos")
        elif len(anomalias_imp) == 1:
            prob_imposto += 10
        
        prob_imposto = max(5, min(85, prob_imposto))
        
        # CLASSIFICAÇÃO
        def classify(p):
            if p >= 70: return NivelRisco.CRITICO.value
            if p >= 50: return NivelRisco.ALTO.value
            if p >= 30: return NivelRisco.MODERADO.value
            if p >= 15: return NivelRisco.BAIXO.value
            return NivelRisco.MINIMO.value
        
        # SCORE
        score = 100
        score -= prob_prejuizo * 0.3
        score -= prob_quebra * 0.4
        score -= prob_imposto * 0.1
        score += len(fatores_positivos) * 5
        score -= anomalias.total * 3
        score = max(0, min(100, score))
        
        # DESCRIÇÃO
        if score >= 70:
            descricao = f"Boa saúde financeira (score {score:.0f}/100)."
            recomendacao = "Manter monitoramento regular e práticas de gestão atuais."
        elif score >= 40:
            descricao = f"Saúde financeira moderada (score {score:.0f}/100). Pontos de atenção identificados."
            if prob_prejuizo > prob_quebra:
                recomendacao = "Priorizar melhoria de margens e redução de custos."
            else:
                recomendacao = "Priorizar gestão de caixa e capital de giro."
        else:
            descricao = f"ALERTA: Saúde financeira preocupante (score {score:.0f}/100)."
            recomendacao = "AÇÃO URGENTE: Reunião com sócios para plano de contingência."
        
        return AnaliseProbabilidades(
            prob_prejuizo=round(prob_prejuizo),
            prob_quebra=round(prob_quebra),
            prob_imposto=round(prob_imposto),
            risco_prejuizo=classify(prob_prejuizo),
            risco_quebra=classify(prob_quebra),
            risco_imposto=classify(prob_imposto),
            score_saude=round(score),
            fatores_risco=list(set(fatores_risco)),
            fatores_positivos=list(set(fatores_positivos)),
            descricao=descricao,
            recomendacao=recomendacao,
        )
