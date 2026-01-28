#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schemas Pydantic - Validação de Dados
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# =============================================================================
# CONTADOR
# =============================================================================

class ContadorBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=200)
    email: EmailStr
    telefone: Optional[str] = None
    crc: Optional[str] = None
    escritorio: Optional[str] = None


class ContadorCreate(ContadorBase):
    senha: str = Field(..., min_length=6)


class ContadorUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    crc: Optional[str] = None
    escritorio: Optional[str] = None


class ContadorResponse(ContadorBase):
    id: int
    ativo: bool
    criado_em: datetime
    
    class Config:
        from_attributes = True


class ContadorLogin(BaseModel):
    email: EmailStr
    senha: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    contador: ContadorResponse


# =============================================================================
# EMPRESA
# =============================================================================

class EmpresaBase(BaseModel):
    razao_social: str = Field(..., min_length=3, max_length=300)
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    contato_nome: Optional[str] = None
    regime_tributario: Optional[str] = None
    cnae_principal: Optional[str] = None
    setor: Optional[str] = None


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    contato_nome: Optional[str] = None
    regime_tributario: Optional[str] = None
    cnae_principal: Optional[str] = None
    setor: Optional[str] = None
    mapeamento_colunas: Optional[Dict] = None
    ativo: Optional[bool] = None


class EmpresaResponse(EmpresaBase):
    id: int
    contador_id: int
    mapeamento_colunas: Optional[Dict] = None
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime
    
    class Config:
        from_attributes = True


class EmpresaResumo(BaseModel):
    """Resumo para listagem."""
    id: int
    razao_social: str
    nome_fantasia: Optional[str]
    cnpj: Optional[str]
    regime_tributario: Optional[str]
    ativo: bool
    ultimo_score: Optional[int] = None
    ultimo_status: Optional[str] = None
    ultima_analise: Optional[datetime] = None
    meses_dados: int = 0
    alertas_pendentes: int = 0
    
    class Config:
        from_attributes = True


# =============================================================================
# REGISTRO MENSAL
# =============================================================================

class RegistroMensalBase(BaseModel):
    competencia: str = Field(..., pattern=r'^\d{4}-\d{2}$')  # YYYY-MM
    receita_bruta: float = Field(default=0, ge=0)
    custos: float = Field(default=0, ge=0)
    despesas_operacionais: float = Field(default=0, ge=0)
    despesas_administrativas: float = Field(default=0, ge=0)
    folha_pagamento: float = Field(default=0, ge=0)
    impostos: float = Field(default=0, ge=0)
    outras_receitas: float = Field(default=0, ge=0)
    outras_despesas: float = Field(default=0, ge=0)
    saldo_caixa: float = Field(default=0)
    contas_receber: float = Field(default=0, ge=0)
    contas_pagar: float = Field(default=0, ge=0)
    observacoes: Optional[str] = None


class RegistroMensalCreate(RegistroMensalBase):
    pass


class RegistroMensalUpdate(BaseModel):
    receita_bruta: Optional[float] = None
    custos: Optional[float] = None
    despesas_operacionais: Optional[float] = None
    despesas_administrativas: Optional[float] = None
    folha_pagamento: Optional[float] = None
    impostos: Optional[float] = None
    outras_receitas: Optional[float] = None
    outras_despesas: Optional[float] = None
    saldo_caixa: Optional[float] = None
    contas_receber: Optional[float] = None
    contas_pagar: Optional[float] = None
    observacoes: Optional[str] = None


class RegistroMensalResponse(RegistroMensalBase):
    id: int
    empresa_id: int
    ano: int
    mes: int
    lucro_bruto: float
    lucro_liquido: float
    margem_bruta: float
    margem_liquida: float
    fonte: Optional[str]
    criado_em: datetime
    atualizado_em: datetime
    
    class Config:
        from_attributes = True


class UploadDadosRequest(BaseModel):
    """Request para upload de dados via CSV."""
    csv_content: str
    mapping: Dict[str, str]
    substituir_existentes: bool = False


# =============================================================================
# ANÁLISE
# =============================================================================

class AnaliseResponse(BaseModel):
    id: int
    empresa_id: int
    periodo_inicio: str
    periodo_fim: str
    meses_analisados: int
    score: int
    score_confianca: float
    status: str
    score_tendencia: Optional[float]
    score_margem: Optional[float]
    score_caixa: Optional[float]
    score_estabilidade: Optional[float]
    score_anomalias: Optional[float]
    resultado_completo: Optional[Dict]
    insights: Optional[List[str]]
    recomendacao_principal: Optional[str]
    versao_modelo: str
    criado_em: datetime
    
    class Config:
        from_attributes = True


class AnaliseResumo(BaseModel):
    """Resumo para listagem."""
    id: int
    periodo_inicio: str
    periodo_fim: str
    meses_analisados: int
    score: int
    status: str
    criado_em: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# ALERTA
# =============================================================================

class AlertaResponse(BaseModel):
    id: int
    empresa_id: int
    tipo: str
    severidade: str
    titulo: str
    mensagem: str
    lido: bool
    lido_em: Optional[datetime]
    criado_em: datetime
    empresa_nome: Optional[str] = None
    
    class Config:
        from_attributes = True


class AlertaUpdate(BaseModel):
    lido: bool


# =============================================================================
# DASHBOARD
# =============================================================================

class DashboardStats(BaseModel):
    """Estatísticas gerais do dashboard."""
    total_empresas: int
    empresas_ativas: int
    empresas_criticas: int
    empresas_atencao: int
    empresas_saudaveis: int
    empresas_sem_analise: int
    alertas_pendentes: int
    score_medio_portfolio: float
    evolucao_scores: List[Dict]  # Últimos 6 meses
    distribuicao_setores: List[Dict]
    top_riscos: List[Dict]


class EmpresaDashboard(BaseModel):
    """Dados de empresa para dashboard."""
    id: int
    razao_social: str
    nome_fantasia: Optional[str]
    cnpj: Optional[str]
    setor: Optional[str]
    score: Optional[int]
    status: Optional[str]
    tendencia: Optional[str]  # up, down, stable
    variacao_score: Optional[int]  # vs análise anterior
    alertas_pendentes: int
    ultima_analise: Optional[datetime]
    ultimo_faturamento: Optional[float]
    variacao_faturamento: Optional[float]


# =============================================================================
# COMPARATIVO
# =============================================================================

class ComparativoEmpresas(BaseModel):
    """Comparativo entre empresas."""
    empresas: List[Dict]
    metricas: List[str]
    periodo: str
