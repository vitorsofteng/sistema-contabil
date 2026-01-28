#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importador XML NFe (Notas Fiscais Eletrônicas)
"""

import re
from datetime import datetime
from typing import List, Dict, Tuple
from xml.etree import ElementTree as ET

from .base import ImportadorBase


class ImportadorNFe(ImportadorBase):
    """Importador para arquivos XML de NFe."""
    
    TIPO = "xml_nfe"
    EXTENSOES = ['.xml']
    
    # Namespaces comuns da NFe
    NAMESPACES = {
        'nfe': 'http://www.portalfiscal.inf.br/nfe',
        'nfe4': 'http://www.portalfiscal.inf.br/nfe'
    }
    
    def ler_arquivo(self, conteudo: bytes, nome_arquivo: str) -> Tuple[List[Dict], List[str]]:
        """Lê arquivo XML de NFe."""
        dados = []
        colunas = ['data', 'numero_nfe', 'cnpj_emitente', 'razao_emitente', 
                   'cnpj_destinatario', 'razao_destinatario', 'valor_total',
                   'valor_produtos', 'valor_icms', 'valor_pis', 'valor_cofins',
                   'natureza_operacao', 'tipo']
        
        # Decodifica
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                texto = conteudo.decode(encoding)
                break
            except:
                continue
        else:
            texto = conteudo.decode('utf-8', errors='ignore')
        
        try:
            root = ET.fromstring(texto)
            
            # Detecta namespace
            ns = self._detectar_namespace(root)
            
            # Busca NFe(s) no XML (pode ter várias em lote)
            nfes = root.findall(f'.//{{{ns}}}NFe') if ns else root.findall('.//NFe')
            
            if not nfes:
                # Tenta sem namespace
                nfes = root.findall('.//NFe')
            
            if not nfes:
                # O próprio root pode ser a NFe
                if 'NFe' in root.tag or 'nfeProc' in root.tag:
                    nfes = [root]
            
            for nfe in nfes:
                try:
                    dado = self._extrair_dados_nfe(nfe, ns)
                    if dado:
                        dados.append(dado)
                except Exception as e:
                    continue
            
            # Se não encontrou NFe, pode ser outro tipo de XML fiscal
            if not dados:
                dados = self._tentar_outros_formatos(root)
                
        except ET.ParseError as e:
            # Tenta extrair com regex como fallback
            dados = self._parse_nfe_regex(texto)
        
        return dados, colunas
    
    def _detectar_namespace(self, root) -> str:
        """Detecta namespace do XML."""
        tag = root.tag
        if '{' in tag:
            ns = tag[tag.find('{') + 1:tag.find('}')]
            return ns
        return ''
    
    def _find_text(self, elem, path: str, ns: str = '') -> str:
        """Busca texto em elemento com ou sem namespace."""
        if ns:
            result = elem.findtext(f'.//{{{ns}}}{path}')
            if result:
                return result
        
        # Tenta sem namespace
        result = elem.findtext(f'.//{path}')
        if result:
            return result
        
        # Tenta com qualquer namespace
        for child in elem.iter():
            if child.tag.endswith(path):
                return child.text or ''
        
        return ''
    
    def _extrair_dados_nfe(self, nfe, ns: str) -> Dict:
        """Extrai dados de uma NFe."""
        dado = {}
        
        # Identificação
        ide = nfe.find(f'.//{{{ns}}}ide') if ns else nfe.find('.//ide')
        if ide is None:
            for child in nfe.iter():
                if child.tag.endswith('ide'):
                    ide = child
                    break
        
        if ide is not None:
            dado['numero_nfe'] = self._find_text(ide, 'nNF', ns) or self._find_text(ide, 'cNF', ns)
            
            # Data
            data_str = self._find_text(ide, 'dhEmi', ns) or self._find_text(ide, 'dEmi', ns)
            if data_str:
                dado['data'] = self._parse_data_nfe(data_str)
            
            dado['natureza_operacao'] = self._find_text(ide, 'natOp', ns)
            
            # Tipo: 0=entrada, 1=saída
            tipo_nf = self._find_text(ide, 'tpNF', ns)
            dado['tipo'] = 'saida' if tipo_nf == '1' else 'entrada'
        
        # Emitente
        emit = nfe.find(f'.//{{{ns}}}emit') if ns else nfe.find('.//emit')
        if emit is None:
            for child in nfe.iter():
                if child.tag.endswith('emit'):
                    emit = child
                    break
        
        if emit is not None:
            dado['cnpj_emitente'] = self._find_text(emit, 'CNPJ', ns) or self._find_text(emit, 'CPF', ns)
            dado['razao_emitente'] = self._find_text(emit, 'xNome', ns)
        
        # Destinatário
        dest = nfe.find(f'.//{{{ns}}}dest') if ns else nfe.find('.//dest')
        if dest is None:
            for child in nfe.iter():
                if child.tag.endswith('dest'):
                    dest = child
                    break
        
        if dest is not None:
            dado['cnpj_destinatario'] = self._find_text(dest, 'CNPJ', ns) or self._find_text(dest, 'CPF', ns)
            dado['razao_destinatario'] = self._find_text(dest, 'xNome', ns)
        
        # Totais
        total = nfe.find(f'.//{{{ns}}}total') if ns else nfe.find('.//total')
        if total is None:
            for child in nfe.iter():
                if child.tag.endswith('total'):
                    total = child
                    break
        
        if total is not None:
            dado['valor_total'] = self._parse_valor(self._find_text(total, 'vNF', ns))
            dado['valor_produtos'] = self._parse_valor(self._find_text(total, 'vProd', ns))
            dado['valor_icms'] = self._parse_valor(self._find_text(total, 'vICMS', ns))
            dado['valor_pis'] = self._parse_valor(self._find_text(total, 'vPIS', ns))
            dado['valor_cofins'] = self._parse_valor(self._find_text(total, 'vCOFINS', ns))
        
        # Mapeia para campos do sistema
        if dado.get('tipo') == 'saida':
            dado['receita'] = dado.get('valor_total', 0)
            dado['despesas'] = 0
        else:
            dado['receita'] = 0
            dado['despesas'] = dado.get('valor_total', 0)
        
        dado['impostos'] = (dado.get('valor_icms', 0) + 
                          dado.get('valor_pis', 0) + 
                          dado.get('valor_cofins', 0))
        
        dado['descricao'] = f"NFe {dado.get('numero_nfe', '')} - {dado.get('natureza_operacao', '')}"
        
        return dado if dado.get('valor_total') else None
    
    def _parse_data_nfe(self, data_str: str) -> str:
        """Parseia data no formato da NFe."""
        if not data_str:
            return ''
        
        # Remove timezone
        data_str = data_str.split('T')[0] if 'T' in data_str else data_str
        data_str = data_str.split('-')[0] if '-' in data_str and len(data_str) > 10 else data_str
        
        formatos = ['%Y-%m-%d', '%d/%m/%Y', '%Y%m%d']
        
        for fmt in formatos:
            try:
                dt = datetime.strptime(data_str[:10], fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        return data_str[:10]
    
    def _parse_valor(self, valor_str: str) -> float:
        """Converte string de valor para float."""
        if not valor_str:
            return 0.0
        
        try:
            return float(valor_str.replace(',', '.'))
        except:
            return 0.0
    
    def _tentar_outros_formatos(self, root) -> List[Dict]:
        """Tenta parsear outros formatos XML fiscais."""
        dados = []
        
        # CT-e (Conhecimento de Transporte)
        ctes = root.findall('.//CTe') or root.findall('.//{*}CTe')
        for cte in ctes:
            try:
                dado = {
                    'tipo': 'entrada',
                    'descricao': 'CT-e',
                    'valor_total': 0,
                    'despesas': 0
                }
                
                # Busca valores
                for elem in cte.iter():
                    if elem.tag.endswith('vTPrest'):
                        dado['valor_total'] = self._parse_valor(elem.text)
                        dado['despesas'] = dado['valor_total']
                    elif elem.tag.endswith('dhEmi') or elem.tag.endswith('dEmi'):
                        dado['data'] = self._parse_data_nfe(elem.text)
                    elif elem.tag.endswith('nCT'):
                        dado['numero_nfe'] = elem.text
                        dado['descricao'] = f"CT-e {elem.text}"
                
                if dado.get('valor_total'):
                    dados.append(dado)
            except:
                continue
        
        # NFS-e (Nota Fiscal de Serviço)
        nfses = root.findall('.//Nfse') or root.findall('.//{*}Nfse') or root.findall('.//CompNfse')
        for nfse in nfses:
            try:
                dado = {
                    'tipo': 'saida',
                    'descricao': 'NFS-e',
                    'valor_total': 0,
                    'receita': 0
                }
                
                for elem in nfse.iter():
                    if elem.tag.endswith('ValorServicos') or elem.tag.endswith('ValorLiquidoNfse'):
                        dado['valor_total'] = self._parse_valor(elem.text)
                        dado['receita'] = dado['valor_total']
                    elif elem.tag.endswith('DataEmissao'):
                        dado['data'] = self._parse_data_nfe(elem.text)
                    elif elem.tag.endswith('Numero'):
                        dado['numero_nfe'] = elem.text
                        dado['descricao'] = f"NFS-e {elem.text}"
                
                if dado.get('valor_total'):
                    dados.append(dado)
            except:
                continue
        
        return dados
    
    def _parse_nfe_regex(self, texto: str) -> List[Dict]:
        """Fallback: extrai dados com regex."""
        dados = []
        
        # Tenta extrair informações básicas
        nf_match = re.search(r'<nNF>(\d+)</nNF>', texto)
        valor_match = re.search(r'<vNF>([0-9.,]+)</vNF>', texto)
        data_match = re.search(r'<dhEmi>([^<]+)</dhEmi>', texto) or re.search(r'<dEmi>([^<]+)</dEmi>', texto)
        tipo_match = re.search(r'<tpNF>(\d)</tpNF>', texto)
        
        if valor_match:
            valor = self._parse_valor(valor_match.group(1))
            tipo = 'saida' if tipo_match and tipo_match.group(1) == '1' else 'entrada'
            
            dado = {
                'numero_nfe': nf_match.group(1) if nf_match else '',
                'data': self._parse_data_nfe(data_match.group(1)) if data_match else '',
                'valor_total': valor,
                'tipo': tipo,
                'receita': valor if tipo == 'saida' else 0,
                'despesas': valor if tipo == 'entrada' else 0,
                'descricao': f"NFe {nf_match.group(1)}" if nf_match else 'NFe'
            }
            dados.append(dado)
        
        return dados
