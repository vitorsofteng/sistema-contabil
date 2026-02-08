#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parecer Consultivo por IA - Sistema Kontabil
Gera análise financeira em linguagem natural usando Claude API.
"""

import os
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger("contabil.parecer_ia")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"


def gerar_parecer(empresa: Dict, indicadores: Dict) -> Optional[str]:
    """
    Gera parecer consultivo financeiro usando Claude API.
    
    Args:
        empresa: dict com razao_social, cnpj, regime_tributario, setor
        indicadores: dict com todos os indicadores calculados
    
    Returns:
        String com o parecer em texto ou None se falhar
    """
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY não configurada. Parecer IA não disponível.")
        return None
    
    try:
        import httpx
    except ImportError:
        try:
            import requests as httpx
            httpx.post = httpx.post  # compatibility
        except ImportError:
            logger.error("Nem httpx nem requests disponível para chamada à API.")
            return None
    
    prompt = _montar_prompt(empresa, indicadores)
    
    try:
        response = httpx.post(
            ANTHROPIC_API_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": MODEL,
                "max_tokens": 3000,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=60
        )
        
        if hasattr(response, 'status_code'):
            status = response.status_code
        else:
            status = response.status
        
        if status != 200:
            logger.error(f"Erro na API Anthropic: status {status}")
            return None
        
        data = response.json()
        texto = data.get("content", [{}])[0].get("text", "")
        
        if not texto:
            logger.error("Resposta vazia da API Anthropic")
            return None
        
        logger.info(f"Parecer IA gerado com sucesso ({len(texto)} caracteres)")
        return texto
        
    except Exception as e:
        logger.error(f"Erro ao gerar parecer IA: {type(e).__name__}")
        return None


def _fmt_moeda(valor):
    """Formata valor para moeda brasileira."""
    if not valor:
        return "R$ 0,00"
    try:
        v = float(valor)
        fmt = f"R$ {abs(v):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"-{fmt}" if v < 0 else fmt
    except:
        return "R$ 0,00"


def _montar_prompt(empresa: Dict, ind: Dict) -> str:
    """Monta o prompt com os dados financeiros para a IA."""
    
    nome = empresa.get('razao_social', 'Empresa')
    cnpj = empresa.get('cnpj', '')
    setor = empresa.get('setor', 'não informado')
    regime = empresa.get('regime_tributario', 'não informado')
    
    return f"""Você é um consultor financeiro sênior especializado em análise de empresas brasileiras. 
Elabore um PARECER CONSULTIVO FINANCEIRO profissional e personalizado com base nos dados abaixo.

EMPRESA: {nome}
CNPJ: {cnpj}
Setor: {setor}
Regime Tributário: {regime}
Período analisado: {ind.get('periodo_inicio', '')} a {ind.get('periodo_fim', '')} ({ind.get('meses_analisados', 0)} meses)

═══════════════════════════════════════
DEMONSTRAÇÃO DO RESULTADO (DRE) - ACUMULADO
═══════════════════════════════════════
Receita Bruta: {_fmt_moeda(ind.get('receita_bruta'))}
Receita de Serviços: {_fmt_moeda(ind.get('receita_servicos'))}
(-) Deduções: {_fmt_moeda(ind.get('deducoes_receita'))}
= Receita Líquida: {_fmt_moeda(ind.get('receita_liquida'))}
(-) Custos: {_fmt_moeda(ind.get('custos_total'))}
= Lucro Bruto: {_fmt_moeda(ind.get('lucro_bruto'))}
(-) Despesas Operacionais: {_fmt_moeda(ind.get('despesas_operacionais'))}
(-) Folha de Pagamento: {_fmt_moeda(ind.get('folha_total'))}
(-) Despesas Financeiras: {_fmt_moeda(ind.get('despesas_financeiras'))}
(+) Receitas Financeiras: {_fmt_moeda(ind.get('receitas_financeiras'))}
= Lucro Operacional: {_fmt_moeda(ind.get('lucro_operacional'))}
= Lucro Líquido: {_fmt_moeda(ind.get('lucro_liquido'))}

═══════════════════════════════════════
BALANÇO PATRIMONIAL (último mês)
═══════════════════════════════════════
Ativo Total: {_fmt_moeda(ind.get('ativo_total'))}
  Ativo Circulante: {_fmt_moeda(ind.get('ativo_circulante'))}
    Disponível (Caixa+Bancos): {_fmt_moeda(ind.get('disponivel'))}
    Clientes: {_fmt_moeda(ind.get('clientes'))}
    Estoques: {_fmt_moeda(ind.get('estoques'))}
  Ativo Não Circulante: {_fmt_moeda(ind.get('ativo_nao_circulante'))}
Passivo Total: {_fmt_moeda(ind.get('passivo_total'))}
  Passivo Circulante: {_fmt_moeda(ind.get('passivo_circulante'))}
    Fornecedores: {_fmt_moeda(ind.get('fornecedores'))}
    Empréstimos CP: {_fmt_moeda(ind.get('emprestimos_cp'))}
  Passivo Não Circulante: {_fmt_moeda(ind.get('passivo_nao_circulante'))}
Patrimônio Líquido: {_fmt_moeda(ind.get('patrimonio_liquido'))}
  Capital Social: {_fmt_moeda(ind.get('capital_social'))}

═══════════════════════════════════════
INDICADORES FINANCEIROS
═══════════════════════════════════════
Score de Saúde: {ind.get('score', 0)}/100

LIQUIDEZ:
  Liquidez Corrente: {ind.get('liquidez_corrente', 0):.2f}
  Liquidez Seca: {ind.get('liquidez_seca', 0):.2f}
  Liquidez Imediata: {ind.get('liquidez_imediata', 0):.2f}
  Capital de Giro: {_fmt_moeda(ind.get('capital_giro'))}

ENDIVIDAMENTO:
  Endividamento Geral: {ind.get('endividamento_geral', 0):.1f}%
  Composição (CP/Total): {ind.get('composicao_endividamento', 0):.1f}%
  Grau de Endividamento: {ind.get('grau_endividamento', 0):.1f}%

RENTABILIDADE:
  Margem Bruta: {ind.get('margem_bruta', 0):.1f}%
  Margem Operacional: {ind.get('margem_operacional', 0):.1f}%
  Margem Líquida: {ind.get('margem_liquida', 0):.1f}%
  ROE: {ind.get('roe', 0):.1f}%
  ROA: {ind.get('roa', 0):.1f}%

TRIBUTÁRIO:
  Carga Tributária: {ind.get('carga_tributaria', 0):.1f}%
  ISS: {_fmt_moeda(ind.get('iss'))} | PIS: {_fmt_moeda(ind.get('pis'))} | COFINS: {_fmt_moeda(ind.get('cofins'))}
  IRPJ: {_fmt_moeda(ind.get('irpj'))} | CSLL: {_fmt_moeda(ind.get('csll'))}
  Total Impostos: {_fmt_moeda(ind.get('impostos_total'))}

EVOLUÇÃO:
  Variação Receita (período): {ind.get('variacao_receita', 0):.1f}%
  Variação Lucro (período): {ind.get('variacao_lucro', 0):.1f}%

═══════════════════════════════════════
INSTRUÇÕES PARA O PARECER
═══════════════════════════════════════

Escreva o parecer com estas seções, usando parágrafos corridos (NÃO use bullet points, listas ou marcadores):

1. DIAGNÓSTICO GERAL (2-3 parágrafos)
Visão geral da saúde financeira da empresa. Contextualize os números com a realidade do mercado brasileiro. Seja específico — cite os valores e o que significam na prática.

2. ANÁLISE DE LIQUIDEZ E CAPITAL DE GIRO (1-2 parágrafos)
Interprete os índices de liquidez. A empresa consegue pagar suas contas? Tem folga? Está apertada? O capital de giro é suficiente para a operação?

3. ESTRUTURA DE CAPITAL E ENDIVIDAMENTO (1-2 parágrafos)
Avalie a dependência de capital de terceiros. O endividamento é saudável ou preocupante? A composição entre curto e longo prazo é adequada?

4. RENTABILIDADE E EFICIÊNCIA (1-2 parágrafos)
As margens são compatíveis com o setor? O retorno aos sócios é atrativo? Compare com alternativas de investimento (CDI, Selic).

5. ANÁLISE TRIBUTÁRIA (1 parágrafo)
A carga tributária está dentro do esperado para o regime? Há espaço para planejamento tributário?

6. RECOMENDAÇÕES ESTRATÉGICAS (2-3 parágrafos)
Ações concretas e priorizadas. O que fazer primeiro? O que monitorar? Quais são as oportunidades? Seja prático e objetivo — o leitor é um empresário, não um acadêmico.

REGRAS:
- Escreva em português brasileiro formal mas acessível
- Use parágrafos corridos, NÃO use listas, bullets ou marcadores
- Cite números específicos do relatório para embasar cada afirmação
- Seja direto e prático — evite jargão desnecessário
- O tom deve ser de um consultor experiente conversando com o empresário
- Se algum indicador estiver zerado ou ausente, não invente — mencione que o dado não está disponível
- Cada seção deve ter um TÍTULO em maiúsculas seguido dos parágrafos
- O parecer total deve ter entre 800 e 1200 palavras
"""
