#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector de Sistemas Contábeis
==============================

Detecta qual sistema contábil gerou o arquivo baseado em padrões.

Sistemas suportados:
- Domínio Sistemas
- (futuros: Contmatic, Alterdata, Prosoft, etc.)
"""

import re
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class ResultadoDeteccao:
    """Resultado da detecção de sistema."""
    sistema: str  # 'dominio', 'contmatic', 'desconhecido', etc.
    confianca: float  # 0.0 a 1.0
    versao: Optional[str] = None
    indicadores: list = None
    
    def __post_init__(self):
        if self.indicadores is None:
            self.indicadores = []


# =============================================================================
# PADRÕES DE DETECÇÃO
# =============================================================================

PADROES_DOMINIO = [
    # Padrões EXCLUSIVOS do Domínio (alta confiança)
    (r'Sistema licenciado para', 0.8),
    (r'Domínio Sistemas', 0.8),
    (r'Dominio Sistemas', 0.8),  # Sem acento
    (r'www\.dominiosistemas', 0.8),
    
    # Padrões muito específicos do Domínio
    (r'N[úu]mero livro:', 0.5),
    (r'mero livro:', 0.4),  # Texto corrompido de "Número livro:"
    
    # Padrões estruturais do balancete Domínio
    # Combinação destes indica Domínio com alta confiança
    (r'Empresa:.*Folha:', 0.4),  # Cabeçalho típico do Domínio
    (r'C\.N\.P\.J\.:', 0.3),     # Formato específico com pontos
    (r'CONTAS DEVEDORAS.*CONTAS CREDORAS', 0.3),
    (r'RESUMO DO BALANCETE', 0.2),
    (r'Classifica[çc][ãa]o.*Descri[çc][ãa]o da conta', 0.3),  # Colunas específicas do Domínio
    (r'Saldo Anterior.*Saldo Atual', 0.2),  # Colunas do Domínio
]

# Threshold mínimo de confiança para considerar como detectado
# Empresa:+Folha: (0.4) + C.N.P.J.: (0.3) = 0.7 → passa
# CONTAS DEVEDORAS (0.3) + RESUMO (0.2) + C.N.P.J. (0.3) = 0.8 → passa
THRESHOLD_CONFIANCA_MINIMO = 0.5  # 50% - permite combinação de padrões estruturais

PADROES_CONTMATIC = [
    (r'Contmatic', 0.5),
    (r'Phoenix', 0.3),
    (r'G5 Phoenix', 0.5),
]

PADROES_ALTERDATA = [
    (r'Alterdata', 0.5),
    (r'Pack', 0.2),
]

PADROES_PROSOFT = [
    (r'Prosoft', 0.5),
]

PADROES_FORTES = [
    (r'Fortes', 0.5),
    (r'Fortes Contábil', 0.5),
]


# =============================================================================
# FUNÇÕES DE DETECÇÃO
# =============================================================================

def extrair_texto_para_deteccao(conteudo: bytes, nome_arquivo: str) -> str:
    """Extrai texto do arquivo para análise de padrões. Suporta apenas PDF."""
    extensao = nome_arquivo.lower().split('.')[-1]
    
    # Para PDF
    if extensao == 'pdf':
        try:
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
                texto = ""
                for pagina in pdf.pages[:3]:  # Só primeiras 3 páginas
                    texto += (pagina.extract_text() or "") + "\n"
                return texto
        except:
            pass
        
        try:
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(conteudo))
            texto = ""
            for pagina in reader.pages[:3]:
                texto += (pagina.extract_text() or "") + "\n"
            return texto
        except:
            pass
        
        # Fallback: extrai strings do binário
        strings = re.findall(rb'[\x20-\x7E\xC0-\xFF]{4,}', conteudo)
        return " ".join(s.decode('latin-1', errors='ignore') for s in strings)
    
    # Para CSV/TXT
    elif extensao in ['csv', 'txt']:
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                return conteudo.decode(encoding)
            except:
                continue
        return ""
    
    # Outros formatos - não suportados
    else:
        return ""


def calcular_score_padroes(texto: str, padroes: list) -> Tuple[float, list]:
    """Calcula score baseado em padrões encontrados."""
    score = 0.0
    indicadores = []
    
    for padrao, peso in padroes:
        if re.search(padrao, texto, re.IGNORECASE):
            score += peso
            indicadores.append(padrao)
    
    return min(score, 1.0), indicadores


def detectar_sistema(conteudo: bytes, nome_arquivo: str) -> ResultadoDeteccao:
    """
    Detecta qual sistema contábil gerou o arquivo.
    
    Args:
        conteudo: Bytes do arquivo
        nome_arquivo: Nome do arquivo com extensão
    
    Returns:
        ResultadoDeteccao com sistema identificado e confiança
    """
    texto = extrair_texto_para_deteccao(conteudo, nome_arquivo)
    
    print(f"[DETECTOR] Arquivo: {nome_arquivo}")
    print(f"[DETECTOR] Texto extraído: {len(texto)} caracteres")
    
    if not texto:
        print(f"[DETECTOR] FALHA: Não foi possível extrair texto")
        return ResultadoDeteccao(
            sistema='desconhecido',
            confianca=0.0,
            indicadores=['Não foi possível extrair texto do arquivo']
        )
    
    # Mostra primeiros 500 chars para debug
    print(f"[DETECTOR] Primeiros 500 chars: {texto[:500]}")
    
    # Testa cada sistema
    resultados = []
    
    # Domínio
    score, indicadores = calcular_score_padroes(texto, PADROES_DOMINIO)
    print(f"[DETECTOR] Domínio - Score: {score:.2f}, Indicadores: {indicadores}")
    if score >= THRESHOLD_CONFIANCA_MINIMO:  # Só adiciona se passou do threshold
        resultados.append(('dominio', score, indicadores))
    else:
        print(f"[DETECTOR] Domínio REJEITADO - Score {score:.2f} < threshold {THRESHOLD_CONFIANCA_MINIMO}")
    
    # Contmatic
    score, indicadores = calcular_score_padroes(texto, PADROES_CONTMATIC)
    print(f"[DETECTOR] Contmatic - Score: {score:.2f}, Indicadores: {indicadores}")
    if score > 0:
        resultados.append(('contmatic', score, indicadores))
    
    # Alterdata
    score, indicadores = calcular_score_padroes(texto, PADROES_ALTERDATA)
    print(f"[DETECTOR] Alterdata - Score: {score:.2f}, Indicadores: {indicadores}")
    if score > 0:
        resultados.append(('alterdata', score, indicadores))
    
    # Prosoft
    score, indicadores = calcular_score_padroes(texto, PADROES_PROSOFT)
    print(f"[DETECTOR] Prosoft - Score: {score:.2f}, Indicadores: {indicadores}")
    if score > 0:
        resultados.append(('prosoft', score, indicadores))
    
    # Fortes
    score, indicadores = calcular_score_padroes(texto, PADROES_FORTES)
    print(f"[DETECTOR] Fortes - Score: {score:.2f}, Indicadores: {indicadores}")
    if score > 0:
        resultados.append(('fortes', score, indicadores))
    
    # Retorna o sistema com maior score
    if resultados:
        resultados.sort(key=lambda x: x[1], reverse=True)
        melhor = resultados[0]
        print(f"[DETECTOR] RESULTADO: {melhor[0]} com confiança {melhor[1]*100:.0f}%")
        return ResultadoDeteccao(
            sistema=melhor[0],
            confianca=melhor[1],
            indicadores=melhor[2]
        )
    
    print(f"[DETECTOR] RESULTADO: Nenhum sistema detectado com confiança suficiente")
    return ResultadoDeteccao(
        sistema='desconhecido',
        confianca=0.0,
        indicadores=['Nenhum padrão reconhecido']
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
        
        resultado = detectar_sistema(conteudo, arquivo)
        print(f"Sistema: {resultado.sistema}")
        print(f"Confiança: {resultado.confianca:.0%}")
        print(f"Indicadores: {resultado.indicadores}")
    else:
        print("Uso: python detector.py <arquivo>")
