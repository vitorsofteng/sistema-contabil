"""
Módulo de Validação de Importação
================================

Valida dados importados e retorna:
- Alertas de inconsistências
- Nível de confiança
- Sugestões de correção

Autor: Kontabil System
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import re


class NivelConfianca(Enum):
    """Níveis de confiança da importação"""
    ALTA = "alta"           # 90-100% - Parser local, todas validações OK
    MEDIA = "media"         # 70-89% - IA com validações OK
    BAIXA = "baixa"         # 50-69% - IA com algumas inconsistências
    MUITO_BAIXA = "muito_baixa"  # <50% - Muitas inconsistências


class TipoAlerta(Enum):
    """Tipos de alertas de validação"""
    ERRO = "erro"           # Inconsistência grave - deve corrigir
    AVISO = "aviso"         # Valor suspeito - revisar
    INFO = "info"           # Informação - normal
    SUCESSO = "sucesso"     # Validação passou


@dataclass
class AlertaValidacao:
    """Alerta de validação"""
    tipo: TipoAlerta
    campo: str
    mensagem: str
    valor_atual: Any = None
    valor_sugerido: Any = None
    detalhes: str = ""


@dataclass
class ResultadoValidacao:
    """Resultado completo da validação"""
    confianca: NivelConfianca
    confianca_percentual: int
    metodo_extracao: str  # "parser_dominio", "ia_claude", etc.
    alertas: List[AlertaValidacao] = field(default_factory=list)
    dados_validados: Dict[str, Any] = field(default_factory=dict)
    campos_editaveis: List[Dict[str, Any]] = field(default_factory=list)
    resumo: str = ""


class ValidadorImportacao:
    """
    Validador de dados importados de balancetes
    """
    
    # Limites para validação
    LIMITES = {
        'margem_liquida': {'min': -50, 'max': 100, 'ideal_min': 0, 'ideal_max': 50},
        'margem_bruta': {'min': 0, 'max': 100, 'ideal_min': 20, 'ideal_max': 80},
        'liquidez_corrente': {'min': 0, 'max': 10, 'ideal_min': 1, 'ideal_max': 3},
        'liquidez_seca': {'min': 0, 'max': 10, 'ideal_min': 0.8, 'ideal_max': 2.5},
        'roe': {'min': -100, 'max': 500, 'ideal_min': 5, 'ideal_max': 50},
        'carga_tributaria': {'min': 0, 'max': 50, 'ideal_min': 5, 'ideal_max': 35},
    }
    
    # Campos do balancete com metadados
    CAMPOS_BALANCETE = [
        # Receitas
        {'nome': 'receita_bruta', 'label': 'Receita Bruta', 'grupo': 'DRE', 'obrigatorio': True},
        {'nome': 'receita_servicos', 'label': 'Receita de Serviços', 'grupo': 'DRE', 'obrigatorio': False},
        {'nome': 'deducoes_receita', 'label': 'Deduções da Receita', 'grupo': 'DRE', 'obrigatorio': False},
        
        # Custos e Despesas
        {'nome': 'custos', 'label': 'Custos', 'grupo': 'DRE', 'obrigatorio': False},
        {'nome': 'despesas_operacionais', 'label': 'Despesas Operacionais', 'grupo': 'DRE', 'obrigatorio': False},
        {'nome': 'despesas_financeiras', 'label': 'Despesas Financeiras', 'grupo': 'DRE', 'obrigatorio': False},
        
        # Resultado
        {'nome': 'lucro_liquido', 'label': 'Lucro Líquido', 'grupo': 'DRE', 'obrigatorio': True},
        
        # Ativo
        {'nome': 'ativo_total', 'label': 'Ativo Total', 'grupo': 'Ativo', 'obrigatorio': True},
        {'nome': 'ativo_circulante', 'label': 'Ativo Circulante', 'grupo': 'Ativo', 'obrigatorio': True},
        {'nome': 'disponivel', 'label': 'Disponível', 'grupo': 'Ativo', 'obrigatorio': False},
        {'nome': 'caixa', 'label': 'Caixa', 'grupo': 'Ativo', 'obrigatorio': False},
        {'nome': 'bancos', 'label': 'Bancos', 'grupo': 'Ativo', 'obrigatorio': False},
        {'nome': 'clientes', 'label': 'Clientes', 'grupo': 'Ativo', 'obrigatorio': False},
        {'nome': 'estoques', 'label': 'Estoques', 'grupo': 'Ativo', 'obrigatorio': False},
        
        # Passivo
        {'nome': 'passivo_circulante', 'label': 'Passivo Circulante', 'grupo': 'Passivo', 'obrigatorio': True},
        {'nome': 'passivo_nao_circulante', 'label': 'Passivo Não Circulante', 'grupo': 'Passivo', 'obrigatorio': False},
        {'nome': 'fornecedores', 'label': 'Fornecedores', 'grupo': 'Passivo', 'obrigatorio': False},
        
        # Patrimônio Líquido
        {'nome': 'patrimonio_liquido', 'label': 'Patrimônio Líquido', 'grupo': 'PL', 'obrigatorio': True},
        {'nome': 'capital_social', 'label': 'Capital Social', 'grupo': 'PL', 'obrigatorio': False},
        
        # Impostos
        {'nome': 'impostos', 'label': 'Total Impostos', 'grupo': 'Impostos', 'obrigatorio': False},
        {'nome': 'icms_deducao', 'label': 'ICMS (DRE)', 'grupo': 'Impostos', 'obrigatorio': False},
        {'nome': 'pis_deducao', 'label': 'PIS (DRE)', 'grupo': 'Impostos', 'obrigatorio': False},
        {'nome': 'cofins_deducao', 'label': 'COFINS (DRE)', 'grupo': 'Impostos', 'obrigatorio': False},
        {'nome': 'irpj_deducao', 'label': 'IRPJ (DRE)', 'grupo': 'Impostos', 'obrigatorio': False},
        {'nome': 'csll_deducao', 'label': 'CSLL (DRE)', 'grupo': 'Impostos', 'obrigatorio': False},
    ]
    
    def __init__(self, dados: Dict[str, Any], metodo: str = "desconhecido"):
        """
        Inicializa o validador
        
        Args:
            dados: Dicionário com dados extraídos do balancete
            metodo: Método de extração (parser_dominio, ia_claude, etc.)
        """
        self.dados = dados
        self.metodo = metodo
        self.alertas: List[AlertaValidacao] = []
        self.pontuacao_confianca = 100  # Começa em 100 e vai diminuindo
        
    def validar(self) -> ResultadoValidacao:
        """
        Executa todas as validações e retorna resultado
        """
        # Resetar
        self.alertas = []
        self.pontuacao_confianca = 100
        
        # Aplicar penalidade base por método
        if 'ia' in self.metodo.lower() or 'claude' in self.metodo.lower():
            self.pontuacao_confianca -= 10  # IA tem 10% menos confiança base
        
        # Executar validações
        self._validar_campos_obrigatorios()
        self._validar_equacao_patrimonial()
        self._validar_margem_liquida()
        self._validar_liquidez()
        self._validar_roe()
        self._validar_carga_tributaria()
        self._validar_consistencia_valores()
        
        # Determinar nível de confiança
        confianca = self._calcular_nivel_confianca()
        
        # Montar campos editáveis
        campos_editaveis = self._montar_campos_editaveis()
        
        # Gerar resumo
        resumo = self._gerar_resumo()
        
        return ResultadoValidacao(
            confianca=confianca,
            confianca_percentual=max(0, min(100, self.pontuacao_confianca)),
            metodo_extracao=self.metodo,
            alertas=self.alertas,
            dados_validados=self.dados,
            campos_editaveis=campos_editaveis,
            resumo=resumo
        )
    
    def _adicionar_alerta(self, tipo: TipoAlerta, campo: str, mensagem: str, 
                          valor_atual: Any = None, valor_sugerido: Any = None,
                          detalhes: str = "", penalidade: int = 0):
        """Adiciona alerta e aplica penalidade na confiança"""
        self.alertas.append(AlertaValidacao(
            tipo=tipo,
            campo=campo,
            mensagem=mensagem,
            valor_atual=valor_atual,
            valor_sugerido=valor_sugerido,
            detalhes=detalhes
        ))
        self.pontuacao_confianca -= penalidade
    
    def _validar_campos_obrigatorios(self):
        """Valida se campos obrigatórios estão preenchidos"""
        for campo in self.CAMPOS_BALANCETE:
            if campo['obrigatorio']:
                valor = self.dados.get(campo['nome'], 0)
                if not valor or valor == 0:
                    self._adicionar_alerta(
                        TipoAlerta.AVISO,
                        campo['nome'],
                        f"{campo['label']} não foi extraído ou é zero",
                        valor_atual=valor,
                        detalhes="Campo obrigatório para análise completa",
                        penalidade=5
                    )
    
    def _validar_equacao_patrimonial(self):
        """Valida: Ativo = Passivo + PL"""
        ativo = float(self.dados.get('ativo_total', 0) or 0)
        passivo_circ = float(self.dados.get('passivo_circulante', 0) or 0)
        passivo_nao_circ = float(self.dados.get('passivo_nao_circulante', 0) or 0)
        pl = float(self.dados.get('patrimonio_liquido', 0) or 0)
        
        if ativo > 0 and (passivo_circ > 0 or pl > 0):
            passivo_total = passivo_circ + passivo_nao_circ
            diferenca = abs(ativo - (passivo_total + pl))
            percentual_diferenca = (diferenca / ativo) * 100 if ativo > 0 else 0
            
            if percentual_diferenca < 1:
                self._adicionar_alerta(
                    TipoAlerta.SUCESSO,
                    'equacao_patrimonial',
                    "Equação patrimonial válida (Ativo = Passivo + PL)",
                    detalhes=f"Diferença de apenas {percentual_diferenca:.2f}%"
                )
            elif percentual_diferenca < 5:
                self._adicionar_alerta(
                    TipoAlerta.AVISO,
                    'equacao_patrimonial',
                    f"Pequena diferença na equação patrimonial ({percentual_diferenca:.1f}%)",
                    valor_atual=f"Ativo: {ativo:,.2f} ≠ Passivo+PL: {passivo_total + pl:,.2f}",
                    detalhes="Pode ser arredondamento ou conta não extraída",
                    penalidade=5
                )
            else:
                self._adicionar_alerta(
                    TipoAlerta.ERRO,
                    'equacao_patrimonial',
                    f"Equação patrimonial inconsistente ({percentual_diferenca:.1f}% de diferença)",
                    valor_atual=f"Ativo: {ativo:,.2f} ≠ Passivo+PL: {passivo_total + pl:,.2f}",
                    detalhes="Verificar valores de Ativo, Passivo e Patrimônio Líquido",
                    penalidade=15
                )
    
    def _validar_margem_liquida(self):
        """Valida margem líquida"""
        receita = float(self.dados.get('receita_bruta', 0) or 0)
        lucro = float(self.dados.get('lucro_liquido', 0) or 0)
        
        if receita > 0:
            margem = (lucro / receita) * 100
            
            if lucro > receita:
                self._adicionar_alerta(
                    TipoAlerta.ERRO,
                    'lucro_liquido',
                    "Lucro maior que receita - valor incorreto",
                    valor_atual=f"Lucro: {lucro:,.2f} > Receita: {receita:,.2f}",
                    valor_sugerido=f"Lucro deveria ser menor que {receita:,.2f}",
                    detalhes="Verificar se o lucro extraído é o correto",
                    penalidade=20
                )
            elif margem < -50:
                self._adicionar_alerta(
                    TipoAlerta.AVISO,
                    'lucro_liquido',
                    f"Margem líquida muito negativa ({margem:.1f}%)",
                    detalhes="Empresa com prejuízo significativo",
                    penalidade=5
                )
            elif margem > 70:
                self._adicionar_alerta(
                    TipoAlerta.AVISO,
                    'lucro_liquido',
                    f"Margem líquida muito alta ({margem:.1f}%)",
                    detalhes="Verificar se valores estão corretos",
                    penalidade=5
                )
            else:
                self._adicionar_alerta(
                    TipoAlerta.SUCESSO,
                    'margem_liquida',
                    f"Margem líquida dentro do esperado ({margem:.1f}%)"
                )
    
    def _validar_liquidez(self):
        """Valida índice de liquidez corrente"""
        ativo_circ = float(self.dados.get('ativo_circulante', 0) or 0)
        passivo_circ = float(self.dados.get('passivo_circulante', 0) or 0)
        
        if passivo_circ > 0:
            liquidez = ativo_circ / passivo_circ
            
            if liquidez < 0.5:
                self._adicionar_alerta(
                    TipoAlerta.AVISO,
                    'liquidez_corrente',
                    f"Liquidez corrente muito baixa ({liquidez:.2f})",
                    detalhes="Empresa pode ter dificuldades para pagar obrigações de curto prazo",
                    penalidade=3
                )
            elif liquidez > 5:
                self._adicionar_alerta(
                    TipoAlerta.INFO,
                    'liquidez_corrente',
                    f"Liquidez corrente muito alta ({liquidez:.2f})",
                    detalhes="Pode indicar recursos ociosos"
                )
            else:
                self._adicionar_alerta(
                    TipoAlerta.SUCESSO,
                    'liquidez_corrente',
                    f"Liquidez corrente adequada ({liquidez:.2f})"
                )
    
    def _validar_roe(self):
        """Valida ROE (Return on Equity)"""
        lucro = float(self.dados.get('lucro_liquido', 0) or 0)
        pl = float(self.dados.get('patrimonio_liquido', 0) or 0)
        
        if pl > 0 and lucro != 0:
            roe = (lucro / pl) * 100
            
            if roe > 200:
                self._adicionar_alerta(
                    TipoAlerta.AVISO,
                    'roe',
                    f"ROE extremamente alto ({roe:.1f}%)",
                    detalhes="Verificar se o Patrimônio Líquido está correto. PL muito baixo gera ROE inflado.",
                    penalidade=5
                )
            elif roe > 100:
                self._adicionar_alerta(
                    TipoAlerta.INFO,
                    'roe',
                    f"ROE muito elevado ({roe:.1f}%)",
                    detalhes="ROE acima de 100% pode indicar PL baixo em relação ao lucro"
                )
            elif roe < -50:
                self._adicionar_alerta(
                    TipoAlerta.AVISO,
                    'roe',
                    f"ROE muito negativo ({roe:.1f}%)",
                    detalhes="Empresa com prejuízo significativo em relação ao PL",
                    penalidade=3
                )
            else:
                self._adicionar_alerta(
                    TipoAlerta.SUCESSO,
                    'roe',
                    f"ROE dentro do esperado ({roe:.1f}%)"
                )
    
    def _validar_carga_tributaria(self):
        """Valida carga tributária"""
        receita = float(self.dados.get('receita_bruta', 0) or 0)
        impostos = float(self.dados.get('impostos', 0) or 0)
        deducoes = float(self.dados.get('deducoes_receita', 0) or 0)
        
        # Usar deduções se não tiver impostos detalhados
        valor_tributos = impostos if impostos > 0 else deducoes
        
        if receita > 0 and valor_tributos > 0:
            carga = (valor_tributos / receita) * 100
            
            if carga > 50:
                self._adicionar_alerta(
                    TipoAlerta.AVISO,
                    'carga_tributaria',
                    f"Carga tributária muito alta ({carga:.1f}%)",
                    detalhes="Verificar se os impostos estão corretos",
                    penalidade=5
                )
            elif carga < 3:
                self._adicionar_alerta(
                    TipoAlerta.AVISO,
                    'carga_tributaria',
                    f"Carga tributária muito baixa ({carga:.1f}%)",
                    detalhes="Verificar se todos os impostos foram extraídos",
                    penalidade=5
                )
            else:
                self._adicionar_alerta(
                    TipoAlerta.SUCESSO,
                    'carga_tributaria',
                    f"Carga tributária dentro do esperado ({carga:.1f}%)"
                )
    
    def _validar_consistencia_valores(self):
        """Valida consistência geral dos valores"""
        # Ativo Circulante deve ser <= Ativo Total
        ac = float(self.dados.get('ativo_circulante', 0) or 0)
        at = float(self.dados.get('ativo_total', 0) or 0)
        
        if ac > 0 and at > 0 and ac > at:
            self._adicionar_alerta(
                TipoAlerta.ERRO,
                'ativo_circulante',
                "Ativo Circulante maior que Ativo Total",
                valor_atual=f"AC: {ac:,.2f} > AT: {at:,.2f}",
                detalhes="Inconsistência nos valores de ativo",
                penalidade=15
            )
        
        # Disponível deve ser <= Ativo Circulante
        disp = float(self.dados.get('disponivel', 0) or 0)
        if disp > 0 and ac > 0 and disp > ac:
            self._adicionar_alerta(
                TipoAlerta.AVISO,
                'disponivel',
                "Disponível maior que Ativo Circulante",
                valor_atual=f"Disp: {disp:,.2f} > AC: {ac:,.2f}",
                penalidade=10
            )
    
    def _calcular_nivel_confianca(self) -> NivelConfianca:
        """Calcula nível de confiança baseado na pontuação"""
        if self.pontuacao_confianca >= 90:
            return NivelConfianca.ALTA
        elif self.pontuacao_confianca >= 70:
            return NivelConfianca.MEDIA
        elif self.pontuacao_confianca >= 50:
            return NivelConfianca.BAIXA
        else:
            return NivelConfianca.MUITO_BAIXA
    
    def _montar_campos_editaveis(self) -> List[Dict[str, Any]]:
        """Monta lista de campos editáveis para o frontend"""
        campos = []
        
        for campo_info in self.CAMPOS_BALANCETE:
            nome = campo_info['nome']
            valor = self.dados.get(nome, 0) or 0
            
            # Verificar se há alerta para este campo
            alertas_campo = [a for a in self.alertas if a.campo == nome]
            tem_erro = any(a.tipo == TipoAlerta.ERRO for a in alertas_campo)
            tem_aviso = any(a.tipo == TipoAlerta.AVISO for a in alertas_campo)
            
            campos.append({
                'nome': nome,
                'label': campo_info['label'],
                'grupo': campo_info['grupo'],
                'valor': valor,
                'obrigatorio': campo_info['obrigatorio'],
                'tem_erro': tem_erro,
                'tem_aviso': tem_aviso,
                'alertas': [{'tipo': a.tipo.value, 'mensagem': a.mensagem} for a in alertas_campo]
            })
        
        return campos
    
    def _gerar_resumo(self) -> str:
        """Gera resumo textual da validação"""
        erros = sum(1 for a in self.alertas if a.tipo == TipoAlerta.ERRO)
        avisos = sum(1 for a in self.alertas if a.tipo == TipoAlerta.AVISO)
        sucessos = sum(1 for a in self.alertas if a.tipo == TipoAlerta.SUCESSO)
        
        if erros > 0:
            return f"⚠️ {erros} erro(s) encontrado(s). Revise os valores destacados."
        elif avisos > 0:
            return f"📝 {avisos} aviso(s). Verifique se os valores estão corretos."
        else:
            return f"✅ {sucessos} validação(ões) OK. Dados parecem consistentes."


def validar_importacao(dados: Dict[str, Any], metodo: str = "desconhecido") -> Dict[str, Any]:
    """
    Função de conveniência para validar importação
    
    Args:
        dados: Dados extraídos do balancete
        metodo: Método de extração
        
    Returns:
        Dicionário com resultado da validação
    """
    validador = ValidadorImportacao(dados, metodo)
    resultado = validador.validar()
    
    return {
        'confianca': resultado.confianca.value,
        'confianca_percentual': resultado.confianca_percentual,
        'metodo_extracao': resultado.metodo_extracao,
        'alertas': [
            {
                'tipo': a.tipo.value,
                'campo': a.campo,
                'mensagem': a.mensagem,
                'valor_atual': a.valor_atual,
                'valor_sugerido': a.valor_sugerido,
                'detalhes': a.detalhes
            }
            for a in resultado.alertas
        ],
        'dados_validados': resultado.dados_validados,
        'campos_editaveis': resultado.campos_editaveis,
        'resumo': resultado.resumo
    }
