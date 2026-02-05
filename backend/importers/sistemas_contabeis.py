#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistemas Contábeis - Enum e Lista
=================================

Lista completa de sistemas contábeis do mercado brasileiro.
O enum é usado para salvar no banco como inteiro.
"""

from enum import IntEnum
from typing import Optional, Dict, List
from dataclasses import dataclass


class SistemaContabil(IntEnum):
    """Enum de sistemas contábeis - salvo como inteiro no banco."""
    
    # 0 = Não definido / Outro
    NAO_DEFINIDO = 0
    
    # Sistemas com parser local implementado (1-99)
    DOMINIO = 1
    
    # Sistemas populares sem parser (100+)
    CONTMATIC_PHOENIX = 100
    ALTERDATA = 101
    PROSOFT = 102
    FORTES = 103
    QUESTOR = 104
    SAGE = 105
    TOTVS_PROTHEUS = 106
    TOTVS_RM = 107
    SENIOR = 108
    SANKHYA = 109
    MASTERMAQ = 110
    THOMSON_REUTERS = 111
    SPED_CONTABIL = 112
    
    # ERPs com módulo contábil
    SAP = 200
    ORACLE = 201
    MICROSIGA = 202
    DATASUL = 203
    
    # Sistemas regionais / menores
    SIACON = 300
    CONTABIL_PHOENIX = 301
    CONTA_AZUL = 302
    OMIE = 303
    BLING = 304
    NIBO = 305
    ACESSORIAS = 306
    SIENGE = 307
    MEGA = 308
    CORDILHEIRA = 309
    SCI = 310
    ATHENAS = 311
    FOLHAMATIC = 312
    SIGER = 313
    EXACTUS = 314
    EASYASSIST = 315
    MAKROSYSTEM = 316
    LINX = 317
    CIGAM = 318
    NASAJON = 319
    CONSISTS = 320
    REINF = 321
    QUESTOR_ZEN = 322
    IOB = 323
    DOMINIO_WEB = 324
    FORTES_WEB = 325
    UNICO = 326
    JB_SOFTWARE = 327
    ECONTAB = 328
    MANAD = 329
    BLUE = 330
    GESTTA = 331
    SICALC = 332
    CALIMA = 333
    SIBRAX = 334
    CONTMATIC_G5 = 335
    W3ERP = 336
    SYSTAX = 337
    TAXONE = 338
    OOBJ = 339
    SYNCHRO = 340
    KEEVO = 341


@dataclass
class InfoSistema:
    """Informações sobre um sistema contábil."""
    id: int
    codigo: str
    nome: str
    fabricante: str
    tem_parser: bool = False
    descricao: str = ""
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


# Lista completa de sistemas com informações
SISTEMAS_CONTABEIS: Dict[int, InfoSistema] = {
    # Não definido
    0: InfoSistema(
        id=0,
        codigo="NAO_DEFINIDO",
        nome="Outro / Não sei",
        fabricante="",
        tem_parser=False,
        descricao="Sistema não listado ou desconhecido",
        keywords=["outro", "nao sei", "desconhecido", "manual"]
    ),
    
    # === SISTEMAS COM PARSER LOCAL ===
    1: InfoSistema(
        id=1,
        codigo="DOMINIO",
        nome="Domínio Sistemas",
        fabricante="Thomson Reuters",
        tem_parser=True,
        descricao="Sistema Domínio Contábil",
        keywords=["dominio", "thomson", "dominiosistemas"]
    ),
    
    # === SISTEMAS POPULARES ===
    100: InfoSistema(
        id=100,
        codigo="CONTMATIC_PHOENIX",
        nome="Contmatic Phoenix",
        fabricante="Contmatic",
        tem_parser=False,
        descricao="G5 Phoenix - Sistema contábil",
        keywords=["contmatic", "phoenix", "g5"]
    ),
    101: InfoSistema(
        id=101,
        codigo="ALTERDATA",
        nome="Alterdata",
        fabricante="Alterdata",
        tem_parser=False,
        descricao="Alterdata Pack e módulos contábeis",
        keywords=["alterdata", "pack"]
    ),
    102: InfoSistema(
        id=102,
        codigo="PROSOFT",
        nome="Prosoft",
        fabricante="Prosoft",
        tem_parser=False,
        descricao="Prosoft Contábil",
        keywords=["prosoft"]
    ),
    103: InfoSistema(
        id=103,
        codigo="FORTES",
        nome="Fortes Contábil",
        fabricante="Fortes Tecnologia",
        tem_parser=False,
        descricao="Fortes Contábil e Fiscal",
        keywords=["fortes", "fortestecnologia"]
    ),
    104: InfoSistema(
        id=104,
        codigo="QUESTOR",
        nome="Questor",
        fabricante="Questor Sistemas",
        tem_parser=False,
        descricao="Questor Contábil",
        keywords=["questor"]
    ),
    105: InfoSistema(
        id=105,
        codigo="SAGE",
        nome="Sage",
        fabricante="Sage",
        tem_parser=False,
        descricao="Sage Contabilidade",
        keywords=["sage"]
    ),
    106: InfoSistema(
        id=106,
        codigo="TOTVS_PROTHEUS",
        nome="TOTVS Protheus",
        fabricante="TOTVS",
        tem_parser=False,
        descricao="TOTVS Protheus - Módulo Contábil",
        keywords=["totvs", "protheus"]
    ),
    107: InfoSistema(
        id=107,
        codigo="TOTVS_RM",
        nome="TOTVS RM",
        fabricante="TOTVS",
        tem_parser=False,
        descricao="TOTVS RM - Módulo Contábil",
        keywords=["totvs", "rm"]
    ),
    108: InfoSistema(
        id=108,
        codigo="SENIOR",
        nome="Senior Sistemas",
        fabricante="Senior",
        tem_parser=False,
        descricao="Senior ERP - Módulo Contábil",
        keywords=["senior"]
    ),
    109: InfoSistema(
        id=109,
        codigo="SANKHYA",
        nome="Sankhya",
        fabricante="Sankhya",
        tem_parser=False,
        descricao="Sankhya Om - Módulo Contábil",
        keywords=["sankhya", "om"]
    ),
    110: InfoSistema(
        id=110,
        codigo="MASTERMAQ",
        nome="Mastermaq",
        fabricante="Mastermaq",
        tem_parser=False,
        descricao="Mastermaq Contábil",
        keywords=["mastermaq"]
    ),
    111: InfoSistema(
        id=111,
        codigo="THOMSON_REUTERS",
        nome="Thomson Reuters (outros)",
        fabricante="Thomson Reuters",
        tem_parser=False,
        descricao="Outros sistemas Thomson Reuters",
        keywords=["thomson", "reuters"]
    ),
    112: InfoSistema(
        id=112,
        codigo="SPED_CONTABIL",
        nome="SPED Contábil (ECD)",
        fabricante="Receita Federal",
        tem_parser=False,
        descricao="Arquivo SPED Contábil - ECD",
        keywords=["sped", "ecd", "escrituracao"]
    ),
    
    # === ERPs ===
    200: InfoSistema(
        id=200,
        codigo="SAP",
        nome="SAP",
        fabricante="SAP",
        tem_parser=False,
        descricao="SAP ERP - Módulo FI",
        keywords=["sap", "fi"]
    ),
    201: InfoSistema(
        id=201,
        codigo="ORACLE",
        nome="Oracle",
        fabricante="Oracle",
        tem_parser=False,
        descricao="Oracle ERP - Módulo Contábil",
        keywords=["oracle"]
    ),
    202: InfoSistema(
        id=202,
        codigo="MICROSIGA",
        nome="Microsiga",
        fabricante="TOTVS",
        tem_parser=False,
        descricao="Microsiga Protheus",
        keywords=["microsiga"]
    ),
    203: InfoSistema(
        id=203,
        codigo="DATASUL",
        nome="Datasul",
        fabricante="TOTVS",
        tem_parser=False,
        descricao="Datasul EMS",
        keywords=["datasul", "ems"]
    ),
    
    # === SISTEMAS REGIONAIS / CLOUD ===
    302: InfoSistema(
        id=302,
        codigo="CONTA_AZUL",
        nome="Conta Azul",
        fabricante="Conta Azul",
        tem_parser=False,
        descricao="Conta Azul - Contabilidade online",
        keywords=["contaazul", "conta azul"]
    ),
    303: InfoSistema(
        id=303,
        codigo="OMIE",
        nome="Omie",
        fabricante="Omie",
        tem_parser=False,
        descricao="Omie ERP",
        keywords=["omie"]
    ),
    304: InfoSistema(
        id=304,
        codigo="BLING",
        nome="Bling",
        fabricante="Bling",
        tem_parser=False,
        descricao="Bling ERP",
        keywords=["bling"]
    ),
    305: InfoSistema(
        id=305,
        codigo="NIBO",
        nome="Nibo",
        fabricante="Nibo",
        tem_parser=False,
        descricao="Nibo - Contabilidade online",
        keywords=["nibo"]
    ),
    319: InfoSistema(
        id=319,
        codigo="NASAJON",
        nome="Nasajon",
        fabricante="Nasajon Sistemas",
        tem_parser=False,
        descricao="Nasajon Sistemas Contábeis",
        keywords=["nasajon"]
    ),
    323: InfoSistema(
        id=323,
        codigo="IOB",
        nome="IOB",
        fabricante="IOB",
        tem_parser=False,
        descricao="IOB Sistemas Contábeis",
        keywords=["iob"]
    ),
    331: InfoSistema(
        id=331,
        codigo="GESTTA",
        nome="Gestta",
        fabricante="Gestta",
        tem_parser=False,
        descricao="Gestta - Gestão Contábil",
        keywords=["gestta"]
    ),
    335: InfoSistema(
        id=335,
        codigo="CONTMATIC_G5",
        nome="Contmatic G5",
        fabricante="Contmatic",
        tem_parser=False,
        descricao="Contmatic G5",
        keywords=["contmatic", "g5"]
    ),
}


def get_sistema_info(sistema_id: int) -> Optional[InfoSistema]:
    """Retorna informações de um sistema pelo ID."""
    return SISTEMAS_CONTABEIS.get(sistema_id)


def get_sistema_por_codigo(codigo: str) -> Optional[InfoSistema]:
    """Retorna informações de um sistema pelo código."""
    codigo_upper = codigo.upper()
    for info in SISTEMAS_CONTABEIS.values():
        if info.codigo == codigo_upper:
            return info
    return None


def sistema_tem_parser(sistema_id: int) -> bool:
    """Verifica se um sistema tem parser local implementado."""
    info = SISTEMAS_CONTABEIS.get(sistema_id)
    return info.tem_parser if info else False


def listar_sistemas_para_dropdown() -> List[dict]:
    """
    Retorna lista de sistemas formatada para dropdown no frontend.
    Ordenada por: sistemas com parser primeiro, depois alfabético.
    """
    sistemas = []
    
    for sistema_id, info in SISTEMAS_CONTABEIS.items():
        sistemas.append({
            'id': sistema_id,
            'codigo': info.codigo,
            'nome': info.nome,
            'fabricante': info.fabricante,
            'tem_parser': info.tem_parser,
            'descricao': info.descricao,
            'label': f"{info.nome}" + (f" ({info.fabricante})" if info.fabricante else ""),
            'keywords': ' '.join([info.nome.lower(), info.fabricante.lower()] + info.keywords)
        })
    
    # Ordena: primeiro "Outro/Não sei", depois com parser, depois alfabético
    def sort_key(s):
        if s['id'] == 0:
            return (0, '')  # Primeiro
        if s['tem_parser']:
            return (1, s['nome'].lower())  # Segundo: com parser
        return (2, s['nome'].lower())  # Terceiro: sem parser, alfabético
    
    sistemas.sort(key=sort_key)
    
    return sistemas


def buscar_sistemas(termo: str) -> List[dict]:
    """
    Busca sistemas por termo (nome, fabricante, keywords).
    """
    if not termo:
        return listar_sistemas_para_dropdown()
    
    termo_lower = termo.lower().strip()
    resultados = []
    
    for sistema in listar_sistemas_para_dropdown():
        if termo_lower in sistema['keywords']:
            resultados.append(sistema)
    
    return resultados


# Mapeamento de ID para parser
PARSERS_DISPONIVEIS = {
    SistemaContabil.DOMINIO: 'parser_dominio',
    # Adicionar novos parsers aqui conforme implementados
}


def get_parser_para_sistema(sistema_id: int) -> Optional[str]:
    """Retorna o nome do módulo do parser para um sistema, ou None se não tem."""
    try:
        sistema = SistemaContabil(sistema_id)
        return PARSERS_DISPONIVEIS.get(sistema)
    except ValueError:
        return None
