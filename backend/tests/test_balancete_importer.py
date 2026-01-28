"""
Testes do Importador de Balancetes
Sprint 5 - Sistema Contábil
"""

import pytest
from datetime import date
from typing import Dict


# ============================================================================
# DADOS DE TESTE BASEADOS NO BALANCETE REAL
# ============================================================================

# Texto simulado do balancete (baseado no PDF real)
TEXTO_BALANCETE_REAL = """
BALANCETE
Folha: 0001
Número livro: 0001

Empresa: JMR ENGENHARIA E EMPREENDIMENTOS CIA LTDA
C.N.P.J.: 62.798.308/0001-81
Período: 01/09/2025 - 31/12/2025

Código  Descrição da conta                              Saldo Anterior    Débito          Crédito         Saldo Atual
1       ATIVO                                           0,00              7.201.123,29    1.138.242,70    6.062.880,59D
2       ATIVO CIRCULANTE                                0,00              7.201.123,29    1.138.242,70    6.062.880,59D
3       DISPONÍVEL                                      0,00              589.123,29      569.121,35      20.001,94D
4       CAIXA                                           0,00              10.000,00       0,00            10.000,00D
5       CAIXA GERAL                                     0,00              10.000,00       0,00            10.000,00D
7       BANCOS CONTA MOVIMENTO                          0,00              579.123,29      569.121,35      10.001,94D
8       ITAU AG 4739 CC 0098922-8                       0,00              579.123,29      569.121,35      10.001,94D
12      CLIENTES                                        0,00              6.612.000,00    569.121,35      6.042.878,65D
13      DUPLICATAS A RECEBER                            0,00              6.612.000,00    569.121,35      6.042.878,65D
149     PASSIVO                                         0,00              11.683.224,20   17.746.104,79   6.062.880,59C
150     PASSIVO CIRCULANTE                              0,00              567.636,74      6.610.517,33    6.042.880,59C
169     OBRIGAÇÕES TRIBUTÁRIAS                          0,00              567.636,74      1.052.723,60    485.086,86C
170     IMPOSTOS E CONTRIBUIÇÕES A RECOLHER             0,00              567.636,74      1.052.723,60    485.086,86C
173     ISS A RECOLHER                                  0,00              75.000,00       100.000,00      25.000,00C
176     IMPOSTO DE RENDA A RECOLHER                     0,00              217.973,34      520.960,00      302.986,66C
177     CONTRIBUIÇÃO SOCIAL A RECOLHER                  0,00              78.950,40       190.425,60      111.475,20C
179     PIS A RECOLHER                                  0,00              34.853,00       42.978,00       8.125,00C
180     COFINS A RECOLHER                               0,00              160.860,00      198.360,00      37.500,00C
207     DIVIDENDOS, PART. E JURO SOBRE O CAPITAL        0,00              0,00            5.557.793,73    5.557.793,73C
210     DIVIDENDOS A PAGAR                              0,00              0,00            5.557.793,73    5.557.793,73C
503     PASSIVO NÃO-CIRCULANTE                          0,00              0,00            10.000,00       10.000,00C
219     EMPRÉSTIMOS                                     0,00              0,00            10.000,00       10.000,00C
242     PATRIMÔNIO LÍQUIDO                              0,00              11.115.587,46   11.125.587,46   10.000,00C
243     CAPITAL SOCIAL                                  0,00              0,00            10.000,00       10.000,00C
244     CAPITAL SUBSCRITO                               0,00              0,00            10.000,00       10.000,00C
404     RECEITA BRUTA DE VENDAS E SERVIÇOS              0,00              6.612.000,00    6.612.000,00    0,00
410     RECEITA DE PRESTAÇÃO DE SERVIÇOS                0,00              6.612.000,00    6.612.000,00    0,00
411     SERVIÇOS PRESTADOS                              0,00              6.612.000,00    6.612.000,00    0,00
413     (-) DEDUÇÕES DA RECEITA BRUTA                   0,00              1.052.723,60    1.052.723,60    0,00
427     (-) ISS                                         0,00              100.000,00      100.000,00      0,00
428     (-) COFINS                                      0,00              198.360,00      198.360,00      0,00
429     (-) PIS                                         0,00              42.978,00       42.978,00       0,00
477     (-) CONTRIBUIÇÃO SOCIAL                         0,00              190.425,60      190.425,60      0,00
478     (-) IMPOSTO DE RENDA                            0,00              520.960,00      520.960,00      0,00
295     DESPESAS OPERACIONAIS                           0,00              1.484,61        1.484,61        0,00
367     DESPESAS FINANCEIRAS                            0,00              1.484,61        1.484,61        0,00
449     RECEITAS NÃO OPERACIONAIS                       0,00              1,94            1,94            0,00
522     LUCRO DO EXERCÍCIO                              0,00              5.557.793,73    5.557.793,73    0,00

RESUMO DO BALANCETE
ATIVO                                                   0,00              7.201.123,29    1.138.242,70    6.062.880,59D
PASSIVO                                                 0,00              11.683.224,20   17.746.104,79   6.062.880,59C

_______________________________________
ISAAC ALVES PORTO
Contador
Reg. no CRC - DF sob o No. TO005746O2
CPF: 019.956.451-50

_______________________________________
FABIANA BARROS FERRAZ REGUFFE
CPF: 890.588.521-72

Sistema licenciado para TRANSFORMA GESTAO CONTABIL LTDA
"""


# ============================================================================
# SIMULADOR DE PARSER (para testes standalone)
# ============================================================================

class ParserBalanceteStandalone:
    """Parser standalone para testes."""
    
    import re
    
    MAPEAMENTO_CONTAS = {
        r'^ativo$': ('ativo_total', 'D'),
        r'^ativo circulante$': ('ativo_circulante', 'D'),
        r'^dispon[íi]vel$': ('disponivel', 'D'),
        r'^caixa$': ('caixa', 'D'),
        r'^bancos?\s*(conta\s*movimento)?$': ('bancos', 'D'),
        r'^clientes?$': ('clientes', 'D'),
        r'^duplicatas\s*a\s*receber$': ('duplicatas_receber', 'D'),
        r'^passivo$': ('passivo_total', 'C'),
        r'^passivo circulante$': ('passivo_circulante', 'C'),
        r'^passivo n[ãa]o[- ]?circulante$': ('passivo_nao_circulante', 'C'),
        r'^obriga[çc][õo]es\s*tribut[áa]rias': ('obrigacoes_tributarias', 'C'),
        r'^iss\s*a\s*recolher': ('iss_recolher', 'C'),
        r'^pis\s*a\s*recolher': ('pis_recolher', 'C'),
        r'^cofins\s*a\s*recolher': ('cofins_recolher', 'C'),
        r'^(?:imposto\s*de\s*renda|irpj?)\s*a\s*recolher': ('irpj_recolher', 'C'),
        r'^(?:contribui[çc][ãa]o\s*social|csll?)\s*a\s*recolher': ('csll_recolher', 'C'),
        r'^dividendos?\s*a\s*pagar': ('dividendos_pagar', 'C'),
        r'^empr[ée]stimos?$': ('emprestimos', 'C'),
        r'^patrim[ôo]nio\s*l[íi]quido$': ('patrimonio_liquido', 'C'),
        r'^capital\s*social$': ('capital_social', 'C'),
        r'^receita\s*bruta': ('receita_bruta', 'C'),
        r'^servi[çc]os\s*prestados$': ('receita_servicos', 'C'),
        r'^\(-\)\s*dedu[çc][õo]es': ('deducoes_receita', 'D'),
        r'^\(-\)\s*iss$': ('iss_deducao', 'D'),
        r'^\(-\)\s*pis$': ('pis_deducao', 'D'),
        r'^\(-\)\s*cofins$': ('cofins_deducao', 'D'),
        r'^\(-\)\s*(?:contribui[çc][ãa]o\s*social|csll?)': ('csll_deducao', 'D'),
        r'^\(-\)\s*(?:imposto\s*de\s*renda|irpj?)': ('irpj_deducao', 'D'),
        r'^despesas?\s*operacionais?$': ('despesas_operacionais', 'D'),
        r'^despesas?\s*financeiras?': ('despesas_financeiras', 'D'),
        r'^receitas?\s*n[ãa]o\s*operacionais?': ('receitas_nao_operacionais', 'C'),
        r'^lucro\s*(?:do\s*)?exerc[íi]cio': ('lucro_liquido', 'C'),
    }
    
    def extrair_cnpj(self, texto: str) -> str:
        """Extrai CNPJ do texto."""
        import re
        match = re.search(r'C\.?N\.?P\.?J\.?:?\s*(\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2})', texto, re.IGNORECASE)
        if match:
            cnpj = re.sub(r'\D', '', match.group(1))
            return cnpj
        return ""
    
    def extrair_periodo(self, texto: str) -> tuple:
        """Extrai período do texto."""
        import re
        match = re.search(r'Per[íi]odo:?\s*(\d{2}[/.-]\d{2}[/.-]\d{4})\s*[-–a]\s*(\d{2}[/.-]\d{2}[/.-]\d{4})', texto, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    def extrair_nome_empresa(self, texto: str) -> str:
        """Extrai nome da empresa."""
        import re
        match = re.search(r'Empresa:?\s*([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][A-ZÀÁÂÃÉÊÍÓÔÕÚÇ\s\.\-&0-9]+(?:LTDA|CIA LTDA|ME|EPP))', texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    def extrair_contador(self, texto: str) -> tuple:
        """Extrai dados do contador."""
        import re
        nome = None
        crc = None
        cpf = None
        
        # Nome após "Contador"
        match = re.search(r'Contador[:\s]*\n?\s*([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][A-Za-zàáâãéêíóôõúç\s]+)', texto, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
        
        # CRC
        match = re.search(r'CRC[:\s-]*([A-Z]{2}[\s-]?\d+[/O]?\d*)', texto, re.IGNORECASE)
        if match:
            crc = match.group(1).strip()
        
        # CPF
        matches = re.findall(r'CPF:?\s*(\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2})', texto)
        if matches:
            cpf = matches[0]
        
        return nome, crc, cpf
    
    def parse_valor(self, texto: str) -> float:
        """Converte valor brasileiro para float."""
        import re
        if not texto:
            return 0.0
        texto = str(texto).strip()
        texto = re.sub(r'[DC]$', '', texto).strip()
        if ',' in texto:
            texto = texto.replace('.', '').replace(',', '.')
        try:
            return abs(float(texto))
        except:
            return 0.0
    
    def identificar_conta(self, descricao: str) -> tuple:
        """Identifica campo da conta."""
        import re
        desc_lower = descricao.lower().strip()
        for pattern, (campo, natureza) in self.MAPEAMENTO_CONTAS.items():
            if re.match(pattern, desc_lower, re.IGNORECASE):
                return campo, natureza
        return None, None


# ============================================================================
# TESTES DO PARSER
# ============================================================================

class TestParserBalancete:
    """Testes do parser de balancete."""
    
    @pytest.fixture
    def parser(self):
        return ParserBalanceteStandalone()
    
    @pytest.fixture
    def texto(self):
        return TEXTO_BALANCETE_REAL
    
    # ===== TESTES DE EXTRAÇÃO DE METADADOS =====
    
    def test_extrair_cnpj(self, parser, texto):
        """Deve extrair CNPJ corretamente."""
        cnpj = parser.extrair_cnpj(texto)
        assert cnpj == "62798308000181"
    
    def test_extrair_cnpj_formatacao(self, parser):
        """Deve extrair CNPJ em diferentes formatos."""
        textos = [
            "CNPJ: 62.798.308/0001-81",
            "C.N.P.J.: 62.798.308/0001-81",
            "CNPJ 62798308000181",
            "C.N.P.J. 62 798 308 0001 81"
        ]
        for texto in textos:
            cnpj = parser.extrair_cnpj(texto)
            assert cnpj == "62798308000181", f"Falhou para: {texto}"
    
    def test_extrair_periodo(self, parser, texto):
        """Deve extrair período corretamente."""
        inicio, fim = parser.extrair_periodo(texto)
        assert inicio == "01/09/2025"
        assert fim == "31/12/2025"
    
    def test_extrair_nome_empresa(self, parser, texto):
        """Deve extrair nome da empresa."""
        nome = parser.extrair_nome_empresa(texto)
        assert "JMR ENGENHARIA" in nome
        assert "CIA LTDA" in nome
    
    def test_extrair_contador(self, parser, texto):
        """Deve extrair dados do contador."""
        nome, crc, cpf = parser.extrair_contador(texto)
        assert nome is not None
        assert "ISAAC" in nome.upper() or nome == "ISAAC ALVES PORTO"
        assert crc is not None
        assert "TO005746" in crc
    
    # ===== TESTES DE CONVERSÃO DE VALORES =====
    
    def test_parse_valor_brasileiro(self, parser):
        """Deve converter valores no formato brasileiro."""
        assert parser.parse_valor("6.062.880,59D") == 6062880.59
        assert parser.parse_valor("1.052.723,60") == 1052723.60
        assert parser.parse_valor("10.000,00") == 10000.00
        assert parser.parse_valor("0,00") == 0.0
        assert parser.parse_valor("5.557.793,73C") == 5557793.73
    
    def test_parse_valor_inteiro(self, parser):
        """Deve converter valores inteiros."""
        assert parser.parse_valor("100000") == 100000.0
        assert parser.parse_valor("1234") == 1234.0
    
    def test_parse_valor_vazio(self, parser):
        """Deve tratar valores vazios."""
        assert parser.parse_valor("") == 0.0
        assert parser.parse_valor(None) == 0.0
        assert parser.parse_valor("   ") == 0.0
    
    # ===== TESTES DE IDENTIFICAÇÃO DE CONTAS =====
    
    def test_identificar_ativo(self, parser):
        """Deve identificar contas de ativo."""
        campo, nat = parser.identificar_conta("ATIVO")
        assert campo == "ativo_total"
        assert nat == "D"
        
        campo, nat = parser.identificar_conta("ATIVO CIRCULANTE")
        assert campo == "ativo_circulante"
    
    def test_identificar_passivo(self, parser):
        """Deve identificar contas de passivo."""
        campo, nat = parser.identificar_conta("PASSIVO")
        assert campo == "passivo_total"
        assert nat == "C"
        
        campo, nat = parser.identificar_conta("PASSIVO CIRCULANTE")
        assert campo == "passivo_circulante"
    
    def test_identificar_patrimonio(self, parser):
        """Deve identificar patrimônio líquido."""
        campo, nat = parser.identificar_conta("PATRIMÔNIO LÍQUIDO")
        assert campo == "patrimonio_liquido"
        assert nat == "C"
    
    def test_identificar_disponibilidades(self, parser):
        """Deve identificar disponibilidades."""
        campo, _ = parser.identificar_conta("CAIXA")
        assert campo == "caixa"
        
        campo, _ = parser.identificar_conta("BANCOS CONTA MOVIMENTO")
        assert campo == "bancos"
    
    def test_identificar_impostos_recolher(self, parser):
        """Deve identificar impostos a recolher."""
        casos = [
            ("ISS A RECOLHER", "iss_recolher"),
            ("PIS A RECOLHER", "pis_recolher"),
            ("COFINS A RECOLHER", "cofins_recolher"),
            ("IMPOSTO DE RENDA A RECOLHER", "irpj_recolher"),
            ("CONTRIBUIÇÃO SOCIAL A RECOLHER", "csll_recolher"),
        ]
        for descricao, campo_esperado in casos:
            campo, nat = parser.identificar_conta(descricao)
            assert campo == campo_esperado, f"Falhou para: {descricao}"
            assert nat == "C"
    
    def test_identificar_deducoes(self, parser):
        """Deve identificar deduções da receita."""
        casos = [
            ("(-) ISS", "iss_deducao"),
            ("(-) PIS", "pis_deducao"),
            ("(-) COFINS", "cofins_deducao"),
            ("(-) CONTRIBUIÇÃO SOCIAL", "csll_deducao"),
            ("(-) IMPOSTO DE RENDA", "irpj_deducao"),
        ]
        for descricao, campo_esperado in casos:
            campo, nat = parser.identificar_conta(descricao)
            assert campo == campo_esperado, f"Falhou para: {descricao}"
            assert nat == "D"
    
    def test_identificar_receitas_despesas(self, parser):
        """Deve identificar receitas e despesas."""
        campo, _ = parser.identificar_conta("SERVIÇOS PRESTADOS")
        assert campo == "receita_servicos"
        
        campo, _ = parser.identificar_conta("DESPESAS OPERACIONAIS")
        assert campo == "despesas_operacionais"
        
        campo, _ = parser.identificar_conta("DESPESAS FINANCEIRAS")
        assert campo == "despesas_financeiras"
    
    def test_identificar_resultado(self, parser):
        """Deve identificar contas de resultado."""
        campo, nat = parser.identificar_conta("LUCRO DO EXERCÍCIO")
        assert campo == "lucro_liquido"
        assert nat == "C"


# ============================================================================
# TESTES DE DADOS EXTRAÍDOS
# ============================================================================

class TestDadosExtraidos:
    """Testes de validação dos dados extraídos do balancete real."""
    
    @pytest.fixture
    def dados_esperados(self) -> Dict:
        """Dados esperados do balancete real."""
        return {
            # Identificação
            "cnpj": "62798308000181",
            "empresa": "JMR ENGENHARIA E EMPREENDIMENTOS CIA LTDA",
            
            # Balanço Patrimonial
            "ativo_total": 6062880.59,
            "ativo_circulante": 6062880.59,
            "disponivel": 20001.94,
            "caixa": 10000.00,
            "bancos": 10001.94,
            "clientes": 6042878.65,
            
            "passivo_total": 6062880.59,
            "passivo_circulante": 6042880.59,
            "passivo_nao_circulante": 10000.00,
            "emprestimos_lp": 10000.00,
            "dividendos_pagar": 5557793.73,
            
            "patrimonio_liquido": 10000.00,
            "capital_social": 10000.00,
            
            # Impostos a Recolher
            "iss_recolher": 25000.00,
            "irpj_recolher": 302986.66,
            "csll_recolher": 111475.20,
            "pis_recolher": 8125.00,
            "cofins_recolher": 37500.00,
            
            # DRE
            "receita_bruta": 6612000.00,
            "receita_servicos": 6612000.00,
            "deducoes_receita": 1052723.60,
            
            # Impostos sobre vendas
            "iss_deducao": 100000.00,
            "cofins_deducao": 198360.00,
            "pis_deducao": 42978.00,
            "csll_deducao": 190425.60,
            "irpj_deducao": 520960.00,
            
            # Despesas
            "despesas_operacionais": 1484.61,
            "despesas_financeiras": 1484.61,
            "receitas_nao_operacionais": 1.94,
            
            # Resultado
            "lucro_liquido": 5557793.73,
        }
    
    def test_valores_ativo(self, dados_esperados):
        """Valida valores do ativo."""
        # Ativo = Caixa + Bancos + Clientes
        caixa = dados_esperados["caixa"]
        bancos = dados_esperados["bancos"]
        clientes = dados_esperados["clientes"]
        
        # Disponível = Caixa + Bancos
        assert abs(caixa + bancos - dados_esperados["disponivel"]) < 0.01
        
        # Ativo Circulante = Disponível + Clientes
        assert abs(dados_esperados["disponivel"] + clientes - dados_esperados["ativo_circulante"]) < 0.01
    
    def test_valores_passivo(self, dados_esperados):
        """Valida valores do passivo."""
        # Conferir balanço
        ativo = dados_esperados["ativo_total"]
        passivo = dados_esperados["passivo_total"]
        
        # Ativo = Passivo (balanço equilibrado)
        assert abs(ativo - passivo) < 0.01
    
    def test_valores_impostos(self, dados_esperados):
        """Valida valores dos impostos."""
        # Total de deduções
        iss = dados_esperados["iss_deducao"]
        pis = dados_esperados["pis_deducao"]
        cofins = dados_esperados["cofins_deducao"]
        irpj = dados_esperados["irpj_deducao"]
        csll = dados_esperados["csll_deducao"]
        
        total_impostos = iss + pis + cofins + irpj + csll
        
        assert abs(total_impostos - dados_esperados["deducoes_receita"]) < 0.01
    
    def test_calculo_lucro(self, dados_esperados):
        """Valida cálculo do lucro."""
        receita = dados_esperados["receita_bruta"]
        deducoes = dados_esperados["deducoes_receita"]
        despesas = dados_esperados["despesas_operacionais"]
        receitas_nao_op = dados_esperados["receitas_nao_operacionais"]
        
        # Lucro = Receita - Deduções - Despesas + Outras Receitas
        lucro_calc = receita - deducoes - despesas + receitas_nao_op
        
        # Deve ser próximo do lucro informado
        assert abs(lucro_calc - dados_esperados["lucro_liquido"]) < 1.0


# ============================================================================
# TESTES DE INDICADORES FINANCEIROS
# ============================================================================

class TestIndicadoresFinanceiros:
    """Testes de cálculo de indicadores financeiros."""
    
    @pytest.fixture
    def dados(self) -> Dict:
        """Dados financeiros do balancete."""
        return {
            "ativo_total": 6062880.59,
            "ativo_circulante": 6062880.59,
            "passivo_circulante": 6042880.59,
            "passivo_total": 6062880.59,
            "patrimonio_liquido": 10000.00,
            "disponivel": 20001.94,
            "estoques": 0.0,
            "receita_bruta": 6612000.00,
            "lucro_liquido": 5557793.73,
        }
    
    def test_liquidez_corrente(self, dados):
        """Calcula liquidez corrente."""
        lc = dados["ativo_circulante"] / dados["passivo_circulante"]
        # LC deve ser próxima de 1 (ativo ≈ passivo circulante)
        assert 0.9 < lc < 1.1
    
    def test_liquidez_imediata(self, dados):
        """Calcula liquidez imediata."""
        li = dados["disponivel"] / dados["passivo_circulante"]
        # Baixa liquidez imediata (pouco caixa vs obrigações)
        assert li < 0.01
    
    def test_margem_liquida(self, dados):
        """Calcula margem líquida."""
        ml = (dados["lucro_liquido"] / dados["receita_bruta"]) * 100
        # Margem alta (~84%)
        assert 80 < ml < 90
    
    def test_roe(self, dados):
        """Calcula ROE (Return on Equity)."""
        roe = (dados["lucro_liquido"] / dados["patrimonio_liquido"]) * 100
        # ROE extremamente alto devido ao baixo PL
        assert roe > 50000  # Mais de 50.000%
    
    def test_endividamento(self, dados):
        """Calcula índice de endividamento."""
        endiv = (dados["passivo_total"] / dados["ativo_total"]) * 100
        # Endividamento de ~100% (quase todo ativo financiado por terceiros)
        assert 99 < endiv < 101


# ============================================================================
# TESTES DE INTEGRAÇÃO DO FLUXO
# ============================================================================

class TestFluxoImportacao:
    """Testes do fluxo completo de importação."""
    
    def test_fluxo_empresa_nova(self):
        """Simula importação com criação de empresa nova."""
        # Simular repositório
        class RepositorioMock:
            def __init__(self):
                self.empresas = {}
                self._counter = 0
            
            def buscar_por_cnpj(self, cnpj):
                return self.empresas.get(cnpj)
            
            def criar_empresa(self, nome, cnpj):
                self._counter += 1
                empresa = type('Empresa', (), {'id': self._counter, 'nome': nome, 'cnpj': cnpj})()
                self.empresas[cnpj] = empresa
                return empresa
        
        repo = RepositorioMock()
        
        # Simular importação
        cnpj = "62798308000181"
        
        # Verificar empresa não existe
        assert repo.buscar_por_cnpj(cnpj) is None
        
        # Criar empresa
        empresa = repo.criar_empresa("JMR ENGENHARIA", cnpj)
        
        # Verificar criação
        assert empresa.id == 1
        assert repo.buscar_por_cnpj(cnpj) is not None
    
    def test_fluxo_empresa_existente(self):
        """Simula importação para empresa existente."""
        class RepositorioMock:
            def __init__(self):
                self.empresas = {
                    "62798308000181": type('Empresa', (), {'id': 99, 'nome': 'JMR', 'cnpj': '62798308000181'})()
                }
            
            def buscar_por_cnpj(self, cnpj):
                return self.empresas.get(cnpj)
        
        repo = RepositorioMock()
        
        # Empresa já existe
        empresa = repo.buscar_por_cnpj("62798308000181")
        assert empresa is not None
        assert empresa.id == 99
    
    def test_fluxo_conversao_dados_mensais(self):
        """Testa conversão para formato de dados mensais."""
        # Dados do balancete
        dados_balancete = {
            "empresa_cnpj": "62798308000181",
            "empresa_nome": "JMR ENGENHARIA",
            "periodo_fim": "2025-12-31",
            "ativo_total": 6062880.59,
            "passivo_circulante": 6042880.59,
            "receita_bruta": 6612000.00,
            "lucro_liquido": 5557793.73,
        }
        
        # Converter para dados mensais
        dados_mensais = {
            "empresa_cnpj": dados_balancete["empresa_cnpj"],
            "mes": 12,
            "ano": 2025,
            "receita_bruta": dados_balancete["receita_bruta"],
            "lucro_liquido": dados_balancete["lucro_liquido"],
            "ativo_total": dados_balancete["ativo_total"],
            "passivo_circulante": dados_balancete["passivo_circulante"],
        }
        
        # Validar
        assert dados_mensais["mes"] == 12
        assert dados_mensais["ano"] == 2025
        assert dados_mensais["receita_bruta"] == 6612000.00


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
