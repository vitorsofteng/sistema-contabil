#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelos do Banco de Dados - Sistema de Gestão Contábil
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

# Base para os modelos
Base = declarative_base()

# Configuração do banco
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./contabil.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para obter sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Contador(Base):
    """Usuário contador que gerencia empresas."""
    __tablename__ = "contadores"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    senha_hash = Column(String(200), nullable=False)
    telefone = Column(String(20))
    crc = Column(String(20))  # Registro no CRC
    escritorio = Column(String(200))
    
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    empresas = relationship("Empresa", back_populates="contador")


class Empresa(Base):
    """Empresa cliente do contador."""
    __tablename__ = "empresas"
    
    id = Column(Integer, primary_key=True, index=True)
    contador_id = Column(Integer, ForeignKey("contadores.id"), nullable=False)
    
    # Dados básicos
    razao_social = Column(String(300), nullable=False)
    nome_fantasia = Column(String(200))
    cnpj = Column(String(20), index=True)
    inscricao_estadual = Column(String(20))
    
    # Endereço
    endereco = Column(String(300))
    cidade = Column(String(100))
    estado = Column(String(2))
    cep = Column(String(10))
    
    # Contato
    telefone = Column(String(20))
    email = Column(String(200))
    contato_nome = Column(String(200))
    
    # Dados fiscais
    regime_tributario = Column(String(50))  # Simples, Lucro Presumido, Lucro Real
    cnae_principal = Column(String(10))
    setor = Column(String(100))
    
    # Configuração de mapeamento de colunas (salvo para reusar)
    mapeamento_colunas = Column(JSON)
    
    # Status
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    contador = relationship("Contador", back_populates="empresas")
    registros_mensais = relationship("RegistroMensal", back_populates="empresa", order_by="desc(RegistroMensal.competencia)")
    analises = relationship("Analise", back_populates="empresa", order_by="desc(Analise.criado_em)")
    alertas = relationship("Alerta", back_populates="empresa", order_by="desc(Alerta.criado_em)")


class RegistroMensal(Base):
    """Dados financeiros mensais de uma empresa."""
    __tablename__ = "registros_mensais"
    
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    # Competência (YYYY-MM)
    competencia = Column(String(7), nullable=False, index=True)  # Ex: 2024-01
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    
    # Dados financeiros
    receita_bruta = Column(Float, default=0)
    custos = Column(Float, default=0)
    despesas_operacionais = Column(Float, default=0)
    despesas_administrativas = Column(Float, default=0)
    folha_pagamento = Column(Float, default=0)
    impostos = Column(Float, default=0)
    outras_receitas = Column(Float, default=0)
    outras_despesas = Column(Float, default=0)
    
    # Calculados
    lucro_bruto = Column(Float, default=0)
    lucro_liquido = Column(Float, default=0)
    margem_bruta = Column(Float, default=0)
    margem_liquida = Column(Float, default=0)
    
    # Caixa/Banco
    saldo_caixa = Column(Float, default=0)
    contas_receber = Column(Float, default=0)
    contas_pagar = Column(Float, default=0)
    
    # Metadata
    fonte = Column(String(100))  # Upload CSV, Manual, API
    observacoes = Column(Text)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    empresa = relationship("Empresa", back_populates="registros_mensais")
    
    def calcular_indicadores(self):
        """Calcula indicadores derivados."""
        self.lucro_bruto = self.receita_bruta - self.custos
        despesas_total = self.despesas_operacionais + self.despesas_administrativas + self.folha_pagamento
        self.lucro_liquido = self.lucro_bruto - despesas_total - self.impostos + self.outras_receitas - self.outras_despesas
        
        if self.receita_bruta > 0:
            self.margem_bruta = (self.lucro_bruto / self.receita_bruta) * 100
            self.margem_liquida = (self.lucro_liquido / self.receita_bruta) * 100
        else:
            self.margem_bruta = 0
            self.margem_liquida = 0


class Analise(Base):
    """Análise de saúde financeira realizada."""
    __tablename__ = "analises"
    
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    # Período analisado
    periodo_inicio = Column(String(7))  # YYYY-MM
    periodo_fim = Column(String(7))
    meses_analisados = Column(Integer)
    
    # Score e status
    score = Column(Integer)
    score_confianca = Column(Float)
    status = Column(String(20))  # saudavel, atencao, critico
    
    # Componentes do score
    score_tendencia = Column(Float)
    score_margem = Column(Float)
    score_caixa = Column(Float)
    score_estabilidade = Column(Float)
    score_anomalias = Column(Float)
    
    # Resultados detalhados (JSON)
    resultado_completo = Column(JSON)
    
    # Insights e recomendações
    insights = Column(JSON)
    recomendacao_principal = Column(Text)
    
    # Metadata
    versao_modelo = Column(String(20), default="1.0")
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    empresa = relationship("Empresa", back_populates="analises")


class Alerta(Base):
    """Alertas e notificações para o contador."""
    __tablename__ = "alertas"
    
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    tipo = Column(String(50))  # score_baixo, tendencia_queda, caixa_critico, anomalia, etc
    severidade = Column(String(20))  # info, warning, critical
    titulo = Column(String(200))
    mensagem = Column(Text)
    
    lido = Column(Boolean, default=False)
    lido_em = Column(DateTime)
    
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    empresa = relationship("Empresa", back_populates="alertas")


class LogAtividade(Base):
    """Log de atividades do sistema."""
    __tablename__ = "logs_atividade"
    
    id = Column(Integer, primary_key=True, index=True)
    contador_id = Column(Integer, ForeignKey("contadores.id"))
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    
    acao = Column(String(100))  # login, cadastro_empresa, upload_dados, analise, etc
    descricao = Column(Text)
    ip = Column(String(50))
    user_agent = Column(String(300))
    
    criado_em = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Cria todas as tabelas."""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Remove todas as tabelas."""
    Base.metadata.drop_all(bind=engine)
