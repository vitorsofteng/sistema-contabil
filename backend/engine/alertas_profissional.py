#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Alertas Profissional

Gera alertas inteligentes baseados em:
- Indicadores de Liquidez
- Indicadores de Rentabilidade  
- Indicadores de Endividamento
- Ciclo Financeiro
- Análise de Tendências
- Comparação com Benchmarks
- Detecção de Anomalias Estatísticas
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import statistics
import math


class CategoriaAlerta(Enum):
    """Categorias de alertas."""
    LIQUIDEZ = "liquidez"
    RENTABILIDADE = "rentabilidade"
    ENDIVIDAMENTO = "endividamento"
    CICLO_FINANCEIRO = "ciclo_financeiro"
    TENDENCIA = "tendencia"
    ANOMALIA = "anomalia"
    TRIBUTARIO = "tributario"
    OPERACIONAL = "operacional"
    PATRIMONIAL = "patrimonial"


class Severidade(Enum):
    """Níveis de severidade."""
    CRITICO = "critico"      # Ação imediata necessária
    ALTO = "alto"            # Atenção urgente
    MEDIO = "medio"          # Monitorar de perto
    BAIXO = "baixo"          # Informativo
    POSITIVO = "positivo"    # Notícia boa


class Urgencia(Enum):
    """Urgência de ação."""
    IMEDIATA = "imediata"      # Agir hoje
    CURTO_PRAZO = "curto_prazo"  # Próximos 7 dias
    MEDIO_PRAZO = "medio_prazo"  # Próximos 30 dias
    LONGO_PRAZO = "longo_prazo"  # Planejamento


@dataclass
class AlertaProfissional:
    """Alerta detalhado com recomendações."""
    id: str
    categoria: str
    severidade: str
    urgencia: str
    titulo: str
    descricao: str
    impacto: str
    recomendacoes: List[str]
    metricas: Dict[str, float] = field(default_factory=dict)
    periodo_referencia: str = ""
    data_geracao: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)


class GeradorAlertasProfissional:
    """Gerador de alertas financeiros profissionais."""
    
    # Benchmarks de referência
    BENCHMARKS = {
        'liquidez_corrente': {'critico': 0.8, 'atencao': 1.0, 'bom': 1.5, 'otimo': 2.0},
        'liquidez_seca': {'critico': 0.5, 'atencao': 0.7, 'bom': 1.0, 'otimo': 1.5},
        'liquidez_imediata': {'critico': 0.1, 'atencao': 0.2, 'bom': 0.5, 'otimo': 1.0},
        'margem_liquida': {'critico': 0, 'atencao': 5, 'bom': 10, 'otimo': 20},
        'margem_bruta': {'critico': 10, 'atencao': 20, 'bom': 35, 'otimo': 50},
        'roe': {'critico': 0, 'atencao': 5, 'bom': 15, 'otimo': 25},
        'roa': {'critico': 0, 'atencao': 3, 'bom': 8, 'otimo': 15},
        'endividamento_geral': {'otimo': 30, 'bom': 50, 'atencao': 70, 'critico': 85},
        'carga_tributaria': {'otimo': 10, 'bom': 18, 'atencao': 25, 'critico': 35},
        'pmr': {'otimo': 30, 'bom': 45, 'atencao': 60, 'critico': 90},  # dias
        'pmp': {'critico': 15, 'atencao': 25, 'bom': 45, 'otimo': 60},  # dias (quanto mais, melhor)
        'giro_ativo': {'critico': 0.3, 'atencao': 0.5, 'bom': 1.0, 'otimo': 2.0},
    }
    
    def __init__(self):
        self.alertas: List[AlertaProfissional] = []
        self.contador_id = 0
    
    def _gerar_id(self, categoria: str) -> str:
        """Gera ID único para o alerta."""
        self.contador_id += 1
        return f"{categoria}_{self.contador_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def gerar_alertas(
        self,
        empresa: Dict,
        dados_mensais: List[Dict],
        indicadores: Dict,
        tendencias: Dict = None,
        ultima_analise: Dict = None
    ) -> List[AlertaProfissional]:
        """
        Gera todos os alertas para a empresa.
        
        Args:
            empresa: Dados da empresa
            dados_mensais: Lista de dados mensais
            indicadores: Indicadores calculados
            tendencias: Tendências identificadas
            ultima_analise: Última análise realizada
            
        Returns:
            Lista de alertas profissionais
        """
        self.alertas = []
        self.contador_id = 0
        
        if not dados_mensais or not indicadores:
            self._criar_alerta_sem_dados(empresa)
            return self.alertas
        
        # Ordenar dados
        dados_ordenados = sorted(
            dados_mensais,
            key=lambda x: x.get('competencia', '') or f"{x.get('ano', 0)}-{x.get('mes', 0):02d}"
        )
        
        ultimo_periodo = dados_ordenados[-1] if dados_ordenados else {}
        periodo_ref = ultimo_periodo.get('competencia', '')
        empresa_nome = empresa.get('razao_social', 'Empresa')
        
        # 1. ALERTAS DE LIQUIDEZ
        self._verificar_liquidez(indicadores, empresa_nome, periodo_ref)
        
        # 2. ALERTAS DE RENTABILIDADE
        self._verificar_rentabilidade(indicadores, dados_ordenados, empresa_nome, periodo_ref)
        
        # 3. ALERTAS DE ENDIVIDAMENTO
        self._verificar_endividamento(indicadores, dados_ordenados, empresa_nome, periodo_ref)
        
        # 4. ALERTAS DE CICLO FINANCEIRO
        self._verificar_ciclo_financeiro(indicadores, dados_ordenados, empresa_nome, periodo_ref)
        
        # 5. ALERTAS TRIBUTÁRIOS
        self._verificar_tributario(indicadores, dados_ordenados, empresa_nome, periodo_ref)
        
        # 6. ALERTAS DE TENDÊNCIA
        self._verificar_tendencias(dados_ordenados, tendencias, empresa_nome, periodo_ref)
        
        # 7. ALERTAS DE ANOMALIAS
        self._verificar_anomalias(dados_ordenados, empresa_nome, periodo_ref)
        
        # 8. ALERTAS OPERACIONAIS
        self._verificar_operacional(indicadores, dados_ordenados, empresa_nome, periodo_ref)
        
        # 9. ALERTAS PATRIMONIAIS
        self._verificar_patrimonial(indicadores, dados_ordenados, empresa_nome, periodo_ref)
        
        # 10. ALERTAS POSITIVOS (boas notícias)
        self._verificar_positivos(indicadores, dados_ordenados, empresa_nome, periodo_ref)
        
        # Ordenar por severidade
        ordem_severidade = {
            Severidade.CRITICO.value: 0,
            Severidade.ALTO.value: 1,
            Severidade.MEDIO.value: 2,
            Severidade.BAIXO.value: 3,
            Severidade.POSITIVO.value: 4
        }
        self.alertas.sort(key=lambda a: ordem_severidade.get(a.severidade, 5))
        
        return self.alertas
    
    def _criar_alerta_sem_dados(self, empresa: Dict):
        """Cria alerta quando não há dados."""
        self.alertas.append(AlertaProfissional(
            id=self._gerar_id("sistema"),
            categoria=CategoriaAlerta.OPERACIONAL.value,
            severidade=Severidade.MEDIO.value,
            urgencia=Urgencia.CURTO_PRAZO.value,
            titulo="📊 Dados Insuficientes para Análise",
            descricao=f"A empresa {empresa.get('razao_social', 'N/A')} não possui dados suficientes para gerar alertas completos.",
            impacto="Sem dados, não é possível identificar riscos ou oportunidades de melhoria.",
            recomendacoes=[
                "Importe os balancetes mensais da empresa",
                "Garanta ao menos 3 meses de dados para análises de tendência",
                "Dados completos permitem alertas mais precisos"
            ]
        ))
    
    # =========================================================================
    # ALERTAS DE LIQUIDEZ
    # =========================================================================
    
    def _verificar_liquidez(self, ind: Dict, empresa: str, periodo: str):
        """Verifica indicadores de liquidez."""
        
        # Liquidez Corrente
        lc = ind.get('liquidez_corrente', 0)
        if lc > 0:
            bench = self.BENCHMARKS['liquidez_corrente']
            
            if lc < bench['critico']:
                self.alertas.append(AlertaProfissional(
                    id=self._gerar_id("liquidez"),
                    categoria=CategoriaAlerta.LIQUIDEZ.value,
                    severidade=Severidade.CRITICO.value,
                    urgencia=Urgencia.IMEDIATA.value,
                    titulo=f"🚨 Liquidez Corrente Crítica: {lc:.2f}",
                    descricao=f"A empresa não possui ativos circulantes suficientes para cobrir suas obrigações de curto prazo. "
                             f"Para cada R$ 1,00 de dívida, há apenas R$ {lc:.2f} em ativos.",
                    impacto="Alto risco de inadimplência com fornecedores e funcionários. Possível necessidade de empréstimo emergencial.",
                    recomendacoes=[
                        "Negociar prazos maiores com fornecedores",
                        "Acelerar recebimento de clientes",
                        "Avaliar venda de ativos não essenciais",
                        "Considerar linha de crédito emergencial",
                        "Rever política de estoque"
                    ],
                    metricas={'liquidez_corrente': lc, 'benchmark_minimo': bench['atencao']},
                    periodo_referencia=periodo
                ))
            elif lc < bench['atencao']:
                self.alertas.append(AlertaProfissional(
                    id=self._gerar_id("liquidez"),
                    categoria=CategoriaAlerta.LIQUIDEZ.value,
                    severidade=Severidade.ALTO.value,
                    urgencia=Urgencia.CURTO_PRAZO.value,
                    titulo=f"⚠️ Liquidez Corrente Baixa: {lc:.2f}",
                    descricao=f"A liquidez está abaixo do recomendado ({bench['atencao']}). "
                             f"Empresa opera com margem de segurança muito baixa.",
                    impacto="Dificuldade em absorver imprevistos financeiros. Vulnerabilidade a atrasos de clientes.",
                    recomendacoes=[
                        "Monitorar fluxo de caixa semanalmente",
                        "Priorizar recebimentos pendentes",
                        "Postergar despesas não essenciais",
                        "Criar reserva de emergência"
                    ],
                    metricas={'liquidez_corrente': lc, 'benchmark_minimo': bench['atencao']},
                    periodo_referencia=periodo
                ))
        
        # Liquidez Imediata
        li = ind.get('liquidez_imediata', 0)
        if li > 0 and li < self.BENCHMARKS['liquidez_imediata']['critico']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("liquidez"),
                categoria=CategoriaAlerta.LIQUIDEZ.value,
                severidade=Severidade.ALTO.value,
                urgencia=Urgencia.CURTO_PRAZO.value,
                titulo=f"💰 Caixa Imediato Insuficiente: {li:.2%}",
                descricao=f"Disponibilidades (caixa + bancos) cobrem apenas {li:.1%} das obrigações imediatas.",
                impacto="Risco de não conseguir pagar despesas urgentes sem depender de recebíveis.",
                recomendacoes=[
                    "Manter saldo mínimo em conta",
                    "Criar fundo de emergência",
                    "Revisar datas de vencimento das contas"
                ],
                metricas={'liquidez_imediata': li},
                periodo_referencia=periodo
            ))
    
    # =========================================================================
    # ALERTAS DE RENTABILIDADE
    # =========================================================================
    
    def _verificar_rentabilidade(self, ind: Dict, dados: List[Dict], empresa: str, periodo: str):
        """Verifica indicadores de rentabilidade."""
        
        # Margem Líquida
        ml = ind.get('margem_liquida', 0)
        bench = self.BENCHMARKS['margem_liquida']
        
        if ml < bench['critico']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("rentabilidade"),
                categoria=CategoriaAlerta.RENTABILIDADE.value,
                severidade=Severidade.CRITICO.value,
                urgencia=Urgencia.IMEDIATA.value,
                titulo=f"🔴 Empresa Operando com Prejuízo: {ml:.1f}%",
                descricao=f"A margem líquida negativa indica que a empresa está perdendo dinheiro em suas operações.",
                impacto="Consumo de capital próprio. Risco de insolvência se persistir.",
                recomendacoes=[
                    "Analisar estrutura de custos imediatamente",
                    "Identificar produtos/serviços deficitários",
                    "Renegociar contratos principais",
                    "Avaliar aumento de preços",
                    "Considerar redução de despesas fixas"
                ],
                metricas={'margem_liquida': ml},
                periodo_referencia=periodo
            ))
        elif ml < bench['atencao']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("rentabilidade"),
                categoria=CategoriaAlerta.RENTABILIDADE.value,
                severidade=Severidade.MEDIO.value,
                urgencia=Urgencia.MEDIO_PRAZO.value,
                titulo=f"📉 Margem Líquida Baixa: {ml:.1f}%",
                descricao=f"Margem abaixo de {bench['atencao']}% indica rentabilidade insuficiente para reinvestimento.",
                impacto="Baixa capacidade de crescimento e formação de reservas.",
                recomendacoes=[
                    "Revisar precificação de produtos/serviços",
                    "Buscar eficiência operacional",
                    "Analisar mix de vendas"
                ],
                metricas={'margem_liquida': ml, 'benchmark': bench['atencao']},
                periodo_referencia=periodo
            ))
        
        # ROE (Retorno sobre Patrimônio)
        roe = ind.get('roe', 0)
        if roe < 0:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("rentabilidade"),
                categoria=CategoriaAlerta.RENTABILIDADE.value,
                severidade=Severidade.CRITICO.value,
                urgencia=Urgencia.IMEDIATA.value,
                titulo=f"📊 ROE Negativo: {roe:.1f}%",
                descricao="O retorno sobre o patrimônio líquido está negativo, indicando destruição de valor para os sócios.",
                impacto="Capital dos sócios está sendo consumido. Empresa não está gerando retorno.",
                recomendacoes=[
                    "Identificar causas do prejuízo",
                    "Revisar estratégia de negócio",
                    "Avaliar viabilidade da operação"
                ],
                metricas={'roe': roe},
                periodo_referencia=periodo
            ))
        elif roe > 0 and roe < self.BENCHMARKS['roe']['atencao']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("rentabilidade"),
                categoria=CategoriaAlerta.RENTABILIDADE.value,
                severidade=Severidade.BAIXO.value,
                urgencia=Urgencia.LONGO_PRAZO.value,
                titulo=f"💹 ROE Abaixo do Mercado: {roe:.1f}%",
                descricao=f"O retorno está abaixo da taxa básica de juros, indicando que o capital poderia render mais em aplicações financeiras.",
                impacto="Custo de oportunidade para os sócios.",
                recomendacoes=[
                    "Avaliar alternativas de investimento",
                    "Buscar melhorar eficiência operacional"
                ],
                metricas={'roe': roe},
                periodo_referencia=periodo
            ))
        elif roe > 100:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("rentabilidade"),
                categoria=CategoriaAlerta.PATRIMONIAL.value,
                severidade=Severidade.MEDIO.value,
                urgencia=Urgencia.MEDIO_PRAZO.value,
                titulo=f"⚠️ ROE Muito Elevado: {roe:.0f}%",
                descricao="ROE acima de 100% geralmente indica patrimônio líquido muito baixo em relação ao lucro.",
                impacto="Empresa pode estar descapitalizada ou distribuindo lucros em excesso.",
                recomendacoes=[
                    "Avaliar política de distribuição de dividendos",
                    "Considerar reinvestir mais lucros na empresa",
                    "Fortalecer patrimônio líquido"
                ],
                metricas={'roe': roe},
                periodo_referencia=periodo
            ))
        
        # ROA
        roa = ind.get('roa', 0)
        if roa > 0 and roa < self.BENCHMARKS['roa']['atencao']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("rentabilidade"),
                categoria=CategoriaAlerta.RENTABILIDADE.value,
                severidade=Severidade.BAIXO.value,
                urgencia=Urgencia.LONGO_PRAZO.value,
                titulo=f"📈 ROA Pode Melhorar: {roa:.1f}%",
                descricao="O retorno sobre ativos está abaixo do esperado, indicando ativos subutilizados.",
                impacto="Capital investido não está gerando retorno adequado.",
                recomendacoes=[
                    "Avaliar utilização dos ativos",
                    "Considerar venda de ativos improdutivos",
                    "Buscar maior giro do ativo"
                ],
                metricas={'roa': roa},
                periodo_referencia=periodo
            ))
    
    # =========================================================================
    # ALERTAS DE ENDIVIDAMENTO
    # =========================================================================
    
    def _verificar_endividamento(self, ind: Dict, dados: List[Dict], empresa: str, periodo: str):
        """Verifica indicadores de endividamento."""
        
        endiv = ind.get('endividamento_geral', 0)
        bench = self.BENCHMARKS['endividamento_geral']
        
        if endiv > bench['critico']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("endividamento"),
                categoria=CategoriaAlerta.ENDIVIDAMENTO.value,
                severidade=Severidade.CRITICO.value,
                urgencia=Urgencia.CURTO_PRAZO.value,
                titulo=f"🔴 Endividamento Crítico: {endiv:.0f}%",
                descricao=f"Mais de {endiv:.0f}% do ativo é financiado por terceiros. Empresa altamente dependente de credores.",
                impacto="Risco elevado de insolvência. Dificuldade em obter novos créditos. Alto custo financeiro.",
                recomendacoes=[
                    "Evitar novos empréstimos",
                    "Priorizar quitação de dívidas mais caras",
                    "Negociar prazos e taxas",
                    "Avaliar aporte de capital dos sócios",
                    "Rever política de distribuição de lucros"
                ],
                metricas={'endividamento_geral': endiv, 'limite_critico': bench['critico']},
                periodo_referencia=periodo
            ))
        elif endiv > bench['atencao']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("endividamento"),
                categoria=CategoriaAlerta.ENDIVIDAMENTO.value,
                severidade=Severidade.ALTO.value,
                urgencia=Urgencia.MEDIO_PRAZO.value,
                titulo=f"⚠️ Endividamento Elevado: {endiv:.0f}%",
                descricao=f"O nível de endividamento de {endiv:.0f}% está acima do recomendado ({bench['atencao']}%).",
                impacto="Maior vulnerabilidade a variações nas taxas de juros. Capacidade de investimento limitada.",
                recomendacoes=[
                    "Monitorar evolução das dívidas mensalmente",
                    "Evitar novos financiamentos de curto prazo",
                    "Buscar alongar perfil da dívida"
                ],
                metricas={'endividamento_geral': endiv},
                periodo_referencia=periodo
            ))
        
        # Composição do Endividamento (curto vs longo prazo)
        comp_endiv = ind.get('composicao_endividamento', 0)
        if comp_endiv > 80:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("endividamento"),
                categoria=CategoriaAlerta.ENDIVIDAMENTO.value,
                severidade=Severidade.MEDIO.value,
                urgencia=Urgencia.MEDIO_PRAZO.value,
                titulo=f"📅 Dívida Concentrada no Curto Prazo: {comp_endiv:.0f}%",
                descricao=f"{comp_endiv:.0f}% das dívidas vencem no curto prazo, pressionando o fluxo de caixa.",
                impacto="Pressão no fluxo de caixa. Necessidade constante de capital de giro.",
                recomendacoes=[
                    "Renegociar prazos com credores",
                    "Buscar financiamentos de longo prazo",
                    "Criar reserva para pagamento de dívidas"
                ],
                metricas={'composicao_endividamento': comp_endiv},
                periodo_referencia=periodo
            ))
        
        # Endividamento sobre PL
        endiv_pl = ind.get('endividamento_pl', 0)
        if endiv_pl > 300:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("endividamento"),
                categoria=CategoriaAlerta.ENDIVIDAMENTO.value,
                severidade=Severidade.ALTO.value,
                urgencia=Urgencia.MEDIO_PRAZO.value,
                titulo=f"💳 Dívida vs Patrimônio: {endiv_pl:.0f}%",
                descricao=f"A dívida é {endiv_pl/100:.1f}x maior que o patrimônio líquido dos sócios.",
                impacto="Sócios têm pouco 'skin in the game'. Credores assumem maior parte do risco.",
                recomendacoes=[
                    "Capitalizar a empresa",
                    "Reduzir distribuição de dividendos",
                    "Amortizar dívidas com lucros"
                ],
                metricas={'endividamento_pl': endiv_pl},
                periodo_referencia=periodo
            ))
    
    # =========================================================================
    # ALERTAS DE CICLO FINANCEIRO
    # =========================================================================
    
    def _verificar_ciclo_financeiro(self, ind: Dict, dados: List[Dict], empresa: str, periodo: str):
        """Verifica ciclo financeiro (PMR, PME, PMP)."""
        
        pmr = ind.get('pmr', 0)
        pme = ind.get('pme', 0)
        pmp = ind.get('pmp', 0)
        ciclo = ind.get('ciclo_financeiro', 0)
        
        # PMR alto
        if pmr > self.BENCHMARKS['pmr']['critico']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("ciclo"),
                categoria=CategoriaAlerta.CICLO_FINANCEIRO.value,
                severidade=Severidade.ALTO.value,
                urgencia=Urgencia.CURTO_PRAZO.value,
                titulo=f"📆 Prazo de Recebimento Muito Longo: {pmr:.0f} dias",
                descricao=f"Clientes demoram em média {pmr:.0f} dias para pagar. Isso imobiliza capital e aumenta risco de inadimplência.",
                impacto="Capital parado em recebíveis. Maior necessidade de capital de giro. Risco de inadimplência.",
                recomendacoes=[
                    "Revisar política de crédito",
                    "Implementar cobrança preventiva",
                    "Oferecer desconto para pagamento antecipado",
                    "Avaliar antecipação de recebíveis",
                    "Analisar perfil dos clientes inadimplentes"
                ],
                metricas={'pmr': pmr, 'limite': self.BENCHMARKS['pmr']['critico']},
                periodo_referencia=periodo
            ))
        elif pmr > self.BENCHMARKS['pmr']['atencao']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("ciclo"),
                categoria=CategoriaAlerta.CICLO_FINANCEIRO.value,
                severidade=Severidade.MEDIO.value,
                urgencia=Urgencia.MEDIO_PRAZO.value,
                titulo=f"⏰ Recebimento Acima do Ideal: {pmr:.0f} dias",
                descricao=f"O prazo médio de recebimento de {pmr:.0f} dias está acima do recomendado ({self.BENCHMARKS['pmr']['atencao']} dias).",
                impacto="Necessidade de mais capital de giro.",
                recomendacoes=[
                    "Monitorar aging de recebíveis",
                    "Acompanhar maiores devedores"
                ],
                metricas={'pmr': pmr},
                periodo_referencia=periodo
            ))
        
        # Ciclo Financeiro muito longo
        if ciclo > 120:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("ciclo"),
                categoria=CategoriaAlerta.CICLO_FINANCEIRO.value,
                severidade=Severidade.ALTO.value,
                urgencia=Urgencia.MEDIO_PRAZO.value,
                titulo=f"🔄 Ciclo Financeiro Extenso: {ciclo:.0f} dias",
                descricao=f"A empresa leva {ciclo:.0f} dias entre pagar seus fornecedores e receber de seus clientes.",
                impacto="Alta necessidade de capital de giro. Empresa financia operação dos clientes.",
                recomendacoes=[
                    "Reduzir prazo de recebimento",
                    "Aumentar prazo com fornecedores",
                    "Otimizar níveis de estoque",
                    "Negociar antecipação de recebíveis"
                ],
                metricas={'ciclo_financeiro': ciclo, 'pmr': pmr, 'pmp': pmp, 'pme': pme},
                periodo_referencia=periodo
            ))
    
    # =========================================================================
    # ALERTAS TRIBUTÁRIOS
    # =========================================================================
    
    def _verificar_tributario(self, ind: Dict, dados: List[Dict], empresa: str, periodo: str):
        """Verifica carga tributária e oportunidades."""
        
        carga = ind.get('carga_tributaria', 0)
        bench = self.BENCHMARKS['carga_tributaria']
        
        if carga > bench['critico']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("tributario"),
                categoria=CategoriaAlerta.TRIBUTARIO.value,
                severidade=Severidade.ALTO.value,
                urgencia=Urgencia.MEDIO_PRAZO.value,
                titulo=f"💰 Carga Tributária Elevada: {carga:.1f}%",
                descricao=f"Impostos representam {carga:.1f}% do faturamento, acima da média do mercado.",
                impacto="Rentabilidade comprometida por alta tributação.",
                recomendacoes=[
                    "Avaliar enquadramento tributário (Simples, Lucro Presumido, Real)",
                    "Verificar benefícios fiscais disponíveis",
                    "Consultar contador sobre planejamento tributário",
                    "Revisar classificação fiscal de produtos/serviços"
                ],
                metricas={'carga_tributaria': carga, 'benchmark': bench['atencao']},
                periodo_referencia=periodo
            ))
        elif carga > bench['atencao']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("tributario"),
                categoria=CategoriaAlerta.TRIBUTARIO.value,
                severidade=Severidade.BAIXO.value,
                urgencia=Urgencia.LONGO_PRAZO.value,
                titulo=f"📋 Oportunidade de Revisão Tributária: {carga:.1f}%",
                descricao=f"Carga tributária de {carga:.1f}% pode ter oportunidades de otimização.",
                impacto="Possível economia tributária com planejamento adequado.",
                recomendacoes=[
                    "Revisar enquadramento tributário anualmente",
                    "Verificar créditos tributários não utilizados"
                ],
                metricas={'carga_tributaria': carga},
                periodo_referencia=periodo
            ))
        
        # Verificar variação brusca de impostos
        if len(dados) >= 3:
            impostos = [d.get('impostos', 0) or d.get('impostos_total', 0) or d.get('deducoes_receita', 0) or 0 for d in dados[-3:]]
            if len(impostos) >= 3 and impostos[0] > 0:
                variacao = ((impostos[-1] - impostos[0]) / impostos[0]) * 100 if impostos[0] > 0 else 0
                if abs(variacao) > 30:
                    self.alertas.append(AlertaProfissional(
                        id=self._gerar_id("tributario"),
                        categoria=CategoriaAlerta.TRIBUTARIO.value,
                        severidade=Severidade.MEDIO.value,
                        urgencia=Urgencia.CURTO_PRAZO.value,
                        titulo=f"📊 Variação Atípica de Impostos: {variacao:+.0f}%",
                        descricao=f"Os impostos variaram {variacao:+.0f}% nos últimos 3 meses. Verificar se está correto.",
                        impacto="Pode indicar erro de apuração ou mudança operacional relevante.",
                        recomendacoes=[
                            "Verificar cálculo dos impostos",
                            "Confirmar classificação fiscal das operações",
                            "Checar se houve mudança de atividade"
                        ],
                        metricas={'variacao_impostos_pct': variacao},
                        periodo_referencia=periodo
                    ))
    
    # =========================================================================
    # ALERTAS DE TENDÊNCIA
    # =========================================================================
    
    def _verificar_tendencias(self, dados: List[Dict], tendencias: Dict, empresa: str, periodo: str):
        """Verifica tendências ao longo do tempo."""
        
        if len(dados) < 3:
            return
        
        # Calcular variação de receita
        receitas = [d.get('receita', 0) or d.get('receita_bruta', 0) or d.get('receita_servicos', 0) or 0 for d in dados]
        receitas_validas = [r for r in receitas if r > 0]
        
        if len(receitas_validas) >= 3:
            primeira_metade = receitas_validas[:len(receitas_validas)//2]
            segunda_metade = receitas_validas[len(receitas_validas)//2:]
            
            media_1 = statistics.mean(primeira_metade) if primeira_metade else 0
            media_2 = statistics.mean(segunda_metade) if segunda_metade else 0
            
            if media_1 > 0:
                variacao = ((media_2 - media_1) / media_1) * 100
                
                if variacao < -20:
                    self.alertas.append(AlertaProfissional(
                        id=self._gerar_id("tendencia"),
                        categoria=CategoriaAlerta.TENDENCIA.value,
                        severidade=Severidade.CRITICO.value,
                        urgencia=Urgencia.IMEDIATA.value,
                        titulo=f"📉 Queda Significativa de Receita: {variacao:.0f}%",
                        descricao=f"A receita média caiu {abs(variacao):.0f}% comparando os períodos.",
                        impacto="Perda de faturamento compromete sustentabilidade do negócio.",
                        recomendacoes=[
                            "Identificar causas da queda (mercado, concorrência, sazonalidade)",
                            "Revisar estratégia comercial",
                            "Avaliar novos canais de venda",
                            "Ajustar estrutura de custos à nova realidade"
                        ],
                        metricas={'variacao_receita': variacao},
                        periodo_referencia=periodo
                    ))
                elif variacao < -10:
                    self.alertas.append(AlertaProfissional(
                        id=self._gerar_id("tendencia"),
                        categoria=CategoriaAlerta.TENDENCIA.value,
                        severidade=Severidade.ALTO.value,
                        urgencia=Urgencia.CURTO_PRAZO.value,
                        titulo=f"⚠️ Receita em Queda: {variacao:.0f}%",
                        descricao=f"Tendência de queda de {abs(variacao):.0f}% na receita.",
                        impacto="Se persistir, pode comprometer fluxo de caixa.",
                        recomendacoes=[
                            "Monitorar de perto nos próximos meses",
                            "Intensificar ações comerciais"
                        ],
                        metricas={'variacao_receita': variacao},
                        periodo_referencia=periodo
                    ))
        
        # Verificar lucro em queda
        lucros = []
        for d in dados:
            receita = d.get('receita', 0) or d.get('receita_bruta', 0) or 0
            custos = d.get('custos', 0) or d.get('custos_total', 0) or 0
            despesas = d.get('despesas', 0) or d.get('despesas_operacionais', 0) or 0
            impostos = d.get('impostos', 0) or d.get('impostos_total', 0) or d.get('deducoes_receita', 0) or 0
            lucro = d.get('lucro_liquido', 0) or (receita - custos - despesas - impostos)
            lucros.append(lucro)
        
        # Contar meses consecutivos de prejuízo
        meses_prejuizo = 0
        for lucro in reversed(lucros):
            if lucro < 0:
                meses_prejuizo += 1
            else:
                break
        
        if meses_prejuizo >= 3:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("tendencia"),
                categoria=CategoriaAlerta.TENDENCIA.value,
                severidade=Severidade.CRITICO.value,
                urgencia=Urgencia.IMEDIATA.value,
                titulo=f"🔴 {meses_prejuizo} Meses Consecutivos de Prejuízo",
                descricao=f"A empresa está operando com prejuízo há {meses_prejuizo} meses consecutivos.",
                impacto="Consumo acelerado de capital próprio. Risco de insolvência.",
                recomendacoes=[
                    "Revisar estrutura de custos urgentemente",
                    "Avaliar viabilidade de produtos/serviços",
                    "Considerar reestruturação operacional",
                    "Buscar apoio de consultoria"
                ],
                metricas={'meses_prejuizo_consecutivos': meses_prejuizo},
                periodo_referencia=periodo
            ))
    
    # =========================================================================
    # ALERTAS DE ANOMALIAS
    # =========================================================================
    
    def _verificar_anomalias(self, dados: List[Dict], empresa: str, periodo: str):
        """Detecta anomalias estatísticas nos dados."""
        
        if len(dados) < 6:
            return
        
        # Verificar anomalias na receita
        receitas = [d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados]
        receitas_validas = [r for r in receitas if r > 0]
        
        if len(receitas_validas) >= 6:
            media = statistics.mean(receitas_validas)
            desvio = statistics.stdev(receitas_validas)
            
            ultimo_valor = receitas_validas[-1]
            
            if desvio > 0:
                z_score = (ultimo_valor - media) / desvio
                
                if z_score < -2:
                    self.alertas.append(AlertaProfissional(
                        id=self._gerar_id("anomalia"),
                        categoria=CategoriaAlerta.ANOMALIA.value,
                        severidade=Severidade.ALTO.value,
                        urgencia=Urgencia.CURTO_PRAZO.value,
                        titulo=f"📊 Receita Atipicamente Baixa",
                        descricao=f"A receita do último período está {abs(z_score):.1f} desvios padrão abaixo da média histórica.",
                        impacto="Pode indicar problema operacional, perda de cliente importante, ou sazonalidade.",
                        recomendacoes=[
                            "Investigar causa específica",
                            "Verificar se houve perda de cliente relevante",
                            "Avaliar se é padrão sazonal"
                        ],
                        metricas={'z_score': z_score, 'valor_atual': ultimo_valor, 'media': media},
                        periodo_referencia=periodo
                    ))
                elif z_score > 2:
                    self.alertas.append(AlertaProfissional(
                        id=self._gerar_id("anomalia"),
                        categoria=CategoriaAlerta.ANOMALIA.value,
                        severidade=Severidade.BAIXO.value,
                        urgencia=Urgencia.MEDIO_PRAZO.value,
                        titulo=f"📈 Receita Atipicamente Alta",
                        descricao=f"A receita do último período está {z_score:.1f} desvios padrão acima da média.",
                        impacto="Pode ser venda pontual, novo cliente, ou erro de lançamento.",
                        recomendacoes=[
                            "Confirmar se receita é recorrente",
                            "Verificar se há compromissos associados",
                            "Planejar para possível normalização"
                        ],
                        metricas={'z_score': z_score, 'valor_atual': ultimo_valor, 'media': media},
                        periodo_referencia=periodo
                    ))
        
        # Verificar anomalias nos custos
        custos = [d.get('custos', 0) or d.get('custos_total', 0) or 0 for d in dados]
        custos_validos = [c for c in custos if c >= 0]
        
        if len(custos_validos) >= 6:
            media_custos = statistics.mean(custos_validos) if custos_validos else 0
            if media_custos > 0:
                desvio_custos = statistics.stdev(custos_validos)
                ultimo_custo = custos_validos[-1]
                
                if desvio_custos > 0:
                    z_custo = (ultimo_custo - media_custos) / desvio_custos
                    
                    if z_custo > 2:
                        self.alertas.append(AlertaProfissional(
                            id=self._gerar_id("anomalia"),
                            categoria=CategoriaAlerta.ANOMALIA.value,
                            severidade=Severidade.MEDIO.value,
                            urgencia=Urgencia.CURTO_PRAZO.value,
                            titulo=f"💸 Custos Atipicamente Altos",
                            descricao=f"Os custos estão {z_custo:.1f} desvios padrão acima do normal.",
                            impacto="Pode comprometer margem se não for pontual.",
                            recomendacoes=[
                                "Verificar lançamentos do período",
                                "Identificar causa do aumento",
                                "Avaliar se é pontual ou recorrente"
                            ],
                            metricas={'z_score_custos': z_custo},
                            periodo_referencia=periodo
                        ))
    
    # =========================================================================
    # ALERTAS OPERACIONAIS
    # =========================================================================
    
    def _verificar_operacional(self, ind: Dict, dados: List[Dict], empresa: str, periodo: str):
        """Verifica eficiência operacional."""
        
        giro = ind.get('giro_ativo', 0)
        bench = self.BENCHMARKS['giro_ativo']
        
        if giro > 0 and giro < bench['critico']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("operacional"),
                categoria=CategoriaAlerta.OPERACIONAL.value,
                severidade=Severidade.MEDIO.value,
                urgencia=Urgencia.LONGO_PRAZO.value,
                titulo=f"🏭 Baixo Giro do Ativo: {giro:.2f}x",
                descricao=f"A empresa gera apenas R$ {giro:.2f} de receita para cada R$ 1,00 de ativo.",
                impacto="Ativos podem estar sendo subutilizados.",
                recomendacoes=[
                    "Avaliar necessidade de todos os ativos",
                    "Considerar venda de ativos ociosos",
                    "Buscar aumentar volume de vendas"
                ],
                metricas={'giro_ativo': giro},
                periodo_referencia=periodo
            ))
        elif giro > 0 and giro < bench['atencao']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("operacional"),
                categoria=CategoriaAlerta.OPERACIONAL.value,
                severidade=Severidade.BAIXO.value,
                urgencia=Urgencia.LONGO_PRAZO.value,
                titulo=f"📦 Giro do Ativo Pode Melhorar: {giro:.2f}x",
                descricao=f"Oportunidade de aumentar eficiência no uso dos ativos.",
                impacto="Melhoria no giro aumenta rentabilidade.",
                recomendacoes=[
                    "Otimizar uso de equipamentos",
                    "Revisar política de investimentos"
                ],
                metricas={'giro_ativo': giro},
                periodo_referencia=periodo
            ))
        
        # Verificar EBITDA
        ebitda = ind.get('ebitda', 0)
        margem_ebitda = ind.get('margem_ebitda', 0)
        
        if ebitda < 0:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("operacional"),
                categoria=CategoriaAlerta.OPERACIONAL.value,
                severidade=Severidade.CRITICO.value,
                urgencia=Urgencia.IMEDIATA.value,
                titulo=f"🔴 EBITDA Negativo",
                descricao="A operação não gera caixa suficiente nem para cobrir custos operacionais.",
                impacto="Operação inviável. Empresa queima caixa todo mês.",
                recomendacoes=[
                    "Revisar modelo de negócio",
                    "Reduzir custos fixos urgentemente",
                    "Avaliar precificação",
                    "Considerar reestruturação"
                ],
                metricas={'ebitda': ebitda},
                periodo_referencia=periodo
            ))
    
    # =========================================================================
    # ALERTAS PATRIMONIAIS
    # =========================================================================
    
    def _verificar_patrimonial(self, ind: Dict, dados: List[Dict], empresa: str, periodo: str):
        """Verifica situação patrimonial."""
        
        if dados:
            ultimo = dados[-1]
            pl = ultimo.get('patrimonio_liquido', 0) or ultimo.get('capital_social', 0) or 0
            
            if pl < 0:
                self.alertas.append(AlertaProfissional(
                    id=self._gerar_id("patrimonial"),
                    categoria=CategoriaAlerta.PATRIMONIAL.value,
                    severidade=Severidade.CRITICO.value,
                    urgencia=Urgencia.IMEDIATA.value,
                    titulo=f"🚨 Patrimônio Líquido Negativo",
                    descricao="A empresa tem mais dívidas do que ativos. Situação conhecida como 'passivo a descoberto'.",
                    impacto="Tecnicamente insolvente. Credores têm direito sobre todos os ativos.",
                    recomendacoes=[
                        "Aporte urgente de capital",
                        "Renegociação de dívidas",
                        "Avaliar recuperação judicial",
                        "Consultar advogado especializado"
                    ],
                    metricas={'patrimonio_liquido': pl},
                    periodo_referencia=periodo
                ))
            elif pl < 10000:
                self.alertas.append(AlertaProfissional(
                    id=self._gerar_id("patrimonial"),
                    categoria=CategoriaAlerta.PATRIMONIAL.value,
                    severidade=Severidade.ALTO.value,
                    urgencia=Urgencia.MEDIO_PRAZO.value,
                    titulo=f"⚠️ Patrimônio Líquido Muito Baixo",
                    descricao=f"O patrimônio de R$ {pl:,.2f} é muito baixo para o porte da operação.",
                    impacto="Empresa altamente alavancada. Pouca margem para absorver prejuízos.",
                    recomendacoes=[
                        "Reter mais lucros na empresa",
                        "Considerar aporte dos sócios",
                        "Evitar distribuição de dividendos"
                    ],
                    metricas={'patrimonio_liquido': pl},
                    periodo_referencia=periodo
                ))
    
    # =========================================================================
    # ALERTAS POSITIVOS
    # =========================================================================
    
    def _verificar_positivos(self, ind: Dict, dados: List[Dict], empresa: str, periodo: str):
        """Identifica pontos positivos para destacar."""
        
        # Margem excelente
        ml = ind.get('margem_liquida', 0)
        if ml >= self.BENCHMARKS['margem_liquida']['otimo']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("positivo"),
                categoria=CategoriaAlerta.RENTABILIDADE.value,
                severidade=Severidade.POSITIVO.value,
                urgencia=Urgencia.LONGO_PRAZO.value,
                titulo=f"🌟 Margem Líquida Excelente: {ml:.1f}%",
                descricao=f"A empresa possui margem líquida de {ml:.1f}%, muito acima da média do mercado.",
                impacto="Alta capacidade de reinvestimento e distribuição de lucros.",
                recomendacoes=[
                    "Manter estratégia de precificação",
                    "Considerar reinvestir em crescimento",
                    "Avaliar diversificação"
                ],
                metricas={'margem_liquida': ml},
                periodo_referencia=periodo
            ))
        
        # Liquidez saudável
        lc = ind.get('liquidez_corrente', 0)
        if lc >= self.BENCHMARKS['liquidez_corrente']['otimo']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("positivo"),
                categoria=CategoriaAlerta.LIQUIDEZ.value,
                severidade=Severidade.POSITIVO.value,
                urgencia=Urgencia.LONGO_PRAZO.value,
                titulo=f"✅ Liquidez Saudável: {lc:.2f}",
                descricao=f"Empresa com excelente capacidade de pagamento no curto prazo.",
                impacto="Tranquilidade para operar e capacidade de aproveitar oportunidades.",
                recomendacoes=[
                    "Avaliar se há caixa em excesso que poderia ser investido",
                    "Manter reserva de segurança"
                ],
                metricas={'liquidez_corrente': lc},
                periodo_referencia=periodo
            ))
        
        # Crescimento de receita
        if len(dados) >= 6:
            receitas = [d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados]
            receitas_validas = [r for r in receitas if r > 0]
            
            if len(receitas_validas) >= 6:
                media_1 = statistics.mean(receitas_validas[:3])
                media_2 = statistics.mean(receitas_validas[-3:])
                
                if media_1 > 0:
                    crescimento = ((media_2 - media_1) / media_1) * 100
                    
                    if crescimento > 20:
                        self.alertas.append(AlertaProfissional(
                            id=self._gerar_id("positivo"),
                            categoria=CategoriaAlerta.TENDENCIA.value,
                            severidade=Severidade.POSITIVO.value,
                            urgencia=Urgencia.LONGO_PRAZO.value,
                            titulo=f"🚀 Crescimento de Receita: +{crescimento:.0f}%",
                            descricao=f"A receita cresceu {crescimento:.0f}% comparando os últimos períodos.",
                            impacto="Empresa em expansão. Possibilidade de ganhos de escala.",
                            recomendacoes=[
                                "Garantir que estrutura suporte crescimento",
                                "Monitorar se margem se mantém",
                                "Investir em capacidade se necessário"
                            ],
                            metricas={'crescimento_receita': crescimento},
                            periodo_referencia=periodo
                        ))
        
        # Baixo endividamento
        endiv = ind.get('endividamento_geral', 0)
        if 0 < endiv < self.BENCHMARKS['endividamento_geral']['otimo']:
            self.alertas.append(AlertaProfissional(
                id=self._gerar_id("positivo"),
                categoria=CategoriaAlerta.ENDIVIDAMENTO.value,
                severidade=Severidade.POSITIVO.value,
                urgencia=Urgencia.LONGO_PRAZO.value,
                titulo=f"💪 Baixo Endividamento: {endiv:.0f}%",
                descricao=f"Empresa sólida com apenas {endiv:.0f}% de endividamento.",
                impacto="Capacidade de buscar financiamentos se necessário. Baixo custo financeiro.",
                recomendacoes=[
                    "Manter disciplina financeira",
                    "Usar capacidade de crédito apenas para boas oportunidades"
                ],
                metricas={'endividamento_geral': endiv},
                periodo_referencia=periodo
            ))


# =============================================================================
# FUNÇÃO DE CONVENIÊNCIA
# =============================================================================

def gerar_alertas_empresa(
    empresa: Dict,
    dados_mensais: List[Dict],
    indicadores: Dict,
    tendencias: Dict = None,
    ultima_analise: Dict = None
) -> List[Dict]:
    """
    Função de conveniência para gerar alertas.
    
    Returns:
        Lista de alertas como dicionários
    """
    gerador = GeradorAlertasProfissional()
    alertas = gerador.gerar_alertas(
        empresa=empresa,
        dados_mensais=dados_mensais,
        indicadores=indicadores,
        tendencias=tendencias,
        ultima_analise=ultima_analise
    )
    
    return [a.to_dict() for a in alertas]
