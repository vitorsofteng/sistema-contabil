#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importador OFX/QIF (Extratos Bancários)
"""

import re
from datetime import datetime
from typing import List, Dict, Tuple
from xml.etree import ElementTree as ET

from .base import ImportadorBase, RegistroImportado


class ImportadorOFX(ImportadorBase):
    """Importador para arquivos OFX (Open Financial Exchange)."""
    
    TIPO = "ofx"
    EXTENSOES = ['.ofx', '.qif', '.qfx']
    
    def ler_arquivo(self, conteudo: bytes, nome_arquivo: str) -> Tuple[List[Dict], List[str]]:
        """Lê arquivo OFX."""
        dados = []
        
        # Decodifica
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                texto = conteudo.decode(encoding)
                break
            except:
                continue
        else:
            texto = conteudo.decode('utf-8', errors='ignore')
        
        # Detecta formato
        if texto.strip().startswith('!Type:'):
            # Formato QIF
            return self._parse_qif(texto)
        else:
            # Formato OFX/XML
            return self._parse_ofx(texto)
    
    def _parse_ofx(self, texto: str) -> Tuple[List[Dict], List[str]]:
        """Parseia formato OFX."""
        dados = []
        colunas = ['data', 'descricao', 'valor', 'tipo', 'fitid']
        
        # Remove header SGML se existir
        if '<OFX>' in texto.upper():
            inicio = texto.upper().find('<OFX>')
            texto = texto[inicio:]
        
        # Converte SGML para XML
        texto = self._sgml_to_xml(texto)
        
        try:
            # Tenta parsear como XML
            root = ET.fromstring(texto)
            
            # Busca transações em diferentes paths
            paths = [
                './/STMTTRN',
                './/BANKTRANLIST/STMTTRN',
                './/CCSTMTRS/BANKTRANLIST/STMTTRN'
            ]
            
            for path in paths:
                for trn in root.findall(path):
                    try:
                        # Data
                        dtposted = trn.findtext('DTPOSTED', '')
                        data = self._parse_ofx_date(dtposted)
                        
                        # Valor
                        trnamt = trn.findtext('TRNAMT', '0')
                        valor = float(trnamt.replace(',', '.'))
                        
                        # Descrição
                        memo = trn.findtext('MEMO', '')
                        name = trn.findtext('NAME', '')
                        descricao = memo or name
                        
                        # Tipo
                        trntype = trn.findtext('TRNTYPE', '')
                        tipo = 'credito' if valor > 0 else 'debito'
                        
                        # ID único
                        fitid = trn.findtext('FITID', '')
                        
                        dados.append({
                            'data': data.strftime('%Y-%m-%d') if data else '',
                            'descricao': descricao,
                            'valor': abs(valor),
                            'tipo': tipo,
                            'fitid': fitid,
                            'receita': valor if valor > 0 else 0,
                            'despesas': abs(valor) if valor < 0 else 0
                        })
                    except Exception as e:
                        continue
                        
        except ET.ParseError:
            # Fallback: regex
            dados = self._parse_ofx_regex(texto)
        
        return dados, colunas
    
    def _sgml_to_xml(self, texto: str) -> str:
        """Converte SGML OFX para XML válido."""
        # Remove headers
        lines = []
        in_body = False
        
        for line in texto.split('\n'):
            if '<OFX>' in line.upper():
                in_body = True
            if in_body:
                lines.append(line)
        
        texto = '\n'.join(lines)
        
        # Tags que precisam ser fechadas
        tags_simples = ['DTSERVER', 'LANGUAGE', 'DTSTART', 'DTEND', 'DTPOSTED', 
                        'TRNAMT', 'FITID', 'NAME', 'MEMO', 'TRNTYPE', 'ACCTID',
                        'BANKID', 'ACCTTYPE', 'BALAMT', 'DTASOF']
        
        for tag in tags_simples:
            # Encontra <TAG>valor e adiciona </TAG>
            pattern = f'<{tag}>([^<\n]*)'
            texto = re.sub(pattern, f'<{tag}>\\1</{tag}>', texto, flags=re.IGNORECASE)
        
        return texto
    
    def _parse_ofx_date(self, date_str: str) -> datetime:
        """Parseia data no formato OFX (YYYYMMDDHHMMSS)."""
        if not date_str:
            return None
        
        # Remove timezone
        date_str = date_str.split('[')[0]
        
        # Formatos comuns
        formatos = ['%Y%m%d%H%M%S', '%Y%m%d', '%Y-%m-%d']
        
        for fmt in formatos:
            try:
                return datetime.strptime(date_str[:len(fmt.replace('%', ''))], fmt)
            except:
                continue
        
        return None
    
    def _parse_ofx_regex(self, texto: str) -> List[Dict]:
        """Fallback: extrai transações com regex."""
        dados = []
        
        # Padrão para transações
        pattern = r'<STMTTRN>(.*?)</STMTTRN>'
        matches = re.findall(pattern, texto, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            trn = {}
            
            # Extrai campos
            for tag in ['DTPOSTED', 'TRNAMT', 'MEMO', 'NAME', 'TRNTYPE', 'FITID']:
                tag_pattern = f'<{tag}>([^<\n]*)'
                tag_match = re.search(tag_pattern, match, re.IGNORECASE)
                if tag_match:
                    trn[tag.lower()] = tag_match.group(1).strip()
            
            if 'trnamt' in trn:
                valor = float(trn.get('trnamt', '0').replace(',', '.'))
                data = self._parse_ofx_date(trn.get('dtposted', ''))
                
                dados.append({
                    'data': data.strftime('%Y-%m-%d') if data else '',
                    'descricao': trn.get('memo') or trn.get('name', ''),
                    'valor': abs(valor),
                    'tipo': 'credito' if valor > 0 else 'debito',
                    'fitid': trn.get('fitid', ''),
                    'receita': valor if valor > 0 else 0,
                    'despesas': abs(valor) if valor < 0 else 0
                })
        
        return dados
    
    def _parse_qif(self, texto: str) -> Tuple[List[Dict], List[str]]:
        """Parseia formato QIF (Quicken Interchange Format)."""
        dados = []
        colunas = ['data', 'valor', 'descricao', 'categoria', 'tipo']
        
        # Separa transações
        transacoes = texto.split('^')
        
        for trn in transacoes:
            if not trn.strip():
                continue
            
            registro = {}
            
            for linha in trn.strip().split('\n'):
                if not linha:
                    continue
                
                codigo = linha[0]
                valor_linha = linha[1:].strip()
                
                if codigo == 'D':  # Data
                    registro['data'] = valor_linha
                elif codigo == 'T':  # Valor
                    try:
                        valor = float(valor_linha.replace(',', '.').replace(' ', ''))
                        registro['valor'] = abs(valor)
                        registro['tipo'] = 'credito' if valor > 0 else 'debito'
                        registro['receita'] = valor if valor > 0 else 0
                        registro['despesas'] = abs(valor) if valor < 0 else 0
                    except:
                        pass
                elif codigo == 'P' or codigo == 'M':  # Descrição/Memo
                    registro['descricao'] = valor_linha
                elif codigo == 'L':  # Categoria
                    registro['categoria'] = valor_linha
            
            if registro.get('valor'):
                dados.append(registro)
        
        return dados, colunas
