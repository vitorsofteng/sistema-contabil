#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importador CSV
"""

import csv
import io
from typing import List, Dict, Tuple

from .base import ImportadorBase


class ImportadorCSV(ImportadorBase):
    """Importador para arquivos CSV."""
    
    TIPO = "csv"
    EXTENSOES = ['.csv', '.txt']
    
    def ler_arquivo(self, conteudo: bytes, nome_arquivo: str) -> Tuple[List[Dict], List[str]]:
        """Lê arquivo CSV."""
        dados = []
        colunas = []
        
        # Tenta detectar encoding
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                texto = conteudo.decode(encoding)
                break
            except:
                continue
        else:
            texto = conteudo.decode('utf-8', errors='ignore')
        
        # Detecta delimitador
        sample = texto[:2000]
        delimitadores = [';', ',', '\t', '|']
        delimitador = ';'
        max_count = 0
        
        for d in delimitadores:
            count = sample.count(d)
            if count > max_count:
                max_count = count
                delimitador = d
        
        # Lê CSV
        reader = csv.DictReader(io.StringIO(texto), delimiter=delimitador)
        colunas = reader.fieldnames or []
        
        for row in reader:
            # Limpa valores
            row_limpa = {}
            for k, v in row.items():
                if k:
                    row_limpa[k.strip()] = v.strip() if v else ''
            if any(row_limpa.values()):
                dados.append(row_limpa)
        
        return dados, [c.strip() for c in colunas if c]
