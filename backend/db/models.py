#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelos SQLAlchemy - Sistema Contábil
=====================================

Features:
- Soft Delete (deleted_at)
- Timestamps automáticos (created_at, updated_at)
- Relacionamentos
- Índices otimizados
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey,
    Index, event, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


# =============================================================================
# MIXIN - Campos comuns
# =============================================================================

class TimestampMixin:
    """Mixin para timestamps automáticos."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin para soft delete."""
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        default=None
    )
    
    @hybrid_property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def soft_delete(self):
        """Marca registro como deletado."""
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restaura registro deletado."""
        self.deleted_at = None


# =============================================================================
# MODELO: Contador (Usuário)
# =============================================================================

class Contador(Base, TimestampMixin, SoftDeleteMixin):
    """Modelo de contador (usuário do sistema)."""
    
    __tablename__ = 'contadores'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    telefone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    crc: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Campos de segurança
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reset_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reset_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relacionamentos
    empresas: Mapped[List["Empresa"]] = relationship(
        "Empresa", 
        back_populates="contador",
        lazy="dynamic"
    )
    sessoes: Mapped[List["Sessao"]] = relationship(
        "Sessao",
        back_populates="contador",
        lazy="dynamic"
    )
    
    # Índices
    __table_args__ = (
        Index('idx_contadores_email_ativo', 'email', 'ativo'),
    )
    
    def to_dict(self) -> dict:
        """Converte para dicionário (sem senha)."""
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'crc': self.crc,
            'ativo': self.ativo,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# MODELO: Sessão
# =============================================================================

class Sessao(Base, TimestampMixin):
    """Modelo de sessão de usuário."""
    
    __tablename__ = 'sessoes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contador_id: Mapped[int] = mapped_column(Integer, ForeignKey('contadores.id'), nullable=False)
    token_jti: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    refresh_token_jti: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    device_info: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    refresh_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Relacionamentos
    contador: Mapped["Contador"] = relationship("Contador", back_populates="sessoes")
    
    # Índices
    __table_args__ = (
        Index('idx_sessoes_contador_ativo', 'contador_id', 'is_active'),
    )


# =============================================================================
# MODELO: Empresa
# =============================================================================

class Empresa(Base, TimestampMixin, SoftDeleteMixin):
    """Modelo de empresa cliente."""
    
    __tablename__ = 'empresas'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contador_id: Mapped[int] = mapped_column(Integer, ForeignKey('contadores.id'), nullable=False)
    razao_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nome_fantasia: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cnpj: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    inscricao_estadual: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    regime_tributario: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    setor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    endereco: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cidade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estado: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contato_nome: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relacionamentos
    contador: Mapped["Contador"] = relationship("Contador", back_populates="empresas")
    dados_mensais: Mapped[List["DadosMensal"]] = relationship(
        "DadosMensal",
        back_populates="empresa",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    analises: Mapped[List["Analise"]] = relationship(
        "Analise",
        back_populates="empresa",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    # Índices
    __table_args__ = (
        Index('idx_empresas_contador', 'contador_id'),
        Index('idx_empresas_contador_ativo', 'contador_id', 'ativo'),
        Index('idx_empresas_cnpj', 'cnpj'),
    )
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            'id': self.id,
            'contador_id': self.contador_id,
            'razao_social': self.razao_social,
            'nome_fantasia': self.nome_fantasia,
            'cnpj': self.cnpj,
            'inscricao_estadual': self.inscricao_estadual,
            'regime_tributario': self.regime_tributario,
            'setor': self.setor,
            'endereco': self.endereco,
            'cidade': self.cidade,
            'estado': self.estado,
            'telefone': self.telefone,
            'email': self.email,
            'contato_nome': self.contato_nome,
            'observacoes': self.observacoes,
            'ativo': self.ativo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# =============================================================================
# MODELO: Dados Mensais
# =============================================================================

class DadosMensal(Base, TimestampMixin, SoftDeleteMixin):
    """Modelo de dados financeiros mensais."""
    
    __tablename__ = 'dados_mensais'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey('empresas.id'), nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    receita: Mapped[float] = mapped_column(Float, default=0)
    custos: Mapped[float] = mapped_column(Float, default=0)
    despesas: Mapped[float] = mapped_column(Float, default=0)
    impostos: Mapped[float] = mapped_column(Float, default=0)
    folha: Mapped[float] = mapped_column(Float, default=0)
    caixa: Mapped[float] = mapped_column(Float, default=0)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="dados_mensais")
    
    # Índices e constraints
    __table_args__ = (
        Index('idx_dados_empresa', 'empresa_id'),
        Index('idx_dados_empresa_periodo', 'empresa_id', 'ano', 'mes'),
        Index('idx_dados_ano_mes', 'ano', 'mes'),
    )
    
    @hybrid_property
    def lucro_bruto(self) -> float:
        """Calcula lucro bruto."""
        return self.receita - self.custos
    
    @hybrid_property
    def lucro_liquido(self) -> float:
        """Calcula lucro líquido."""
        return self.receita - self.custos - self.despesas - self.impostos - self.folha
    
    @hybrid_property
    def margem_bruta(self) -> float:
        """Calcula margem bruta."""
        return (self.lucro_bruto / self.receita * 100) if self.receita > 0 else 0
    
    @hybrid_property
    def margem_liquida(self) -> float:
        """Calcula margem líquida."""
        return (self.lucro_liquido / self.receita * 100) if self.receita > 0 else 0
    
    @property
    def competencia(self) -> str:
        """Retorna competência no formato YYYY-MM."""
        return f"{self.ano}-{self.mes:02d}"
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'ano': self.ano,
            'mes': self.mes,
            'competencia': self.competencia,
            'receita': self.receita,
            'custos': self.custos,
            'despesas': self.despesas,
            'impostos': self.impostos,
            'folha': self.folha,
            'caixa': self.caixa,
            'lucro_bruto': self.lucro_bruto,
            'lucro_liquido': self.lucro_liquido,
            'margem_bruta': self.margem_bruta,
            'margem_liquida': self.margem_liquida,
            'observacoes': self.observacoes
        }


# =============================================================================
# MODELO: Análise
# =============================================================================

class Analise(Base, TimestampMixin):
    """Modelo de análise financeira."""
    
    __tablename__ = 'analises'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey('empresas.id'), nullable=False)
    data_analise: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    periodo_inicio: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    periodo_fim: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    meses_analisados: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score_confianca: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    resultado_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="analises")
    
    # Índices
    __table_args__ = (
        Index('idx_analises_empresa', 'empresa_id'),
        Index('idx_analises_empresa_data', 'empresa_id', 'data_analise'),
    )
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        import json
        resultado = {}
        if self.resultado_json:
            try:
                resultado = json.loads(self.resultado_json)
            except:
                pass
        
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'data_analise': self.data_analise.isoformat() if self.data_analise else None,
            'periodo_inicio': self.periodo_inicio,
            'periodo_fim': self.periodo_fim,
            'meses_analisados': self.meses_analisados,
            'score': self.score,
            'score_confianca': self.score_confianca,
            'status': self.status,
            'resultado_completo': resultado,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# MODELO: Login Attempts (Rate Limiting)
# =============================================================================

class LoginAttempt(Base):
    """Modelo para registro de tentativas de login."""
    
    __tablename__ = 'login_attempts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_login_attempts_identifier_time', 'identifier', 'created_at'),
    )


# =============================================================================
# MODELO: Token Blacklist
# =============================================================================

class TokenBlacklist(Base):
    """Modelo para blacklist de tokens."""
    
    __tablename__ = 'token_blacklist'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_token_blacklist_expires', 'expires_at'),
    )
