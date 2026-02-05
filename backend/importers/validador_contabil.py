#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador Contábil - Sistema de Validação em Camadas
=====================================================

Valida dados extraídos por qualquer método (Parser ou IA) usando
regras contábeis fundamentais para garantir consistência.

Camadas de Validação:
1. Validação Estrutural (campos obrigatórios)
2. Validação Matemática (equações contábeis)
3. Validação de Razoabilidade (limites e proporções)
4. Validação Cruzada (consistência entre campos)

O objetivo é ALERTAR inconsistências, não bloquear.
O usuário decide se aceita ou corrige.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re


class NivelAlerta(Enum):
    """Níveis de severidade dos alertas."""
    ERRO_CRITICO = "erro_critico"      # Dados claramente errados
    INCONSISTENCIA = "inconsistencia"  # Possível erro, revisar
    AVISO = "aviso"                    # Pode estar certo, mas é incomum
    INFO = "info"                      # Informativo apenas


@dataclass
class Alerta:
    """Um alerta de validação."""
    nivel: NivelAlerta
    campo: str
    mensagem: str
    valor_atual: float = 0
    valor_esperado: float = 0
    sugestao: str = ""
    pode_corrigir_auto: bool = False
    correcao_sugerida: float = 0


@dataclass
class ResultadoValidacao:
    """Resultado completo da validação."""
    valido: bool = True
    confiavel: bool = True  # True se pode salvar sem revisão
    alertas: List[Alerta] = field(default_factory=list)
    dados_corrigidos: Dict = field(default_factory=dict)
    score_confianca: int = 100  # 0-100
    resumo: str = ""
    
    @property
    def tem_erros_criticos(self) -> bool:
        return any(a.nivel == NivelAlerta.ERRO_CRITICO for a in self.alertas)
    
    @property
    def tem_inconsistencias(self) -> bool:
        return any(a.nivel == NivelAlerta.INCONSISTENCIA for a in self.alertas)
    
    @property
    def total_alertas(self) -> int:
        return len(self.alertas)


class ValidadorContabil:
    """
    Validador de dados contábeis extraídos.
    
    Aplica regras contábeis fundamentais para identificar
    possíveis erros de extração.
    """
    
    # Tolerância para validações (5%)
    TOLERANCIA = 0.05
    
    # Campos obrigatórios mínimos
    CAMPOS_OBRIGATORIOS = [
        'receita_bruta', 'ativo_total', 'passivo_circulante',
        'patrimonio_liquido', 'capital_social'
    ]
    
    # Campos que devem ser positivos (ou zero)
    CAMPOS_POSITIVOS = [
        'receita_bruta', 'receita_liquida', 'ativo_total',
        'ativo_circulante', 'disponivel', 'caixa', 'bancos',
        'clientes', 'estoques', 'passivo_circulante', 'fornecedores',
        'capital_social', 'impostos', 'custos', 'despesas_operacionais'
    ]
    
    def validar(self, dados: Dict, fonte: str = "desconhecida") -> ResultadoValidacao:
        """
        Executa validação completa dos dados.
        
        Args:
            dados: Dicionário com dados contábeis extraídos
            fonte: Origem dos dados ("parser", "ia", etc)
        
        Returns:
            ResultadoValidacao com alertas e dados corrigidos
        """
        resultado = ResultadoValidacao()
        resultado.dados_corrigidos = dados.copy()
        
        # Executa validações em ordem
        self._validar_estrutura(dados, resultado)
        self._validar_valores_positivos(dados, resultado)
        self._validar_equacao_fundamental(dados, resultado)
        self._validar_patrimonio_liquido(dados, resultado)
        self._validar_dre(dados, resultado)
        self._validar_proporcoes(dados, resultado)
        self._validar_razoabilidade(dados, resultado)
        
        # Calcula score de confiança
        resultado.score_confianca = self._calcular_score(resultado)
        
        # Define se é confiável (pode salvar sem revisão manual obrigatória)
        resultado.confiavel = (
            resultado.score_confianca >= 80 and
            not resultado.tem_erros_criticos
        )
        
        # Define se é válido (dados minimamente utilizáveis)
        resultado.valido = resultado.score_confianca >= 40
        
        # Gera resumo
        resultado.resumo = self._gerar_resumo(resultado, fonte)
        
        return resultado
    
    def _validar_estrutura(self, dados: Dict, resultado: ResultadoValidacao):
        """Valida se campos obrigatórios existem e têm valores."""
        campos_faltando = []
        campos_zerados = []
        
        for campo in self.CAMPOS_OBRIGATORIOS:
            valor = dados.get(campo)
            if valor is None:
                campos_faltando.append(campo)
            elif valor == 0:
                campos_zerados.append(campo)
        
        if campos_faltando:
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.ERRO_CRITICO,
                campo="estrutura",
                mensagem=f"Campos obrigatórios não encontrados: {', '.join(campos_faltando)}",
                sugestao="Verifique se o arquivo está no formato correto"
            ))
        
        # Receita e Ativo zerados são críticos
        if 'receita_bruta' in campos_zerados:
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.INCONSISTENCIA,
                campo="receita_bruta",
                mensagem="Receita Bruta está zerada",
                valor_atual=0,
                sugestao="Verifique se a empresa teve faturamento no período"
            ))
        
        if 'ativo_total' in campos_zerados:
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.ERRO_CRITICO,
                campo="ativo_total",
                mensagem="Ativo Total está zerado - dados provavelmente incorretos",
                valor_atual=0,
                sugestao="Revise manualmente o balancete"
            ))
    
    def _validar_valores_positivos(self, dados: Dict, resultado: ResultadoValidacao):
        """Valida se campos que devem ser positivos não são negativos."""
        for campo in self.CAMPOS_POSITIVOS:
            valor = dados.get(campo, 0) or 0
            if valor < 0:
                resultado.alertas.append(Alerta(
                    nivel=NivelAlerta.INCONSISTENCIA,
                    campo=campo,
                    mensagem=f"{campo} tem valor negativo: R$ {valor:,.2f}",
                    valor_atual=valor,
                    valor_esperado=abs(valor),
                    sugestao="Valores negativos podem indicar erro de extração",
                    pode_corrigir_auto=True,
                    correcao_sugerida=abs(valor)
                ))
                # Corrige automaticamente
                resultado.dados_corrigidos[campo] = abs(valor)
    
    def _validar_equacao_fundamental(self, dados: Dict, resultado: ResultadoValidacao):
        """
        Valida a equação fundamental da contabilidade:
        ATIVO = PASSIVO + PATRIMÔNIO LÍQUIDO
        """
        ativo = dados.get('ativo_total', 0) or 0
        passivo_c = dados.get('passivo_circulante', 0) or 0
        passivo_nc = dados.get('passivo_nao_circulante', 0) or 0
        pl = dados.get('patrimonio_liquido', 0) or 0
        
        # Se não temos passivo total, calcula
        passivo_total = dados.get('passivo_total', 0) or (passivo_c + passivo_nc)
        
        if ativo == 0:
            return  # Já tratado em validação estrutural
        
        # Lado direito da equação
        lado_direito = passivo_total + pl
        
        # Diferença
        diferenca = abs(ativo - lado_direito)
        diferenca_pct = (diferenca / ativo * 100) if ativo > 0 else 0
        
        if diferenca_pct > 10:
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.ERRO_CRITICO,
                campo="equacao_fundamental",
                mensagem=f"Equação Ativo = Passivo + PL não fecha! Diferença de {diferenca_pct:.1f}%",
                valor_atual=ativo,
                valor_esperado=lado_direito,
                sugestao=f"Ativo: R$ {ativo:,.2f} ≠ Passivo ({passivo_total:,.2f}) + PL ({pl:,.2f}) = R$ {lado_direito:,.2f}"
            ))
        elif diferenca_pct > 5:
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.INCONSISTENCIA,
                campo="equacao_fundamental",
                mensagem=f"Equação contábil com diferença de {diferenca_pct:.1f}%",
                valor_atual=ativo,
                valor_esperado=lado_direito,
                sugestao="Pequena diferença pode ser arredondamento ou conta não capturada"
            ))
        elif diferenca_pct > 1:
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.AVISO,
                campo="equacao_fundamental",
                mensagem=f"Pequena diferença de {diferenca_pct:.1f}% na equação contábil",
                valor_atual=ativo,
                valor_esperado=lado_direito
            ))
    
    def _validar_patrimonio_liquido(self, dados: Dict, resultado: ResultadoValidacao):
        """
        Valida consistência do Patrimônio Líquido.
        PL = Capital Social + Reservas + Lucros Acumulados + Resultado do Exercício
        """
        pl = dados.get('patrimonio_liquido', 0) or 0
        capital = dados.get('capital_social', 0) or 0
        lucros_acum = dados.get('lucros_acumulados', 0) or 0
        lucro_exerc = dados.get('lucro_liquido', 0) or 0
        
        if pl == 0 and capital == 0:
            return  # Já tratado em estrutura
        
        # PL esperado (simplificado)
        pl_calculado = capital + lucros_acum + lucro_exerc
        
        # Se PL informado é muito diferente do calculado
        if pl > 0 and pl_calculado > 0:
            diferenca_pct = abs(pl - pl_calculado) / max(pl, pl_calculado) * 100
            
            if diferenca_pct > 20:
                resultado.alertas.append(Alerta(
                    nivel=NivelAlerta.AVISO,
                    campo="patrimonio_liquido",
                    mensagem=f"PL informado difere {diferenca_pct:.0f}% do calculado",
                    valor_atual=pl,
                    valor_esperado=pl_calculado,
                    sugestao=f"PL={pl:,.2f} vs Capital({capital:,.2f})+Lucros({lucros_acum:,.2f})+Resultado({lucro_exerc:,.2f})={pl_calculado:,.2f}"
                ))
        
        # Alerta se PL é negativo (passivo a descoberto)
        if pl < 0:
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.AVISO,
                campo="patrimonio_liquido",
                mensagem=f"Patrimônio Líquido NEGATIVO: R$ {pl:,.2f} (Passivo a Descoberto)",
                valor_atual=pl,
                sugestao="Empresa com mais dívidas que ativos - pode estar correto"
            ))
    
    def _validar_dre(self, dados: Dict, resultado: ResultadoValidacao):
        """
        Valida consistência da DRE.
        - Receita Líquida <= Receita Bruta
        - Lucro Bruto <= Receita Líquida
        - Lucro Líquido <= Lucro Bruto (geralmente)
        """
        receita_bruta = dados.get('receita_bruta', 0) or 0
        receita_liquida = dados.get('receita_liquida', 0) or 0
        lucro_bruto = dados.get('lucro_bruto', 0) or 0
        lucro_liquido = dados.get('lucro_liquido', 0) or 0
        deducoes = dados.get('deducoes_receita', 0) or 0
        custos = dados.get('custos_total', 0) or dados.get('custos', 0) or 0
        
        if receita_bruta == 0:
            return
        
        # Receita Líquida não pode ser maior que Bruta
        if receita_liquida > receita_bruta * 1.01:  # 1% tolerância
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.ERRO_CRITICO,
                campo="receita_liquida",
                mensagem="Receita Líquida MAIOR que Receita Bruta!",
                valor_atual=receita_liquida,
                valor_esperado=receita_bruta,
                sugestao="Valores provavelmente invertidos ou errados"
            ))
        
        # Lucro não pode ser maior que receita
        if lucro_liquido > receita_bruta * 1.01:
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.ERRO_CRITICO,
                campo="lucro_liquido",
                mensagem="Lucro Líquido MAIOR que Receita Bruta!",
                valor_atual=lucro_liquido,
                valor_esperado=receita_bruta * 0.5,
                sugestao="Lucro não pode superar a receita - verifique extração"
            ))
        
        # Verifica se Receita Líquida = Receita Bruta - Deduções
        if receita_liquida > 0 and deducoes > 0:
            rl_esperada = receita_bruta - deducoes
            if abs(receita_liquida - rl_esperada) > receita_bruta * 0.05:
                resultado.alertas.append(Alerta(
                    nivel=NivelAlerta.AVISO,
                    campo="receita_liquida",
                    mensagem="Receita Líquida não confere com (Bruta - Deduções)",
                    valor_atual=receita_liquida,
                    valor_esperado=rl_esperada,
                    sugestao=f"Esperado: {receita_bruta:,.2f} - {deducoes:,.2f} = {rl_esperada:,.2f}"
                ))
        
        # Margem líquida muito alta (>50%) é suspeita
        margem = (lucro_liquido / receita_bruta * 100) if receita_bruta > 0 else 0
        if margem > 60:
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.AVISO,
                campo="lucro_liquido",
                mensagem=f"Margem Líquida muito alta: {margem:.1f}%",
                valor_atual=margem,
                sugestao="Margens acima de 60% são raras - verifique se está correto"
            ))
    
    def _validar_proporcoes(self, dados: Dict, resultado: ResultadoValidacao):
        """Valida proporções típicas entre contas."""
        ativo = dados.get('ativo_total', 0) or 0
        ac = dados.get('ativo_circulante', 0) or 0
        pc = dados.get('passivo_circulante', 0) or 0
        disponivel = dados.get('disponivel', 0) or 0
        
        if ativo == 0:
            return
        
        # AC não pode ser maior que Ativo Total
        if ac > ativo * 1.01:
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.ERRO_CRITICO,
                campo="ativo_circulante",
                mensagem="Ativo Circulante MAIOR que Ativo Total!",
                valor_atual=ac,
                valor_esperado=ativo,
                sugestao="Ativo Circulante é parte do Ativo Total"
            ))
        
        # Disponível não pode ser maior que AC
        if disponivel > ac * 1.01 and ac > 0:
            resultado.alertas.append(Alerta(
                nivel=NivelAlerta.ERRO_CRITICO,
                campo="disponivel",
                mensagem="Disponível MAIOR que Ativo Circulante!",
                valor_atual=disponivel,
                valor_esperado=ac,
                sugestao="Disponível é parte do Ativo Circulante"
            ))
    
    def _validar_razoabilidade(self, dados: Dict, resultado: ResultadoValidacao):
        """Valida se valores estão dentro de ranges razoáveis."""
        receita = dados.get('receita_bruta', 0) or 0
        impostos = dados.get('impostos', 0) or dados.get('impostos_total', 0) or 0
        
        if receita > 0 and impostos > 0:
            carga_trib = (impostos / receita) * 100
            
            # Carga tributária > 50% é muito suspeita
            if carga_trib > 50:
                resultado.alertas.append(Alerta(
                    nivel=NivelAlerta.INCONSISTENCIA,
                    campo="impostos",
                    mensagem=f"Carga tributária muito alta: {carga_trib:.1f}%",
                    valor_atual=carga_trib,
                    valor_esperado=30,
                    sugestao="Carga acima de 50% é rara - pode ter capturado valor errado"
                ))
            elif carga_trib > 40:
                resultado.alertas.append(Alerta(
                    nivel=NivelAlerta.AVISO,
                    campo="impostos",
                    mensagem=f"Carga tributária alta: {carga_trib:.1f}%",
                    valor_atual=carga_trib,
                    sugestao="Verifique se inclui apenas impostos sobre faturamento"
                ))
    
    def _calcular_score(self, resultado: ResultadoValidacao) -> int:
        """Calcula score de confiança baseado nos alertas."""
        score = 100
        
        for alerta in resultado.alertas:
            if alerta.nivel == NivelAlerta.ERRO_CRITICO:
                score -= 25
            elif alerta.nivel == NivelAlerta.INCONSISTENCIA:
                score -= 10
            elif alerta.nivel == NivelAlerta.AVISO:
                score -= 3
        
        return max(0, min(100, score))
    
    def _gerar_resumo(self, resultado: ResultadoValidacao, fonte: str) -> str:
        """Gera resumo textual da validação."""
        erros = sum(1 for a in resultado.alertas if a.nivel == NivelAlerta.ERRO_CRITICO)
        inconsist = sum(1 for a in resultado.alertas if a.nivel == NivelAlerta.INCONSISTENCIA)
        avisos = sum(1 for a in resultado.alertas if a.nivel == NivelAlerta.AVISO)
        
        if resultado.score_confianca >= 90:
            status = "✅ DADOS CONFIÁVEIS"
        elif resultado.score_confianca >= 70:
            status = "⚠️ REVISAR RECOMENDADO"
        elif resultado.score_confianca >= 40:
            status = "🔶 REVISÃO OBRIGATÓRIA"
        else:
            status = "❌ DADOS INCONSISTENTES"
        
        partes = [
            f"{status} (Score: {resultado.score_confianca}/100)",
            f"Fonte: {fonte.upper()}"
        ]
        
        if erros > 0:
            partes.append(f"❌ {erros} erro(s) crítico(s)")
        if inconsist > 0:
            partes.append(f"⚠️ {inconsist} inconsistência(s)")
        if avisos > 0:
            partes.append(f"ℹ️ {avisos} aviso(s)")
        
        if resultado.confiavel:
            partes.append("Pode salvar diretamente.")
        else:
            partes.append("Revise os dados antes de salvar!")
        
        return " | ".join(partes)


def validar_dados_importados(dados: Dict, fonte: str = "parser") -> ResultadoValidacao:
    """
    Função de conveniência para validar dados importados.
    
    Args:
        dados: Dicionário com dados contábeis
        fonte: "parser", "ia", ou nome do sistema
    
    Returns:
        ResultadoValidacao
    """
    validador = ValidadorContabil()
    return validador.validar(dados, fonte)


def comparar_extracoes(dados_parser: Dict, dados_ia: Dict) -> Dict:
    """
    Compara resultados de duas extrações diferentes.
    Útil para identificar discrepâncias entre Parser e IA.
    
    Returns:
        Dicionário com campos divergentes e recomendação
    """
    campos_comparar = [
        'receita_bruta', 'receita_liquida', 'lucro_liquido',
        'ativo_total', 'passivo_circulante', 'patrimonio_liquido',
        'capital_social', 'impostos'
    ]
    
    divergencias = []
    
    for campo in campos_comparar:
        v_parser = dados_parser.get(campo, 0) or 0
        v_ia = dados_ia.get(campo, 0) or 0
        
        if v_parser == 0 and v_ia == 0:
            continue
        
        # Calcula diferença percentual
        max_val = max(abs(v_parser), abs(v_ia))
        if max_val > 0:
            diff_pct = abs(v_parser - v_ia) / max_val * 100
        else:
            diff_pct = 0
        
        if diff_pct > 5:  # Mais de 5% de diferença
            divergencias.append({
                'campo': campo,
                'valor_parser': v_parser,
                'valor_ia': v_ia,
                'diferenca_pct': diff_pct,
                'recomendacao': 'parser' if v_parser > 0 else 'ia'
            })
    
    # Valida cada um
    validador = ValidadorContabil()
    valid_parser = validador.validar(dados_parser, "parser")
    valid_ia = validador.validar(dados_ia, "ia")
    
    return {
        'divergencias': divergencias,
        'total_divergencias': len(divergencias),
        'score_parser': valid_parser.score_confianca,
        'score_ia': valid_ia.score_confianca,
        'recomendacao': 'parser' if valid_parser.score_confianca >= valid_ia.score_confianca else 'ia',
        'mensagem': f"Parser: {valid_parser.score_confianca}/100 | IA: {valid_ia.score_confianca}/100"
    }


# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Exemplo de dados extraídos
    dados_teste = {
        'receita_bruta': 521818.00,
        'receita_liquida': 386156.60,
        'deducoes_receita': 135661.40,
        'lucro_bruto': 385706.60,
        'lucro_liquido': 284743.10,
        'ativo_total': 1065383.05,
        'ativo_circulante': 1018519.81,
        'disponivel': 217800.80,
        'passivo_circulante': 629933.20,
        'passivo_nao_circulante': 0,
        'patrimonio_liquido': 384743.10,  # Capital + Resultado
        'capital_social': 100000.00,
        'impostos': 135661.40,
    }
    
    resultado = validar_dados_importados(dados_teste, "parser_dominio")
    
    print("\n" + "="*60)
    print("RESULTADO DA VALIDAÇÃO")
    print("="*60)
    print(f"\n{resultado.resumo}\n")
    
    for alerta in resultado.alertas:
        icon = {
            NivelAlerta.ERRO_CRITICO: "❌",
            NivelAlerta.INCONSISTENCIA: "⚠️",
            NivelAlerta.AVISO: "ℹ️",
            NivelAlerta.INFO: "📝"
        }.get(alerta.nivel, "•")
        
        print(f"{icon} [{alerta.campo}] {alerta.mensagem}")
        if alerta.sugestao:
            print(f"   → {alerta.sugestao}")
    
    print(f"\nScore de Confiança: {resultado.score_confianca}/100")
    print(f"Confiável (salvar direto): {resultado.confiavel}")
