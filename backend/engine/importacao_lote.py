"""
Serviço de Importação em Lote e Análise Profunda
Sistema Contábil Profissional

Este módulo:
1. Processa múltiplos arquivos de balancete
2. Extrai dados completos de cada período
3. Calcula indicadores avançados
4. Gera insights e alertas automáticos
"""

import os
import hashlib
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json


# Importar o importador de balancetes
try:
    from importers.importador_balancete_final import (
        importar_balancete,
        ImportadorBalancete,
        BalanceteImportado,
        ResultadoImportacao
    )
    IMPORTADOR_DISPONIVEL = True
except ImportError:
    IMPORTADOR_DISPONIVEL = False


# ============================================================================
# ESTRUTURAS DE DADOS
# ============================================================================

@dataclass
class ArquivoProcessado:
    """Resultado do processamento de um arquivo."""
    nome_arquivo: str
    sucesso: bool
    mensagem: str
    competencia: Optional[str] = None
    dados: Optional[Dict] = None
    avisos: List[str] = field(default_factory=list)
    erros: List[str] = field(default_factory=list)


@dataclass
class ResultadoImportacaoLote:
    """Resultado da importação em lote."""
    total_arquivos: int
    processados_sucesso: int
    processados_erro: int
    empresa_id: Optional[int] = None
    empresa_nome: Optional[str] = None
    empresa_cnpj: Optional[str] = None
    empresa_criada: bool = False
    arquivos: List[ArquivoProcessado] = field(default_factory=list)
    resumo: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'total_arquivos': self.total_arquivos,
            'processados_sucesso': self.processados_sucesso,
            'processados_erro': self.processados_erro,
            'empresa': {
                'id': self.empresa_id,
                'nome': self.empresa_nome,
                'cnpj': self.empresa_cnpj,
                'criada': self.empresa_criada
            },
            'arquivos': [
                {
                    'nome': a.nome_arquivo,
                    'sucesso': a.sucesso,
                    'mensagem': a.mensagem,
                    'competencia': a.competencia,
                    'avisos': a.avisos,
                    'erros': a.erros
                }
                for a in self.arquivos
            ],
            'resumo': self.resumo
        }


# ============================================================================
# CALCULADORA DE INDICADORES
# ============================================================================

class CalculadoraIndicadores:
    """Calcula indicadores financeiros avançados."""
    
    @staticmethod
    def calcular_todos(dados: Dict) -> Dict:
        """Calcula todos os indicadores a partir dos dados do balancete."""
        indicadores = {}
        
        # Extrair valores base - aceitar múltiplos nomes de campos
        at = float(dados.get('ativo_total') or dados.get('ativo_circulante') or 0)
        ac = float(dados.get('ativo_circulante') or dados.get('ativo_total') or 0)
        anc = float(dados.get('ativo_nao_circulante') or 0)
        disp = float(dados.get('disponivel') or dados.get('caixa') or 0) + float(dados.get('bancos') or 0)
        est = float(dados.get('estoques') or 0)
        clientes = float(dados.get('clientes') or dados.get('duplicatas_receber') or 0)
        
        pt = float(dados.get('passivo_total') or 0)
        pc = float(dados.get('passivo_circulante') or 0)
        pnc = float(dados.get('passivo_nao_circulante') or 0)
        fornecedores = float(dados.get('fornecedores') or 0)
        
        pl = float(dados.get('patrimonio_liquido') or dados.get('capital_social') or 0)
        
        # Receita - aceitar vários nomes
        rb = float(dados.get('receita_bruta') or dados.get('receita_servicos') or dados.get('receita') or 0)
        ded = float(dados.get('deducoes_receita') or dados.get('impostos_sobre_vendas') or dados.get('impostos') or 0)
        rl = rb - ded
        
        custos = float(dados.get('custos_total') or dados.get('custos') or dados.get('cmv') or dados.get('csp') or 0)
        lb = rl - custos
        
        desp_op = float(dados.get('despesas_operacionais') or dados.get('despesas') or 0)
        desp_fin = float(dados.get('despesas_financeiras') or 0)
        rec_fin = float(dados.get('receitas_financeiras') or 0)
        
        ll = float(dados.get('lucro_liquido') or dados.get('lucro_exercicio') or 0)
        
        # Se não tem lucro_liquido, calcular
        if ll == 0 and rb > 0:
            ll = rb - ded - custos - desp_op - desp_fin + rec_fin
        
        # Impostos - aceitar vários formatos
        iss = float(dados.get('iss_deducao') or dados.get('iss') or 0)
        pis = float(dados.get('pis_deducao') or dados.get('pis') or 0)
        cofins = float(dados.get('cofins_deducao') or dados.get('cofins') or 0)
        irpj = float(dados.get('irpj_deducao') or dados.get('irpj') or 0)
        csll = float(dados.get('csll_deducao') or dados.get('csll') or 0)
        icms = float(dados.get('icms_deducao') or dados.get('icms') or 0)
        impostos_total = iss + pis + cofins + irpj + csll + icms
        
        # Se não tem impostos detalhados, usar deduções
        if impostos_total == 0:
            impostos_total = ded
        
        # Depreciação
        depreciacao = float(dados.get('depreciacao_amortizacao') or 0)
        
        # =========================================================================
        # INDICADORES DE LIQUIDEZ
        # =========================================================================
        if pc > 0:
            indicadores['liquidez_corrente'] = round(ac / pc, 2)
            indicadores['liquidez_seca'] = round((ac - est) / pc, 2)
            indicadores['liquidez_imediata'] = round(disp / pc, 4)
        else:
            indicadores['liquidez_corrente'] = 0
            indicadores['liquidez_seca'] = 0
            indicadores['liquidez_imediata'] = 0
        
        if (pc + pnc) > 0:
            indicadores['liquidez_geral'] = round((ac + anc) / (pc + pnc), 2)
        else:
            indicadores['liquidez_geral'] = 0
        
        # =========================================================================
        # INDICADORES DE RENTABILIDADE
        # =========================================================================
        if rb > 0:
            indicadores['margem_bruta'] = round((lb / rb) * 100, 2)
            indicadores['margem_operacional'] = round(((lb - desp_op) / rb) * 100, 2)
            indicadores['margem_liquida'] = round((ll / rb) * 100, 2)
            indicadores['carga_tributaria'] = round((impostos_total / rb) * 100, 2)
            
            # EBITDA = Lucro Operacional + Depreciação
            ebitda = ll + desp_fin - rec_fin + depreciacao + irpj + csll
            indicadores['ebitda'] = round(ebitda, 2)
            indicadores['margem_ebitda'] = round((ebitda / rb) * 100, 2)
        else:
            indicadores['margem_bruta'] = 0
            indicadores['margem_operacional'] = 0
            indicadores['margem_liquida'] = 0
            indicadores['carga_tributaria'] = 0
            indicadores['ebitda'] = 0
            indicadores['margem_ebitda'] = 0
        
        if pl > 0:
            indicadores['roe'] = round((ll / pl) * 100, 2)
        else:
            indicadores['roe'] = 0
        
        if at > 0:
            indicadores['roa'] = round((ll / at) * 100, 2)
            indicadores['giro_ativo'] = round(rb / at, 2)
        else:
            indicadores['roa'] = 0
            indicadores['giro_ativo'] = 0
        
        # ROIC = NOPAT / Capital Investido
        capital_investido = pl + pnc
        nopat = ll + desp_fin * 0.66  # Ajuste fiscal aproximado
        if capital_investido > 0:
            indicadores['roic'] = round((nopat / capital_investido) * 100, 2)
            indicadores['nopat'] = round(nopat, 2)
        else:
            indicadores['roic'] = 0
            indicadores['nopat'] = 0
        
        # =========================================================================
        # INDICADORES DE ENDIVIDAMENTO
        # =========================================================================
        if at > 0:
            indicadores['endividamento_geral'] = round(((pc + pnc) / at) * 100, 2)
        else:
            indicadores['endividamento_geral'] = 0
        
        if pl > 0:
            indicadores['endividamento_pl'] = round(((pc + pnc) / pl) * 100, 2)
        else:
            indicadores['endividamento_pl'] = 0
        
        if (pc + pnc) > 0:
            indicadores['composicao_endividamento'] = round((pc / (pc + pnc)) * 100, 2)
        else:
            indicadores['composicao_endividamento'] = 0
        
        if pl > 0:
            imob = float(dados.get('imobilizado', 0) or 0)
            indicadores['imobilizacao_pl'] = round((imob / pl) * 100, 2)
        else:
            indicadores['imobilizacao_pl'] = 0
        
        # =========================================================================
        # INDICADORES DE ATIVIDADE (Prazos Médios)
        # =========================================================================
        clientes = float(dados.get('clientes', 0) or dados.get('duplicatas_receber', 0) or 0)
        fornecedores = float(dados.get('fornecedores', 0) or 0)
        
        if rb > 0:
            # PMR = (Clientes / Receita) * 360
            indicadores['pmr'] = round((clientes / rb) * 360, 0)
        else:
            indicadores['pmr'] = 0
        
        if custos > 0:
            # PME = (Estoques / Custo) * 360
            indicadores['pme'] = round((est / custos) * 360, 0) if est > 0 else 0
            # PMP = (Fornecedores / Custo) * 360
            indicadores['pmp'] = round((fornecedores / custos) * 360, 0) if fornecedores > 0 else 0
        else:
            indicadores['pme'] = 0
            indicadores['pmp'] = 0
        
        # Ciclo Financeiro = PME + PMR - PMP
        indicadores['ciclo_financeiro'] = indicadores['pme'] + indicadores['pmr'] - indicadores['pmp']
        
        return indicadores


# ============================================================================
# GERADOR DE INSIGHTS
# ============================================================================

class GeradorInsights:
    """Gera insights e alertas a partir dos indicadores."""
    
    # Parâmetros de referência
    REFERENCIAS = {
        'liquidez_corrente': {'min': 1.0, 'ideal': 1.5, 'max': 3.0},
        'liquidez_seca': {'min': 0.8, 'ideal': 1.2, 'max': 2.5},
        'liquidez_imediata': {'min': 0.1, 'ideal': 0.3, 'max': 1.0},
        'margem_bruta': {'min': 20, 'ideal': 35, 'max': 70},
        'margem_liquida': {'min': 5, 'ideal': 15, 'max': 50},
        'roe': {'min': 10, 'ideal': 20, 'max': 100},
        'roa': {'min': 5, 'ideal': 10, 'max': 30},
        'endividamento_geral': {'min': 0, 'ideal': 50, 'max': 80},
        'carga_tributaria': {'min': 5, 'ideal': 20, 'max': 40},
        'ciclo_financeiro': {'min': -30, 'ideal': 30, 'max': 90},
    }
    
    @classmethod
    def gerar_insights(cls, indicadores: Dict, dados: Dict) -> List[Dict]:
        """Gera lista de insights baseados nos indicadores."""
        insights = []
        
        # =====================================================================
        # ANÁLISE DE LIQUIDEZ
        # =====================================================================
        lc = indicadores.get('liquidez_corrente', 0)
        if lc < 1.0:
            insights.append({
                'tipo': 'alerta',
                'categoria': 'liquidez',
                'titulo': 'Liquidez Corrente Crítica',
                'descricao': f'Liquidez corrente de {lc:.2f} indica que a empresa pode ter dificuldades para pagar suas dívidas de curto prazo.',
                'recomendacao': 'Considere renegociar prazos com fornecedores, antecipar recebíveis ou buscar capital de giro.',
                'severidade': 'alta',
                'valor': lc
            })
        elif lc > 3.0:
            insights.append({
                'tipo': 'atencao',
                'categoria': 'liquidez',
                'titulo': 'Liquidez Corrente Elevada',
                'descricao': f'Liquidez corrente de {lc:.2f} pode indicar recursos ociosos que poderiam ser melhor aplicados.',
                'recomendacao': 'Avalie oportunidades de investimento ou expansão do negócio.',
                'severidade': 'baixa',
                'valor': lc
            })
        elif lc >= 1.5:
            insights.append({
                'tipo': 'positivo',
                'categoria': 'liquidez',
                'titulo': 'Liquidez Corrente Saudável',
                'descricao': f'Liquidez corrente de {lc:.2f} indica boa capacidade de pagamento.',
                'severidade': 'info',
                'valor': lc
            })
        
        # =====================================================================
        # ANÁLISE DE RENTABILIDADE
        # =====================================================================
        ml = indicadores.get('margem_liquida', 0)
        if ml < 5:
            insights.append({
                'tipo': 'alerta',
                'categoria': 'rentabilidade',
                'titulo': 'Margem Líquida Baixa',
                'descricao': f'Margem líquida de {ml:.2f}% está abaixo do ideal para a maioria dos setores.',
                'recomendacao': 'Revise estrutura de custos, renegocie com fornecedores e avalie política de preços.',
                'severidade': 'alta',
                'valor': ml
            })
        elif ml > 30:
            insights.append({
                'tipo': 'positivo',
                'categoria': 'rentabilidade',
                'titulo': 'Margem Líquida Excelente',
                'descricao': f'Margem líquida de {ml:.2f}% é excelente. A empresa está muito rentável.',
                'severidade': 'info',
                'valor': ml
            })
        
        roe = indicadores.get('roe', 0)
        if roe > 100:
            insights.append({
                'tipo': 'atencao',
                'categoria': 'rentabilidade',
                'titulo': 'ROE Muito Elevado',
                'descricao': f'ROE de {roe:.2f}% pode indicar patrimônio líquido muito baixo em relação ao lucro.',
                'recomendacao': 'Considere aumentar o capital social para fortalecer a estrutura patrimonial.',
                'severidade': 'media',
                'valor': roe
            })
        elif roe > 20:
            insights.append({
                'tipo': 'positivo',
                'categoria': 'rentabilidade',
                'titulo': 'Excelente Retorno sobre Patrimônio',
                'descricao': f'ROE de {roe:.2f}% indica excelente retorno para os sócios.',
                'severidade': 'info',
                'valor': roe
            })
        
        # =====================================================================
        # ANÁLISE DE ENDIVIDAMENTO
        # =====================================================================
        end = indicadores.get('endividamento_geral', 0)
        if end > 80:
            insights.append({
                'tipo': 'alerta',
                'categoria': 'endividamento',
                'titulo': 'Endividamento Elevado',
                'descricao': f'Endividamento de {end:.2f}% do ativo total é considerado alto.',
                'recomendacao': 'Priorize a redução de dívidas e evite novos financiamentos.',
                'severidade': 'alta',
                'valor': end
            })
        elif end < 30:
            insights.append({
                'tipo': 'positivo',
                'categoria': 'endividamento',
                'titulo': 'Baixo Endividamento',
                'descricao': f'Endividamento de {end:.2f}% indica estrutura conservadora.',
                'severidade': 'info',
                'valor': end
            })
        
        # =====================================================================
        # ANÁLISE TRIBUTÁRIA
        # =====================================================================
        ct = indicadores.get('carga_tributaria', 0)
        rb = float(dados.get('receita_bruta', 0) or 0)
        
        if ct > 0 and rb > 0:
            if ct > 30:
                insights.append({
                    'tipo': 'atencao',
                    'categoria': 'tributario',
                    'titulo': 'Carga Tributária Elevada',
                    'descricao': f'Carga tributária de {ct:.2f}% está acima da média. Pode haver oportunidades de planejamento tributário.',
                    'recomendacao': 'Consulte um especialista para avaliar enquadramento fiscal e benefícios disponíveis.',
                    'severidade': 'media',
                    'valor': ct
                })
            
            # Analisar distribuição de impostos
            iss = float(dados.get('iss_deducao', 0) or 0)
            irpj = float(dados.get('irpj_deducao', 0) or 0)
            csll = float(dados.get('csll_deducao', 0) or 0)
            
            if irpj + csll > rb * 0.15:  # Mais de 15% da receita
                insights.append({
                    'tipo': 'atencao',
                    'categoria': 'tributario',
                    'titulo': 'Alto IRPJ/CSLL',
                    'descricao': f'IRPJ e CSLL representam mais de 15% da receita.',
                    'recomendacao': 'Avalie se o regime de Lucro Presumido é o mais vantajoso para a empresa.',
                    'severidade': 'media',
                    'valor': (irpj + csll) / rb * 100 if rb > 0 else 0
                })
        
        # =====================================================================
        # ANÁLISE DE CAPITAL DE GIRO
        # =====================================================================
        ciclo = indicadores.get('ciclo_financeiro', 0)
        if ciclo > 60:
            insights.append({
                'tipo': 'alerta',
                'categoria': 'capital_giro',
                'titulo': 'Ciclo Financeiro Longo',
                'descricao': f'Ciclo financeiro de {ciclo:.0f} dias indica necessidade elevada de capital de giro.',
                'recomendacao': 'Busque reduzir prazos de recebimento e estoques, ou aumentar prazos com fornecedores.',
                'severidade': 'media',
                'valor': ciclo
            })
        elif ciclo < 0:
            insights.append({
                'tipo': 'positivo',
                'categoria': 'capital_giro',
                'titulo': 'Ciclo Financeiro Negativo',
                'descricao': f'Ciclo financeiro de {ciclo:.0f} dias é positivo - a empresa financia suas operações com recursos de terceiros.',
                'severidade': 'info',
                'valor': ciclo
            })
        
        # =====================================================================
        # ANÁLISE DE CLIENTES
        # =====================================================================
        clientes = float(dados.get('clientes', 0) or 0)
        if clientes > 0 and rb > 0:
            concentracao = clientes / rb * 100
            if concentracao > 50:
                insights.append({
                    'tipo': 'atencao',
                    'categoria': 'comercial',
                    'titulo': 'Alta Concentração em Recebíveis',
                    'descricao': f'Clientes a receber representam {concentracao:.1f}% da receita bruta.',
                    'recomendacao': 'Monitore a inadimplência e considere políticas de cobrança mais efetivas.',
                    'severidade': 'media',
                    'valor': concentracao
                })
        
        # =====================================================================
        # ANÁLISE DE DISTRIBUIÇÃO DE LUCROS
        # =====================================================================
        dividendos = float(dados.get('dividendos_pagar', 0) or 0)
        ll = float(dados.get('lucro_liquido', 0) or 0)
        
        if ll > 0 and dividendos > ll * 0.8:
            insights.append({
                'tipo': 'atencao',
                'categoria': 'patrimonial',
                'titulo': 'Alta Distribuição de Lucros',
                'descricao': f'Dividendos representam mais de 80% do lucro líquido.',
                'recomendacao': 'Considere reter mais lucros para fortalecer o capital de giro.',
                'severidade': 'baixa',
                'valor': dividendos / ll * 100 if ll > 0 else 0
            })
        
        return insights
    
    @classmethod
    def calcular_score(cls, indicadores: Dict) -> int:
        """Calcula score de saúde financeira de 0 a 100."""
        score = 50  # Base
        
        # Liquidez (peso 25)
        lc = indicadores.get('liquidez_corrente', 0)
        if lc >= 1.5:
            score += 10
        elif lc >= 1.0:
            score += 5
        elif lc < 0.8:
            score -= 10
        
        li = indicadores.get('liquidez_imediata', 0)
        if li >= 0.3:
            score += 5
        elif li < 0.1:
            score -= 5
        
        # Rentabilidade (peso 30)
        ml = indicadores.get('margem_liquida', 0)
        if ml >= 20:
            score += 15
        elif ml >= 10:
            score += 10
        elif ml >= 5:
            score += 5
        elif ml < 0:
            score -= 15
        
        roe = indicadores.get('roe', 0)
        if 15 <= roe <= 50:
            score += 10
        elif roe > 50:
            score += 5
        elif roe < 5:
            score -= 5
        
        # Endividamento (peso 20)
        end = indicadores.get('endividamento_geral', 0)
        if end <= 40:
            score += 10
        elif end <= 60:
            score += 5
        elif end > 80:
            score -= 10
        
        # Eficiência (peso 15)
        giro = indicadores.get('giro_ativo', 0)
        if giro >= 1.5:
            score += 10
        elif giro >= 1.0:
            score += 5
        
        ciclo = indicadores.get('ciclo_financeiro', 0)
        if ciclo <= 30:
            score += 5
        elif ciclo > 90:
            score -= 5
        
        # Garantir limites
        return max(0, min(100, score))


# ============================================================================
# SERVIÇO DE IMPORTAÇÃO EM LOTE
# ============================================================================

class ServicoImportacaoLote:
    """Serviço para importar múltiplos balancetes."""
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.importador = ImportadorBalancete() if IMPORTADOR_DISPONIVEL else None
        self.calculadora = CalculadoraIndicadores()
        self.gerador_insights = GeradorInsights()
    
    def processar_arquivos(
        self, 
        arquivos: List[Tuple[bytes, str]], 
        contador_id: int
    ) -> ResultadoImportacaoLote:
        """
        Processa múltiplos arquivos de balancete.
        
        Args:
            arquivos: Lista de tuplas (conteudo_bytes, nome_arquivo)
            contador_id: ID do contador
        
        Returns:
            ResultadoImportacaoLote com status de cada arquivo
        """
        resultado = ResultadoImportacaoLote(
            total_arquivos=len(arquivos),
            processados_sucesso=0,
            processados_erro=0
        )
        
        empresa_info = None
        dados_por_competencia = {}
        
        # Processar cada arquivo
        for conteudo, nome_arquivo in arquivos:
            try:
                # Importar balancete
                res = self.importador.importar(conteudo, nome_arquivo)
                
                if not res.sucesso:
                    resultado.arquivos.append(ArquivoProcessado(
                        nome_arquivo=nome_arquivo,
                        sucesso=False,
                        mensagem=res.mensagem,
                        erros=res.erros
                    ))
                    resultado.processados_erro += 1
                    continue
                
                # Extrair dados
                balancete = res.balancete
                
                # Capturar info da empresa (do primeiro arquivo com sucesso)
                if empresa_info is None:
                    empresa_info = {
                        'nome': balancete.empresa.nome,
                        'cnpj': balancete.empresa.cnpj,
                        'cnpj_formatado': balancete.empresa.cnpj_formatado,
                        'contador_nome': balancete.empresa.contador_nome,
                        'contador_crc': balancete.empresa.contador_crc,
                        'contador_cpf': balancete.empresa.contador_cpf,
                        'sistema': balancete.empresa.sistema_origem,
                        'socios': [s.to_dict() for s in balancete.empresa.socios]
                    }
                
                # Determinar competência
                if balancete.periodo_fim:
                    competencia = balancete.periodo_fim.strftime('%Y-%m')
                else:
                    competencia = datetime.now().strftime('%Y-%m')
                
                # Calcular indicadores
                balancete.calcular_indicadores()
                
                # Preparar dados completos para salvar
                dados_completos = {
                    'competencia': competencia,
                    'periodo_inicio': balancete.periodo_inicio.isoformat() if balancete.periodo_inicio else None,
                    'periodo_fim': balancete.periodo_fim.isoformat() if balancete.periodo_fim else None,
                    **balancete.totais,
                    **{f'ind_{k}': v for k, v in balancete.indicadores.items()},
                    'arquivo_origem': nome_arquivo,
                    'hash_arquivo': hashlib.md5(conteudo).hexdigest(),
                    'clientes': [c.to_dict() for c in balancete.clientes],
                    'insights': self.gerador_insights.gerar_insights(balancete.indicadores, balancete.totais),
                    'score': self.gerador_insights.calcular_score(balancete.indicadores)
                }
                
                dados_por_competencia[competencia] = dados_completos
                
                resultado.arquivos.append(ArquivoProcessado(
                    nome_arquivo=nome_arquivo,
                    sucesso=True,
                    mensagem=f'Processado: {competencia}',
                    competencia=competencia,
                    dados=dados_completos,
                    avisos=res.avisos
                ))
                resultado.processados_sucesso += 1
                
            except Exception as e:
                resultado.arquivos.append(ArquivoProcessado(
                    nome_arquivo=nome_arquivo,
                    sucesso=False,
                    mensagem=f'Erro: {str(e)}',
                    erros=[str(e)]
                ))
                resultado.processados_erro += 1
        
        # Definir info da empresa no resultado
        if empresa_info:
            resultado.empresa_nome = empresa_info['nome']
            resultado.empresa_cnpj = empresa_info['cnpj']
        
        # Gerar resumo consolidado
        if dados_por_competencia:
            resultado.resumo = self._gerar_resumo(dados_por_competencia, empresa_info)
        
        return resultado
    
    def _gerar_resumo(self, dados_por_competencia: Dict, empresa_info: Dict) -> Dict:
        """Gera resumo consolidado de todos os períodos."""
        competencias = sorted(dados_por_competencia.keys())
        
        if not competencias:
            return {}
        
        # Pegar dados mais recentes
        ultimo = dados_por_competencia[competencias[-1]]
        
        # Calcular totais acumulados e médias
        total_receita = sum(d.get('receita_bruta', 0) or 0 for d in dados_por_competencia.values())
        total_lucro = sum(d.get('lucro_liquido', 0) or 0 for d in dados_por_competencia.values())
        total_impostos = sum(
            (d.get('iss_deducao', 0) or 0) +
            (d.get('pis_deducao', 0) or 0) +
            (d.get('cofins_deducao', 0) or 0) +
            (d.get('irpj_deducao', 0) or 0) +
            (d.get('csll_deducao', 0) or 0)
            for d in dados_por_competencia.values()
        )
        
        # Evolução
        if len(competencias) > 1:
            primeiro = dados_por_competencia[competencias[0]]
            receita_primeiro = primeiro.get('receita_bruta', 0) or 0
            receita_ultimo = ultimo.get('receita_bruta', 0) or 0
            
            if receita_primeiro > 0:
                variacao_receita = ((receita_ultimo - receita_primeiro) / receita_primeiro) * 100
            else:
                variacao_receita = 0
        else:
            variacao_receita = 0
        
        return {
            'empresa': empresa_info,
            'periodos': competencias,
            'total_meses': len(competencias),
            'periodo_inicial': competencias[0],
            'periodo_final': competencias[-1],
            'totais_acumulados': {
                'receita_bruta': total_receita,
                'lucro_liquido': total_lucro,
                'impostos': total_impostos,
                'margem_media': round(total_lucro / total_receita * 100, 2) if total_receita > 0 else 0
            },
            'ultimo_periodo': {
                'ativo_total': ultimo.get('ativo_total', 0),
                'passivo_total': ultimo.get('passivo_total', 0),
                'patrimonio_liquido': ultimo.get('patrimonio_liquido', 0),
                'receita_bruta': ultimo.get('receita_bruta', 0),
                'lucro_liquido': ultimo.get('lucro_liquido', 0),
                'score': ultimo.get('score', 50)
            },
            'evolucao': {
                'variacao_receita': round(variacao_receita, 2)
            },
            'insights': ultimo.get('insights', [])[:5]  # Top 5 insights
        }


# ============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# ============================================================================

def processar_importacao_lote(
    arquivos: List[Tuple[bytes, str]], 
    contador_id: int
) -> Dict:
    """
    Processa importação em lote e retorna resultado.
    
    Args:
        arquivos: Lista de (conteudo_bytes, nome_arquivo)
        contador_id: ID do contador
    
    Returns:
        Dicionário com resultado completo
    """
    servico = ServicoImportacaoLote()
    resultado = servico.processar_arquivos(arquivos, contador_id)
    return resultado.to_dict()


def calcular_indicadores(dados: Dict) -> Dict:
    """Calcula todos os indicadores para um conjunto de dados."""
    return CalculadoraIndicadores.calcular_todos(dados)


def gerar_insights(indicadores: Dict, dados: Dict) -> List[Dict]:
    """Gera insights a partir dos indicadores."""
    return GeradorInsights.gerar_insights(indicadores, dados)


def calcular_score(indicadores: Dict) -> int:
    """Calcula score de saúde financeira."""
    return GeradorInsights.calcular_score(indicadores)
