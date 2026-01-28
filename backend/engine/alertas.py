#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de Alertas Inteligentes

Sistema que analisa dados financeiros e gera alertas automáticos
para o contador baseado em regras configuráveis.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import statistics


class TipoAlerta(Enum):
    """Tipos de alertas disponíveis."""
    CAIXA_CRITICO = "caixa_critico"
    CAIXA_ATENCAO = "caixa_atencao"
    MARGEM_BAIXA = "margem_baixa"
    MARGEM_QUEDA = "margem_queda"
    TENDENCIA_NEGATIVA = "tendencia_negativa"
    QUEDA_FATURAMENTO = "queda_faturamento"
    ANOMALIA_RECEITA = "anomalia_receita"
    ANOMALIA_CUSTO = "anomalia_custo"
    SCORE_CRITICO = "score_critico"
    SCORE_QUEDA = "score_queda"
    SEM_DADOS = "sem_dados"
    # Novos alertas de crise
    INSOLVENCIA = "insolvencia"
    PASSIVO_DESCOBERTO = "passivo_descoberto"
    ENDIVIDAMENTO_CRITICO = "endividamento_critico"
    PREJUIZO_RECORRENTE = "prejuizo_recorrente"
    LIQUIDEZ_SECA_CRITICA = "liquidez_seca_critica"
    CAPITAL_GIRO_NEGATIVO = "capital_giro_negativo"
    FORNECEDORES_ATRASADOS = "fornecedores_atrasados"


class Severidade(Enum):
    """Níveis de severidade."""
    CRITICO = "critico"
    ATENCAO = "atencao"
    INFO = "info"


@dataclass
class Alerta:
    """Representa um alerta gerado."""
    tipo: str
    severidade: str
    codigo: str
    titulo: str
    mensagem: str
    valor_atual: Optional[float] = None
    valor_limite: Optional[float] = None
    valor_anterior: Optional[float] = None
    dados_json: Optional[str] = None
    periodo_referencia: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ConfiguracaoAlerta:
    """Configuração padrão de alertas."""
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        
        # Caixa
        self.alerta_caixa_ativo = config.get('alerta_caixa_ativo', True)
        self.caixa_dias_critico = config.get('caixa_dias_critico', 30)
        self.caixa_dias_atencao = config.get('caixa_dias_atencao', 60)
        
        # Margem
        self.alerta_margem_ativo = config.get('alerta_margem_ativo', True)
        self.margem_minima = config.get('margem_minima', 5.0)
        self.margem_queda_pct = config.get('margem_queda_pct', 20.0)
        
        # Tendência
        self.alerta_tendencia_ativo = config.get('alerta_tendencia_ativo', True)
        self.tendencia_meses_negativos = config.get('tendencia_meses_negativos', 3)
        self.queda_faturamento_pct = config.get('queda_faturamento_pct', 15.0)
        
        # Anomalias
        self.alerta_anomalias_ativo = config.get('alerta_anomalias_ativo', True)
        self.anomalia_desvio_padrao = config.get('anomalia_desvio_padrao', 2.0)
        
        # Score
        self.alerta_score_ativo = config.get('alerta_score_ativo', True)
        self.score_critico = config.get('score_critico', 40)
        self.score_queda_pontos = config.get('score_queda_pontos', 15)
        
        # === NOVOS: Alertas de Crise ===
        self.alerta_liquidez_ativo = config.get('alerta_liquidez_ativo', True)
        self.liquidez_corrente_critica = config.get('liquidez_corrente_critica', 1.0)
        self.liquidez_seca_critica = config.get('liquidez_seca_critica', 0.8)
        self.endividamento_critico = config.get('endividamento_critico', 80.0)
        self.meses_prejuizo_alerta = config.get('meses_prejuizo_alerta', 3)


class MotorAlertas:
    """Motor principal de geração de alertas."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = ConfiguracaoAlerta(config)
    
    def analisar(
        self,
        empresa: Dict,
        dados_mensais: List[Dict],
        analise_atual: Optional[Dict] = None,
        analise_anterior: Optional[Dict] = None
    ) -> List[Alerta]:
        """
        Analisa dados da empresa e gera alertas.
        
        Args:
            empresa: Dados da empresa
            dados_mensais: Lista de dados mensais (ordenados por data)
            analise_atual: Última análise realizada
            analise_anterior: Análise anterior (para comparação)
        
        Returns:
            Lista de alertas gerados
        """
        alertas = []
        
        if not dados_mensais:
            # Alerta se não há dados
            alertas.append(Alerta(
                tipo=TipoAlerta.SEM_DADOS.value,
                severidade=Severidade.INFO.value,
                codigo="sem_dados_mensais",
                titulo="Sem dados financeiros",
                mensagem=f"A empresa {empresa.get('razao_social', 'N/A')} não possui dados financeiros cadastrados. "
                         f"Importe dados para começar a receber análises e alertas.",
            ))
            return alertas
        
        # Ordenar dados por período (mais recente primeiro para algumas análises)
        dados_ordenados = sorted(
            dados_mensais,
            key=lambda x: (x.get('ano', 0), x.get('mes', 0)),
            reverse=True
        )
        
        # Último mês disponível
        ultimo_mes = dados_ordenados[0] if dados_ordenados else None
        periodo_ref = f"{ultimo_mes.get('mes', 0):02d}/{ultimo_mes.get('ano', 0)}" if ultimo_mes else None
        
        # 1. Alertas de Caixa
        if self.config.alerta_caixa_ativo:
            alertas.extend(self._verificar_caixa(empresa, dados_ordenados, periodo_ref))
        
        # 2. Alertas de Margem
        if self.config.alerta_margem_ativo:
            alertas.extend(self._verificar_margem(empresa, dados_ordenados, periodo_ref))
        
        # 3. Alertas de Tendência
        if self.config.alerta_tendencia_ativo:
            alertas.extend(self._verificar_tendencia(empresa, dados_ordenados, periodo_ref))
        
        # 4. Alertas de Anomalias
        if self.config.alerta_anomalias_ativo:
            alertas.extend(self._verificar_anomalias(empresa, dados_ordenados, periodo_ref))
        
        # 5. Alertas de Score
        if self.config.alerta_score_ativo and analise_atual:
            alertas.extend(self._verificar_score(empresa, analise_atual, analise_anterior, periodo_ref))
        
        # 6. NOVOS: Alertas de Liquidez e Estrutura (Crise)
        if self.config.alerta_liquidez_ativo:
            alertas.extend(self._verificar_liquidez_estrutura(empresa, dados_ordenados, periodo_ref))
        
        return alertas
    
    def _verificar_liquidez_estrutura(self, empresa: Dict, dados: List[Dict], periodo_ref: str) -> List[Alerta]:
        """Verifica alertas de liquidez, endividamento e estrutura de capital."""
        alertas = []
        
        if not dados:
            return alertas
        
        ultimo = dados[0]  # Dados mais recentes
        
        # Extrair dados do balanço
        ac = ultimo.get('ativo_circulante') or 0
        pc = ultimo.get('passivo_circulante') or 0
        anc = ultimo.get('ativo_nao_circulante') or ultimo.get('imobilizado') or 0
        pnc = ultimo.get('passivo_nao_circulante') or 0
        at = ultimo.get('ativo_total') or (ac + anc) or 0
        pt = pc + pnc
        pl = ultimo.get('patrimonio_liquido') or 0
        estoques = ultimo.get('estoques') or 0
        disponivel = ultimo.get('disponivel') or ultimo.get('caixa') or ultimo.get('disponibilidades') or 0
        
        # === 1. INSOLVÊNCIA (Liquidez Corrente < 1) ===
        if pc > 0 and ac > 0:
            liquidez_corrente = ac / pc
            if liquidez_corrente < self.config.liquidez_corrente_critica:
                alertas.append(Alerta(
                    tipo=TipoAlerta.INSOLVENCIA.value,
                    severidade=Severidade.CRITICO.value,
                    codigo=f"insolvencia_{periodo_ref}",
                    titulo="🚨 INSOLVÊNCIA TÉCNICA",
                    mensagem=f"Liquidez corrente de {liquidez_corrente:.2f} indica que a empresa NÃO consegue "
                             f"pagar suas dívidas de curto prazo. Ativo Circulante (R$ {ac:,.0f}) é menor que "
                             f"Passivo Circulante (R$ {pc:,.0f}). Risco iminente de falência!",
                    valor_atual=liquidez_corrente,
                    valor_limite=self.config.liquidez_corrente_critica,
                    periodo_referencia=periodo_ref
                ))
        
        # === 2. PASSIVO A DESCOBERTO (PL Negativo) ===
        if pl < 0:
            alertas.append(Alerta(
                tipo=TipoAlerta.PASSIVO_DESCOBERTO.value,
                severidade=Severidade.CRITICO.value,
                codigo=f"passivo_descoberto_{periodo_ref}",
                titulo="🚨 PASSIVO A DESCOBERTO",
                mensagem=f"Patrimônio Líquido NEGATIVO de R$ {pl:,.0f}! A empresa está tecnicamente falida. "
                         f"Os prejuízos acumulados superaram todo o capital investido. "
                         f"Situação extremamente crítica que exige ação imediata.",
                valor_atual=pl,
                valor_limite=0,
                periodo_referencia=periodo_ref
            ))
        
        # === 3. ENDIVIDAMENTO CRÍTICO (> 80%) ===
        if at > 0:
            endividamento = (pt / at) * 100
            if endividamento > self.config.endividamento_critico:
                alertas.append(Alerta(
                    tipo=TipoAlerta.ENDIVIDAMENTO_CRITICO.value,
                    severidade=Severidade.CRITICO.value,
                    codigo=f"endividamento_critico_{periodo_ref}",
                    titulo="⚠️ ENDIVIDAMENTO CRÍTICO",
                    mensagem=f"Endividamento geral de {endividamento:.1f}% está muito acima do limite seguro. "
                             f"Passivo Total (R$ {pt:,.0f}) representa mais de {self.config.endividamento_critico}% "
                             f"do Ativo Total (R$ {at:,.0f}). Alto risco de insolvência.",
                    valor_atual=endividamento,
                    valor_limite=self.config.endividamento_critico,
                    periodo_referencia=periodo_ref
                ))
        
        # === 4. LIQUIDEZ SECA CRÍTICA (< 0.8) ===
        if pc > 0 and ac > 0:
            liquidez_seca = (ac - estoques) / pc
            if liquidez_seca < self.config.liquidez_seca_critica:
                alertas.append(Alerta(
                    tipo=TipoAlerta.LIQUIDEZ_SECA_CRITICA.value,
                    severidade=Severidade.ATENCAO.value if liquidez_seca >= 0.5 else Severidade.CRITICO.value,
                    codigo=f"liquidez_seca_critica_{periodo_ref}",
                    titulo="⚠️ LIQUIDEZ SECA BAIXA",
                    mensagem=f"Liquidez seca de {liquidez_seca:.2f} indica dependência excessiva de estoques "
                             f"para pagar dívidas. Sem contar estoques (R$ {estoques:,.0f}), a empresa não consegue "
                             f"cobrir o passivo circulante. Estoques podem estar encalhados.",
                    valor_atual=liquidez_seca,
                    valor_limite=self.config.liquidez_seca_critica,
                    periodo_referencia=periodo_ref
                ))
        
        # === 5. CAPITAL DE GIRO NEGATIVO ===
        capital_giro = ac - pc
        if capital_giro < 0:
            alertas.append(Alerta(
                tipo=TipoAlerta.CAPITAL_GIRO_NEGATIVO.value,
                severidade=Severidade.CRITICO.value,
                codigo=f"capital_giro_negativo_{periodo_ref}",
                titulo="🚨 CAPITAL DE GIRO NEGATIVO",
                mensagem=f"Capital de Giro de R$ {capital_giro:,.0f}. A empresa está financiando ativos "
                         f"de longo prazo com dívidas de curto prazo. Situação insustentável que pode "
                         f"levar à falência rapidamente.",
                valor_atual=capital_giro,
                valor_limite=0,
                periodo_referencia=periodo_ref
            ))
        
        # === 6. PREJUÍZO RECORRENTE ===
        meses_prejuizo = 0
        for d in dados[:6]:  # Últimos 6 meses
            receita = d.get('receita') or d.get('receita_bruta') or 0
            custos = d.get('custos') or d.get('custos_total') or 0
            despesas = d.get('despesas') or d.get('despesas_operacionais') or 0
            folha = d.get('folha') or d.get('despesas_pessoal') or 0
            impostos = d.get('impostos') or 0
            
            lucro = receita - custos - despesas - folha - impostos
            if lucro < 0:
                meses_prejuizo += 1
        
        if meses_prejuizo >= self.config.meses_prejuizo_alerta:
            alertas.append(Alerta(
                tipo=TipoAlerta.PREJUIZO_RECORRENTE.value,
                severidade=Severidade.CRITICO.value,
                codigo=f"prejuizo_recorrente_{periodo_ref}",
                titulo="🚨 PREJUÍZO RECORRENTE",
                mensagem=f"A empresa teve PREJUÍZO em {meses_prejuizo} dos últimos {min(6, len(dados))} meses! "
                         f"Prejuízos consecutivos estão consumindo o patrimônio e comprometendo a "
                         f"capacidade de pagamento. Revisão urgente da operação necessária.",
                valor_atual=meses_prejuizo,
                valor_limite=self.config.meses_prejuizo_alerta,
                periodo_referencia=periodo_ref
            ))
        
        # === 7. CAIXA PRATICAMENTE ZERADO ===
        if disponivel <= 1000 and pc > 10000:  # Caixa muito baixo vs dívidas relevantes
            alertas.append(Alerta(
                tipo=TipoAlerta.CAIXA_CRITICO.value,
                severidade=Severidade.CRITICO.value,
                codigo=f"caixa_zerado_{periodo_ref}",
                titulo="🚨 CAIXA ZERADO",
                mensagem=f"Disponibilidades de apenas R$ {disponivel:,.0f} com Passivo Circulante de "
                         f"R$ {pc:,.0f}. A empresa não tem recursos para operar no dia a dia. "
                         f"Situação de emergência financeira!",
                valor_atual=disponivel,
                valor_limite=pc * 0.05,  # 5% do PC como mínimo
                periodo_referencia=periodo_ref
            ))
        
        return alertas
    
    def _verificar_caixa(self, empresa: Dict, dados: List[Dict], periodo_ref: str) -> List[Alerta]:
        """Verifica alertas relacionados ao caixa."""
        alertas = []
        
        if not dados:
            return alertas
        
        ultimo = dados[0]
        caixa_atual = ultimo.get('caixa', 0) or 0
        
        # Calcular despesas mensais médias (últimos 3 meses)
        despesas_mensais = []
        for d in dados[:3]:
            custos = d.get('custos', 0) or 0
            despesas = d.get('despesas', 0) or 0
            impostos = d.get('impostos', 0) or 0
            folha = d.get('folha', 0) or 0
            despesas_mensais.append(custos + despesas + impostos + folha)
        
        if not despesas_mensais:
            return alertas
        
        despesa_media = statistics.mean(despesas_mensais) if despesas_mensais else 0
        
        if despesa_media <= 0:
            return alertas
        
        # Calcular runway (meses de caixa)
        runway_dias = (caixa_atual / (despesa_media / 30)) if despesa_media > 0 else 999
        
        empresa_nome = empresa.get('razao_social', 'Empresa')
        
        if runway_dias < self.config.caixa_dias_critico:
            alertas.append(Alerta(
                tipo=TipoAlerta.CAIXA_CRITICO.value,
                severidade=Severidade.CRITICO.value,
                codigo=f"caixa_critico_{periodo_ref}",
                titulo=f"🚨 Caixa Crítico - {empresa_nome}",
                mensagem=f"O caixa atual de R$ {caixa_atual:,.2f} cobre apenas {runway_dias:.0f} dias de operação. "
                         f"Ação imediata necessária para evitar problemas de liquidez.",
                valor_atual=runway_dias,
                valor_limite=self.config.caixa_dias_critico,
                periodo_referencia=periodo_ref,
                dados_json=json.dumps({
                    'caixa_atual': caixa_atual,
                    'despesa_media_mensal': despesa_media,
                    'runway_dias': runway_dias
                })
            ))
        elif runway_dias < self.config.caixa_dias_atencao:
            alertas.append(Alerta(
                tipo=TipoAlerta.CAIXA_ATENCAO.value,
                severidade=Severidade.ATENCAO.value,
                codigo=f"caixa_atencao_{periodo_ref}",
                titulo=f"⚠️ Caixa Baixo - {empresa_nome}",
                mensagem=f"O caixa atual de R$ {caixa_atual:,.2f} cobre aproximadamente {runway_dias:.0f} dias. "
                         f"Recomenda-se monitorar de perto e planejar ações preventivas.",
                valor_atual=runway_dias,
                valor_limite=self.config.caixa_dias_atencao,
                periodo_referencia=periodo_ref,
                dados_json=json.dumps({
                    'caixa_atual': caixa_atual,
                    'despesa_media_mensal': despesa_media,
                    'runway_dias': runway_dias
                })
            ))
        
        return alertas
    
    def _verificar_margem(self, empresa: Dict, dados: List[Dict], periodo_ref: str) -> List[Alerta]:
        """Verifica alertas relacionados à margem."""
        alertas = []
        
        if len(dados) < 1:
            return alertas
        
        empresa_nome = empresa.get('razao_social', 'Empresa')
        
        # Calcular margem do último mês
        ultimo = dados[0]
        receita = ultimo.get('receita', 0) or 0
        custos = ultimo.get('custos', 0) or 0
        despesas = ultimo.get('despesas', 0) or 0
        impostos = ultimo.get('impostos', 0) or 0
        folha = ultimo.get('folha', 0) or 0
        
        if receita <= 0:
            return alertas
        
        lucro = receita - custos - despesas - impostos - folha
        margem_atual = (lucro / receita) * 100
        
        # Verificar margem mínima
        if margem_atual < self.config.margem_minima:
            alertas.append(Alerta(
                tipo=TipoAlerta.MARGEM_BAIXA.value,
                severidade=Severidade.CRITICO.value if margem_atual < 0 else Severidade.ATENCAO.value,
                codigo=f"margem_baixa_{periodo_ref}",
                titulo=f"{'🚨' if margem_atual < 0 else '⚠️'} Margem {'Negativa' if margem_atual < 0 else 'Baixa'} - {empresa_nome}",
                mensagem=f"A margem líquida atual é de {margem_atual:.1f}%, "
                         f"{'abaixo de zero' if margem_atual < 0 else f'abaixo do mínimo recomendado de {self.config.margem_minima}%'}. "
                         f"Revise custos e despesas para melhorar a rentabilidade.",
                valor_atual=margem_atual,
                valor_limite=self.config.margem_minima,
                periodo_referencia=periodo_ref,
                dados_json=json.dumps({
                    'receita': receita,
                    'lucro': lucro,
                    'margem': margem_atual
                })
            ))
        
        # Verificar queda de margem (comparar com média dos 3 meses anteriores)
        if len(dados) >= 4:
            margens_anteriores = []
            for d in dados[1:4]:
                r = d.get('receita', 0) or 0
                if r > 0:
                    c = d.get('custos', 0) or 0
                    de = d.get('despesas', 0) or 0
                    im = d.get('impostos', 0) or 0
                    fo = d.get('folha', 0) or 0
                    l = r - c - de - im - fo
                    margens_anteriores.append((l / r) * 100)
            
            if margens_anteriores:
                margem_media_anterior = statistics.mean(margens_anteriores)
                
                if margem_media_anterior > 0:
                    queda_pct = ((margem_media_anterior - margem_atual) / margem_media_anterior) * 100
                    
                    if queda_pct >= self.config.margem_queda_pct:
                        alertas.append(Alerta(
                            tipo=TipoAlerta.MARGEM_QUEDA.value,
                            severidade=Severidade.ATENCAO.value,
                            codigo=f"margem_queda_{periodo_ref}",
                            titulo=f"📉 Queda de Margem - {empresa_nome}",
                            mensagem=f"A margem caiu {queda_pct:.1f}% em relação à média dos últimos 3 meses "
                                     f"(de {margem_media_anterior:.1f}% para {margem_atual:.1f}%). "
                                     f"Investigue as causas dessa redução.",
                            valor_atual=margem_atual,
                            valor_anterior=margem_media_anterior,
                            periodo_referencia=periodo_ref,
                            dados_json=json.dumps({
                                'margem_atual': margem_atual,
                                'margem_media_anterior': margem_media_anterior,
                                'queda_percentual': queda_pct
                            })
                        ))
        
        return alertas
    
    def _verificar_tendencia(self, empresa: Dict, dados: List[Dict], periodo_ref: str) -> List[Alerta]:
        """Verifica alertas relacionados à tendência."""
        alertas = []
        
        n_meses = self.config.tendencia_meses_negativos
        if len(dados) < n_meses:
            return alertas
        
        empresa_nome = empresa.get('razao_social', 'Empresa')
        
        # Verificar meses consecutivos com lucro negativo
        meses_negativos = 0
        for d in dados[:n_meses]:
            receita = d.get('receita', 0) or 0
            custos = d.get('custos', 0) or 0
            despesas = d.get('despesas', 0) or 0
            impostos = d.get('impostos', 0) or 0
            folha = d.get('folha', 0) or 0
            lucro = receita - custos - despesas - impostos - folha
            
            if lucro < 0:
                meses_negativos += 1
            else:
                break  # Interrompe se encontrar mês positivo
        
        if meses_negativos >= n_meses:
            alertas.append(Alerta(
                tipo=TipoAlerta.TENDENCIA_NEGATIVA.value,
                severidade=Severidade.CRITICO.value,
                codigo=f"tendencia_negativa_{periodo_ref}",
                titulo=f"🚨 Tendência Negativa - {empresa_nome}",
                mensagem=f"A empresa apresenta {meses_negativos} meses consecutivos com resultado negativo. "
                         f"É urgente revisar a estrutura de custos e estratégia de receitas.",
                valor_atual=meses_negativos,
                valor_limite=n_meses,
                periodo_referencia=periodo_ref,
            ))
        
        # Verificar queda de faturamento
        if len(dados) >= 2:
            receita_atual = dados[0].get('receita', 0) or 0
            receita_anterior = dados[1].get('receita', 0) or 0
            
            if receita_anterior > 0:
                queda_pct = ((receita_anterior - receita_atual) / receita_anterior) * 100
                
                if queda_pct >= self.config.queda_faturamento_pct:
                    alertas.append(Alerta(
                        tipo=TipoAlerta.QUEDA_FATURAMENTO.value,
                        severidade=Severidade.ATENCAO.value,
                        codigo=f"queda_faturamento_{periodo_ref}",
                        titulo=f"📉 Queda no Faturamento - {empresa_nome}",
                        mensagem=f"O faturamento caiu {queda_pct:.1f}% em relação ao mês anterior "
                                 f"(de R$ {receita_anterior:,.2f} para R$ {receita_atual:,.2f}). "
                                 f"Verifique se há sazonalidade ou perda de clientes.",
                        valor_atual=receita_atual,
                        valor_anterior=receita_anterior,
                        periodo_referencia=periodo_ref,
                        dados_json=json.dumps({
                            'receita_atual': receita_atual,
                            'receita_anterior': receita_anterior,
                            'queda_percentual': queda_pct
                        })
                    ))
        
        return alertas
    
    def _verificar_anomalias(self, empresa: Dict, dados: List[Dict], periodo_ref: str) -> List[Alerta]:
        """Verifica alertas de anomalias estatísticas."""
        alertas = []
        
        if len(dados) < 6:  # Precisa de histórico mínimo
            return alertas
        
        empresa_nome = empresa.get('razao_social', 'Empresa')
        ultimo = dados[0]
        historico = dados[1:13]  # Até 12 meses de histórico
        
        # Verificar anomalia em receita
        receitas = [d.get('receita', 0) or 0 for d in historico if d.get('receita')]
        if len(receitas) >= 3:
            media_receita = statistics.mean(receitas)
            desvio_receita = statistics.stdev(receitas) if len(receitas) > 1 else 0
            receita_atual = ultimo.get('receita', 0) or 0
            
            if desvio_receita > 0:
                z_score = abs(receita_atual - media_receita) / desvio_receita
                
                if z_score > self.config.anomalia_desvio_padrao:
                    direcao = "acima" if receita_atual > media_receita else "abaixo"
                    alertas.append(Alerta(
                        tipo=TipoAlerta.ANOMALIA_RECEITA.value,
                        severidade=Severidade.INFO.value,
                        codigo=f"anomalia_receita_{periodo_ref}",
                        titulo=f"🔍 Receita Atípica - {empresa_nome}",
                        mensagem=f"A receita de R$ {receita_atual:,.2f} está {z_score:.1f} desvios padrão "
                                 f"{direcao} da média histórica (R$ {media_receita:,.2f}). "
                                 f"Investigue se há fatores extraordinários.",
                        valor_atual=receita_atual,
                        valor_anterior=media_receita,
                        periodo_referencia=periodo_ref,
                        dados_json=json.dumps({
                            'receita_atual': receita_atual,
                            'media_historica': media_receita,
                            'desvio_padrao': desvio_receita,
                            'z_score': z_score
                        })
                    ))
        
        # Verificar anomalia em custos
        custos_list = [d.get('custos', 0) or 0 for d in historico if d.get('custos')]
        if len(custos_list) >= 3:
            media_custos = statistics.mean(custos_list)
            desvio_custos = statistics.stdev(custos_list) if len(custos_list) > 1 else 0
            custos_atual = ultimo.get('custos', 0) or 0
            
            if desvio_custos > 0:
                z_score = (custos_atual - media_custos) / desvio_custos
                
                # Só alertar se custos estão ACIMA do normal
                if z_score > self.config.anomalia_desvio_padrao:
                    alertas.append(Alerta(
                        tipo=TipoAlerta.ANOMALIA_CUSTO.value,
                        severidade=Severidade.ATENCAO.value,
                        codigo=f"anomalia_custo_{periodo_ref}",
                        titulo=f"⚠️ Custos Atípicos - {empresa_nome}",
                        mensagem=f"Os custos de R$ {custos_atual:,.2f} estão {z_score:.1f} desvios padrão "
                                 f"acima da média histórica (R$ {media_custos:,.2f}). "
                                 f"Verifique se há despesas extraordinárias ou problemas operacionais.",
                        valor_atual=custos_atual,
                        valor_anterior=media_custos,
                        periodo_referencia=periodo_ref,
                        dados_json=json.dumps({
                            'custos_atual': custos_atual,
                            'media_historica': media_custos,
                            'desvio_padrao': desvio_custos,
                            'z_score': z_score
                        })
                    ))
        
        return alertas
    
    def _verificar_score(
        self,
        empresa: Dict,
        analise_atual: Dict,
        analise_anterior: Optional[Dict],
        periodo_ref: str
    ) -> List[Alerta]:
        """Verifica alertas relacionados ao score de saúde."""
        alertas = []
        
        empresa_nome = empresa.get('razao_social', 'Empresa')
        score_atual = analise_atual.get('score', 0)
        status = analise_atual.get('status', '')
        
        # Score crítico
        if score_atual < self.config.score_critico:
            alertas.append(Alerta(
                tipo=TipoAlerta.SCORE_CRITICO.value,
                severidade=Severidade.CRITICO.value,
                codigo=f"score_critico_{periodo_ref}",
                titulo=f"🚨 Score Crítico - {empresa_nome}",
                mensagem=f"O score de saúde financeira é {score_atual}/100, classificado como '{status}'. "
                         f"A empresa precisa de atenção urgente. Revise o diagnóstico completo.",
                valor_atual=score_atual,
                valor_limite=self.config.score_critico,
                periodo_referencia=periodo_ref,
                dados_json=json.dumps({
                    'score': score_atual,
                    'status': status,
                    'confianca': analise_atual.get('score_confianca', 0)
                })
            ))
        
        # Queda de score
        if analise_anterior:
            score_anterior = analise_anterior.get('score', 0)
            queda = score_anterior - score_atual
            
            if queda >= self.config.score_queda_pontos:
                alertas.append(Alerta(
                    tipo=TipoAlerta.SCORE_QUEDA.value,
                    severidade=Severidade.ATENCAO.value,
                    codigo=f"score_queda_{periodo_ref}",
                    titulo=f"📉 Queda no Score - {empresa_nome}",
                    mensagem=f"O score de saúde caiu {queda} pontos "
                             f"(de {score_anterior} para {score_atual}). "
                             f"Compare as análises para identificar os fatores.",
                    valor_atual=score_atual,
                    valor_anterior=score_anterior,
                    periodo_referencia=periodo_ref,
                    dados_json=json.dumps({
                        'score_atual': score_atual,
                        'score_anterior': score_anterior,
                        'queda': queda
                    })
                ))
        
        return alertas


def gerar_alertas_empresa(
    empresa: Dict,
    dados_mensais: List[Dict],
    analise_atual: Optional[Dict] = None,
    analise_anterior: Optional[Dict] = None,
    config: Optional[Dict] = None
) -> List[Dict]:
    """
    Gera alertas profissionais para uma empresa.
    
    Usa todos os indicadores disponíveis (liquidez, rentabilidade, endividamento,
    ciclo financeiro, tendências) para gerar alertas detalhados.
    
    Args:
        empresa: Dados da empresa
        dados_mensais: Lista de dados mensais
        analise_atual: Última análise (contém indicadores calculados)
        analise_anterior: Análise anterior
        config: Configuração de alertas
    
    Returns:
        Lista de alertas como dicionários
    """
    alertas = []
    
    if not dados_mensais:
        return [{
            'tipo': 'sem_dados',
            'severidade': 'info',
            'codigo': 'sem_dados_001',
            'titulo': '📊 Sem Dados para Análise',
            'mensagem': f"A empresa {empresa.get('razao_social', 'N/A')} não possui dados financeiros. Importe balancetes para receber alertas.",
            'valor_atual': None,
            'valor_limite': None,
            'valor_anterior': None,
            'dados_json': None,
            'periodo_referencia': None
        }]
    
    # Ordenar dados
    dados_ordenados = sorted(
        dados_mensais,
        key=lambda x: (x.get('ano', 0), x.get('mes', 0))
    )
    
    ultimo = dados_ordenados[-1]
    periodo_ref = f"{ultimo.get('mes', 0):02d}/{ultimo.get('ano', 0)}"
    empresa_nome = empresa.get('razao_social', 'Empresa')
    
    # Extrair indicadores (da análise ou calcular)
    indicadores = {}
    if analise_atual:
        resultado = analise_atual.get('resultado_completo', analise_atual.get('resultado', analise_atual))
        indicadores = resultado.get('indicadores', {})
    
    # Se não tem indicadores da análise, calcular do último período
    if not indicadores:
        indicadores = _calcular_indicadores_basicos(ultimo, dados_ordenados)
    
    # =========================================================================
    # 1. ALERTAS DE LIQUIDEZ
    # =========================================================================
    lc = indicadores.get('liquidez_corrente', 0)
    if lc > 0:
        if lc < 0.8:
            alertas.append({
                'tipo': 'liquidez_critica',
                'severidade': 'critico',
                'codigo': f'liq_crit_{periodo_ref}',
                'titulo': f'🚨 Liquidez Corrente Crítica: {lc:.2f}',
                'mensagem': f'{empresa_nome}: Ativo circulante insuficiente para cobrir dívidas de curto prazo. '
                           f'Para cada R$ 1,00 de dívida, há apenas R$ {lc:.2f} em ativos. '
                           f'AÇÃO IMEDIATA: Negociar prazos com fornecedores, acelerar recebimentos, avaliar empréstimo.',
                'valor_atual': lc,
                'valor_limite': 1.0,
                'valor_anterior': None,
                'dados_json': json.dumps({'liquidez_corrente': lc, 'recomendacao': 'Ideal acima de 1.5'}),
                'periodo_referencia': periodo_ref
            })
        elif lc < 1.0:
            alertas.append({
                'tipo': 'liquidez_baixa',
                'severidade': 'atencao',
                'codigo': f'liq_baixa_{periodo_ref}',
                'titulo': f'⚠️ Liquidez Corrente Baixa: {lc:.2f}',
                'mensagem': f'{empresa_nome}: Liquidez abaixo do recomendado (1.0). '
                           f'Empresa opera com margem de segurança muito baixa para imprevistos.',
                'valor_atual': lc,
                'valor_limite': 1.0,
                'valor_anterior': None,
                'dados_json': json.dumps({'liquidez_corrente': lc}),
                'periodo_referencia': periodo_ref
            })
    
    li = indicadores.get('liquidez_imediata', 0)
    if li > 0 and li < 0.1:
        alertas.append({
            'tipo': 'caixa_insuficiente',
            'severidade': 'atencao',
            'codigo': f'caixa_baixo_{periodo_ref}',
            'titulo': f'💰 Caixa Imediato Baixo: {li:.1%}',
            'mensagem': f'{empresa_nome}: Disponibilidades cobrem apenas {li:.1%} das obrigações imediatas. '
                       f'Risco de não conseguir pagar despesas urgentes.',
            'valor_atual': li,
            'valor_limite': 0.2,
            'valor_anterior': None,
            'dados_json': json.dumps({'liquidez_imediata': li}),
            'periodo_referencia': periodo_ref
        })
    
    # =========================================================================
    # 2. ALERTAS DE RENTABILIDADE
    # =========================================================================
    ml = indicadores.get('margem_liquida', 0)
    if ml < 0:
        alertas.append({
            'tipo': 'prejuizo',
            'severidade': 'critico',
            'codigo': f'prejuizo_{periodo_ref}',
            'titulo': f'🔴 Empresa com Prejuízo: {ml:.1f}%',
            'mensagem': f'{empresa_nome}: Margem líquida negativa indica perda em cada venda. '
                       f'URGENTE: Revisar precificação, cortar custos, analisar produtos deficitários.',
            'valor_atual': ml,
            'valor_limite': 0,
            'valor_anterior': None,
            'dados_json': json.dumps({'margem_liquida': ml}),
            'periodo_referencia': periodo_ref
        })
    elif ml > 0 and ml < 5:
        alertas.append({
            'tipo': 'margem_baixa',
            'severidade': 'atencao',
            'codigo': f'margem_baixa_{periodo_ref}',
            'titulo': f'📉 Margem Líquida Baixa: {ml:.1f}%',
            'mensagem': f'{empresa_nome}: Margem de {ml:.1f}% é insuficiente para reinvestimento e crescimento. '
                       f'Média saudável: 10-15%.',
            'valor_atual': ml,
            'valor_limite': 5,
            'valor_anterior': None,
            'dados_json': json.dumps({'margem_liquida': ml}),
            'periodo_referencia': periodo_ref
        })
    elif ml >= 70:
        alertas.append({
            'tipo': 'margem_excelente',
            'severidade': 'info',
            'codigo': f'margem_otima_{periodo_ref}',
            'titulo': f'🌟 Margem Líquida Excelente: {ml:.1f}%',
            'mensagem': f'{empresa_nome}: Margem excepcional de {ml:.1f}%. '
                       f'Empresa muito lucrativa. Considere reinvestir ou distribuir dividendos.',
            'valor_atual': ml,
            'valor_limite': None,
            'valor_anterior': None,
            'dados_json': json.dumps({'margem_liquida': ml}),
            'periodo_referencia': periodo_ref
        })
    
    roe = indicadores.get('roe', 0)
    if roe < 0:
        alertas.append({
            'tipo': 'roe_negativo',
            'severidade': 'critico',
            'codigo': f'roe_neg_{periodo_ref}',
            'titulo': f'📊 ROE Negativo: {roe:.1f}%',
            'mensagem': f'{empresa_nome}: Retorno sobre patrimônio negativo indica destruição de valor. '
                       f'Capital dos sócios está sendo consumido.',
            'valor_atual': roe,
            'valor_limite': 0,
            'valor_anterior': None,
            'dados_json': json.dumps({'roe': roe}),
            'periodo_referencia': periodo_ref
        })
    elif roe > 100:
        alertas.append({
            'tipo': 'roe_muito_alto',
            'severidade': 'atencao',
            'codigo': f'roe_alto_{periodo_ref}',
            'titulo': f'⚠️ ROE Muito Elevado: {roe:.0f}%',
            'mensagem': f'{empresa_nome}: ROE de {roe:.0f}% indica patrimônio líquido muito baixo. '
                       f'Empresa pode estar descapitalizada ou distribuindo lucros em excesso.',
            'valor_atual': roe,
            'valor_limite': 100,
            'valor_anterior': None,
            'dados_json': json.dumps({'roe': roe, 'recomendacao': 'Avaliar capitalização'}),
            'periodo_referencia': periodo_ref
        })
    
    # =========================================================================
    # 3. ALERTAS DE ENDIVIDAMENTO
    # =========================================================================
    endiv = indicadores.get('endividamento_geral', 0)
    if endiv > 85:
        alertas.append({
            'tipo': 'endividamento_critico',
            'severidade': 'critico',
            'codigo': f'endiv_crit_{periodo_ref}',
            'titulo': f'🔴 Endividamento Crítico: {endiv:.0f}%',
            'mensagem': f'{empresa_nome}: {endiv:.0f}% do ativo é financiado por terceiros. '
                       f'Alto risco de insolvência. Evite novos empréstimos, priorize quitação de dívidas.',
            'valor_atual': endiv,
            'valor_limite': 70,
            'valor_anterior': None,
            'dados_json': json.dumps({'endividamento_geral': endiv}),
            'periodo_referencia': periodo_ref
        })
    elif endiv > 70:
        alertas.append({
            'tipo': 'endividamento_alto',
            'severidade': 'atencao',
            'codigo': f'endiv_alto_{periodo_ref}',
            'titulo': f'⚠️ Endividamento Elevado: {endiv:.0f}%',
            'mensagem': f'{empresa_nome}: Endividamento de {endiv:.0f}% acima do recomendado (70%). '
                       f'Maior vulnerabilidade a juros. Capacidade de investimento limitada.',
            'valor_atual': endiv,
            'valor_limite': 70,
            'valor_anterior': None,
            'dados_json': json.dumps({'endividamento_geral': endiv}),
            'periodo_referencia': periodo_ref
        })
    elif endiv > 0 and endiv < 30:
        alertas.append({
            'tipo': 'endividamento_baixo',
            'severidade': 'info',
            'codigo': f'endiv_baixo_{periodo_ref}',
            'titulo': f'💪 Baixo Endividamento: {endiv:.0f}%',
            'mensagem': f'{empresa_nome}: Empresa sólida com apenas {endiv:.0f}% de endividamento. '
                       f'Boa capacidade de crédito se precisar.',
            'valor_atual': endiv,
            'valor_limite': None,
            'valor_anterior': None,
            'dados_json': json.dumps({'endividamento_geral': endiv}),
            'periodo_referencia': periodo_ref
        })
    
    comp_endiv = indicadores.get('composicao_endividamento', 0)
    if comp_endiv > 80:
        alertas.append({
            'tipo': 'divida_curto_prazo',
            'severidade': 'atencao',
            'codigo': f'div_cp_{periodo_ref}',
            'titulo': f'📅 Dívida Concentrada no Curto Prazo: {comp_endiv:.0f}%',
            'mensagem': f'{empresa_nome}: {comp_endiv:.0f}% das dívidas vencem no curto prazo. '
                       f'Pressão no fluxo de caixa. Renegociar prazos com credores.',
            'valor_atual': comp_endiv,
            'valor_limite': 70,
            'valor_anterior': None,
            'dados_json': json.dumps({'composicao_endividamento': comp_endiv}),
            'periodo_referencia': periodo_ref
        })
    
    # =========================================================================
    # 4. ALERTAS DE CICLO FINANCEIRO
    # =========================================================================
    pmr = indicadores.get('pmr', 0)
    if pmr > 90:
        alertas.append({
            'tipo': 'pmr_alto',
            'severidade': 'atencao',
            'codigo': f'pmr_alto_{periodo_ref}',
            'titulo': f'📆 Prazo de Recebimento Longo: {pmr:.0f} dias',
            'mensagem': f'{empresa_nome}: Clientes demoram {pmr:.0f} dias para pagar. '
                       f'Capital parado em recebíveis. Revisar política de crédito, oferecer desconto para antecipação.',
            'valor_atual': pmr,
            'valor_limite': 60,
            'valor_anterior': None,
            'dados_json': json.dumps({'pmr_dias': pmr}),
            'periodo_referencia': periodo_ref
        })
    elif pmr > 365:
        alertas.append({
            'tipo': 'pmr_critico',
            'severidade': 'critico',
            'codigo': f'pmr_crit_{periodo_ref}',
            'titulo': f'🚨 Recebíveis Muito Antigos: {pmr:.0f} dias',
            'mensagem': f'{empresa_nome}: Prazo médio de {pmr:.0f} dias indica problemas graves de cobrança. '
                       f'Possível inadimplência. URGENTE: Analisar aging, considerar provisão para devedores duvidosos.',
            'valor_atual': pmr,
            'valor_limite': 90,
            'valor_anterior': None,
            'dados_json': json.dumps({'pmr_dias': pmr}),
            'periodo_referencia': periodo_ref
        })
    
    ciclo = indicadores.get('ciclo_financeiro', 0)
    if ciclo > 120:
        alertas.append({
            'tipo': 'ciclo_longo',
            'severidade': 'atencao',
            'codigo': f'ciclo_{periodo_ref}',
            'titulo': f'🔄 Ciclo Financeiro Extenso: {ciclo:.0f} dias',
            'mensagem': f'{empresa_nome}: {ciclo:.0f} dias entre pagar fornecedores e receber de clientes. '
                       f'Alta necessidade de capital de giro. Reduzir PMR ou aumentar PMP.',
            'valor_atual': ciclo,
            'valor_limite': 90,
            'valor_anterior': None,
            'dados_json': json.dumps({'ciclo_financeiro': ciclo}),
            'periodo_referencia': periodo_ref
        })
    
    # =========================================================================
    # 5. ALERTAS TRIBUTÁRIOS
    # =========================================================================
    carga = indicadores.get('carga_tributaria', 0)
    if carga > 25:
        alertas.append({
            'tipo': 'carga_tributaria_alta',
            'severidade': 'atencao',
            'codigo': f'trib_alto_{periodo_ref}',
            'titulo': f'💰 Carga Tributária Elevada: {carga:.1f}%',
            'mensagem': f'{empresa_nome}: Impostos representam {carga:.1f}% do faturamento. '
                       f'Avaliar enquadramento tributário, verificar benefícios fiscais.',
            'valor_atual': carga,
            'valor_limite': 20,
            'valor_anterior': None,
            'dados_json': json.dumps({'carga_tributaria': carga}),
            'periodo_referencia': periodo_ref
        })
    
    # =========================================================================
    # 6. ALERTAS DE TENDÊNCIA
    # =========================================================================
    if len(dados_ordenados) >= 3:
        receitas = [d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados_ordenados]
        receitas_validas = [r for r in receitas if r > 0]
        
        if len(receitas_validas) >= 3:
            media_inicio = statistics.mean(receitas_validas[:len(receitas_validas)//2]) if receitas_validas[:len(receitas_validas)//2] else 0
            media_fim = statistics.mean(receitas_validas[len(receitas_validas)//2:]) if receitas_validas[len(receitas_validas)//2:] else 0
            
            if media_inicio > 0:
                variacao = ((media_fim - media_inicio) / media_inicio) * 100
                
                if variacao < -20:
                    alertas.append({
                        'tipo': 'queda_receita_grave',
                        'severidade': 'critico',
                        'codigo': f'queda_rec_{periodo_ref}',
                        'titulo': f'📉 Queda Significativa de Receita: {variacao:.0f}%',
                        'mensagem': f'{empresa_nome}: Receita caiu {abs(variacao):.0f}% no período. '
                                   f'URGENTE: Identificar causas, revisar estratégia comercial, ajustar custos.',
                        'valor_atual': variacao,
                        'valor_limite': -10,
                        'valor_anterior': None,
                        'dados_json': json.dumps({'variacao_receita': variacao}),
                        'periodo_referencia': periodo_ref
                    })
                elif variacao < -10:
                    alertas.append({
                        'tipo': 'queda_receita',
                        'severidade': 'atencao',
                        'codigo': f'queda_rec_mod_{periodo_ref}',
                        'titulo': f'⚠️ Receita em Queda: {variacao:.0f}%',
                        'mensagem': f'{empresa_nome}: Tendência de queda de {abs(variacao):.0f}%. '
                                   f'Monitorar de perto, intensificar ações comerciais.',
                        'valor_atual': variacao,
                        'valor_limite': -10,
                        'valor_anterior': None,
                        'dados_json': json.dumps({'variacao_receita': variacao}),
                        'periodo_referencia': periodo_ref
                    })
                elif variacao > 20:
                    alertas.append({
                        'tipo': 'crescimento_receita',
                        'severidade': 'info',
                        'codigo': f'cresc_rec_{periodo_ref}',
                        'titulo': f'🚀 Crescimento de Receita: +{variacao:.0f}%',
                        'mensagem': f'{empresa_nome}: Receita cresceu {variacao:.0f}% no período. '
                                   f'Garantir que estrutura suporte crescimento, monitorar margens.',
                        'valor_atual': variacao,
                        'valor_limite': None,
                        'valor_anterior': None,
                        'dados_json': json.dumps({'variacao_receita': variacao}),
                        'periodo_referencia': periodo_ref
                    })
    
    # =========================================================================
    # 7. ALERTAS DE PREJUÍZO CONSECUTIVO
    # =========================================================================
    meses_prejuizo = 0
    for d in reversed(dados_ordenados):
        receita = d.get('receita', 0) or d.get('receita_bruta', 0) or 0
        custos = d.get('custos', 0) or d.get('custos_total', 0) or 0
        despesas = d.get('despesas', 0) or d.get('despesas_operacionais', 0) or 0
        impostos = d.get('impostos', 0) or d.get('deducoes_receita', 0) or 0
        lucro = d.get('lucro_liquido', 0) or (receita - custos - despesas - impostos)
        
        if lucro < 0:
            meses_prejuizo += 1
        else:
            break
    
    if meses_prejuizo >= 3:
        alertas.append({
            'tipo': 'prejuizo_consecutivo',
            'severidade': 'critico',
            'codigo': f'prej_consec_{periodo_ref}',
            'titulo': f'🔴 {meses_prejuizo} Meses Consecutivos de Prejuízo',
            'mensagem': f'{empresa_nome}: Empresa opera com prejuízo há {meses_prejuizo} meses. '
                       f'Consumo acelerado de capital. URGENTE: Reestruturação necessária.',
            'valor_atual': meses_prejuizo,
            'valor_limite': 2,
            'valor_anterior': None,
            'dados_json': json.dumps({'meses_prejuizo': meses_prejuizo}),
            'periodo_referencia': periodo_ref
        })
    
    # =========================================================================
    # 8. ALERTAS DE ANOMALIAS
    # =========================================================================
    if len(dados_ordenados) >= 6:
        receitas = [d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados_ordenados]
        receitas_validas = [r for r in receitas if r > 0]
        
        if len(receitas_validas) >= 6:
            media = statistics.mean(receitas_validas)
            desvio = statistics.stdev(receitas_validas) if len(receitas_validas) > 1 else 0
            
            if desvio > 0:
                ultimo_valor = receitas_validas[-1]
                z_score = (ultimo_valor - media) / desvio
                
                if z_score < -2:
                    alertas.append({
                        'tipo': 'anomalia_receita_baixa',
                        'severidade': 'atencao',
                        'codigo': f'anom_baixa_{periodo_ref}',
                        'titulo': f'📊 Receita Atipicamente Baixa',
                        'mensagem': f'{empresa_nome}: Receita {abs(z_score):.1f} desvios padrão abaixo da média. '
                                   f'Investigar: perda de cliente, sazonalidade, ou problema operacional.',
                        'valor_atual': ultimo_valor,
                        'valor_limite': media - (2 * desvio),
                        'valor_anterior': media,
                        'dados_json': json.dumps({'z_score': z_score, 'media': media}),
                        'periodo_referencia': periodo_ref
                    })
    
    # =========================================================================
    # 9. ALERTAS DE GIRO DO ATIVO
    # =========================================================================
    giro = indicadores.get('giro_ativo', 0)
    if giro > 0 and giro < 0.3:
        alertas.append({
            'tipo': 'giro_baixo',
            'severidade': 'atencao',
            'codigo': f'giro_baixo_{periodo_ref}',
            'titulo': f'🏭 Baixo Giro do Ativo: {giro:.2f}x',
            'mensagem': f'{empresa_nome}: Gera apenas R$ {giro:.2f} de receita para cada R$ 1 de ativo. '
                       f'Ativos podem estar subutilizados. Avaliar venda de ativos ociosos.',
            'valor_atual': giro,
            'valor_limite': 0.5,
            'valor_anterior': None,
            'dados_json': json.dumps({'giro_ativo': giro}),
            'periodo_referencia': periodo_ref
        })
    
    # =========================================================================
    # 10. ALERTAS DE EBITDA
    # =========================================================================
    ebitda = indicadores.get('ebitda', 0)
    if ebitda < 0:
        alertas.append({
            'tipo': 'ebitda_negativo',
            'severidade': 'critico',
            'codigo': f'ebitda_neg_{periodo_ref}',
            'titulo': f'🔴 EBITDA Negativo',
            'mensagem': f'{empresa_nome}: Operação não gera caixa. Modelo de negócio inviável no formato atual. '
                       f'URGENTE: Revisar estrutura de custos e precificação.',
            'valor_atual': ebitda,
            'valor_limite': 0,
            'valor_anterior': None,
            'dados_json': json.dumps({'ebitda': ebitda}),
            'periodo_referencia': periodo_ref
        })
    
    # Ordenar por severidade
    ordem = {'critico': 0, 'atencao': 1, 'info': 2}
    alertas.sort(key=lambda a: ordem.get(a.get('severidade', 'info'), 3))
    
    return alertas


def _calcular_indicadores_basicos(ultimo: Dict, dados: List[Dict]) -> Dict:
    """Calcula indicadores básicos quando não há análise disponível."""
    indicadores = {}
    
    # Extrair valores
    receita = ultimo.get('receita', 0) or ultimo.get('receita_bruta', 0) or 0
    custos = ultimo.get('custos', 0) or ultimo.get('custos_total', 0) or 0
    despesas = ultimo.get('despesas', 0) or ultimo.get('despesas_operacionais', 0) or 0
    impostos = ultimo.get('impostos', 0) or ultimo.get('deducoes_receita', 0) or 0
    caixa = ultimo.get('caixa', 0) or ultimo.get('disponivel', 0) or 0
    
    ac = ultimo.get('ativo_circulante', 0) or ultimo.get('ativo_total', 0) or 0
    pc = ultimo.get('passivo_circulante', 0) or 0
    at = ultimo.get('ativo_total', 0) or ac
    pl = ultimo.get('patrimonio_liquido', 0) or ultimo.get('capital_social', 0) or 0
    
    lucro = ultimo.get('lucro_liquido', 0) or (receita - custos - despesas - impostos)
    
    # Liquidez
    if pc > 0:
        indicadores['liquidez_corrente'] = ac / pc
        indicadores['liquidez_imediata'] = caixa / pc
    
    # Rentabilidade
    if receita > 0:
        indicadores['margem_liquida'] = (lucro / receita) * 100
        indicadores['carga_tributaria'] = (impostos / receita) * 100
    
    # ROE e ROA
    if pl > 0:
        indicadores['roe'] = (lucro / pl) * 100
    if at > 0:
        indicadores['roa'] = (lucro / at) * 100
        indicadores['giro_ativo'] = receita / at
    
    # Endividamento
    if at > 0 and pc > 0:
        pnc = ultimo.get('passivo_nao_circulante', 0) or 0
        indicadores['endividamento_geral'] = ((pc + pnc) / at) * 100
        if (pc + pnc) > 0:
            indicadores['composicao_endividamento'] = (pc / (pc + pnc)) * 100
    
    # Ciclo financeiro (simplificado)
    clientes = ultimo.get('clientes', 0) or ultimo.get('duplicatas_receber', 0) or 0
    if receita > 0 and clientes > 0:
        indicadores['pmr'] = (clientes / receita) * 360
    
    indicadores['ciclo_financeiro'] = indicadores.get('pmr', 0)
    
    return indicadores


def gerar_resumo_alertas(alertas: List[Dict]) -> Dict:
    """
    Gera um resumo dos alertas.
    
    Args:
        alertas: Lista de alertas
    
    Returns:
        Resumo com contagens por severidade e tipo
    """
    resumo = {
        'total': len(alertas),
        'por_severidade': {
            'critico': 0,
            'atencao': 0,
            'info': 0
        },
        'por_tipo': {},
        'mais_recentes': alertas[:5] if alertas else []
    }
    
    for a in alertas:
        sev = a.get('severidade', 'info')
        tipo = a.get('tipo', 'outro')
        
        if sev in resumo['por_severidade']:
            resumo['por_severidade'][sev] += 1
        
        if tipo not in resumo['por_tipo']:
            resumo['por_tipo'][tipo] = 0
        resumo['por_tipo'][tipo] += 1
    
    return resumo
