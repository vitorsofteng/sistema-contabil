#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser Domínio Sistemas
=======================

Parser específico para arquivos PDF do Domínio Sistemas.
Suporta apenas: PDF

Estrutura típica do balancete Domínio:
- Cabeçalho com empresa, CNPJ, período
- Colunas: Código | Descrição | Saldo Anterior (D/C) | Débito | Crédito | Saldo Atual (D/C)
- Rodapé com resumo e assinaturas
"""

import re
import io
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ResultadoParser:
    """Resultado do parser."""
    sucesso: bool
    dados: Dict = field(default_factory=dict)
    empresa: str = ""
    cnpj: str = ""
    periodo: str = ""
    ano: int = 0
    mes: int = 0
    erro: str = ""
    observacoes: List[str] = field(default_factory=list)
    contas_processadas: int = 0


# =============================================================================
# MAPEAMENTO DE CONTAS DOMÍNIO
# =============================================================================

# Padrões para identificar contas específicas
MAPEAMENTO_CONTAS = {
    # DRE - Receitas
    'receita_bruta': [
        r'RECEITA BRUTA',
        r'RECEITA DE PRESTA.*SERVI',
        r'SERVI.*PRESTADOS',
        r'VENDAS DE MERCADORIAS',
        r'RECEITA OPERACIONAL BRUTA',
    ],
    'receita_servicos': [
        r'RECEITA DE PRESTA.*SERVI',
        r'SERVI.*PRESTADOS',
        r'RECEITA DE SERVI',
    ],
    
    # DRE - Deduções
    'deducoes_receita': [
        r'DEDU.*RECEITA BRUTA',
        r'IMPOSTOS SOBRE VENDAS',
        r'IMPOSTOS INCIDENTES',
    ],
    'iss': [
        r'\(-\)\s*ISS(?!\s*A\s*RECOLHER)',
        r'ISS SOBRE SERVI',
        r'ISS DEDU',
    ],
    'pis': [
        r'\(-\)\s*PIS(?!\s*A\s*RECOLHER)',
        r'PIS SOBRE FATURAMENTO',
        r'PIS DEDU',
    ],
    'cofins': [
        r'\(-\)\s*COFINS(?!\s*A\s*RECOLHER)',
        r'COFINS SOBRE FATURAMENTO',
        r'COFINS DEDU',
    ],
    'irpj': [
        r'\(-\)\s*IMPOSTO DE RENDA(?!\s*A\s*RECOLHER)',
        r'\(-\)\s*IRPJ',
        r'IRPJ DEDU',
    ],
    'csll': [
        r'\(-\)\s*CONTRIBUI.*SOCIAL(?!\s*A\s*RECOLHER)',
        r'\(-\)\s*CSLL',
        r'CSLL DEDU',
    ],
    
    # DRE - Custos e Despesas
    'custos': [
        r'CUSTOS DOS PRODUTOS',
        r'CUSTOS DOS SERVI',
        r'CUSTO DAS MERCADORIAS',
        r'CMV',
        r'CPV',
    ],
    'despesas_operacionais': [
        r'DESPESAS OPERACIONAIS',
        r'DESPESAS ADMINISTRATIVAS',
        r'DESPESAS GERAIS',
    ],
    'despesas_financeiras': [
        r'DESPESAS FINANCEIRAS',
        r'JUROS PASSIVOS',
        r'JUROS PAGOS',
    ],
    'folha': [
        r'FOLHA DE PAGAMENTO',
        r'SAL.*RIOS',
        r'DESPESAS COM PESSOAL',
        r'PRO.?LABORE',
    ],
    
    # DRE - Resultado
    'lucro_liquido': [
        r'RESULTADO L.*QUIDO',
        r'LUCRO L.*QUIDO',
        r'LUCRO DO EXERC',
        r'RESULTADO DO EXERC',
    ],
    
    # Balanço - Ativo
    'ativo_total': [
        r'^ATIVO$',
        r'TOTAL DO ATIVO',
        r'ATIVO TOTAL',
    ],
    'ativo_circulante': [
        r'ATIVO CIRCULANTE',
    ],
    'disponivel': [
        r'DISPON.*VEL',
        r'DISPONIBILIDADES',
    ],
    'caixa': [
        r'CAIXA(?!\s*E\s*EQUIV)',
        r'CAIXA GERAL',
    ],
    'bancos': [
        r'BANCOS CONTA MOVIMENTO',
        r'BANCOS C/MOVIMENTO',
        r'BANCO(?!S)',
    ],
    'clientes': [
        r'CLIENTES',
        r'DUPLICATAS A RECEBER',
        r'CONTAS A RECEBER',
    ],
    'estoques': [
        r'ESTOQUES',
        r'MERCADORIAS',
        r'PRODUTOS ACABADOS',
    ],
    
    # Balanço - Passivo
    'passivo_total': [
        r'^PASSIVO$',
        r'TOTAL DO PASSIVO',
        r'PASSIVO TOTAL',
    ],
    'passivo_circulante': [
        r'PASSIVO CIRCULANTE',
    ],
    'passivo_nao_circulante': [
        r'PASSIVO N.*CIRCULANTE',
        r'EXIG.*VEL.*LONGO PRAZO',
    ],
    'fornecedores': [
        r'FORNECEDORES',
        r'DUPLICATAS A PAGAR',
    ],
    'dividendos_pagar': [
        r'DIVIDENDOS A PAGAR',
        r'DIVIDENDOS.*PART.*JURO',
        r'LUCROS.*DIVIDENDOS A PAGAR',
    ],
    'patrimonio_liquido': [
        r'PATRIM.*NIO L.*QUIDO',
        r'^PL$',
    ],
    'capital_social': [
        r'CAPITAL SOCIAL',
        r'CAPITAL SUBSCRITO',
        r'CAPITAL INTEGRALIZADO',
    ],
}


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def parse_valor_brasileiro(valor_str: str) -> float:
    """Converte valor em formato brasileiro para float."""
    if not valor_str or valor_str.strip() in ['', '-', '0']:
        return 0.0
    
    # Remove espaços
    valor_str = str(valor_str).strip()
    
    # Remove indicador D/C do final
    valor_str = re.sub(r'\s*[DCdc]\s*$', '', valor_str)
    
    # Remove pontos de milhar e troca vírgula por ponto
    # Formato: 1.234.567,89 -> 1234567.89
    valor_str = valor_str.replace('.', '').replace(',', '.')
    
    try:
        return abs(float(valor_str))
    except:
        return 0.0


def identificar_conta(descricao: str) -> Optional[str]:
    """Identifica qual campo a conta representa."""
    descricao_upper = descricao.upper().strip()
    
    for campo, padroes in MAPEAMENTO_CONTAS.items():
        for padrao in padroes:
            if re.search(padrao, descricao_upper):
                return campo
    
    return None


def extrair_periodo(texto: str) -> Tuple[int, int, str]:
    """Extrai ano e mês do período."""
    # Procura padrão DD/MM/AAAA - DD/MM/AAAA
    match = re.search(r'(\d{2})/(\d{2})/(\d{4})\s*-\s*(\d{2})/(\d{2})/(\d{4})', texto)
    if match:
        # Usa a data final
        dia_fim, mes_fim, ano_fim = int(match.group(4)), int(match.group(5)), int(match.group(6))
        periodo_str = f"{mes_fim:02d}/{ano_fim}"
        return ano_fim, mes_fim, periodo_str
    
    # Procura padrão MM/AAAA
    match = re.search(r'(\d{2})/(\d{4})', texto)
    if match:
        mes, ano = int(match.group(1)), int(match.group(2))
        return ano, mes, f"{mes:02d}/{ano}"
    
    return 0, 0, ""


def extrair_cnpj(texto: str) -> str:
    """Extrai CNPJ do texto."""
    match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
    return match.group(0) if match else ""


# =============================================================================
# PARSER PDF
# =============================================================================

def parse_dominio_pdf(conteudo: bytes, nome_arquivo: str) -> ResultadoParser:
    """
    Parser para arquivos PDF do Domínio Sistemas.
    Extrai dados estruturados do balancete.
    """
    resultado = ResultadoParser(sucesso=False)
    
    try:
        # Extrai texto do PDF
        texto = ""
        
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
                for pagina in pdf.pages:
                    texto += (pagina.extract_text() or "") + "\n"
            print(f"[PARSER_DOMINIO_PDF] Extraído {len(texto)} chars via pdfplumber")
        except ImportError:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(io.BytesIO(conteudo))
                for pagina in reader.pages:
                    texto += (pagina.extract_text() or "") + "\n"
                print(f"[PARSER_DOMINIO_PDF] Extraído {len(texto)} chars via PyPDF2")
            except ImportError:
                resultado.erro = "Nenhuma biblioteca PDF disponível"
                return resultado
        
        if not texto.strip():
            resultado.erro = "Não foi possível extrair texto do PDF"
            return resultado
        
        # === EXTRAI CABEÇALHO ===
        
        # Debug: mostrar primeiras linhas
        linhas = texto.split('\n')
        print(f"[PARSER_DOMINIO_PDF] Primeiras 15 linhas do texto:")
        for i, linha in enumerate(linhas[:15]):
            print(f"  [{i}] '{linha[:80]}'" if len(linha) > 80 else f"  [{i}] '{linha}'")
        
        # Estratégia 1 (PRIORITÁRIA): formato "Empresa: NOME Folha:"
        # Captura tudo entre "Empresa:" e "Folha:" usando greedy match
        match_empresa = re.search(r'Empresa:\s*(.+)\s+Folha:', texto, re.IGNORECASE)
        if match_empresa:
            nome = match_empresa.group(1).strip()
            print(f"[PARSER_DOMINIO_PDF] DEBUG regex capturou: '{nome}'")
            if nome and len(nome) > 2 and nome.lower() != 'empresa':
                resultado.empresa = nome
                print(f"[PARSER_DOMINIO_PDF] Nome empresa via 'Empresa: NOME Folha:': {resultado.empresa}")
        
        # Estratégia 2: Buscar padrão de nome de empresa (LTDA, S/A, ME, EPP, EIRELI)
        # Mas excluir se for apenas "Empresa"
        if not resultado.empresa:
            match_empresa_padrao = re.search(
                r'([A-ZÀ-Ú][A-ZÀ-Ú0-9\s\.\-&]+(?:LTDA|S/?A|ME|EPP|EIRELI|CIA)(?:\s*-?\s*(?:ME|EPP))?)',
                texto, re.IGNORECASE
            )
            if match_empresa_padrao:
                nome = match_empresa_padrao.group(1).strip()
                print(f"[PARSER_DOMINIO_PDF] DEBUG regex LTDA capturou: '{nome}'")
                # Excluir se for só "Empresa" ou começar com "Empresa:"
                if nome and len(nome) > 3 and nome.upper() not in ['EMPRESA', 'EMPRESA:']:
                    if not nome.upper().startswith('EMPRESA:'):
                        resultado.empresa = nome
                        print(f"[PARSER_DOMINIO_PDF] Nome empresa via padrão LTDA: {resultado.empresa}")
        
        # Estratégia 3: Nome na primeira linha (antes de qualquer número ou label)
        if not resultado.empresa:
            for i, linha in enumerate(linhas[:10]):
                linha_limpa = linha.strip()
                # Pula linhas vazias, numéricas, ou com labels
                if not linha_limpa:
                    continue
                if re.match(r'^[\d./-]+$', linha_limpa):  # CNPJ ou número
                    continue
                if linha_limpa.lower().startswith('empresa:'):
                    continue
                if linha_limpa.lower() in ['c.n.p.j.:', 'cnpj:', 'balancete']:
                    continue
                if 'período' in linha_limpa.lower() or 'folha:' in linha_limpa.lower():
                    continue
                if 'código' in linha_limpa.lower() or 'saldo' in linha_limpa.lower():
                    continue
                # Primeira linha com texto é provavelmente o nome da empresa
                if len(linha_limpa) > 3:
                    resultado.empresa = linha_limpa
                    print(f"[PARSER_DOMINIO_PDF] Nome empresa na linha {i}: {resultado.empresa}")
                    break
        
        # Estratégia 4: Buscar nome antes do CNPJ
        if not resultado.empresa:
            match = re.search(r'^(.+?)\n\s*\d{2}\.\d{3}\.\d{3}[/\.\-]\d{4}[/\.\-]?\d{2}', texto, re.MULTILINE)
            if match:
                nome_candidato = match.group(1).strip()
                if len(nome_candidato) > 3 and not re.match(r'^[\d\s./-]+$', nome_candidato):
                    if not nome_candidato.lower().startswith('empresa:'):
                        resultado.empresa = nome_candidato
                        print(f"[PARSER_DOMINIO_PDF] Nome empresa antes do CNPJ: {resultado.empresa}")
        
        # CNPJ
        resultado.cnpj = extrair_cnpj(texto)
        
        # Período
        match_periodo = re.search(r'Per[ií]odo[:\s]*(\d{2})/(\d{2})/(\d{4})\s*-\s*(\d{2})/(\d{2})/(\d{4})', texto, re.IGNORECASE)
        if match_periodo:
            resultado.ano = int(match_periodo.group(6))
            resultado.mes = int(match_periodo.group(5))
            resultado.periodo = f"{match_periodo.group(5)}/{match_periodo.group(6)}"
        
        print(f"[PARSER_DOMINIO_PDF] Empresa: {resultado.empresa}")
        print(f"[PARSER_DOMINIO_PDF] CNPJ: {resultado.cnpj}")
        print(f"[PARSER_DOMINIO_PDF] Período: {resultado.periodo}")
        
        # === INICIALIZA DADOS ===
        dados = {
            'receita_bruta': 0.0, 'receita_servicos': 0.0, 'deducoes_receita': 0.0,
            'receita': 0.0, 'custos': 0.0, 'despesas_operacionais': 0.0,
            'despesas_financeiras': 0.0, 'lucro_liquido': 0.0,
            'ativo_total': 0.0, 'ativo_circulante': 0.0, 'disponivel': 0.0,
            'caixa': 0.0, 'bancos': 0.0, 'clientes': 0.0, 'estoques': 0.0,
            'passivo_total': 0.0, 'passivo_circulante': 0.0, 'passivo_nao_circulante': 0.0,
            'fornecedores': 0.0, 'dividendos_pagar': 0.0, 'patrimonio_liquido': 0.0, 'capital_social': 0.0,
            'lucros_acumulados': 0.0,  # Para calcular PL corretamente
            # Impostos DEDUZIDOS da receita (DRE) - para carga tributária
            # Estes são os campos principais que serão usados pelo frontend
            'icms': 0.0, 'iss': 0.0, 'pis': 0.0, 'cofins': 0.0, 'irpj': 0.0, 'csll': 0.0,
            # Campos auxiliares para debug
            'icms_deducao': 0.0, 'pis_deducao': 0.0, 'cofins_deducao': 0.0, 
            'irpj_deducao': 0.0, 'csll_deducao': 0.0,
            'impostos': 0.0, 'folha': 0.0,
        }
        
        # Variável para armazenar lucros acumulados da conta 266
        lucros_acumulados_conta = 0.0
        
        # ============================================================
        # EXTRAÇÃO DO LUCRO LÍQUIDO - ESTRATÉGIA CORRETA
        # ============================================================
        # O balancete Domínio tem estrutura específica:
        #
        # Conta 402: "RESULTADO LÍQUIDO DO PERÍODO ANTES DO IRPJ, CSLL..."
        #            Este valor é ANTES dos impostos! NÃO usar!
        #
        # No final do documento (RESUMO DO BALANCETE):
        #   RESULTADO DO MES: movimento do mês atual
        #   RESULTADO DO EXERCÍCIO: acumulado, MAS pode ser antes de impostos
        #   
        #   RESUMO DO BALANCETE
        #   ...
        #   RESULTADO DO EXERCÍCIO 84.650,59C 22.728,87 118.670,69 95.941,82C
        #                                                         ^^^^^^^^^^
        #                                                         ESTE é o lucro!
        #
        # O valor correto é o ÚLTIMO valor com "C" na linha "RESULTADO DO EXERCÍCIO"
        # ============================================================
        
        # Buscar lucro no RESUMO DO BALANCETE
        lucro_extraido = False
        
        # Método 1 (MELHOR): Buscar linha "RESULTADO DO EXERCÍCIO" e pegar ÚLTIMO valor com C
        # Formato: "RESULTADO DO EXERCÍCIO 84.650,59C 22.728,87 118.670,69 95.941,82C"
        # O último valor é o Saldo Atual (lucro acumulado do exercício)
        match_resultado_exerc = re.search(
            r'RESULTADO DO EXERC[ÍI]CIO\s+([\d.,]+C?\s+[\d.,]+\s+[\d.,]+\s+)([\d]{1,3}(?:\.[\d]{3})*,[\d]{2})\s*C',
            texto, re.IGNORECASE
        )
        if match_resultado_exerc:
            dados['lucro_liquido'] = parse_valor_brasileiro(match_resultado_exerc.group(2))
            print(f"[PARSER_DOMINIO_PDF] lucro_liquido (RESULTADO DO EXERCÍCIO - último valor): R$ {dados['lucro_liquido']:,.2f}")
            lucro_extraido = True
        
        # Método 2: Buscar a linha RESULTADO DO EXERCÍCIO de forma mais flexível
        if not lucro_extraido:
            for linha in texto.split('\n'):
                if 'RESULTADO DO EXERC' in linha.upper() and 'MES' not in linha.upper() and 'ANTES' not in linha.upper():
                    # Extrai todos os valores com C da linha
                    valores_c = re.findall(r'([\d]{1,3}(?:\.[\d]{3})*,[\d]{2})\s*C', linha)
                    if valores_c:
                        # O ÚLTIMO valor com C é o Saldo Atual (lucro do exercício)
                        dados['lucro_liquido'] = parse_valor_brasileiro(valores_c[-1])
                        print(f"[PARSER_DOMINIO_PDF] lucro_liquido (RESULTADO DO EXERCÍCIO linha): R$ {dados['lucro_liquido']:,.2f}")
                        lucro_extraido = True
                        break
        
        # Método 3: Buscar último valor com C após "RESUMO DO BALANCETE"
        if not lucro_extraido:
            pos_resumo = texto.upper().find('RESUMO DO BALANCETE')
            if pos_resumo > 0:
                texto_apos_resumo = texto[pos_resumo:]
                valores_credito = re.findall(r'([\d]{1,3}(?:\.[\d]{3})*,[\d]{2})\s*C', texto_apos_resumo)
                if valores_credito:
                    dados['lucro_liquido'] = parse_valor_brasileiro(valores_credito[-1])
                    print(f"[PARSER_DOMINIO_PDF] lucro_liquido (último C após RESUMO): R$ {dados['lucro_liquido']:,.2f}")
                    lucro_extraido = True
        
        if not lucro_extraido:
            print(f"[PARSER_DOMINIO_PDF] AVISO: Não foi possível extrair lucro líquido do RESUMO")
        
        # === PROCESSA RESUMO DO BALANCETE (para outros dados) ===
        resumo = re.search(r'RESUMO DO BALANCETE(.+?)(?:___|Sistema licenciado|$)', texto, re.DOTALL)
        if resumo:
            resumo_texto = resumo.group(1)
            print(f"[PARSER_DOMINIO_PDF] Processando RESUMO DO BALANCETE...")
            
            # Também extrai PATRIMÔNIO LÍQUIDO do RESUMO
            linhas_resumo = resumo_texto.split('\n')
            for i, linha in enumerate(linhas_resumo):
                if 'PATRIM' in linha.upper() and 'QUIDO' in linha.upper():
                    # Busca valores na mesma linha ou próximas
                    valores_linha = re.findall(r'([\d]{1,3}(?:\.[\d]{3})*,[\d]{2})', linha)
                    if valores_linha and len(valores_linha) >= 4:
                        # Formato: saldo_ant, débito, crédito, saldo_atual
                        dados['patrimonio_liquido'] = parse_valor_brasileiro(valores_linha[3])
                        print(f"[PARSER_DOMINIO_PDF] patrimonio_liquido (RESUMO): R$ {dados['patrimonio_liquido']:,.2f}")
                    break
            
            # Ativo Total - formato: "ATIVO 596.403,88D 165.307,83 168.104,91 593.606,80D"
            match = re.search(r'^ATIVO\s+([\d.,]+)[DC]?\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)[DC]?', resumo_texto, re.MULTILINE)
            if match:
                ativo_valor = parse_valor_brasileiro(match.group(4))
                if dados['ativo_total'] == 0 and ativo_valor > 0:
                    dados['ativo_total'] = ativo_valor
                    print(f"[PARSER_DOMINIO_PDF] ativo_total (RESUMO): R$ {dados['ativo_total']:,.2f}")
            
            # Passivo Total - formato similar
            match = re.search(r'^PASSIVO\s+([\d.,]+)[DC]?\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)[DC]?', resumo_texto, re.MULTILINE)
            if match:
                dados['passivo_total'] = parse_valor_brasileiro(match.group(4))
                print(f"[PARSER_DOMINIO_PDF] passivo_total: R$ {dados['passivo_total']:,.2f}")
            
            # ============================================================
            # NÃO usar "RESULTADO LÍQUIDO DO PERÍODO ANTES DO IRPJ/CSLL" (conta 402)
            # Esse valor é ANTES dos impostos, não é o lucro final!
            # O valor correto é "RESULTADO DO EXERCÍCIO" que já foi extraído acima
            # ============================================================
        
        # === PROCESSA LINHAS INDIVIDUAIS ===
        # O texto tem problemas de OCR, então usamos padrões flexíveis
        
        for linha in texto.split('\n'):
            # Extrai valores numéricos (formato: 1.234.567,89)
            valores = re.findall(r'([\d]{1,3}(?:\.[\d]{3})*,[\d]{2})', linha)
            if len(valores) < 4:
                continue
            
            # Valores: [Saldo Anterior, Débito, Crédito, Saldo Atual]
            # IMPORTANTE: Usar ÚLTIMO valor como saldo atual (mais confiável)
            saldo_atual = parse_valor_brasileiro(valores[-1])
            debito = parse_valor_brasileiro(valores[1]) if len(valores) > 1 else 0
            credito = parse_valor_brasileiro(valores[2]) if len(valores) > 2 else 0
            
            linha_upper = linha.upper()
            linha_strip = linha.strip()
            
            # ============================================================
            # ATIVO TOTAL - conta raiz 1 (linha "1 1 ATIVO")
            # ============================================================
            if (linha_strip.startswith('1 1 ATIVO') or 
                re.match(r'^1\s+1\s+ATIVO\b', linha_strip)) and 'CIRCULANTE' not in linha_upper:
                if dados['ativo_total'] == 0 and saldo_atual > 0:
                    dados['ativo_total'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] ativo_total (conta 1): R$ {saldo_atual:,.2f}")
            
            # === CONTAS PATRIMONIAIS (usar Saldo Atual) ===
            
            # Ativo Circulante - texto pode estar corrompido como "ATIVO2 CIRACTUIVLOA"
            if ('CIRCULANTE' in linha_upper and 'ATIVO' in linha_upper and 'PASSIVO' not in linha_upper) or \
               'ATIVO2 CIRAC' in linha or linha_strip.startswith('2 ATIVO') or linha_strip.startswith('2 1.1'):
                if dados['ativo_circulante'] == 0 and saldo_atual > 0:
                    dados['ativo_circulante'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] ativo_circulante: R$ {saldo_atual:,.2f}")
            
            # Disponível
            if 'DISPON' in linha_upper:
                if dados['disponivel'] == 0 and saldo_atual > 0:
                    dados['disponivel'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] disponivel: R$ {saldo_atual:,.2f}")
            
            # Caixa
            if 'CAIXA' in linha_upper and 'GERAL' not in linha_upper:
                if dados['caixa'] == 0 and saldo_atual > 0:
                    dados['caixa'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] caixa: R$ {saldo_atual:,.2f}")
            
            # Bancos - código 7 (texto malformado: "BANC7OS CONTBAAN MCOOSV")
            if linha_strip.startswith('7 ') or 'BANC7OS' in linha or \
               ('BANC' in linha_upper and 'MOV' in linha_upper):
                if dados['bancos'] == 0 and saldo_atual > 0:
                    dados['bancos'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] bancos: R$ {saldo_atual:,.2f}")
            
            # Clientes
            if 'CLIENTES' in linha_upper and 'DUPLICATA' not in linha_upper:
                if dados['clientes'] == 0 and saldo_atual > 0:
                    dados['clientes'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] clientes: R$ {saldo_atual:,.2f}")
            
            # ============================================================
            # ESTOQUES - conta sintética 53 ou 1.1.5
            # ============================================================
            # Exemplos de linha:
            # "53 1.1.5 ESTOQUE 353.568,24D 19.509,60 2.046,07 371.031,77D"
            # "ESTO5Q3UE1.1.5 ESTOQUE" (texto corrompido)
            # ============================================================
            if ('ESTOQUE' in linha_upper or 'ESTOQUES' in linha_upper or 
                'EST5' in linha or '5Q3UE' in linha or  # Texto corrompido
                linha_strip.startswith('53 ') or '1.1.5 ' in linha):
                
                # Evitar pegar subcontas (mercadorias específicas)
                if 'MERCADORIA' not in linha_upper and '.5.' not in linha:
                    if dados['estoques'] == 0 and saldo_atual > 0:
                        dados['estoques'] = saldo_atual
                        print(f"[PARSER_DOMINIO_PDF] estoques: R$ {saldo_atual:,.2f}")
            
            # ============================================================
            # FORNECEDORES - conta sintética 164 ou 2.1.1
            # ============================================================
            # Exemplos:
            # "164 2.1.1 FORNECEDORES 169.563,45C ..."
            # "FOR1N64ECEDOFROESR NFOECRNEECDEODROERESS" (texto corrompido)
            # ============================================================
            if ('FORNECEDORES' in linha_upper or 'FORNECEDOR' in linha_upper or
                'FOR1N6' in linha or 'F1O6R4' in linha or  # Texto corrompido
                linha_strip.startswith('164 ') or '2.1.1 ' in linha):
                
                # Evitar subcontas
                if '2.1.1.' not in linha and '.1.' not in linha[10:]:
                    if dados['fornecedores'] == 0 and saldo_atual > 0:
                        dados['fornecedores'] = saldo_atual
                        print(f"[PARSER_DOMINIO_PDF] fornecedores: R$ {saldo_atual:,.2f}")
            
            # ============================================================
            # PASSIVO CIRCULANTE
            # ============================================================
            if 'PASSIVO' in linha_upper and 'CIRCULANTE' in linha_upper:
                if 'NÃO' not in linha_upper and 'NAO' not in linha_upper and 'N-C' not in linha_upper and 'EXIG' not in linha_upper:
                    if dados['passivo_circulante'] == 0 and saldo_atual > 0:
                        dados['passivo_circulante'] = saldo_atual
                        print(f"[PARSER_DOMINIO_PDF] passivo_circulante: R$ {saldo_atual:,.2f}")
            
            # ============================================================
            # PASSIVO NÃO CIRCULANTE / EXIGÍVEL A LONGO PRAZO
            # ============================================================
            # Códigos comuns: 217, 503
            # Pode aparecer como "EXIGÍVEL A LONGO PRAZO" ou "PASSIVO NÃO CIRCULANTE"
            # ============================================================
            if (linha_strip.startswith('217 ') or linha_strip.startswith('503 ') or
                ('PASSIVO' in linha_upper and ('NÃO' in linha_upper or 'NAO' in linha_upper or 'N-C' in linha_upper)) or
                ('EXIG' in linha_upper and 'LONGO' in linha_upper) or
                ('EMPREST' in linha_upper and 'LONGO' in linha_upper)):
                
                # Evitar subcontas de empréstimos
                if '219' not in linha and '.1.' not in linha[10:]:
                    if dados['passivo_nao_circulante'] == 0 and saldo_atual > 0:
                        dados['passivo_nao_circulante'] = saldo_atual
                        print(f"[PARSER_DOMINIO_PDF] passivo_nao_circulante: R$ {saldo_atual:,.2f}")
            
            # Patrimônio Líquido - código 242 (texto malformado: "PAT2R42IMÔNPIAOT RLIÍMQÔUNIIDO")
            # Linha pode ser: "PAT2R42IM2Ô.3NIO LÍQUIDO PATRIMÔNIO LÍQUIDO 100.000,00C..."
            if (linha_strip.startswith('242 ') or '2R42' in linha or 
                (('PATRIMÔNIO' in linha_upper or 'PATRIMONIO' in linha_upper) and 
                 ('LÍQUIDO' in linha_upper or 'LIQUIDO' in linha_upper) and
                 'RESULTADO' not in linha_upper)):
                if dados['patrimonio_liquido'] == 0 and saldo_atual > 0:
                    dados['patrimonio_liquido'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] patrimonio_liquido: R$ {saldo_atual:,.2f}")
            
            # Capital Social
            if 'CAPITAL' in linha_upper and 'SOCIAL' in linha_upper:
                if dados['capital_social'] == 0 and saldo_atual > 0:
                    dados['capital_social'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] capital_social: R$ {saldo_atual:,.2f}")
            
            # Dividendos a Pagar - conta 207/208/210
            # IMPORTANTE: São lucros de exercícios anteriores que não foram pagos
            # Exemplo: "207 2.1.7 DIVIDENDOS, PART. E JURO SOBRE O CAPITAL"
            if ('DIVIDENDOS' in linha_upper and ('PAGAR' in linha_upper or 'PART' in linha_upper or 'JURO' in linha_upper)) or \
               linha_strip.startswith('207 ') or linha_strip.startswith('208 ') or linha_strip.startswith('210 '):
                if dados['dividendos_pagar'] == 0 and saldo_atual > 0:
                    dados['dividendos_pagar'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] dividendos_pagar: R$ {saldo_atual:,.2f}")
            
            # Lucros Acumulados - conta 266 (SALDO ATUAL, não movimento!)
            # O saldo atual mostra o lucro acumulado até este mês
            if 'LUCROS ACUMULADOS' in linha_upper and 'PREJUÍZO' not in linha_upper:
                if dados['lucros_acumulados'] == 0 and saldo_atual > 0:
                    dados['lucros_acumulados'] = saldo_atual
                    lucros_acumulados_conta = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] lucros_acumulados (conta 266): R$ {saldo_atual:,.2f}")
            
            # Lucro do Exercício - conta 522 (é o lucro líquido REAL do período)
            # IMPORTANTE: NÃO sobrescrever se já temos valor do RESUMO DO BALANCETE
            # O RESUMO tem o valor mais confiável (RESULTADO DO EXERCÍCIO)
            # Texto corrompido: "LUC5R2O2 DO EXERLUCCÍRCO IDOO EXERCÍCIO"
            if ('LUCRO DO EXERC' in linha_upper or 'LUC5R2O2 DO EXER' in linha or '522' in linha[:10]) and 'RESULTADO' not in linha_upper:
                # Só usa se ainda não temos valor (não sobrescrever!)
                if saldo_atual > 0 and dados['lucro_liquido'] == 0:
                    dados['lucro_liquido'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] lucro_liquido (conta 522 LUCRO DO EXERCÍCIO): R$ {saldo_atual:,.2f}")
            
            # === IMPOSTOS A RECOLHER (usar Saldo Atual) ===
            # Nota: texto do PDF pode estar malformado, usar códigos como fallback
            
            # ISS - código 173
            if ('ISS' in linha_upper and 'RECOLHER' in linha_upper and 'SOBRE' not in linha_upper) or \
               (linha_strip.startswith('173 ') or '173RECOLHER' in linha.replace(' ', '')):
                if dados['iss'] == 0 and saldo_atual > 0:
                    dados['iss'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] iss: R$ {saldo_atual:,.2f}")
            
            # PIS - código 179
            if ('PIS' in linha_upper and 'RECOLHER' in linha_upper) or linha_strip.startswith('179 '):
                if dados['pis'] == 0 and saldo_atual > 0:
                    dados['pis'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] pis: R$ {saldo_atual:,.2f}")
            
            # COFINS - código 180 (texto malformado: "COF1I8N0S A RECOCLOHFIENSR")
            if ('COF' in linha_upper and 'RECOLHER' in linha_upper) or \
               linha_strip.startswith('180 ') or '1I8N0S' in linha or 'COF1' in linha:
                if dados['cofins'] == 0 and saldo_atual > 0:
                    dados['cofins'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] cofins: R$ {saldo_atual:,.2f}")
            
            # IRPJ - código 176
            if ('IMPOSTO DE RENDA' in linha_upper and 'RECOLHER' in linha_upper) or linha_strip.startswith('176 '):
                if dados['irpj'] == 0 and saldo_atual > 0:
                    dados['irpj'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] irpj: R$ {saldo_atual:,.2f}")
            
            # CSLL - código 177 (texto malformado: "CON1T77RIBUIÇÃOC")
            if linha_strip.startswith('177 ') or '1T77' in linha or \
               ('SOCIAL' in linha_upper and 'RECOLHER' in linha_upper and 'IMPOSTO' not in linha_upper):
                if dados['csll'] == 0 and saldo_atual > 0:
                    dados['csll'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] csll: R$ {saldo_atual:,.2f}")
            
            # ============================================================
            # === CONTAS DE RESULTADO (DRE) - usar SALDO ATUAL! ===
            # ============================================================
            # IMPORTANTE: Em balancetes brasileiros, a DRE é ACUMULADA no exercício!
            # A coluna "Crédito" mostra apenas o movimento do mês
            # A coluna "Saldo Atual" mostra o valor ACUMULADO do exercício
            # Devemos usar SALDO ATUAL para ter o valor correto!
            # ============================================================
            
            if 'RECEITA BRUTA' in linha_upper and 'VENDAS' in linha_upper:
                # Usar SALDO ATUAL (acumulado), não crédito (mensal)
                if dados['receita_bruta'] == 0 and saldo_atual > 0:
                    dados['receita_bruta'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] receita_bruta (SALDO ATUAL): R$ {saldo_atual:,.2f}")
            
            if 'SERVI' in linha_upper and 'PRESTADO' in linha_upper:
                # Usar SALDO ATUAL (acumulado)
                if dados['receita_servicos'] == 0 and saldo_atual > 0:
                    dados['receita_servicos'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] receita_servicos (SALDO ATUAL): R$ {saldo_atual:,.2f}")
            
            if 'DEDU' in linha_upper and 'RECEITA' in linha_upper and 'BRUTA' in linha_upper:
                # Usar SALDO ATUAL (acumulado)
                if dados['deducoes_receita'] == 0 and saldo_atual > 0:
                    dados['deducoes_receita'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] deducoes_receita (SALDO ATUAL): R$ {saldo_atual:,.2f}")
            
            # ============================================================
            # IMPOSTOS DA DRE (DEDUÇÕES SOBRE VENDAS) - para carga tributária
            # ============================================================
            # Estes são os impostos DEDUZIDOS da receita (diferentes dos "a recolher"!)
            # Contas 3.1.2.03.xxxxx: (-) ICMS, (-) PIS, (-) COFINS, (-) IR, (-) CSLL
            # ============================================================
            
            # (-) ICMS - conta 426 ou similar (3.1.2.03.00002)
            # Linhas: "426 3.1.2.03.00002 (-) ICMS 0,00 10.088,44 0,00 10.088,44D"
            # Ou: "(-) ICMS 426 3.1.2.03.00002 (-) ICMS 29.205,46D..."
            # Ou texto corrompido: "(-) I4C26MS3.1.2.03.00002 (-) ICMS..."
            icms_deducao_match = (
                linha_strip.startswith('426 ') or 
                '426' in linha_strip[:15] or  # Código pode aparecer após texto
                'I4C26MS' in linha or  # Texto corrompido comum
                '4C26M' in linha or  # Variação de corrupção
                ('(-) ICMS' in linha and 'RECOLHER' not in linha_upper and 'RECUPERAR' not in linha_upper) or
                (re.match(r'^\d+\s+3\.1\.2\.03', linha_strip) and 'ICMS' in linha_upper and 'RECOLHER' not in linha_upper) or
                ('3.1.2.03' in linha and 'ICMS' in linha_upper and 'RECOLHER' not in linha_upper)
            )
            if icms_deducao_match:
                if saldo_atual > 0:
                    dados['icms_deducao'] = saldo_atual
                    dados['icms'] = saldo_atual  # Copiar para campo principal
                    print(f"[PARSER_DOMINIO_PDF] icms (dedução DRE): R$ {saldo_atual:,.2f}")
            
            # (-) PIS - conta 429 (3.1.2.03.00005)
            # Formatos possíveis:
            # "429 3.1.2.03.00005 (-) PIS 255,75D..."
            # "(-) PIS 429 3.1.2.03.00005 (-) PIS 752,79D..."
            pis_deducao_match = (
                linha_strip.startswith('429 ') or 
                '429' in linha_strip[:15] or  # Código pode estar em posição diferente
                ('(-) PIS' in linha and 'RECOLHER' not in linha_upper) or
                (re.match(r'^\d+\s+3\.1\.2\.03', linha_strip) and 'PIS' in linha_upper and 'RECOLHER' not in linha_upper) or
                ('3.1.2.03' in linha and 'PIS' in linha_upper and 'RECOLHER' not in linha_upper)
            )
            if pis_deducao_match:
                if saldo_atual > 0:
                    dados['pis_deducao'] = saldo_atual
                    dados['pis'] = saldo_atual  # Copiar para campo principal
                    print(f"[PARSER_DOMINIO_PDF] pis (dedução DRE): R$ {saldo_atual:,.2f}")
            
            # (-) COFINS - conta 428 (3.1.2.03.00004)
            # Nota: texto pode estar corrompido como "(-) C42O8FI3N.1.S2.03.00004 (-) COFINS"
            if (linha_strip.startswith('428 ') or 
                '428' in linha_strip[:10] or
                ('(-) COFINS' in linha and 'RECOLHER' not in linha_upper) or
                ('COFINS' in linha_upper and '3.1.2.03' in linha and 'RECOLHER' not in linha_upper)):
                if saldo_atual > 0:
                    dados['cofins_deducao'] = saldo_atual
                    dados['cofins'] = saldo_atual  # Copiar para campo principal
                    print(f"[PARSER_DOMINIO_PDF] cofins (dedução DRE): R$ {saldo_atual:,.2f}")
            
            # (-) CONTRIBUIÇÃO SOCIAL (CSLL) - conta 477 (3.1.2.03.00006)
            if ('(-) CONTRIBUI' in linha_upper and 'SOCIAL' in linha_upper) or linha_strip.startswith('477 '):
                if saldo_atual > 0:
                    dados['csll_deducao'] = saldo_atual
                    dados['csll'] = saldo_atual  # Copiar para campo principal
                    print(f"[PARSER_DOMINIO_PDF] csll (dedução DRE): R$ {saldo_atual:,.2f}")
            
            # (-) IMPOSTO DE RENDA - conta 478 (3.1.2.03.00007)
            if ('(-) IMPOSTO' in linha_upper and 'RENDA' in linha_upper) or linha_strip.startswith('478 '):
                if saldo_atual > 0:
                    dados['irpj_deducao'] = saldo_atual
                    dados['irpj'] = saldo_atual  # Copiar para campo principal
                    print(f"[PARSER_DOMINIO_PDF] irpj (dedução DRE): R$ {saldo_atual:,.2f}")
            
            # Alternativa: IMPOSTOS SOBRE VENDAS E SERVIÇOS (conta 424)
            # Este é o TOTAL de impostos deduzidos da receita - fonte MAIS CONFIÁVEL!
            # Formatos:
            # "424 3.1.2.03 IMPOSTOS SOBRE VENDAS E SERVIÇOS 48.216,04D"
            # "IMPOSTOS SOBRE VENDAS 424 ..."
            impostos_vendas_match = (
                ('IMPOSTOS SOBRE' in linha_upper and 'VENDAS' in linha_upper) or
                ('IMPOSTOS S/' in linha_upper and 'VENDAS' in linha_upper) or
                linha_strip.startswith('424 ') or
                '424' in linha_strip[:15] or
                ('3.1.2.03' in linha and 'IMPOSTOS' in linha_upper and 'VEND' in linha_upper)
            )
            if impostos_vendas_match:
                # Usar SALDO ATUAL (acumulado)
                if saldo_atual > 0:
                    dados['impostos_sobre_vendas'] = saldo_atual  # Guardar para referência
                    # SEMPRE sobrescrever deducoes_receita se for maior (conta 424 é mais precisa)
                    if saldo_atual > dados['deducoes_receita']:
                        dados['deducoes_receita'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] impostos_sobre_vendas (conta 424): R$ {saldo_atual:,.2f}")
            
            if 'DESPESAS OPERACIONAIS' in linha_upper:
                # Usar SALDO ATUAL (acumulado)
                if dados['despesas_operacionais'] == 0 and saldo_atual > 0:
                    dados['despesas_operacionais'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] despesas_operacionais (SALDO ATUAL): R$ {saldo_atual:,.2f}")
            
            if 'DESPESAS FINANCEIRAS' in linha_upper:
                # Usar SALDO ATUAL (acumulado)
                if dados['despesas_financeiras'] == 0 and saldo_atual > 0:
                    dados['despesas_financeiras'] = saldo_atual
                    print(f"[PARSER_DOMINIO_PDF] despesas_financeiras (SALDO ATUAL): R$ {saldo_atual:,.2f}")
        
        # === CALCULA CAMPOS DERIVADOS ===
        
        if dados['receita_bruta'] == 0 and dados['receita_servicos'] > 0:
            dados['receita_bruta'] = dados['receita_servicos']
        
        if dados['receita'] == 0:
            dados['receita'] = dados['receita_bruta'] - dados['deducoes_receita']
            if dados['receita'] < 0:
                dados['receita'] = dados['receita_bruta']
        
        # ============================================================
        # CÁLCULO DE IMPOSTOS PARA CARGA TRIBUTÁRIA
        # ============================================================
        # IMPORTANTE: Para carga tributária, usar DEDUÇÕES DA RECEITA (DRE)
        # NÃO usar impostos A RECOLHER do passivo!
        # 
        # Deduções são os impostos efetivamente deduzidos da receita bruta
        # A recolher são os valores pendentes de pagamento
        # ============================================================
        
        # Primeiro: tenta usar impostos detalhados da DRE (deduções)
        impostos_dre = (
            dados.get('icms_deducao', 0) + 
            dados.get('pis_deducao', 0) + 
            dados.get('cofins_deducao', 0) + 
            dados.get('irpj_deducao', 0) + 
            dados.get('csll_deducao', 0)
        )
        
        # Valor da conta 424 (IMPOSTOS SOBRE VENDAS) - fonte mais confiável
        impostos_conta_424 = dados.get('impostos_sobre_vendas', 0)
        
        if impostos_dre > 0:
            dados['impostos'] = impostos_dre
            print(f"[PARSER_DOMINIO_PDF] impostos (via soma DRE): R$ {impostos_dre:,.2f}")
            # Validar contra conta 424 se disponível
            if impostos_conta_424 > 0 and abs(impostos_dre - impostos_conta_424) > 100:
                print(f"[PARSER_DOMINIO_PDF] AVISO: Soma DRE ({impostos_dre:,.2f}) difere da conta 424 ({impostos_conta_424:,.2f})")
        elif impostos_conta_424 > 0:
            # Usar valor da conta 424 diretamente (mais confiável que soma manual)
            dados['impostos'] = impostos_conta_424
            print(f"[PARSER_DOMINIO_PDF] impostos (via conta 424): R$ {impostos_conta_424:,.2f}")
        elif dados['deducoes_receita'] > 0:
            # Fallback: usar deduções totais (inclui devoluções, mas é melhor que nada)
            dados['impostos'] = dados['deducoes_receita']
            print(f"[PARSER_DOMINIO_PDF] impostos (via deducoes_receita): R$ {dados['deducoes_receita']:,.2f}")
        else:
            # Último fallback: usar impostos do passivo + ICMS (menos preciso para carga tributária)
            dados['impostos'] = dados['icms'] + dados['iss'] + dados['pis'] + dados['cofins'] + dados['irpj'] + dados['csll']
            print(f"[PARSER_DOMINIO_PDF] impostos (via passivo - menos preciso): R$ {dados['impostos']:,.2f}")
        
        # ============================================================
        # PATRIMÔNIO LÍQUIDO - CÁLCULO TÉCNICO CORRETO
        # ============================================================
        # O Patrimônio Líquido durante o exercício DEVE incluir o 
        # Resultado do Período, conforme a estrutura contábil:
        #
        #   Capital Social
        #   + Reservas de Capital/Lucros
        #   + Lucros/Prejuízos Acumulados
        #   + RESULTADO DO EXERCÍCIO (grupo 3, ainda não encerrado)
        #   = PATRIMÔNIO LÍQUIDO TOTAL
        #
        # O ROE correto usa o PL Total (com resultado), pois:
        # - Durante o exercício, o resultado pertence aos sócios
        # - Ao final, será destinado (dividendos, reservas ou acumulado)
        # - Usar PL sem resultado distorce o indicador (ROE muito alto)
        #
        # Nota: Dividendos a Pagar são PASSIVO (lucros já deliberados),
        # não fazem parte do PL.
        # ============================================================
        
        lucros_acum = dados.get('lucros_acumulados', 0) or 0  # Lucros de exercícios ANTERIORES
        lucro_exerc = dados.get('lucro_liquido', 0) or 0      # Lucro do exercício ATUAL
        capital = dados.get('capital_social', 0) or 0
        dividendos = dados.get('dividendos_pagar', 0) or 0    # Lucros já deliberados (passivo)
        
        # PL Inicial (sem resultado do exercício atual)
        pl_inicial = capital + lucros_acum
        
        # PL Total = Capital + Lucros Anteriores + Resultado do Exercício
        pl_total = capital + lucros_acum + lucro_exerc
        
        # Se o PL informado é apenas Capital Social, usamos o PL Total
        if dados['patrimonio_liquido'] == 0 or dados['patrimonio_liquido'] == capital:
            # Usa PL Total (com resultado do exercício)
            dados['patrimonio_liquido'] = pl_total
            print(f"[PARSER_DOMINIO_PDF] PL Total (Capital + Lucros + Resultado): R$ {pl_total:,.2f}")
        elif dados['patrimonio_liquido'] > 0 and dados['patrimonio_liquido'] < pl_total:
            # PL informado pode ser apenas Capital, atualiza para PL Total
            dados['patrimonio_liquido'] = pl_total
            print(f"[PARSER_DOMINIO_PDF] PL atualizado para Total: R$ {pl_total:,.2f}")
        
        # Fallback se não temos capital
        if dados['patrimonio_liquido'] == 0 and dados['ativo_total'] > 0 and dados['passivo_circulante'] > 0:
            pl_residual = dados['ativo_total'] - dados['passivo_circulante'] - dados['passivo_nao_circulante']
            if pl_residual > 0:
                dados['patrimonio_liquido'] = pl_residual
                print(f"[PARSER_DOMINIO_PDF] PL (Ativo - Passivo): R$ {pl_residual:,.2f}")
        
        # Guarda o PL inicial (para ROE sobre capital inicial, se necessário)
        dados['patrimonio_liquido_inicial'] = pl_inicial
        dados['patrimonio_liquido_total'] = pl_total  # PL contábil completo
        
        print(f"[PARSER_DOMINIO_PDF] Capital: R$ {capital:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] Lucros Acumulados (anteriores): R$ {lucros_acum:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] Resultado do Exercício: R$ {lucro_exerc:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] Dividendos a Pagar (passivo): R$ {dividendos:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] PL Inicial (s/ resultado): R$ {pl_inicial:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] PL Total (c/ resultado): R$ {pl_total:,.2f}")
        
        # ============================================================
        # VERIFICAÇÃO DE CONSISTÊNCIA DO LUCRO
        # ============================================================
        # Se o lucro extraído é maior que a receita, há problema
        # Isso pode acontecer se pegamos o valor errado
        # ============================================================
        if dados['receita_bruta'] > 0 and dados['lucro_liquido'] > dados['receita_bruta']:
            print(f"[PARSER_DOMINIO_PDF] AVISO: Lucro ({dados['lucro_liquido']:,.2f}) > Receita ({dados['receita_bruta']:,.2f})")
            # Tenta usar os lucros acumulados como lucro do período
            if lucros_acum > 0 and lucros_acum <= dados['receita_bruta']:
                dados['lucro_liquido'] = lucros_acum
                print(f"[PARSER_DOMINIO_PDF] lucro_liquido (via lucros acumulados): R$ {lucros_acum:,.2f}")
            else:
                # Calcula lucro estimado: Receita - Deduções - Impostos - Despesas
                deducoes = dados['deducoes_receita'] if dados['deducoes_receita'] > 0 else dados['impostos']
                lucro_estimado = dados['receita_bruta'] - deducoes - dados['despesas_operacionais'] - dados['despesas_financeiras']
                
                if lucro_estimado > 0 and lucro_estimado <= dados['receita_bruta']:
                    dados['lucro_liquido'] = lucro_estimado
                    print(f"[PARSER_DOMINIO_PDF] lucro_liquido_estimado: R$ {lucro_estimado:,.2f}")
                else:
                    # Último recurso: limita a 80% da receita
                    dados['lucro_liquido'] = dados['receita_bruta'] * 0.80
                    print(f"[PARSER_DOMINIO_PDF] AVISO: Lucro limitado a 80% da receita")
        
        # ============================================================
        # FLAG: VALORES SÃO ACUMULADOS NO EXERCÍCIO
        # ============================================================
        # O balancete do Domínio mostra valores ACUMULADOS para DRE
        # Isso precisa ser considerado na análise para não duplicar
        # ============================================================
        dados['_valores_acumulados'] = True
        dados['_mes'] = resultado.mes if resultado.mes else None
        dados['_ano'] = resultado.ano if resultado.ano else None
        
        # === VERIFICA RESULTADO ===
        
        campos_com_valor = [k for k, v in dados.items() if isinstance(v, (int, float)) and v > 0]
        print(f"[PARSER_DOMINIO_PDF] Campos extraídos: {len(campos_com_valor)}")
        
        # Log dos principais valores para debug
        print(f"[PARSER_DOMINIO_PDF] === RESUMO FINAL ===")
        print(f"[PARSER_DOMINIO_PDF] Receita Bruta: R$ {dados['receita_bruta']:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] Deduções Receita: R$ {dados['deducoes_receita']:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] IMPOSTOS (total): R$ {dados['impostos']:,.2f}")
        print(f"[PARSER_DOMINIO_PDF]   - ICMS: R$ {dados['icms']:,.2f}")
        print(f"[PARSER_DOMINIO_PDF]   - PIS: R$ {dados['pis']:,.2f}")
        print(f"[PARSER_DOMINIO_PDF]   - COFINS: R$ {dados['cofins']:,.2f}")
        print(f"[PARSER_DOMINIO_PDF]   - IRPJ: R$ {dados.get('irpj', 0):,.2f}")
        print(f"[PARSER_DOMINIO_PDF]   - CSLL: R$ {dados.get('csll', 0):,.2f}")
        print(f"[PARSER_DOMINIO_PDF] Lucro Líquido: R$ {dados['lucro_liquido']:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] Patrimônio Líquido: R$ {dados['patrimonio_liquido']:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] Capital Social: R$ {dados['capital_social']:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] Estoques: R$ {dados['estoques']:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] Fornecedores: R$ {dados['fornecedores']:,.2f}")
        print(f"[PARSER_DOMINIO_PDF] Carga Tributária: {(dados['impostos']/dados['receita_bruta']*100) if dados['receita_bruta'] > 0 else 0:.2f}%")
        print(f"[PARSER_DOMINIO_PDF] ===================")
        
        if len(campos_com_valor) < 3:
            resultado.erro = "Poucos dados extraídos do PDF"
            return resultado
        
        resultado.dados = dados
        resultado.sucesso = True
        resultado.sistema = "dominio"
        resultado.contas_processadas = len(campos_com_valor)
        resultado.observacoes = [
            f"Parser local extraiu {len(campos_com_valor)} campos",
            "Sistema: Domínio Sistemas (PDF)"
        ]
        
        return resultado
        
    except Exception as e:
        resultado.erro = f"Erro ao processar PDF: {str(e)}"
        return resultado


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================


def parse_dominio(conteudo: bytes, nome_arquivo: str) -> ResultadoParser:
    """
    Parser principal para Domínio Sistemas.
    Suporta apenas arquivos PDF.
    """
    extensao = nome_arquivo.lower().split('.')[-1]
    
    if extensao == 'pdf':
        return parse_dominio_pdf(conteudo, nome_arquivo)
    else:
        return ResultadoParser(
            sucesso=False,
            erro=f"Formato não suportado: {extensao}. Use apenas PDF."
        )


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        arquivo = sys.argv[1]
        with open(arquivo, 'rb') as f:
            conteudo = f.read()
        
        resultado = parse_dominio(conteudo, arquivo)
        print(f"Sucesso: {resultado.sucesso}")
        print(f"Empresa: {resultado.empresa}")
        print(f"CNPJ: {resultado.cnpj}")
        print(f"Período: {resultado.periodo}")
        print(f"Contas processadas: {resultado.contas_processadas}")
        print(f"Dados: {resultado.dados}")
        if resultado.erro:
            print(f"Erro: {resultado.erro}")
    else:
        print("Uso: python parser_dominio.py <arquivo.pdf>")
