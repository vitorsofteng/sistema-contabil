#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serviço de Importação Inteligente
=================================

Fluxo:
1. Detecta o sistema contábil de origem
2. Se sistema reconhecido → usa parser local (grátis, rápido)
3. Se não reconhecido → usa IA como fallback

Vantagens:
- Parser local: gratuito, instantâneo, consistente
- IA fallback: funciona com qualquer sistema
"""

from typing import Dict, Optional
from dataclasses import dataclass, field, asdict
from .detector import detectar_sistema, ResultadoDeteccao
from .parser_dominio import parse_dominio, ResultadoParser


@dataclass
class ResultadoImportacao:
    """Resultado unificado da importação."""
    sucesso: bool
    dados: Dict = field(default_factory=dict)
    empresa: str = ""
    cnpj: str = ""
    periodo: str = ""
    ano: int = 0
    mes: int = 0
    sistema_detectado: str = ""
    metodo_usado: str = ""  # 'parser_local' ou 'ia'
    confianca: str = ""
    campos_extraidos: list = field(default_factory=list)
    observacoes: list = field(default_factory=list)
    erro: str = ""
    custo_estimado: float = 0.0
    tokens_usados: int = 0
    
    def to_dict(self):
        return asdict(self)


# Mapeamento de sistemas para parsers
PARSERS_DISPONIVEIS = {
    'dominio': parse_dominio,
    # Futuros parsers:
    # 'contmatic': parse_contmatic,
    # 'alterdata': parse_alterdata,
    # 'prosoft': parse_prosoft,
    # 'fortes': parse_fortes,
}

# Confiança mínima para usar parser local
CONFIANCA_MINIMA = 0.3


def importar_inteligente(
    conteudo: bytes,
    nome_arquivo: str,
    empresa_id: int = None,
    forcar_ia: bool = False
) -> ResultadoImportacao:
    """
    Importa arquivo usando a melhor estratégia disponível.
    
    Args:
        conteudo: Bytes do arquivo
        nome_arquivo: Nome do arquivo com extensão
        empresa_id: ID da empresa (opcional)
        forcar_ia: Se True, pula detecção e usa IA direto
    
    Returns:
        ResultadoImportacao com dados extraídos
    """
    resultado = ResultadoImportacao(sucesso=False)
    
    # Se forçar IA, vai direto
    if forcar_ia:
        print("[IMPORT] Forçando uso de IA...")
        return _importar_com_ia(conteudo, nome_arquivo, empresa_id, resultado)
    
    # 1. Detecta o sistema
    print(f"[IMPORT] Detectando sistema do arquivo: {nome_arquivo}")
    deteccao = detectar_sistema(conteudo, nome_arquivo)
    resultado.sistema_detectado = deteccao.sistema
    
    print(f"[IMPORT] Sistema detectado: {deteccao.sistema} (confiança: {deteccao.confianca:.0%})")
    print(f"[IMPORT] Indicadores: {deteccao.indicadores}")
    
    # 2. Verifica se tem parser disponível e confiança suficiente
    if deteccao.sistema in PARSERS_DISPONIVEIS and deteccao.confianca >= CONFIANCA_MINIMA:
        print(f"[IMPORT] Usando parser local para {deteccao.sistema}...")
        
        parser = PARSERS_DISPONIVEIS[deteccao.sistema]
        resultado_parser = parser(conteudo, nome_arquivo)
        
        if resultado_parser.sucesso:
            # Parser funcionou!
            resultado.sucesso = True
            resultado.dados = resultado_parser.dados
            resultado.empresa = resultado_parser.empresa
            resultado.cnpj = resultado_parser.cnpj
            resultado.periodo = resultado_parser.periodo
            resultado.ano = resultado_parser.ano
            resultado.mes = resultado_parser.mes
            resultado.metodo_usado = 'parser_local'
            resultado.confianca = 'alta' if deteccao.confianca > 0.7 else 'media'
            resultado.campos_extraidos = [k for k, v in resultado.dados.items() if v and v > 0]
            resultado.observacoes = resultado_parser.observacoes + [
                f"Parser local: {deteccao.sistema}",
                f"Confiança detecção: {deteccao.confianca:.0%}",
                "Custo: R$ 0,00 (gratuito)"
            ]
            resultado.custo_estimado = 0.0
            
            # Adiciona ano/mes aos dados
            if resultado.ano:
                resultado.dados['ano'] = resultado.ano
            if resultado.mes:
                resultado.dados['mes'] = resultado.mes
            
            print(f"[IMPORT] Parser local bem-sucedido!")
            print(f"[IMPORT] Campos extraídos: {resultado.campos_extraidos}")
            return resultado
        else:
            print(f"[IMPORT] Parser local falhou: {resultado_parser.erro}")
            print("[IMPORT] Tentando fallback com IA...")
            resultado.observacoes.append(f"Parser local falhou: {resultado_parser.erro}")
    else:
        if deteccao.sistema == 'desconhecido':
            print("[IMPORT] Sistema não reconhecido, usando IA...")
        else:
            print(f"[IMPORT] Confiança baixa ({deteccao.confianca:.0%}), usando IA...")
    
    # 3. Fallback: usa IA
    return _importar_com_ia(conteudo, nome_arquivo, empresa_id, resultado)


def _importar_com_ia(
    conteudo: bytes,
    nome_arquivo: str,
    empresa_id: int,
    resultado: ResultadoImportacao
) -> ResultadoImportacao:
    """Importa usando IA como fallback."""
    try:
        from .importacao_ia import importar_com_ia
        
        print("[IMPORT] Chamando IA Claude para extração...")
        resultado_ia = importar_com_ia(conteudo, nome_arquivo, empresa_id)
        
        if resultado_ia.sucesso:
            resultado.sucesso = True
            resultado.dados = resultado_ia.dados
            resultado.empresa = resultado_ia.empresa
            resultado.cnpj = resultado_ia.cnpj
            resultado.periodo = resultado_ia.periodo
            resultado.ano = resultado_ia.ano
            resultado.mes = resultado_ia.mes
            resultado.metodo_usado = 'ia'
            resultado.confianca = resultado_ia.confianca
            resultado.campos_extraidos = resultado_ia.campos_extraidos
            resultado.tokens_usados = resultado_ia.tokens_usados
            resultado.custo_estimado = resultado_ia.custo_estimado
            resultado.observacoes = resultado.observacoes + resultado_ia.observacoes + [
                "Método: IA Claude",
                f"Tokens: {resultado_ia.tokens_usados}",
                f"Custo: R$ {resultado_ia.custo_estimado:.4f}"
            ]
            
            if resultado_ia.sistema_detectado:
                resultado.sistema_detectado = resultado_ia.sistema_detectado
            
            print(f"[IMPORT] IA bem-sucedida!")
            return resultado
        else:
            resultado.erro = resultado_ia.erro
            resultado.observacoes = resultado_ia.observacoes
            print(f"[IMPORT] IA falhou: {resultado_ia.erro}")
            return resultado
            
    except ImportError as e:
        resultado.erro = f"Módulo de IA não disponível: {e}"
        print(f"[IMPORT] ERRO: {resultado.erro}")
        return resultado
    except Exception as e:
        resultado.erro = f"Erro na importação com IA: {str(e)}"
        print(f"[IMPORT] ERRO: {resultado.erro}")
        return resultado


def verificar_status() -> Dict:
    """Retorna status dos parsers e IA disponíveis."""
    status = {
        'parsers_locais': list(PARSERS_DISPONIVEIS.keys()),
        'ia_disponivel': False,
        'ia_configurada': False,
    }
    
    try:
        from .importacao_ia import verificar_configuracao
        config = verificar_configuracao()
        status['ia_disponivel'] = True
        status['ia_configurada'] = config.get('configurado', False)
        status['ia_modelo'] = config.get('modelo', '')
    except ImportError:
        pass
    
    return status


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("=== Status do Sistema ===")
    status = verificar_status()
    print(f"Parsers locais: {status['parsers_locais']}")
    print(f"IA disponível: {status['ia_disponivel']}")
    print(f"IA configurada: {status['ia_configurada']}")
    
    if len(sys.argv) > 1:
        arquivo = sys.argv[1]
        print(f"\n=== Testando arquivo: {arquivo} ===")
        
        with open(arquivo, 'rb') as f:
            conteudo = f.read()
        
        resultado = importar_inteligente(conteudo, arquivo)
        
        print(f"\nSucesso: {resultado.sucesso}")
        print(f"Método: {resultado.metodo_usado}")
        print(f"Sistema: {resultado.sistema_detectado}")
        print(f"Empresa: {resultado.empresa}")
        print(f"CNPJ: {resultado.cnpj}")
        print(f"Período: {resultado.periodo}")
        print(f"Campos: {resultado.campos_extraidos}")
        print(f"Custo: R$ {resultado.custo_estimado:.4f}")
        if resultado.erro:
            print(f"Erro: {resultado.erro}")
