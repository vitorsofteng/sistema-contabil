#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Roteador de Importação de Balancetes
====================================

Decide qual método usar para importar balancete:
- Parser local (se disponível para o sistema contábil)
- IA (fallback ou para sistemas sem parser)

Baseado no campo sistema_contabil da empresa.
"""

import os
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

# Importar sistemas contábeis
try:
    from importers.sistemas_contabeis import (
        SistemaContabil,
        sistema_tem_parser,
        get_parser_para_sistema,
        get_sistema_info,
        PARSERS_DISPONIVEIS
    )
    SISTEMAS_AVAILABLE = True
except ImportError:
    SISTEMAS_AVAILABLE = False
    
    def sistema_tem_parser(codigo):
        return codigo == 1  # Só Domínio
    
    def get_parser_para_sistema(codigo):
        return 'parser_dominio' if codigo == 1 else None
    
    def get_sistema_info(codigo):
        return None


@dataclass
class ResultadoRoteamento:
    """Resultado da decisão de roteamento."""
    usar_parser_local: bool
    nome_parser: Optional[str]
    nome_sistema: str
    motivo: str


def decidir_metodo_importacao(
    sistema_contabil: int,
    nome_arquivo: str,
    forcar_ia: bool = False
) -> ResultadoRoteamento:
    """
    Decide qual método usar para importar o balancete.
    
    Args:
        sistema_contabil: Código do sistema contábil da empresa
        nome_arquivo: Nome do arquivo para validar extensão
        forcar_ia: Se True, força uso de IA independente do sistema
    
    Returns:
        ResultadoRoteamento indicando qual método usar
    """
    # Obter info do sistema
    info = get_sistema_info(sistema_contabil) if SISTEMAS_AVAILABLE else None
    nome_sistema = info.nome if info else ("Domínio" if sistema_contabil == 1 else "Desconhecido")
    
    # Forçar IA se solicitado
    if forcar_ia:
        return ResultadoRoteamento(
            usar_parser_local=False,
            nome_parser=None,
            nome_sistema=nome_sistema,
            motivo="IA forçada pelo usuário"
        )
    
    # Sistema desconhecido/outro -> usa IA
    if sistema_contabil == 0:
        return ResultadoRoteamento(
            usar_parser_local=False,
            nome_parser=None,
            nome_sistema="Outro / Não especificado",
            motivo="Sistema não especificado, usando IA"
        )
    
    # Verificar se tem parser local
    if sistema_tem_parser(sistema_contabil):
        nome_parser = get_parser_para_sistema(sistema_contabil)
        return ResultadoRoteamento(
            usar_parser_local=True,
            nome_parser=nome_parser,
            nome_sistema=nome_sistema,
            motivo=f"Parser local disponível para {nome_sistema}"
        )
    
    # Não tem parser -> usa IA
    return ResultadoRoteamento(
        usar_parser_local=False,
        nome_parser=None,
        nome_sistema=nome_sistema,
        motivo=f"Sistema {nome_sistema} não tem parser local, usando IA"
    )


def importar_com_roteamento(
    conteudo: bytes,
    nome_arquivo: str,
    sistema_contabil: int = 0,
    forcar_ia: bool = False
) -> Tuple[Dict, ResultadoRoteamento]:
    """
    Importa balancete usando o método apropriado.
    
    Args:
        conteudo: Bytes do arquivo
        nome_arquivo: Nome do arquivo
        sistema_contabil: Código do sistema contábil
        forcar_ia: Forçar uso de IA
    
    Returns:
        Tupla (dados_extraidos, resultado_roteamento)
    """
    # Decidir método
    roteamento = decidir_metodo_importacao(sistema_contabil, nome_arquivo, forcar_ia)
    
    if roteamento.usar_parser_local:
        # Usar parser local
        dados = _importar_com_parser_local(conteudo, nome_arquivo, roteamento.nome_parser)
    else:
        # Usar IA
        dados = _importar_com_ia(conteudo, nome_arquivo)
    
    return dados, roteamento


def _importar_com_parser_local(conteudo: bytes, nome_arquivo: str, nome_parser: str) -> Dict:
    """
    Importa usando parser local específico.
    """
    if nome_parser == 'parser_dominio':
        try:
            from importers.parser_dominio import parse_dominio
            resultado = parse_dominio(conteudo, nome_arquivo)
            
            if resultado.sucesso:
                return {
                    'sucesso': True,
                    'metodo': 'parser_local',
                    'parser': 'dominio',
                    'dados': resultado.dados,
                    'empresa': resultado.empresa,
                    'cnpj': resultado.cnpj,
                    'periodo': resultado.periodo,
                    'ano': resultado.ano,
                    'mes': resultado.mes,
                    'contas_processadas': resultado.contas_processadas,
                    'observacoes': resultado.observacoes
                }
            else:
                # Parser falhou, retorna erro para tentar IA
                return {
                    'sucesso': False,
                    'metodo': 'parser_local',
                    'parser': 'dominio',
                    'erro': resultado.erro,
                    'fallback_ia': True  # Indica que deve tentar IA
                }
        except Exception as e:
            return {
                'sucesso': False,
                'metodo': 'parser_local',
                'parser': 'dominio',
                'erro': str(e),
                'fallback_ia': True
            }
    
    # Parser não implementado
    return {
        'sucesso': False,
        'metodo': 'parser_local',
        'parser': nome_parser,
        'erro': f"Parser '{nome_parser}' não implementado",
        'fallback_ia': True
    }


def _importar_com_ia(conteudo: bytes, nome_arquivo: str) -> Dict:
    """
    Importa usando IA (Claude/OpenAI).
    
    Esta função deve ser implementada com a chamada real à API de IA.
    Por enquanto, retorna placeholder.
    """
    # TODO: Implementar chamada real à IA
    # Por enquanto, tenta usar o importador genérico
    try:
        from importers.balancete_importer import importar_balancete_bytes
        resultado = importar_balancete_bytes(conteudo, nome_arquivo)
        
        if resultado.sucesso:
            return {
                'sucesso': True,
                'metodo': 'ia',
                'dados': resultado.dados.to_dict() if resultado.dados else {},
                'empresa': resultado.dados.empresa.nome if resultado.dados else None,
                'cnpj': resultado.dados.empresa.cnpj if resultado.dados else None,
                'observacoes': [resultado.mensagem]
            }
    except Exception as e:
        pass
    
    return {
        'sucesso': False,
        'metodo': 'ia',
        'erro': 'Importação por IA não configurada. Configure a API key.',
        'requer_configuracao': True
    }


def importar_balancete_inteligente(
    conteudo: bytes,
    nome_arquivo: str,
    sistema_contabil: int = 0,
    forcar_ia: bool = False,
    fallback_ia: bool = True
) -> Dict:
    """
    Importa balancete de forma inteligente.
    
    Fluxo:
    1. Decide método baseado no sistema_contabil
    2. Tenta parser local se disponível
    3. Faz fallback para IA se parser falhar (e fallback_ia=True)
    
    Args:
        conteudo: Bytes do arquivo
        nome_arquivo: Nome do arquivo
        sistema_contabil: Código do sistema contábil
        forcar_ia: Forçar uso de IA
        fallback_ia: Permitir fallback para IA se parser falhar
    
    Returns:
        Dict com dados extraídos e metadados
    """
    # Primeira tentativa
    dados, roteamento = importar_com_roteamento(
        conteudo, nome_arquivo, sistema_contabil, forcar_ia
    )
    
    # Se parser local falhou e fallback habilitado, tenta IA
    if not dados.get('sucesso') and dados.get('fallback_ia') and fallback_ia:
        print(f"[ROTEADOR] Parser local falhou, tentando IA: {dados.get('erro')}")
        dados_ia = _importar_com_ia(conteudo, nome_arquivo)
        
        if dados_ia.get('sucesso'):
            dados_ia['metodo_original'] = 'parser_local'
            dados_ia['fallback_usado'] = True
            dados_ia['erro_parser'] = dados.get('erro')
            return dados_ia
        
        # IA também falhou
        return {
            'sucesso': False,
            'metodo': 'ambos_falharam',
            'erro_parser': dados.get('erro'),
            'erro_ia': dados_ia.get('erro'),
            'erro': 'Não foi possível importar o arquivo. Verifique o formato.'
        }
    
    # Adiciona info de roteamento
    dados['roteamento'] = {
        'sistema': roteamento.nome_sistema,
        'usou_parser_local': roteamento.usar_parser_local,
        'motivo': roteamento.motivo
    }
    
    return dados


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    print("=== TESTE DO ROTEADOR DE IMPORTAÇÃO ===\n")
    
    # Testar decisões de roteamento
    testes = [
        (0, "arquivo.pdf", False),   # Desconhecido -> IA
        (1, "balancete.pdf", False), # Domínio -> Parser local
        (100, "arquivo.pdf", False), # Contmatic -> IA
        (1, "balancete.pdf", True),  # Domínio mas forçar IA
    ]
    
    for sistema, arquivo, forcar in testes:
        resultado = decidir_metodo_importacao(sistema, arquivo, forcar)
        metodo = "Parser Local" if resultado.usar_parser_local else "IA"
        print(f"Sistema {sistema:3d} | {arquivo:20s} | Forçar IA: {forcar} | -> {metodo}")
        print(f"           Motivo: {resultado.motivo}\n")
