#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalização de Dados Contábeis
===============================

Este módulo trata a conversão de valores ACUMULADOS (como aparecem nos balancetes)
para valores MENSAIS (como devem ser armazenados para análise correta).

Problema:
---------
Balancetes brasileiros (especialmente do Domínio Sistemas) mostram a DRE com valores
ACUMULADOS no exercício:
- Janeiro: Receita = 50.000 (só janeiro)
- Fevereiro: Receita = 120.000 (jan + fev, ou seja, fev = 70.000)
- Março: Receita = 190.000 (jan + fev + mar, ou seja, mar = 70.000)

Se somarmos diretamente: 50.000 + 120.000 + 190.000 = 360.000 (ERRADO!)
O correto seria: 190.000 (valor acumulado do trimestre)

Solução:
--------
1. Detectar se os valores são acumulados (crescentes no exercício)
2. Converter para valores mensais: valor_mes = acumulado_atual - acumulado_anterior
3. Armazenar valores mensais para análise correta

Autor: Kontabil
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DadosMes:
    """Dados de um mês específico."""
    ano: int
    mes: int
    dados: Dict
    acumulado: bool = True  # Assume que são acumulados por padrão


# Campos que são ACUMULADOS na DRE (valores do exercício até o mês)
CAMPOS_ACUMULADOS_DRE = [
    'receita_bruta',
    'receita_servicos',
    'receita',
    'deducoes_receita',
    'custos',
    'despesas_operacionais',
    'despesas_financeiras',
    'despesas_administrativas',
    'lucro_liquido',
    'lucro_bruto',
    'iss',
    'pis',
    'cofins',
    'irpj',
    'csll',
    'impostos',
    'folha',
]

# Campos que são INSTANTÂNEOS (saldo no momento - Balanço Patrimonial)
CAMPOS_INSTANTANEOS = [
    'ativo_total',
    'ativo_circulante',
    'disponivel',
    'caixa',
    'bancos',
    'clientes',
    'estoques',
    'passivo_total',
    'passivo_circulante',
    'passivo_nao_circulante',
    'fornecedores',
    'patrimonio_liquido',
    'capital_social',
    'lucros_acumulados',
]


def detectar_valores_acumulados(meses: List[DadosMes]) -> bool:
    """
    Detecta se os valores de receita parecem ser acumulados.
    
    Heurística: Se a receita é crescente ao longo dos meses do mesmo ano,
    provavelmente são valores acumulados.
    """
    if len(meses) < 2:
        return True  # Assume acumulado por padrão
    
    # Ordena por ano/mes
    meses_ordenados = sorted(meses, key=lambda m: (m.ano, m.mes))
    
    # Verifica se receita é crescente no mesmo ano
    receitas_por_ano = {}
    for m in meses_ordenados:
        ano = m.ano
        receita = m.dados.get('receita_bruta', 0) or m.dados.get('receita', 0)
        if receita > 0:
            if ano not in receitas_por_ano:
                receitas_por_ano[ano] = []
            receitas_por_ano[ano].append((m.mes, receita))
    
    # Para cada ano, verifica se receita é crescente
    for ano, receitas in receitas_por_ano.items():
        if len(receitas) >= 2:
            # Ordena por mês
            receitas.sort(key=lambda x: x[0])
            valores = [r[1] for r in receitas]
            
            # Se cada valor é maior ou igual ao anterior, é acumulado
            crescente = all(valores[i] >= valores[i-1] * 0.95 for i in range(1, len(valores)))
            if crescente:
                return True
    
    return False


def converter_acumulado_para_mensal(
    meses: List[DadosMes],
    campos_acumulados: List[str] = None
) -> List[DadosMes]:
    """
    Converte valores acumulados para mensais.
    
    Para cada campo acumulado:
    valor_mensal = valor_acumulado_atual - valor_acumulado_mes_anterior
    
    Args:
        meses: Lista de dados mensais (com valores acumulados)
        campos_acumulados: Lista de campos a converter (default: CAMPOS_ACUMULADOS_DRE)
    
    Returns:
        Lista de dados mensais com valores mensais (não acumulados)
    """
    if not meses:
        return meses
    
    if campos_acumulados is None:
        campos_acumulados = CAMPOS_ACUMULADOS_DRE
    
    # Ordena por ano/mes
    meses_ordenados = sorted(meses, key=lambda m: (m.ano, m.mes))
    
    resultado = []
    valores_anteriores = {}  # {ano: {campo: valor_acumulado}}
    
    for i, mes in enumerate(meses_ordenados):
        ano = mes.ano
        mes_num = mes.mes
        
        # Cria cópia dos dados
        dados_convertidos = dict(mes.dados)
        
        # No primeiro mês do ano, valor mensal = valor acumulado
        if ano not in valores_anteriores:
            valores_anteriores[ano] = {}
        
        # Converte cada campo acumulado
        for campo in campos_acumulados:
            valor_atual = mes.dados.get(campo, 0) or 0
            
            if campo in valores_anteriores[ano] and mes_num > 1:
                valor_anterior = valores_anteriores[ano].get(campo, 0)
                # Valor mensal = atual - anterior
                valor_mensal = valor_atual - valor_anterior
                
                # Não permite valor negativo (pode acontecer em ajustes)
                dados_convertidos[campo] = max(0, valor_mensal)
            else:
                # Primeiro mês do ano: valor mensal = valor acumulado
                # (assumindo que o exercício começa zerado)
                dados_convertidos[campo] = valor_atual
            
            # Atualiza valor anterior para próximo mês
            valores_anteriores[ano][campo] = valor_atual
        
        # Cria novo DadosMes com valores mensais
        resultado.append(DadosMes(
            ano=ano,
            mes=mes_num,
            dados=dados_convertidos,
            acumulado=False
        ))
    
    return resultado


def normalizar_dados_importacao(
    dados_meses: List[Dict],
    forcar_conversao: bool = False
) -> Tuple[List[Dict], List[str]]:
    """
    Normaliza dados importados, detectando e convertendo valores acumulados.
    
    Args:
        dados_meses: Lista de dicionários com dados mensais
        forcar_conversao: Se True, força conversão mesmo se não detectar acumulado
    
    Returns:
        Tuple (dados_normalizados, observacoes)
    """
    observacoes = []
    
    if not dados_meses:
        return dados_meses, observacoes
    
    # Converte para DadosMes
    meses = []
    for d in dados_meses:
        ano = d.get('ano', 0)
        mes = d.get('mes', 0)
        if ano and mes:
            meses.append(DadosMes(ano=ano, mes=mes, dados=d))
    
    if len(meses) < 2:
        observacoes.append("Apenas 1 mês importado, valores mantidos como estão")
        return dados_meses, observacoes
    
    # Detecta se são acumulados
    parece_acumulado = detectar_valores_acumulados(meses)
    
    if parece_acumulado or forcar_conversao:
        observacoes.append("⚠️ Valores detectados como ACUMULADOS no exercício")
        observacoes.append("Convertendo para valores MENSAIS para análise correta")
        
        # Converte
        meses_convertidos = converter_acumulado_para_mensal(meses)
        
        # Reconstrói lista de dicts
        resultado = []
        for mes_conv in meses_convertidos:
            dados = dict(mes_conv.dados)
            dados['ano'] = mes_conv.ano
            dados['mes'] = mes_conv.mes
            dados['_convertido_de_acumulado'] = True
            resultado.append(dados)
        
        # Log da conversão
        print(f"[NORMALIZAÇÃO] Convertidos {len(meses)} meses de acumulado para mensal")
        for i, (orig, conv) in enumerate(zip(meses, meses_convertidos)):
            rec_orig = orig.dados.get('receita_bruta', 0)
            rec_conv = conv.dados.get('receita_bruta', 0)
            print(f"[NORMALIZAÇÃO]   {orig.mes:02d}/{orig.ano}: Receita {rec_orig:,.2f} -> {rec_conv:,.2f}")
        
        return resultado, observacoes
    else:
        observacoes.append("Valores parecem ser mensais, mantidos como estão")
        return dados_meses, observacoes


def calcular_totais_periodo(dados_meses: List[Dict]) -> Dict:
    """
    Calcula totais corretos para um período de múltiplos meses.
    
    Se os dados já são mensais, soma os valores.
    Se são acumulados, usa o último mês (que já contém o total).
    
    Args:
        dados_meses: Lista de dados mensais
    
    Returns:
        Dict com totais do período
    """
    if not dados_meses:
        return {}
    
    # Verifica se já foram convertidos
    ja_convertido = any(d.get('_convertido_de_acumulado', False) for d in dados_meses)
    
    if ja_convertido or len(dados_meses) == 1:
        # Soma os valores mensais
        totais = {}
        for campo in CAMPOS_ACUMULADOS_DRE:
            totais[campo] = sum(d.get(campo, 0) or 0 for d in dados_meses)
        
        # Para campos instantâneos, usa o último valor
        ultimo = sorted(dados_meses, key=lambda d: (d.get('ano', 0), d.get('mes', 0)))[-1]
        for campo in CAMPOS_INSTANTANEOS:
            totais[campo] = ultimo.get(campo, 0) or 0
        
        return totais
    else:
        # Se não convertido, assume acumulado - usa o último mês
        ultimo = sorted(dados_meses, key=lambda d: (d.get('ano', 0), d.get('mes', 0)))[-1]
        return {k: v for k, v in ultimo.items() if isinstance(v, (int, float))}


def validar_consistencia(dados: Dict) -> List[str]:
    """
    Valida se os dados extraídos são consistentes.
    
    Returns:
        Lista de alertas/erros encontrados
    """
    alertas = []
    
    # Receita deve ser positiva
    receita = dados.get('receita_bruta', 0) or dados.get('receita', 0)
    if receita < 0:
        alertas.append("⚠️ Receita negativa detectada")
    
    # Lucro não pode ser maior que receita
    lucro = dados.get('lucro_liquido', 0)
    if lucro > receita and receita > 0:
        alertas.append(f"⚠️ Lucro ({lucro:,.2f}) maior que Receita ({receita:,.2f})")
    
    # Ativo deve ser positivo
    ativo = dados.get('ativo_total', 0)
    if ativo < 0:
        alertas.append("⚠️ Ativo total negativo")
    
    # Ativo = Passivo (equação patrimonial)
    passivo = dados.get('passivo_total', 0)
    if ativo > 0 and passivo > 0:
        diff = abs(ativo - passivo)
        if diff > max(ativo, passivo) * 0.01:  # Tolerância de 1%
            alertas.append(f"⚠️ Ativo ({ativo:,.2f}) ≠ Passivo ({passivo:,.2f})")
    
    # Margem não pode ser > 100%
    if receita > 0 and lucro > 0:
        margem = (lucro / receita) * 100
        if margem > 100:
            alertas.append(f"⚠️ Margem improvável: {margem:.1f}%")
    
    return alertas


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    # Simula dados acumulados do Domínio
    dados_acumulados = [
        {'ano': 2024, 'mes': 1, 'receita_bruta': 49182.20, 'lucro_liquido': 24155.25},
        {'ano': 2024, 'mes': 2, 'receita_bruta': 144767.30, 'lucro_liquido': 84650.59},
        {'ano': 2024, 'mes': 3, 'receita_bruta': 190523.80, 'lucro_liquido': 95941.82},
    ]
    
    print("=== DADOS ORIGINAIS (ACUMULADOS) ===")
    for d in dados_acumulados:
        print(f"  {d['mes']:02d}/{d['ano']}: Receita={d['receita_bruta']:,.2f}, Lucro={d['lucro_liquido']:,.2f}")
    
    print("\n=== DETECTANDO... ===")
    meses = [DadosMes(ano=d['ano'], mes=d['mes'], dados=d) for d in dados_acumulados]
    acumulado = detectar_valores_acumulados(meses)
    print(f"Detectado como acumulado: {acumulado}")
    
    print("\n=== DADOS CONVERTIDOS (MENSAIS) ===")
    dados_normalizados, obs = normalizar_dados_importacao(dados_acumulados)
    for d in dados_normalizados:
        print(f"  {d['mes']:02d}/{d['ano']}: Receita={d['receita_bruta']:,.2f}, Lucro={d['lucro_liquido']:,.2f}")
    
    print("\n=== TOTAIS DO PERÍODO ===")
    totais = calcular_totais_periodo(dados_normalizados)
    print(f"Receita Total: R$ {totais.get('receita_bruta', 0):,.2f}")
    print(f"Lucro Total: R$ {totais.get('lucro_liquido', 0):,.2f}")
    
    print("\n=== OBSERVAÇÕES ===")
    for o in obs:
        print(f"  {o}")
