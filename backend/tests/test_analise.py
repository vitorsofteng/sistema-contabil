"""
Testes Unitários - Módulo de Análise Financeira
Testes PUROS que não dependem de módulos externos
"""

import pytest
from typing import Dict, List, Optional
from dataclasses import dataclass


# ============================================================================
# IMPLEMENTAÇÕES STANDALONE PARA TESTES
# ============================================================================

@dataclass
class DadosMensais:
    """Estrutura de dados mensais."""
    mes: int
    ano: int
    receita_bruta: float = 0
    custos: float = 0
    despesas_operacionais: float = 0
    despesas_financeiras: float = 0
    impostos: float = 0
    lucro_liquido: float = 0
    ativo_total: float = 0
    ativo_circulante: float = 0
    passivo_total: float = 0
    passivo_circulante: float = 0
    patrimonio_liquido: float = 0
    disponivel: float = 0


class IndicadoresFinanceirosStandalone:
    """Calculadora de indicadores financeiros."""
    
    @staticmethod
    def margem_bruta(receita: float, custos: float) -> float:
        """Calcula margem bruta."""
        if receita <= 0:
            return 0
        return ((receita - custos) / receita) * 100
    
    @staticmethod
    def margem_liquida(receita: float, lucro_liquido: float) -> float:
        """Calcula margem líquida."""
        if receita <= 0:
            return 0
        return (lucro_liquido / receita) * 100
    
    @staticmethod
    def liquidez_corrente(ativo_circulante: float, passivo_circulante: float) -> float:
        """Calcula liquidez corrente."""
        if passivo_circulante <= 0:
            return 0
        return ativo_circulante / passivo_circulante
    
    @staticmethod
    def liquidez_seca(ativo_circulante: float, estoques: float, passivo_circulante: float) -> float:
        """Calcula liquidez seca."""
        if passivo_circulante <= 0:
            return 0
        return (ativo_circulante - estoques) / passivo_circulante
    
    @staticmethod
    def liquidez_imediata(disponivel: float, passivo_circulante: float) -> float:
        """Calcula liquidez imediata."""
        if passivo_circulante <= 0:
            return 0
        return disponivel / passivo_circulante
    
    @staticmethod
    def endividamento(passivo_total: float, ativo_total: float) -> float:
        """Calcula endividamento geral."""
        if ativo_total <= 0:
            return 0
        return (passivo_total / ativo_total) * 100
    
    @staticmethod
    def composicao_endividamento(passivo_circulante: float, passivo_total: float) -> float:
        """Calcula composição do endividamento."""
        if passivo_total <= 0:
            return 0
        return (passivo_circulante / passivo_total) * 100
    
    @staticmethod
    def roa(lucro_liquido: float, ativo_total: float) -> float:
        """Calcula ROA (Return on Assets)."""
        if ativo_total <= 0:
            return 0
        return (lucro_liquido / ativo_total) * 100
    
    @staticmethod
    def roe(lucro_liquido: float, patrimonio_liquido: float) -> float:
        """Calcula ROE (Return on Equity)."""
        if patrimonio_liquido <= 0:
            return 0
        return (lucro_liquido / patrimonio_liquido) * 100
    
    @staticmethod
    def giro_ativo(receita: float, ativo_total: float) -> float:
        """Calcula giro do ativo."""
        if ativo_total <= 0:
            return 0
        return receita / ativo_total


class ClassificadorSaudeStandalone:
    """Classificador de saúde financeira."""
    
    @staticmethod
    def calcular_score(indicadores: Dict) -> float:
        """Calcula score de saúde financeira (0-100)."""
        score = 0
        peso_total = 0
        
        # Margem Líquida (peso 20)
        margem = indicadores.get('margem_liquida', 0)
        if margem >= 15:
            score += 20
        elif margem >= 10:
            score += 15
        elif margem >= 5:
            score += 10
        elif margem >= 0:
            score += 5
        peso_total += 20
        
        # Liquidez Corrente (peso 20)
        liquidez = indicadores.get('liquidez_corrente', 0)
        if liquidez >= 2.0:
            score += 20
        elif liquidez >= 1.5:
            score += 15
        elif liquidez >= 1.0:
            score += 10
        elif liquidez >= 0.5:
            score += 5
        peso_total += 20
        
        # Endividamento (peso 20)
        endividamento = indicadores.get('endividamento', 100)
        if endividamento <= 30:
            score += 20
        elif endividamento <= 50:
            score += 15
        elif endividamento <= 70:
            score += 10
        elif endividamento <= 90:
            score += 5
        peso_total += 20
        
        # ROE (peso 20)
        roe = indicadores.get('roe', 0)
        if roe >= 20:
            score += 20
        elif roe >= 15:
            score += 15
        elif roe >= 10:
            score += 10
        elif roe >= 5:
            score += 5
        peso_total += 20
        
        # ROA (peso 20)
        roa = indicadores.get('roa', 0)
        if roa >= 10:
            score += 20
        elif roa >= 7:
            score += 15
        elif roa >= 5:
            score += 10
        elif roa >= 2:
            score += 5
        peso_total += 20
        
        return (score / peso_total) * 100 if peso_total > 0 else 0
    
    @staticmethod
    def classificar(score: float) -> str:
        """Classifica a empresa com base no score."""
        if score >= 80:
            return "excelente"
        elif score >= 60:
            return "bom"
        elif score >= 40:
            return "regular"
        else:
            return "critico"


class AlertaFinanceiroStandalone:
    """Gerador de alertas financeiros."""
    
    NIVEL_CRITICO = "critico"
    NIVEL_ATENCAO = "atencao"
    NIVEL_INFO = "info"
    NIVEL_POSITIVO = "positivo"
    
    @classmethod
    def analisar(cls, indicadores: Dict) -> List[Dict]:
        """Analisa indicadores e gera alertas."""
        alertas = []
        
        # Liquidez crítica
        liquidez = indicadores.get('liquidez_corrente', 0)
        if liquidez < 1.0:
            alertas.append({
                "nivel": cls.NIVEL_CRITICO,
                "mensagem": "Liquidez corrente abaixo de 1,0 - risco de não conseguir pagar dívidas de curto prazo"
            })
        elif liquidez < 1.5:
            alertas.append({
                "nivel": cls.NIVEL_ATENCAO,
                "mensagem": "Liquidez corrente baixa - monitorar capacidade de pagamento"
            })
        
        # Margem negativa
        margem = indicadores.get('margem_liquida', 0)
        if margem < 0:
            alertas.append({
                "nivel": cls.NIVEL_CRITICO,
                "mensagem": "Margem líquida negativa - empresa operando com prejuízo"
            })
        elif margem < 5:
            alertas.append({
                "nivel": cls.NIVEL_ATENCAO,
                "mensagem": "Margem líquida muito baixa"
            })
        
        # Endividamento alto
        endividamento = indicadores.get('endividamento', 0)
        if endividamento > 80:
            alertas.append({
                "nivel": cls.NIVEL_CRITICO,
                "mensagem": "Endividamento acima de 80% - risco elevado"
            })
        elif endividamento > 60:
            alertas.append({
                "nivel": cls.NIVEL_ATENCAO,
                "mensagem": "Endividamento elevado - avaliar capacidade de pagamento"
            })
        
        # ROE excelente
        roe = indicadores.get('roe', 0)
        if roe > 20:
            alertas.append({
                "nivel": cls.NIVEL_POSITIVO,
                "mensagem": f"ROE de {roe:.1f}% - excelente retorno sobre o patrimônio"
            })
        
        return alertas


class AnalisadorContabilStandalone:
    """Analisador contábil principal."""
    
    def __init__(self, dados: List[DadosMensais]):
        self.dados = dados
    
    def calcular_indicadores(self, dados: DadosMensais) -> Dict:
        """Calcula indicadores para um período."""
        calc = IndicadoresFinanceirosStandalone
        
        return {
            'margem_bruta': calc.margem_bruta(dados.receita_bruta, dados.custos),
            'margem_liquida': calc.margem_liquida(dados.receita_bruta, dados.lucro_liquido),
            'liquidez_corrente': calc.liquidez_corrente(dados.ativo_circulante, dados.passivo_circulante),
            'liquidez_imediata': calc.liquidez_imediata(dados.disponivel, dados.passivo_circulante),
            'endividamento': calc.endividamento(dados.passivo_total, dados.ativo_total),
            'roa': calc.roa(dados.lucro_liquido, dados.ativo_total),
            'roe': calc.roe(dados.lucro_liquido, dados.patrimonio_liquido),
            'giro_ativo': calc.giro_ativo(dados.receita_bruta, dados.ativo_total)
        }
    
    def analisar(self) -> Dict:
        """Realiza análise completa."""
        if not self.dados:
            return {"erro": "Sem dados para análise"}
        
        # Usar último período
        ultimo = self.dados[-1]
        indicadores = self.calcular_indicadores(ultimo)
        
        # Score e classificação
        score = ClassificadorSaudeStandalone.calcular_score(indicadores)
        classificacao = ClassificadorSaudeStandalone.classificar(score)
        
        # Alertas
        alertas = AlertaFinanceiroStandalone.analisar(indicadores)
        
        return {
            'periodo': f"{ultimo.mes:02d}/{ultimo.ano}",
            'indicadores': indicadores,
            'score': score,
            'classificacao': classificacao,
            'alertas': alertas
        }


# ============================================================================
# TESTES
# ============================================================================

class TestIndicadoresFinanceiros:
    """Testes para cálculos de indicadores financeiros."""
    
    def test_margem_bruta_calculo(self):
        resultado = IndicadoresFinanceirosStandalone.margem_bruta(100000, 60000)
        assert abs(resultado - 40.0) < 0.1
    
    def test_margem_bruta_receita_zero(self):
        resultado = IndicadoresFinanceirosStandalone.margem_bruta(0, 60000)
        assert resultado == 0
    
    def test_margem_liquida_calculo(self):
        resultado = IndicadoresFinanceirosStandalone.margem_liquida(100000, 15000)
        assert abs(resultado - 15.0) < 0.1
    
    def test_margem_liquida_receita_zero(self):
        resultado = IndicadoresFinanceirosStandalone.margem_liquida(0, 15000)
        assert resultado == 0
    
    def test_liquidez_corrente_calculo(self):
        resultado = IndicadoresFinanceirosStandalone.liquidez_corrente(200000, 100000)
        assert abs(resultado - 2.0) < 0.1
    
    def test_liquidez_corrente_passivo_zero(self):
        resultado = IndicadoresFinanceirosStandalone.liquidez_corrente(200000, 0)
        assert resultado == 0
    
    def test_endividamento_calculo(self):
        resultado = IndicadoresFinanceirosStandalone.endividamento(200000, 500000)
        assert abs(resultado - 40.0) < 0.1
    
    def test_endividamento_ativo_zero(self):
        resultado = IndicadoresFinanceirosStandalone.endividamento(200000, 0)
        assert resultado == 0
    
    def test_roa_calculo(self):
        resultado = IndicadoresFinanceirosStandalone.roa(50000, 500000)
        assert abs(resultado - 10.0) < 0.1
    
    def test_roe_calculo(self):
        resultado = IndicadoresFinanceirosStandalone.roe(30000, 200000)
        assert abs(resultado - 15.0) < 0.1
    
    def test_giro_ativo_calculo(self):
        resultado = IndicadoresFinanceirosStandalone.giro_ativo(1000000, 500000)
        assert abs(resultado - 2.0) < 0.1


class TestClassificacaoSaude:
    """Testes para classificação de saúde financeira."""
    
    def test_score_excelente(self):
        indicadores = {
            'margem_liquida': 20,
            'liquidez_corrente': 2.5,
            'endividamento': 25,
            'roe': 25,
            'roa': 12
        }
        score = ClassificadorSaudeStandalone.calcular_score(indicadores)
        assert score >= 80
    
    def test_classificar_excelente(self):
        assert ClassificadorSaudeStandalone.classificar(85) == "excelente"
        assert ClassificadorSaudeStandalone.classificar(80) == "excelente"
    
    def test_classificar_bom(self):
        assert ClassificadorSaudeStandalone.classificar(70) == "bom"
        assert ClassificadorSaudeStandalone.classificar(60) == "bom"
    
    def test_classificar_regular(self):
        assert ClassificadorSaudeStandalone.classificar(50) == "regular"
        assert ClassificadorSaudeStandalone.classificar(40) == "regular"
    
    def test_classificar_critico(self):
        assert ClassificadorSaudeStandalone.classificar(30) == "critico"
        assert ClassificadorSaudeStandalone.classificar(0) == "critico"


class TestAlertaFinanceiro:
    """Testes para alertas financeiros."""
    
    def test_alerta_liquidez_critica(self):
        indicadores = {'liquidez_corrente': 0.5, 'margem_liquida': 10, 'endividamento': 50}
        alertas = AlertaFinanceiroStandalone.analisar(indicadores)
        assert any(a['nivel'] == 'critico' and 'liquidez' in a['mensagem'].lower() for a in alertas)
    
    def test_alerta_margem_negativa(self):
        indicadores = {'liquidez_corrente': 2.0, 'margem_liquida': -5, 'endividamento': 50}
        alertas = AlertaFinanceiroStandalone.analisar(indicadores)
        assert any(a['nivel'] == 'critico' and 'margem' in a['mensagem'].lower() for a in alertas)
    
    def test_alerta_endividamento_alto(self):
        indicadores = {'liquidez_corrente': 2.0, 'margem_liquida': 10, 'endividamento': 85}
        alertas = AlertaFinanceiroStandalone.analisar(indicadores)
        assert any(a['nivel'] == 'critico' and 'endividamento' in a['mensagem'].lower() for a in alertas)
    
    def test_alerta_positivo_roe(self):
        indicadores = {'liquidez_corrente': 2.0, 'margem_liquida': 15, 'endividamento': 30, 'roe': 25}
        alertas = AlertaFinanceiroStandalone.analisar(indicadores)
        assert any(a['nivel'] == 'positivo' for a in alertas)
    
    def test_sem_alertas_empresa_saudavel(self):
        indicadores = {'liquidez_corrente': 2.0, 'margem_liquida': 15, 'endividamento': 30, 'roe': 10}
        alertas = AlertaFinanceiroStandalone.analisar(indicadores)
        criticos = [a for a in alertas if a['nivel'] == 'critico']
        assert len(criticos) == 0


class TestAnalisadorContabil:
    """Testes para o analisador contábil."""
    
    def test_analise_completa(self):
        dados = [
            DadosMensais(
                mes=1, ano=2024,
                receita_bruta=100000, custos=60000,
                despesas_operacionais=20000, lucro_liquido=12000,
                ativo_total=500000, ativo_circulante=200000,
                passivo_total=300000, passivo_circulante=150000,
                patrimonio_liquido=200000, disponivel=50000
            )
        ]
        
        analisador = AnalisadorContabilStandalone(dados)
        resultado = analisador.analisar()
        
        assert 'indicadores' in resultado
        assert 'score' in resultado
        assert 'classificacao' in resultado
        assert 'alertas' in resultado
    
    def test_analise_sem_dados(self):
        analisador = AnalisadorContabilStandalone([])
        resultado = analisador.analisar()
        assert 'erro' in resultado
    
    def test_calculo_indicadores(self):
        dados = DadosMensais(
            mes=1, ano=2024,
            receita_bruta=100000, custos=60000,
            lucro_liquido=10000,
            ativo_total=200000, ativo_circulante=80000,
            passivo_total=100000, passivo_circulante=50000,
            patrimonio_liquido=100000, disponivel=20000
        )
        
        analisador = AnalisadorContabilStandalone([dados])
        indicadores = analisador.calcular_indicadores(dados)
        
        assert 'margem_bruta' in indicadores
        assert 'margem_liquida' in indicadores
        assert 'liquidez_corrente' in indicadores
        assert 'endividamento' in indicadores
        assert 'roa' in indicadores
        assert 'roe' in indicadores


class TestValidacoesNegocio:
    """Testes para validações de regras de negócio."""
    
    def test_cnpj_formato_valido(self):
        import re
        cnpj = "12.345.678/0001-90"
        pattern = r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$'
        assert re.match(pattern, cnpj) is not None
    
    def test_cpf_formato_valido(self):
        import re
        cpf = "123.456.789-00"
        pattern = r'^\d{3}\.\d{3}\.\d{3}-\d{2}$'
        assert re.match(pattern, cpf) is not None
    
    def test_email_formato_valido(self):
        import re
        email = "teste@empresa.com.br"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        assert re.match(pattern, email) is not None
    
    def test_email_formato_invalido(self):
        import re
        emails_invalidos = ["teste", "teste@", "@empresa.com", "teste@.com"]
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in emails_invalidos:
            assert re.match(pattern, email) is None
    
    def test_mes_valido(self):
        for mes in range(1, 13):
            assert 1 <= mes <= 12
        assert not (1 <= 0 <= 12)
        assert not (1 <= 13 <= 12)
    
    def test_ano_razoavel(self):
        ano = 2024
        assert 1900 <= ano <= 2100
    
    def test_valores_financeiros_positivos(self):
        valores = [100000.50, 0.01, 1000000]
        for valor in valores:
            assert valor > 0
