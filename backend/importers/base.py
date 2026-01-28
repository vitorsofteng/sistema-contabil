#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importadores - Sistema Contábil
================================

Suporte a múltiplos formatos: CSV, Excel, OFX, XML NFe
"""

import os
import io
import json
import hashlib
import re
import unicodedata
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Session

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import Base, get_db


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RegistroImportado:
    """Registro individual importado."""
    linha: int
    data: Optional[date] = None
    ano: Optional[int] = None
    mes: Optional[int] = None
    receita: float = 0
    custos: float = 0
    despesas: float = 0
    impostos: float = 0
    folha: float = 0
    caixa: float = 0
    descricao: str = ""
    categoria: str = ""
    tipo: str = ""  # receita, despesa, nfe, extrato
    dados_originais: Dict = field(default_factory=dict)
    erro: Optional[str] = None
    is_duplicado: bool = False
    hash: str = ""


@dataclass
class ResultadoImportacao:
    """Resultado da importação."""
    sucesso: bool = False
    total_registros: int = 0
    registros_importados: int = 0
    registros_duplicados: int = 0
    registros_erro: int = 0
    registros: List[RegistroImportado] = field(default_factory=list)
    erros: List[Dict] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    colunas_detectadas: List[str] = field(default_factory=list)
    mapeamento_sugerido: Dict = field(default_factory=dict)
    periodo_inicio: str = ""
    periodo_fim: str = ""


# =============================================================================
# MODELOS
# =============================================================================

class HistoricoImportacao(Base):
    """Histórico de importações."""
    __tablename__ = 'importacoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organizacao_id = Column(Integer, ForeignKey('organizacoes.id'))
    empresa_id = Column(Integer, ForeignKey('empresas.id'))
    contador_id = Column(Integer, ForeignKey('contadores.id'), nullable=False)
    
    nome_arquivo = Column(String(255), nullable=False)
    tipo_arquivo = Column(String(20), nullable=False)
    tamanho_bytes = Column(Integer)
    hash_arquivo = Column(String(64), index=True)
    
    status = Column(String(20), default='processando')
    total_registros = Column(Integer, default=0)
    registros_importados = Column(Integer, default=0)
    registros_duplicados = Column(Integer, default=0)
    registros_erro = Column(Integer, default=0)
    
    erros = Column(Text)
    mapeamento_usado = Column(Text)
    periodo_inicio = Column(String(7))
    periodo_fim = Column(String(7))
    
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nome_arquivo': self.nome_arquivo,
            'tipo_arquivo': self.tipo_arquivo,
            'tamanho_bytes': self.tamanho_bytes,
            'status': self.status,
            'status_label': self._get_status_label(),
            'total_registros': self.total_registros,
            'registros_importados': self.registros_importados,
            'registros_duplicados': self.registros_duplicados,
            'registros_erro': self.registros_erro,
            'periodo': f"{self.periodo_inicio} a {self.periodo_fim}" if self.periodo_inicio else None,
            'erros': json.loads(self.erros) if self.erros else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def _get_status_label(self) -> str:
        labels = {
            'processando': 'Processando',
            'sucesso': 'Sucesso',
            'parcial': 'Parcial',
            'erro': 'Erro'
        }
        return labels.get(self.status, self.status)


class MapeamentoImportacao(Base):
    """Mapeamento salvo para importações."""
    __tablename__ = 'mapeamentos_importacao'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organizacao_id = Column(Integer, ForeignKey('organizacoes.id'))
    empresa_id = Column(Integer, ForeignKey('empresas.id'))
    contador_id = Column(Integer, ForeignKey('contadores.id'), nullable=False)
    
    nome = Column(String(100), nullable=False)
    tipo_arquivo = Column(String(20), nullable=False)
    mapeamento = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nome': self.nome,
            'tipo_arquivo': self.tipo_arquivo,
            'mapeamento': json.loads(self.mapeamento) if self.mapeamento else {},
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class RegistroImportadoDB(Base):
    """Registro importado para detecção de duplicatas."""
    __tablename__ = 'registros_importados'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    importacao_id = Column(Integer, ForeignKey('importacoes.id'), nullable=False)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    
    hash_registro = Column(String(64), nullable=False)
    competencia = Column(String(7), nullable=False)
    tipo = Column(String(20))
    dados_originais = Column(Text)
    
    created_at = Column(DateTime, default=func.now())


# =============================================================================
# CLASSE BASE IMPORTADOR
# =============================================================================

class ImportadorBase(ABC):
    """Classe base para importadores."""
    
    TIPO = "base"
    EXTENSOES = []
    
    # Campos padrão do sistema
    CAMPOS_SISTEMA = [
        'data', 'ano', 'mes', 'receita', 'custos', 'despesas', 
        'impostos', 'folha', 'caixa', 'descricao', 'categoria'
    ]
    
    # Aliases comuns para detectar automaticamente
    ALIASES = {
        'data': ['data', 'date', 'dt', 'periodo', 'competencia', 'competência', 'data_competencia', 'mes_ano', 'ref', 'referencia', 'referência', 'mes', 'month'],
        'ano': ['ano', 'year', 'exercicio', 'exercício'],
        'mes': ['mes', 'mês', 'month', 'periodo', 'período'],
        'receita': ['receita', 'receita_bruta', 'faturamento', 'vendas', 'revenue', 'entradas', 'creditos', 'créditos', 'receita bruta', 'total vendas'],
        'custos': ['custos', 'custo', 'cmv', 'cpv', 'cost', 'custo_mercadoria', 'custo mercadoria', 'custo dos produtos'],
        'despesas': ['despesas', 'despesa', 'despesas_operacionais', 'despesas operacionais', 'expenses', 'gastos', 'saidas', 'saídas', 'debitos', 'débitos'],
        'impostos': ['impostos', 'imposto', 'tributos', 'taxes', 'icms', 'pis', 'cofins', 'tributo'],
        'folha': ['folha', 'folha_pagamento', 'folha de pagamento', 'salarios', 'salários', 'payroll', 'pessoal', 'funcionarios', 'funcionários', 'folha pagamento'],
        'caixa': ['caixa', 'saldo', 'saldo_caixa', 'saldo caixa', 'saldo em caixa', 'cash', 'disponivel', 'disponível', 'banco', 'disponibilidades'],
        'descricao': ['descricao', 'descrição', 'description', 'historico', 'histórico', 'obs', 'observacao', 'observação', 'memo'],
        'categoria': ['categoria', 'category', 'tipo', 'classificacao', 'classificação', 'conta']
    }
    
    def __init__(self, empresa_id: int = None):
        self.empresa_id = empresa_id
    
    @abstractmethod
    def ler_arquivo(self, conteudo: bytes, nome_arquivo: str) -> Tuple[List[Dict], List[str]]:
        """Lê arquivo e retorna lista de dicts e colunas detectadas."""
        pass
    
    def _normalizar_texto(self, texto: str) -> str:
        """Normaliza texto removendo acentos e convertendo para minúsculas."""
        texto = texto.lower().strip()
        # Remove acentos
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
        return texto
    
    def detectar_mapeamento(self, colunas: List[str]) -> Dict[str, str]:
        """Detecta mapeamento automático baseado nos aliases."""
        mapeamento = {}
        
        # Cria dicionário normalizado -> original
        colunas_norm = {}
        for c in colunas:
            norm = self._normalizar_texto(c)
            colunas_norm[norm] = c
            # Também adiciona versão com underscore no lugar de espaço
            colunas_norm[norm.replace(' ', '_')] = c
        
        for campo, aliases in self.ALIASES.items():
            for alias in aliases:
                alias_norm = self._normalizar_texto(alias)
                if alias_norm in colunas_norm:
                    mapeamento[campo] = colunas_norm[alias_norm]
                    break
                # Tenta também com underscore
                alias_underscore = alias_norm.replace(' ', '_')
                if alias_underscore in colunas_norm:
                    mapeamento[campo] = colunas_norm[alias_underscore]
                    break
        
        return mapeamento
    
    def aplicar_mapeamento(self, dados: List[Dict], mapeamento: Dict[str, str]) -> List[RegistroImportado]:
        """Aplica mapeamento aos dados brutos."""
        registros = []
        
        for i, row in enumerate(dados, 1):
            try:
                reg = RegistroImportado(linha=i)
                reg.dados_originais = row
                
                # Extrai data/período
                if 'data' in mapeamento and mapeamento['data'] in row:
                    data_str = str(row[mapeamento['data']])
                    parsed = self._parse_data(data_str)
                    if parsed:
                        reg.data = parsed
                        reg.ano = parsed.year
                        reg.mes = parsed.month
                
                # Se não tem data, tenta ano/mes separados
                if not reg.ano and 'ano' in mapeamento and mapeamento['ano'] in row:
                    try:
                        reg.ano = int(float(str(row[mapeamento['ano']])))
                    except:
                        pass
                
                if not reg.mes and 'mes' in mapeamento and mapeamento['mes'] in row:
                    try:
                        reg.mes = int(float(str(row[mapeamento['mes']])))
                    except:
                        pass
                
                # Extrai valores numéricos
                for campo in ['receita', 'custos', 'despesas', 'impostos', 'folha', 'caixa']:
                    if campo in mapeamento and mapeamento[campo] in row:
                        valor = self._parse_numero(row[mapeamento[campo]])
                        setattr(reg, campo, valor)
                
                # Extrai textos
                for campo in ['descricao', 'categoria']:
                    if campo in mapeamento and mapeamento[campo] in row:
                        setattr(reg, campo, str(row[mapeamento[campo]] or ''))
                
                # Valida registro
                if not reg.ano or not reg.mes:
                    reg.erro = "Data/período não identificado"
                elif reg.ano < 2000 or reg.ano > 2100:
                    reg.erro = f"Ano inválido: {reg.ano}"
                elif reg.mes < 1 or reg.mes > 12:
                    reg.erro = f"Mês inválido: {reg.mes}"
                
                # Calcula hash para detecção de duplicatas
                reg.hash = self._calcular_hash(reg)
                
                registros.append(reg)
                
            except Exception as e:
                reg = RegistroImportado(linha=i, erro=str(e))
                registros.append(reg)
        
        return registros
    
    def _parse_data(self, valor: str) -> Optional[date]:
        """Tenta parsear data em vários formatos."""
        if not valor or valor == 'nan':
            return None
        
        valor = str(valor).strip()
        
        # Formatos comuns
        formatos = [
            '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d',
            '%d/%m/%y', '%m/%Y', '%Y-%m', '%m-%Y',
            '%d.%m.%Y', '%Y.%m.%d'
        ]
        
        for fmt in formatos:
            try:
                return datetime.strptime(valor, fmt).date()
            except:
                pass
        
        # Tenta extrair ano-mês de strings como "jan/2024", "2024-01", etc
        match = re.search(r'(\d{4})[-/]?(\d{1,2})', valor)
        if match:
            try:
                ano = int(match.group(1))
                mes = int(match.group(2))
                return date(ano, mes, 1)
            except:
                pass
        
        match = re.search(r'(\d{1,2})[-/](\d{4})', valor)
        if match:
            try:
                mes = int(match.group(1))
                ano = int(match.group(2))
                return date(ano, mes, 1)
            except:
                pass
        
        return None
    
    def _parse_numero(self, valor) -> float:
        """Converte valor para número."""
        if valor is None or valor == '' or str(valor).lower() == 'nan':
            return 0.0
        
        try:
            # Se já é número
            if isinstance(valor, (int, float)):
                return float(valor)
            
            # Remove caracteres não numéricos exceto vírgula e ponto
            valor_str = str(valor).strip()
            valor_str = re.sub(r'[^\d,.\-]', '', valor_str)
            
            # Trata formato brasileiro (1.234,56) vs americano (1,234.56)
            if ',' in valor_str and '.' in valor_str:
                if valor_str.rfind(',') > valor_str.rfind('.'):
                    # Formato brasileiro
                    valor_str = valor_str.replace('.', '').replace(',', '.')
                else:
                    # Formato americano
                    valor_str = valor_str.replace(',', '')
            elif ',' in valor_str:
                valor_str = valor_str.replace(',', '.')
            
            return float(valor_str) if valor_str else 0.0
        except:
            return 0.0
    
    def _calcular_hash(self, reg: RegistroImportado) -> str:
        """Calcula hash único do registro."""
        dados = f"{reg.ano}-{reg.mes}-{reg.receita}-{reg.custos}-{reg.despesas}-{reg.impostos}-{reg.folha}-{reg.caixa}"
        return hashlib.sha256(dados.encode()).hexdigest()[:32]
    
    def verificar_duplicatas(self, registros: List[RegistroImportado]) -> List[RegistroImportado]:
        """Marca registros duplicados."""
        if not self.empresa_id:
            return registros
        
        with get_db() as db:
            # Busca hashes existentes
            hashes_existentes = set()
            existentes = db.query(RegistroImportadoDB.hash_registro).filter(
                RegistroImportadoDB.empresa_id == self.empresa_id
            ).all()
            hashes_existentes = {h[0] for h in existentes}
            
            # Marca duplicados
            for reg in registros:
                if reg.hash in hashes_existentes:
                    reg.is_duplicado = True
        
        return registros
    
    def processar(self, conteudo: bytes, nome_arquivo: str, mapeamento: Dict = None) -> ResultadoImportacao:
        """Processa arquivo completo."""
        resultado = ResultadoImportacao()
        
        try:
            # Lê arquivo
            dados, colunas = self.ler_arquivo(conteudo, nome_arquivo)
            resultado.colunas_detectadas = colunas
            resultado.total_registros = len(dados)
            
            if not dados:
                resultado.erros.append({'linha': 0, 'erro': 'Arquivo vazio ou formato inválido'})
                return resultado
            
            # Detecta ou usa mapeamento
            if not mapeamento:
                mapeamento = self.detectar_mapeamento(colunas)
            resultado.mapeamento_sugerido = mapeamento
            
            # Aplica mapeamento
            registros = self.aplicar_mapeamento(dados, mapeamento)
            
            # Verifica duplicatas
            registros = self.verificar_duplicatas(registros)
            
            # Conta resultados
            for reg in registros:
                if reg.erro:
                    resultado.registros_erro += 1
                    resultado.erros.append({'linha': reg.linha, 'erro': reg.erro})
                elif reg.is_duplicado:
                    resultado.registros_duplicados += 1
                else:
                    resultado.registros_importados += 1
            
            resultado.registros = registros
            resultado.sucesso = resultado.registros_erro == 0
            
            # Período
            periodos = [(r.ano, r.mes) for r in registros if r.ano and r.mes and not r.erro]
            if periodos:
                periodos.sort()
                resultado.periodo_inicio = f"{periodos[0][0]}-{periodos[0][1]:02d}"
                resultado.periodo_fim = f"{periodos[-1][0]}-{periodos[-1][1]:02d}"
            
        except Exception as e:
            resultado.erros.append({'linha': 0, 'erro': f'Erro ao processar: {str(e)}'})
        
        return resultado
