"""
Analyzer Profissional - Sistema Contábil
Análise completa usando todos os dados expandidos do balancete

Este módulo integra:
1. Calculadora de indicadores avançados
2. Gerador de insights inteligentes
3. Análise de tendências
4. Detecção de anomalias
5. Projeções e recomendações
"""

import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# Importar calculadora de indicadores
try:
    from engine.importacao_lote import (
        CalculadoraIndicadores,
        GeradorInsights,
        calcular_indicadores,
        gerar_insights,
        calcular_score
    )
    CALCULADORA_DISPONIVEL = True
except ImportError:
    CALCULADORA_DISPONIVEL = False


# ============================================================================
# ENUMS E ESTRUTURAS
# ============================================================================

class StatusSaude(str, Enum):
    CRITICO = "Crítico"
    ATENCAO = "Atenção"
    REGULAR = "Regular"
    BOM = "Bom"
    EXCELENTE = "Excelente"


class TipoTendencia(str, Enum):
    CRESCIMENTO_FORTE = "Crescimento Forte"
    CRESCIMENTO = "Crescimento"
    ESTAVEL = "Estável"
    QUEDA = "Queda"
    QUEDA_FORTE = "Queda Forte"


class CategoriaInsight(str, Enum):
    LIQUIDEZ = "liquidez"
    RENTABILIDADE = "rentabilidade"
    ENDIVIDAMENTO = "endividamento"
    TRIBUTARIO = "tributario"
    CAPITAL_GIRO = "capital_giro"
    OPERACIONAL = "operacional"


@dataclass
class ResultadoAnalise:
    """Resultado completo da análise."""
    # Identificação
    empresa_id: int
    empresa_nome: str
    periodo_analise: str
    periodo_inicio: str = ""
    periodo_fim: str = ""
    meses_analisados: int = 0
    data_analise: datetime = field(default_factory=datetime.now)
    
    # Score geral
    score: int = 50
    status: str = "Regular"
    
    # Indicadores calculados
    indicadores: Dict = field(default_factory=dict)
    
    # Insights e alertas
    insights: List[Dict] = field(default_factory=list)
    alertas_criticos: List[Dict] = field(default_factory=list)
    
    # Análise de tendências
    tendencias: Dict = field(default_factory=dict)
    
    # Comparativo setorial (quando disponível)
    comparativo: Dict = field(default_factory=dict)
    
    # Projeções
    projecoes: Dict = field(default_factory=dict)
    
    # Recomendações priorizadas
    recomendacoes: List[Dict] = field(default_factory=list)
    
    # Resumo executivo
    resumo: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'empresa_id': self.empresa_id,
            'empresa_nome': self.empresa_nome,
            'periodo_analise': self.periodo_analise,
            'periodo_inicio': self.periodo_inicio,
            'periodo_fim': self.periodo_fim,
            'meses_analisados': self.meses_analisados,
            'data_analise': self.data_analise.isoformat(),
            'score': self.score,
            'status': self.status,
            'indicadores': self.indicadores,
            'insights': self.insights,
            'alertas_criticos': self.alertas_criticos,
            'tendencias': self.tendencias,
            'comparativo': self.comparativo,
            'projecoes': self.projecoes,
            'recomendacoes': self.recomendacoes,
            'resumo': self.resumo
        }


# ============================================================================
# ANALYZER PROFISSIONAL
# ============================================================================

class AnalyzerProfissional:
    """
    Analyzer profissional que usa todos os dados expandidos.
    """
    
    def __init__(self):
        self.calculadora = CalculadoraIndicadores() if CALCULADORA_DISPONIVEL else None
        self.gerador_insights = GeradorInsights() if CALCULADORA_DISPONIVEL else None
    
    def analisar(
        self,
        dados_mensais: List[Dict],
        empresa_id: int,
        empresa_nome: str
    ) -> ResultadoAnalise:
        """
        Executa análise completa dos dados.
        
        Args:
            dados_mensais: Lista de dicionários com dados de cada mês
            empresa_id: ID da empresa
            empresa_nome: Nome da empresa
        
        Returns:
            ResultadoAnalise com análise completa
        """
        if not dados_mensais:
            return ResultadoAnalise(
                empresa_id=empresa_id,
                empresa_nome=empresa_nome,
                periodo_analise="Sem dados",
                resumo="Não há dados suficientes para análise."
            )
        
        # Ordenar por competência
        dados_ordenados = sorted(dados_mensais, key=lambda x: x.get('competencia', ''))
        
        # Pegar período
        periodo_inicio = dados_ordenados[0].get('competencia', '')
        periodo_fim = dados_ordenados[-1].get('competencia', '')
        periodo_analise = f"{periodo_inicio} a {periodo_fim}" if periodo_inicio != periodo_fim else periodo_fim
        
        # Dados mais recentes para indicadores
        dados_recentes = dados_ordenados[-1]
        
        # Calcular indicadores
        indicadores = self._calcular_indicadores(dados_recentes)
        
        # Gerar insights
        insights = self._gerar_insights(indicadores, dados_recentes)
        
        # Calcular score
        score = self._calcular_score(indicadores)
        status = self._determinar_status(score)
        
        # Analisar tendências
        tendencias = self._analisar_tendencias(dados_ordenados)
        
        # Gerar projeções
        projecoes = self._gerar_projecoes(dados_ordenados, indicadores)
        
        # Extrair alertas críticos
        alertas_criticos = [i for i in insights if i.get('severidade') == 'alta']
        
        # Gerar recomendações priorizadas
        recomendacoes = self._gerar_recomendacoes(insights, indicadores, tendencias)
        
        # Gerar resumo executivo
        resumo = self._gerar_resumo(
            empresa_nome, periodo_analise, score, status,
            indicadores, alertas_criticos, tendencias
        )
        
        return ResultadoAnalise(
            empresa_id=empresa_id,
            empresa_nome=empresa_nome,
            periodo_analise=periodo_analise,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            meses_analisados=len(dados_ordenados),
            score=score,
            status=status,
            indicadores=indicadores,
            insights=insights,
            alertas_criticos=alertas_criticos,
            tendencias=tendencias,
            projecoes=projecoes,
            recomendacoes=recomendacoes,
            resumo=resumo
        )
    
    def _calcular_indicadores(self, dados: Dict) -> Dict:
        """Calcula todos os indicadores financeiros."""
        if CALCULADORA_DISPONIVEL:
            return calcular_indicadores(dados)
        
        # Fallback manual
        indicadores = {}
        
        # Extrair valores - aceitar múltiplos nomes de campos
        rb = float(dados.get('receita_bruta') or dados.get('receita_servicos') or dados.get('receita') or 0)
        ll = float(dados.get('lucro_liquido') or dados.get('lucro_exercicio') or 0)
        
        # Se não tem lucro_liquido calculado, calcular
        if ll == 0 and rb > 0:
            custos_val = float(dados.get('custos_total') or dados.get('custos') or 0)
            desp_val = float(dados.get('despesas_operacionais') or dados.get('despesas') or 0)
            imp_val = float(dados.get('impostos_total') or dados.get('deducoes_receita') or dados.get('impostos') or 0)
            ll = rb - custos_val - desp_val - imp_val
        
        at = float(dados.get('ativo_total') or dados.get('ativo_circulante') or 0)
        ac = float(dados.get('ativo_circulante') or dados.get('ativo_total') or 0)
        pc = float(dados.get('passivo_circulante') or 0)
        pnc = float(dados.get('passivo_nao_circulante') or 0)
        pl = float(dados.get('patrimonio_liquido') or dados.get('capital_social') or 0)
        disp = float(dados.get('disponivel') or dados.get('caixa') or 0)
        est = float(dados.get('estoques') or 0)
        clientes = float(dados.get('clientes') or dados.get('duplicatas_receber') or 0)
        fornecedores = float(dados.get('fornecedores') or 0)
        custos = float(dados.get('custos_total') or dados.get('custos') or 0)
        desp = float(dados.get('despesas_operacionais') or dados.get('despesas') or 0)
        impostos = float(dados.get('impostos_total') or dados.get('deducoes_receita') or dados.get('impostos') or 0)
        
        # Liquidez
        if pc > 0:
            indicadores['liquidez_corrente'] = round(ac / pc, 2)
            indicadores['liquidez_seca'] = round((ac - est) / pc, 2)
            indicadores['liquidez_imediata'] = round(disp / pc, 4)
        else:
            indicadores['liquidez_corrente'] = 0
            indicadores['liquidez_seca'] = 0
            indicadores['liquidez_imediata'] = 0
        
        # Rentabilidade
        if rb > 0:
            rl = rb - impostos
            lb = rl - custos
            indicadores['margem_bruta'] = round((lb / rb) * 100, 2) if rb > 0 else 0
            indicadores['margem_liquida'] = round((ll / rb) * 100, 2)
            indicadores['carga_tributaria'] = round((impostos / rb) * 100, 2)
        else:
            indicadores['margem_bruta'] = 0
            indicadores['margem_liquida'] = 0
            indicadores['carga_tributaria'] = 0
        
        if pl > 0:
            indicadores['roe'] = round((ll / pl) * 100, 2)
        else:
            indicadores['roe'] = 0
        
        if at > 0:
            indicadores['roa'] = round((ll / at) * 100, 2)
            indicadores['giro_ativo'] = round(rb / at, 2)
            indicadores['endividamento_geral'] = round(((pc + float(dados.get('passivo_nao_circulante', 0) or 0)) / at) * 100, 2)
        else:
            indicadores['roa'] = 0
            indicadores['giro_ativo'] = 0
            indicadores['endividamento_geral'] = 0
        
        # EBITDA simplificado
        depreciacao = float(dados.get('depreciacao_amortizacao', 0) or 0)
        desp_fin = float(dados.get('despesas_financeiras', 0) or 0)
        irpj = float(dados.get('irpj_deducao', 0) or 0)
        csll = float(dados.get('csll_deducao', 0) or 0)
        ebitda = ll + desp_fin + depreciacao + irpj + csll
        indicadores['ebitda'] = round(ebitda, 2)
        if rb > 0:
            indicadores['margem_ebitda'] = round((ebitda / rb) * 100, 2)
        else:
            indicadores['margem_ebitda'] = 0
        
        return indicadores
    
    def _gerar_insights(self, indicadores: Dict, dados: Dict) -> List[Dict]:
        """Gera insights inteligentes."""
        if CALCULADORA_DISPONIVEL:
            return gerar_insights(indicadores, dados)
        
        # Fallback manual
        insights = []
        
        # Liquidez
        lc = indicadores.get('liquidez_corrente', 0)
        if lc < 1.0:
            insights.append({
                'tipo': 'alerta',
                'categoria': 'liquidez',
                'titulo': 'Liquidez Corrente Crítica',
                'descricao': f'Liquidez corrente de {lc:.2f} indica dificuldade para pagar dívidas de curto prazo.',
                'recomendacao': 'Renegociar prazos com fornecedores ou buscar capital de giro.',
                'severidade': 'alta',
                'valor': lc
            })
        elif lc >= 1.5:
            insights.append({
                'tipo': 'positivo',
                'categoria': 'liquidez',
                'titulo': 'Boa Liquidez',
                'descricao': f'Liquidez corrente de {lc:.2f} indica boa capacidade de pagamento.',
                'severidade': 'info',
                'valor': lc
            })
        
        # Margem
        ml = indicadores.get('margem_liquida', 0)
        if ml < 5:
            insights.append({
                'tipo': 'alerta',
                'categoria': 'rentabilidade',
                'titulo': 'Margem Líquida Baixa',
                'descricao': f'Margem de {ml:.2f}% está abaixo do ideal.',
                'recomendacao': 'Revisar estrutura de custos e política de preços.',
                'severidade': 'alta' if ml < 0 else 'media',
                'valor': ml
            })
        elif ml > 20:
            insights.append({
                'tipo': 'positivo',
                'categoria': 'rentabilidade',
                'titulo': 'Excelente Margem',
                'descricao': f'Margem de {ml:.2f}% indica alta rentabilidade.',
                'severidade': 'info',
                'valor': ml
            })
        
        # Endividamento
        end = indicadores.get('endividamento_geral', 0)
        if end > 70:
            insights.append({
                'tipo': 'alerta',
                'categoria': 'endividamento',
                'titulo': 'Alto Endividamento',
                'descricao': f'Endividamento de {end:.2f}% é considerado elevado.',
                'recomendacao': 'Priorizar redução de dívidas.',
                'severidade': 'alta' if end > 80 else 'media',
                'valor': end
            })
        
        # Carga tributária
        ct = indicadores.get('carga_tributaria', 0)
        if ct > 25:
            insights.append({
                'tipo': 'atencao',
                'categoria': 'tributario',
                'titulo': 'Carga Tributária Elevada',
                'descricao': f'Impostos representam {ct:.2f}% da receita.',
                'recomendacao': 'Avaliar planejamento tributário.',
                'severidade': 'media',
                'valor': ct
            })
        
        return insights
    
    def _calcular_score(self, indicadores: Dict) -> int:
        """Calcula score de saúde financeira (0-100)."""
        if CALCULADORA_DISPONIVEL:
            return calcular_score(indicadores)
        
        score = 50
        
        # Liquidez (+/- 15 pontos)
        lc = indicadores.get('liquidez_corrente', 0)
        if lc >= 1.5:
            score += 10
        elif lc >= 1.0:
            score += 5
        elif lc < 0.8:
            score -= 10
        
        # Rentabilidade (+/- 20 pontos)
        ml = indicadores.get('margem_liquida', 0)
        if ml >= 15:
            score += 15
        elif ml >= 10:
            score += 10
        elif ml >= 5:
            score += 5
        elif ml < 0:
            score -= 15
        
        # Endividamento (+/- 10 pontos)
        end = indicadores.get('endividamento_geral', 0)
        if end <= 40:
            score += 10
        elif end <= 60:
            score += 5
        elif end > 80:
            score -= 10
        
        # ROE (+/- 10 pontos)
        roe = indicadores.get('roe', 0)
        if 15 <= roe <= 50:
            score += 10
        elif roe > 50:
            score += 5
        elif roe < 5:
            score -= 5
        
        return max(0, min(100, score))
    
    def _determinar_status(self, score: int) -> str:
        """Determina status baseado no score."""
        if score >= 85:
            return StatusSaude.EXCELENTE.value
        elif score >= 70:
            return StatusSaude.BOM.value
        elif score >= 50:
            return StatusSaude.REGULAR.value
        elif score >= 30:
            return StatusSaude.ATENCAO.value
        else:
            return StatusSaude.CRITICO.value
    
    def _analisar_tendencias(self, dados_ordenados: List[Dict]) -> Dict:
        """Analisa tendências dos últimos meses."""
        tendencias = {
            'receita': {'direcao': 'estavel', 'variacao': 0},
            'lucro': {'direcao': 'estavel', 'variacao': 0},
            'margem': {'direcao': 'estavel', 'variacao': 0},
            'liquidez': {'direcao': 'estavel', 'variacao': 0}
        }
        
        if len(dados_ordenados) < 2:
            return tendencias
        
        # Receita
        receitas = [float(d.get('receita_bruta', 0) or 0) for d in dados_ordenados[-6:]]
        if len(receitas) >= 2 and receitas[0] > 0:
            var_receita = ((receitas[-1] - receitas[0]) / receitas[0]) * 100
            tendencias['receita'] = {
                'direcao': 'alta' if var_receita > 5 else ('baixa' if var_receita < -5 else 'estavel'),
                'variacao': round(var_receita, 2),
                'valores': receitas
            }
        
        # Lucro
        lucros = [float(d.get('lucro_liquido', 0) or 0) for d in dados_ordenados[-6:]]
        if len(lucros) >= 2 and lucros[0] != 0:
            var_lucro = ((lucros[-1] - lucros[0]) / abs(lucros[0])) * 100 if lucros[0] != 0 else 0
            tendencias['lucro'] = {
                'direcao': 'alta' if var_lucro > 5 else ('baixa' if var_lucro < -5 else 'estavel'),
                'variacao': round(var_lucro, 2),
                'valores': lucros
            }
        
        # Margem
        margens = []
        for d in dados_ordenados[-6:]:
            rb = float(d.get('receita_bruta', 0) or 0)
            ll = float(d.get('lucro_liquido', 0) or 0)
            if rb > 0:
                margens.append(round((ll / rb) * 100, 2))
        
        if len(margens) >= 2:
            var_margem = margens[-1] - margens[0]
            tendencias['margem'] = {
                'direcao': 'alta' if var_margem > 2 else ('baixa' if var_margem < -2 else 'estavel'),
                'variacao': round(var_margem, 2),
                'valores': margens
            }
        
        return tendencias
    
    def _gerar_projecoes(self, dados_ordenados: List[Dict], indicadores: Dict) -> Dict:
        """Gera projeções para os próximos meses."""
        projecoes = {}
        
        if len(dados_ordenados) < 3:
            return projecoes
        
        # Receita projetada (média dos últimos 3 meses + tendência)
        receitas = [float(d.get('receita_bruta', 0) or 0) for d in dados_ordenados[-3:]]
        media_receita = sum(receitas) / len(receitas)
        
        # Calcular tendência
        if len(receitas) >= 2 and receitas[0] > 0:
            taxa_crescimento = (receitas[-1] / receitas[0]) ** (1/len(receitas)) - 1
        else:
            taxa_crescimento = 0
        
        projecoes['receita_proximos_3m'] = round(media_receita * (1 + taxa_crescimento) * 3, 2)
        projecoes['receita_proximos_12m'] = round(media_receita * (1 + taxa_crescimento) ** 12 * 12, 2)
        
        # Lucro projetado
        margem = indicadores.get('margem_liquida', 0) / 100
        projecoes['lucro_proximos_3m'] = round(projecoes['receita_proximos_3m'] * margem, 2)
        projecoes['lucro_proximos_12m'] = round(projecoes['receita_proximos_12m'] * margem, 2)
        
        # Impostos projetados
        carga = indicadores.get('carga_tributaria', 0) / 100
        projecoes['impostos_proximos_12m'] = round(projecoes['receita_proximos_12m'] * carga, 2)
        
        return projecoes
    
    def _gerar_recomendacoes(
        self, 
        insights: List[Dict], 
        indicadores: Dict,
        tendencias: Dict
    ) -> List[Dict]:
        """Gera lista priorizada de recomendações."""
        recomendacoes = []
        
        # Extrair recomendações dos insights
        for insight in insights:
            if insight.get('recomendacao'):
                recomendacoes.append({
                    'prioridade': 1 if insight.get('severidade') == 'alta' else (2 if insight.get('severidade') == 'media' else 3),
                    'categoria': insight.get('categoria'),
                    'titulo': insight.get('titulo'),
                    'acao': insight.get('recomendacao'),
                    'impacto': 'Alto' if insight.get('severidade') == 'alta' else 'Médio'
                })
        
        # Adicionar recomendações baseadas em tendências
        if tendencias.get('receita', {}).get('direcao') == 'baixa':
            recomendacoes.append({
                'prioridade': 1,
                'categoria': 'comercial',
                'titulo': 'Receita em Queda',
                'acao': 'Intensificar ações comerciais e revisar estratégia de vendas.',
                'impacto': 'Alto'
            })
        
        if tendencias.get('margem', {}).get('direcao') == 'baixa':
            recomendacoes.append({
                'prioridade': 2,
                'categoria': 'operacional',
                'titulo': 'Margem em Queda',
                'acao': 'Revisar estrutura de custos e renegociar com fornecedores.',
                'impacto': 'Médio'
            })
        
        # Ordenar por prioridade
        recomendacoes.sort(key=lambda x: x['prioridade'])
        
        return recomendacoes[:10]  # Top 10 recomendações
    
    def _gerar_resumo(
        self,
        empresa_nome: str,
        periodo: str,
        score: int,
        status: str,
        indicadores: Dict,
        alertas: List[Dict],
        tendencias: Dict
    ) -> str:
        """Gera resumo executivo da análise."""
        # Determinar tom do resumo
        if score >= 70:
            abertura = f"A empresa {empresa_nome} apresenta situação financeira {status.lower()}."
        elif score >= 50:
            abertura = f"A empresa {empresa_nome} apresenta situação financeira que requer atenção."
        else:
            abertura = f"A empresa {empresa_nome} apresenta situação financeira preocupante que demanda ações imediatas."
        
        # Principais indicadores
        ml = indicadores.get('margem_liquida', 0)
        lc = indicadores.get('liquidez_corrente', 0)
        end = indicadores.get('endividamento_geral', 0)
        
        principais = f"A margem líquida é de {ml:.1f}%, a liquidez corrente de {lc:.2f} e o endividamento de {end:.1f}%."
        
        # Tendência
        tend_receita = tendencias.get('receita', {})
        if tend_receita.get('direcao') == 'alta':
            tendencia_txt = f"A receita apresenta tendência de alta ({tend_receita.get('variacao', 0):.1f}% no período)."
        elif tend_receita.get('direcao') == 'baixa':
            tendencia_txt = f"A receita apresenta tendência de queda ({tend_receita.get('variacao', 0):.1f}% no período), o que requer atenção."
        else:
            tendencia_txt = "A receita se mantém estável no período analisado."
        
        # Alertas
        if alertas:
            alertas_txt = f"Foram identificados {len(alertas)} ponto(s) crítico(s) que demandam atenção imediata."
        else:
            alertas_txt = "Não foram identificados pontos críticos."
        
        return f"{abertura} {principais} {tendencia_txt} {alertas_txt}"


# ============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# ============================================================================

def executar_analise(
    dados_mensais: List[Dict],
    empresa_id: int,
    empresa_nome: str
) -> Dict:
    """
    Executa análise completa e retorna resultado como dicionário.
    """
    analyzer = AnalyzerProfissional()
    resultado = analyzer.analisar(dados_mensais, empresa_id, empresa_nome)
    return resultado.to_dict()


def calcular_indicadores_rapido(dados: Dict) -> Dict:
    """Calcula indicadores de um único período."""
    analyzer = AnalyzerProfissional()
    return analyzer._calcular_indicadores(dados)


def obter_score_rapido(dados: Dict) -> int:
    """Calcula score de um único período."""
    analyzer = AnalyzerProfissional()
    indicadores = analyzer._calcular_indicadores(dados)
    return analyzer._calcular_score(indicadores)
