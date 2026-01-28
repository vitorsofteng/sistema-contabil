#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Billing - Sistema Contábil
======================================

Planos, Assinaturas, Faturas e Integração Stripe
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, Index, UniqueConstraint, func, and_, or_, desc
)
from sqlalchemy.orm import relationship, Session

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import Base, get_db

# Configuração Stripe
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
STRIPE_AVAILABLE = False

try:
    import stripe
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
        STRIPE_AVAILABLE = True
except ImportError:
    stripe = None


# =============================================================================
# MODELOS
# =============================================================================

class Plano(Base):
    """Modelo de plano."""
    __tablename__ = 'planos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    preco_mensal = Column(Float, default=0)
    preco_anual = Column(Float, default=0)
    moeda = Column(String(3), default='BRL')
    
    # Limites
    max_usuarios = Column(Integer, default=1)
    max_empresas = Column(Integer, default=5)
    max_analises_mes = Column(Integer, default=10)
    max_storage_mb = Column(Integer, default=100)
    
    # Features
    permite_api = Column(Boolean, default=False)
    permite_whitelabel = Column(Boolean, default=False)
    permite_relatorios_pdf = Column(Boolean, default=True)
    permite_exportar_excel = Column(Boolean, default=False)
    suporte_prioritario = Column(Boolean, default=False)
    
    # Stripe
    stripe_price_id_mensal = Column(String(100))
    stripe_price_id_anual = Column(String(100))
    
    ativo = Column(Boolean, default=True)
    ordem = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco_mensal': self.preco_mensal,
            'preco_anual': self.preco_anual,
            'preco_mensal_formatado': f"R$ {self.preco_mensal:.2f}".replace('.', ','),
            'preco_anual_formatado': f"R$ {self.preco_anual:.2f}".replace('.', ','),
            'economia_anual': round((self.preco_mensal * 12 - self.preco_anual) if self.preco_mensal > 0 else 0, 2),
            'moeda': self.moeda,
            'limites': {
                'usuarios': self.max_usuarios,
                'empresas': self.max_empresas,
                'analises_mes': self.max_analises_mes,
                'storage_mb': self.max_storage_mb
            },
            'features': {
                'api': self.permite_api,
                'whitelabel': self.permite_whitelabel,
                'relatorios_pdf': self.permite_relatorios_pdf,
                'exportar_excel': self.permite_exportar_excel,
                'suporte_prioritario': self.suporte_prioritario
            },
            'ativo': self.ativo
        }


class Assinatura(Base):
    """Modelo de assinatura."""
    __tablename__ = 'assinaturas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organizacao_id = Column(Integer, ForeignKey('organizacoes.id'), nullable=False, index=True)
    plano_id = Column(Integer, ForeignKey('planos.id'), nullable=False)
    
    status = Column(String(30), default='active')
    ciclo = Column(String(10), default='mensal')
    
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    canceled_at = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    
    stripe_customer_id = Column(String(100))
    stripe_subscription_id = Column(String(100), index=True)
    stripe_payment_method_id = Column(String(100))
    
    desconto_percentual = Column(Float, default=0)
    cupom_codigo = Column(String(50))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    plano = relationship("Plano")
    faturas = relationship("Fatura", back_populates="assinatura")
    
    @property
    def is_active(self) -> bool:
        return self.status in ('active', 'trialing')
    
    @property
    def is_trialing(self) -> bool:
        return self.status == 'trialing' and self.trial_end and self.trial_end > datetime.now()
    
    @property
    def dias_restantes_trial(self) -> int:
        if not self.is_trialing:
            return 0
        return max(0, (self.trial_end - datetime.now()).days)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'organizacao_id': self.organizacao_id,
            'plano': self.plano.to_dict() if self.plano else None,
            'status': self.status,
            'status_label': self._get_status_label(),
            'ciclo': self.ciclo,
            'is_active': self.is_active,
            'is_trialing': self.is_trialing,
            'dias_restantes_trial': self.dias_restantes_trial,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'desconto_percentual': self.desconto_percentual,
            'cupom_codigo': self.cupom_codigo,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def _get_status_label(self) -> str:
        labels = {
            'active': 'Ativa',
            'trialing': 'Período de Teste',
            'past_due': 'Pagamento Pendente',
            'canceled': 'Cancelada',
            'paused': 'Pausada'
        }
        return labels.get(self.status, self.status)


class Fatura(Base):
    """Modelo de fatura."""
    __tablename__ = 'faturas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    assinatura_id = Column(Integer, ForeignKey('assinaturas.id'), nullable=False, index=True)
    organizacao_id = Column(Integer, ForeignKey('organizacoes.id'), nullable=False, index=True)
    
    valor_bruto = Column(Float, nullable=False)
    desconto = Column(Float, default=0)
    valor_liquido = Column(Float, nullable=False)
    moeda = Column(String(3), default='BRL')
    
    status = Column(String(30), default='pending')
    data_vencimento = Column(DateTime, nullable=False)
    data_pagamento = Column(DateTime)
    
    stripe_invoice_id = Column(String(100), index=True)
    stripe_payment_intent_id = Column(String(100))
    stripe_charge_id = Column(String(100))
    
    pdf_url = Column(String(500))
    numero = Column(String(50))
    
    periodo_inicio = Column(DateTime)
    periodo_fim = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    assinatura = relationship("Assinatura", back_populates="faturas")
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'numero': self.numero or f'#{self.id:06d}',
            'valor_bruto': self.valor_bruto,
            'desconto': self.desconto,
            'valor_liquido': self.valor_liquido,
            'valor_formatado': f"R$ {self.valor_liquido:.2f}".replace('.', ','),
            'moeda': self.moeda,
            'status': self.status,
            'status_label': self._get_status_label(),
            'data_vencimento': self.data_vencimento.isoformat() if self.data_vencimento else None,
            'data_pagamento': self.data_pagamento.isoformat() if self.data_pagamento else None,
            'pdf_url': self.pdf_url,
            'periodo_inicio': self.periodo_inicio.isoformat() if self.periodo_inicio else None,
            'periodo_fim': self.periodo_fim.isoformat() if self.periodo_fim else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def _get_status_label(self) -> str:
        labels = {
            'pending': 'Pendente',
            'paid': 'Paga',
            'failed': 'Falhou',
            'refunded': 'Reembolsada',
            'canceled': 'Cancelada'
        }
        return labels.get(self.status, self.status)


class UsoMensal(Base):
    """Modelo de uso mensal."""
    __tablename__ = 'uso_mensal'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organizacao_id = Column(Integer, ForeignKey('organizacoes.id'), nullable=False)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    
    usuarios_ativos = Column(Integer, default=0)
    empresas_ativas = Column(Integer, default=0)
    analises_realizadas = Column(Integer, default=0)
    storage_usado_mb = Column(Float, default=0)
    api_calls = Column(Integer, default=0)
    relatorios_gerados = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('organizacao_id', 'ano', 'mes', name='uq_uso_org_periodo'),
        Index('idx_uso_org_periodo', 'organizacao_id', 'ano', 'mes'),
    )
    
    def to_dict(self) -> dict:
        return {
            'ano': self.ano,
            'mes': self.mes,
            'periodo': f"{self.ano}-{self.mes:02d}",
            'usuarios_ativos': self.usuarios_ativos,
            'empresas_ativas': self.empresas_ativas,
            'analises_realizadas': self.analises_realizadas,
            'storage_usado_mb': self.storage_usado_mb,
            'api_calls': self.api_calls,
            'relatorios_gerados': self.relatorios_gerados
        }


class Cupom(Base):
    """Modelo de cupom."""
    __tablename__ = 'cupons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    descricao = Column(String(255))
    tipo = Column(String(20), default='percentual')
    valor = Column(Float, nullable=False)
    max_usos = Column(Integer)
    usos_atual = Column(Integer, default=0)
    valido_ate = Column(DateTime)
    planos_validos = Column(String(255))
    ativo = Column(Boolean, default=True)
    stripe_coupon_id = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'codigo': self.codigo,
            'descricao': self.descricao,
            'tipo': self.tipo,
            'valor': self.valor,
            'desconto_texto': f"{self.valor}%" if self.tipo == 'percentual' else f"R$ {self.valor:.2f}",
            'max_usos': self.max_usos,
            'usos_restantes': (self.max_usos - self.usos_atual) if self.max_usos else None,
            'valido_ate': self.valido_ate.isoformat() if self.valido_ate else None,
            'ativo': self.ativo and (not self.valido_ate or self.valido_ate > datetime.now())
        }


class StripeWebhook(Base):
    """Log de webhooks Stripe."""
    __tablename__ = 'stripe_webhooks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(100), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text)
    processado = Column(Boolean, default=False)
    erro = Column(Text)
    created_at = Column(DateTime, default=func.now())


# =============================================================================
# FUNÇÕES DE SERVIÇO - PLANOS
# =============================================================================

def listar_planos(apenas_ativos: bool = True) -> List[Dict]:
    """Lista todos os planos."""
    with get_db() as db:
        query = db.query(Plano)
        if apenas_ativos:
            query = query.filter(Plano.ativo == True)
        planos = query.order_by(Plano.ordem).all()
        return [p.to_dict() for p in planos]


def obter_plano(codigo_ou_id) -> Optional[Dict]:
    """Obtém um plano por código ou ID."""
    with get_db() as db:
        if isinstance(codigo_ou_id, int):
            plano = db.query(Plano).filter(Plano.id == codigo_ou_id).first()
        else:
            plano = db.query(Plano).filter(Plano.codigo == codigo_ou_id).first()
        return plano.to_dict() if plano else None


# =============================================================================
# FUNÇÕES DE SERVIÇO - ASSINATURAS
# =============================================================================

def obter_assinatura_org(org_id: int) -> Optional[Dict]:
    """Obtém assinatura ativa de uma organização."""
    with get_db() as db:
        assinatura = db.query(Assinatura).filter(
            Assinatura.organizacao_id == org_id
        ).order_by(desc(Assinatura.created_at)).first()
        
        if not assinatura:
            # Cria assinatura free padrão
            plano_free = db.query(Plano).filter(Plano.codigo == 'free').first()
            if plano_free:
                assinatura = Assinatura(
                    organizacao_id=org_id,
                    plano_id=plano_free.id,
                    status='active',
                    current_period_start=datetime.now(),
                    current_period_end=datetime.now() + timedelta(days=365*100)  # "infinito"
                )
                db.add(assinatura)
                db.flush()
        
        return assinatura.to_dict() if assinatura else None


def criar_assinatura_trial(org_id: int, plano_codigo: str = 'pro', dias: int = 14) -> Dict:
    """Cria assinatura trial."""
    with get_db() as db:
        # Verifica se já tem assinatura
        existing = db.query(Assinatura).filter(
            Assinatura.organizacao_id == org_id,
            Assinatura.status.in_(['active', 'trialing'])
        ).first()
        
        if existing and existing.status == 'trialing':
            raise ValueError("Organização já está em período de teste")
        
        plano = db.query(Plano).filter(Plano.codigo == plano_codigo).first()
        if not plano:
            raise ValueError(f"Plano {plano_codigo} não encontrado")
        
        now = datetime.now()
        assinatura = Assinatura(
            organizacao_id=org_id,
            plano_id=plano.id,
            status='trialing',
            trial_start=now,
            trial_end=now + timedelta(days=dias),
            current_period_start=now,
            current_period_end=now + timedelta(days=dias)
        )
        db.add(assinatura)
        
        # Atualiza limites da organização
        from auth.multitenancy import Organizacao
        org = db.query(Organizacao).filter(Organizacao.id == org_id).first()
        if org:
            org.plano = plano_codigo
            org.max_usuarios = plano.max_usuarios
            org.max_empresas = plano.max_empresas
            org.trial_ends_at = now + timedelta(days=dias)
        
        db.flush()
        return assinatura.to_dict()


def iniciar_assinatura(
    org_id: int, 
    plano_codigo: str, 
    ciclo: str = 'mensal',
    cupom_codigo: str = None
) -> Dict:
    """Inicia uma assinatura paga."""
    with get_db() as db:
        plano = db.query(Plano).filter(Plano.codigo == plano_codigo).first()
        if not plano:
            raise ValueError(f"Plano {plano_codigo} não encontrado")
        
        # Verifica cupom
        desconto = 0
        if cupom_codigo:
            cupom = db.query(Cupom).filter(
                Cupom.codigo == cupom_codigo,
                Cupom.ativo == True
            ).first()
            if cupom and (not cupom.valido_ate or cupom.valido_ate > datetime.now()):
                if cupom.max_usos and cupom.usos_atual >= cupom.max_usos:
                    raise ValueError("Cupom esgotado")
                if cupom.planos_validos:
                    planos_validos = json.loads(cupom.planos_validos)
                    if plano_codigo not in planos_validos:
                        raise ValueError("Cupom não válido para este plano")
                desconto = cupom.valor
                cupom.usos_atual += 1
        
        now = datetime.now()
        periodo_fim = now + timedelta(days=30 if ciclo == 'mensal' else 365)
        
        # Cancela assinatura anterior se existir
        db.query(Assinatura).filter(
            Assinatura.organizacao_id == org_id,
            Assinatura.status.in_(['active', 'trialing'])
        ).update({'status': 'canceled', 'canceled_at': now})
        
        assinatura = Assinatura(
            organizacao_id=org_id,
            plano_id=plano.id,
            status='active',
            ciclo=ciclo,
            current_period_start=now,
            current_period_end=periodo_fim,
            desconto_percentual=desconto if cupom_codigo else 0,
            cupom_codigo=cupom_codigo
        )
        db.add(assinatura)
        
        # Atualiza limites da organização
        from auth.multitenancy import Organizacao
        org = db.query(Organizacao).filter(Organizacao.id == org_id).first()
        if org:
            org.plano = plano_codigo
            org.max_usuarios = plano.max_usuarios
            org.max_empresas = plano.max_empresas
            org.trial_ends_at = None
        
        # Cria fatura
        preco = plano.preco_mensal if ciclo == 'mensal' else plano.preco_anual
        valor_desconto = preco * (desconto / 100) if desconto > 0 else 0
        valor_final = preco - valor_desconto
        
        fatura = Fatura(
            assinatura_id=assinatura.id,
            organizacao_id=org_id,
            valor_bruto=preco,
            desconto=valor_desconto,
            valor_liquido=valor_final,
            status='pending',
            data_vencimento=now + timedelta(days=7),
            periodo_inicio=now,
            periodo_fim=periodo_fim
        )
        db.add(fatura)
        
        db.flush()
        return assinatura.to_dict()


def cancelar_assinatura(org_id: int, imediatamente: bool = False) -> Dict:
    """Cancela assinatura."""
    with get_db() as db:
        assinatura = db.query(Assinatura).filter(
            Assinatura.organizacao_id == org_id,
            Assinatura.status.in_(['active', 'trialing'])
        ).first()
        
        if not assinatura:
            raise ValueError("Nenhuma assinatura ativa encontrada")
        
        now = datetime.now()
        
        if imediatamente:
            assinatura.status = 'canceled'
            assinatura.canceled_at = now
            
            # Volta para plano free
            plano_free = db.query(Plano).filter(Plano.codigo == 'free').first()
            from auth.multitenancy import Organizacao
            org = db.query(Organizacao).filter(Organizacao.id == org_id).first()
            if org and plano_free:
                org.plano = 'free'
                org.max_usuarios = plano_free.max_usuarios
                org.max_empresas = plano_free.max_empresas
        else:
            assinatura.cancel_at_period_end = True
        
        return assinatura.to_dict()


def alterar_plano(org_id: int, novo_plano_codigo: str, ciclo: str = None) -> Dict:
    """Altera o plano da assinatura (upgrade/downgrade)."""
    with get_db() as db:
        assinatura = db.query(Assinatura).filter(
            Assinatura.organizacao_id == org_id,
            Assinatura.status.in_(['active', 'trialing'])
        ).first()
        
        if not assinatura:
            raise ValueError("Nenhuma assinatura ativa")
        
        novo_plano = db.query(Plano).filter(Plano.codigo == novo_plano_codigo).first()
        if not novo_plano:
            raise ValueError(f"Plano {novo_plano_codigo} não encontrado")
        
        plano_atual = assinatura.plano
        
        # Determina se é upgrade ou downgrade
        is_upgrade = novo_plano.preco_mensal > plano_atual.preco_mensal
        
        assinatura.plano_id = novo_plano.id
        if ciclo:
            assinatura.ciclo = ciclo
        
        # Atualiza organização
        from auth.multitenancy import Organizacao
        org = db.query(Organizacao).filter(Organizacao.id == org_id).first()
        if org:
            org.plano = novo_plano_codigo
            org.max_usuarios = novo_plano.max_usuarios
            org.max_empresas = novo_plano.max_empresas
        
        # Se upgrade, gera fatura pro-rata
        if is_upgrade and assinatura.status == 'active':
            dias_restantes = (assinatura.current_period_end - datetime.now()).days
            preco_diario_novo = novo_plano.preco_mensal / 30
            preco_diario_atual = plano_atual.preco_mensal / 30
            valor_prorata = (preco_diario_novo - preco_diario_atual) * dias_restantes
            
            if valor_prorata > 0:
                fatura = Fatura(
                    assinatura_id=assinatura.id,
                    organizacao_id=org_id,
                    valor_bruto=valor_prorata,
                    desconto=0,
                    valor_liquido=valor_prorata,
                    status='pending',
                    data_vencimento=datetime.now() + timedelta(days=7),
                    periodo_inicio=datetime.now(),
                    periodo_fim=assinatura.current_period_end
                )
                db.add(fatura)
        
        return assinatura.to_dict()


# =============================================================================
# FUNÇÕES DE SERVIÇO - FATURAS
# =============================================================================

def listar_faturas(org_id: int, limite: int = 12) -> List[Dict]:
    """Lista faturas de uma organização."""
    with get_db() as db:
        faturas = db.query(Fatura).filter(
            Fatura.organizacao_id == org_id
        ).order_by(desc(Fatura.created_at)).limit(limite).all()
        
        return [f.to_dict() for f in faturas]


def obter_fatura(fatura_id: int, org_id: int) -> Optional[Dict]:
    """Obtém uma fatura específica."""
    with get_db() as db:
        fatura = db.query(Fatura).filter(
            Fatura.id == fatura_id,
            Fatura.organizacao_id == org_id
        ).first()
        return fatura.to_dict() if fatura else None


def marcar_fatura_paga(fatura_id: int, stripe_charge_id: str = None) -> Dict:
    """Marca uma fatura como paga."""
    with get_db() as db:
        fatura = db.query(Fatura).filter(Fatura.id == fatura_id).first()
        if not fatura:
            raise ValueError("Fatura não encontrada")
        
        fatura.status = 'paid'
        fatura.data_pagamento = datetime.now()
        if stripe_charge_id:
            fatura.stripe_charge_id = stripe_charge_id
        
        return fatura.to_dict()


# =============================================================================
# FUNÇÕES DE SERVIÇO - USO
# =============================================================================

def obter_uso_atual(org_id: int) -> Dict:
    """Obtém uso do mês atual."""
    now = datetime.now()
    with get_db() as db:
        uso = db.query(UsoMensal).filter(
            UsoMensal.organizacao_id == org_id,
            UsoMensal.ano == now.year,
            UsoMensal.mes == now.month
        ).first()
        
        if not uso:
            uso = UsoMensal(
                organizacao_id=org_id,
                ano=now.year,
                mes=now.month
            )
            db.add(uso)
            db.flush()
        
        return uso.to_dict()


def incrementar_uso(org_id: int, campo: str, quantidade: int = 1):
    """Incrementa um campo de uso."""
    now = datetime.now()
    with get_db() as db:
        uso = db.query(UsoMensal).filter(
            UsoMensal.organizacao_id == org_id,
            UsoMensal.ano == now.year,
            UsoMensal.mes == now.month
        ).first()
        
        if not uso:
            uso = UsoMensal(
                organizacao_id=org_id,
                ano=now.year,
                mes=now.month
            )
            db.add(uso)
        
        valor_atual = getattr(uso, campo, 0) or 0
        setattr(uso, campo, valor_atual + quantidade)


def verificar_limite(org_id: int, recurso: str) -> bool:
    """Verifica se organização atingiu limite."""
    with get_db() as db:
        assinatura = db.query(Assinatura).filter(
            Assinatura.organizacao_id == org_id,
            Assinatura.status.in_(['active', 'trialing'])
        ).first()
        
        if not assinatura or not assinatura.plano:
            return False
        
        plano = assinatura.plano
        uso = obter_uso_atual(org_id)
        
        limites = {
            'analises': (uso.get('analises_realizadas', 0), plano.max_analises_mes),
            'empresas': (uso.get('empresas_ativas', 0), plano.max_empresas),
            'usuarios': (uso.get('usuarios_ativos', 0), plano.max_usuarios),
            'storage': (uso.get('storage_usado_mb', 0), plano.max_storage_mb)
        }
        
        if recurso in limites:
            atual, maximo = limites[recurso]
            return atual < maximo
        
        return True


# =============================================================================
# FUNÇÕES DE SERVIÇO - CUPONS
# =============================================================================

def validar_cupom(codigo: str, plano_codigo: str = None) -> Optional[Dict]:
    """Valida um cupom."""
    with get_db() as db:
        cupom = db.query(Cupom).filter(
            Cupom.codigo == codigo.upper(),
            Cupom.ativo == True
        ).first()
        
        if not cupom:
            return None
        
        if cupom.valido_ate and cupom.valido_ate < datetime.now():
            return None
        
        if cupom.max_usos and cupom.usos_atual >= cupom.max_usos:
            return None
        
        if plano_codigo and cupom.planos_validos:
            planos_validos = json.loads(cupom.planos_validos)
            if plano_codigo not in planos_validos:
                return None
        
        return cupom.to_dict()


# =============================================================================
# FUNÇÕES STRIPE
# =============================================================================

def criar_checkout_session(org_id: int, plano_codigo: str, ciclo: str = 'mensal', success_url: str = None, cancel_url: str = None) -> Dict:
    """Cria sessão de checkout Stripe."""
    if not STRIPE_AVAILABLE:
        raise ValueError("Stripe não configurado")
    
    with get_db() as db:
        plano = db.query(Plano).filter(Plano.codigo == plano_codigo).first()
        if not plano:
            raise ValueError(f"Plano {plano_codigo} não encontrado")
        
        price_id = plano.stripe_price_id_mensal if ciclo == 'mensal' else plano.stripe_price_id_anual
        if not price_id:
            raise ValueError("Plano não configurado no Stripe")
        
        # Busca ou cria customer
        assinatura = db.query(Assinatura).filter(
            Assinatura.organizacao_id == org_id
        ).first()
        
        customer_id = assinatura.stripe_customer_id if assinatura else None
        
        if not customer_id:
            from auth.multitenancy import Organizacao
            org = db.query(Organizacao).filter(Organizacao.id == org_id).first()
            customer = stripe.Customer.create(
                name=org.nome,
                email=org.email,
                metadata={'org_id': org_id}
            )
            customer_id = customer.id
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=success_url or 'http://localhost/configuracoes/plano?success=true',
            cancel_url=cancel_url or 'http://localhost/configuracoes/plano?canceled=true',
            metadata={'org_id': org_id, 'plano': plano_codigo, 'ciclo': ciclo}
        )
        
        return {'checkout_url': session.url, 'session_id': session.id}


def processar_webhook(payload: str, sig_header: str) -> Dict:
    """Processa webhook do Stripe."""
    if not STRIPE_AVAILABLE:
        raise ValueError("Stripe não configurado")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise ValueError(f"Webhook inválido: {str(e)}")
    
    with get_db() as db:
        # Salva webhook
        webhook_log = StripeWebhook(
            event_id=event['id'],
            event_type=event['type'],
            payload=payload
        )
        db.add(webhook_log)
        
        try:
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                org_id = int(session['metadata']['org_id'])
                plano = session['metadata']['plano']
                ciclo = session['metadata']['ciclo']
                
                # Ativa assinatura
                assinatura = db.query(Assinatura).filter(
                    Assinatura.organizacao_id == org_id
                ).first()
                
                if assinatura:
                    assinatura.stripe_customer_id = session['customer']
                    assinatura.stripe_subscription_id = session['subscription']
                    assinatura.status = 'active'
            
            elif event['type'] == 'invoice.paid':
                invoice = event['data']['object']
                subscription_id = invoice.get('subscription')
                
                assinatura = db.query(Assinatura).filter(
                    Assinatura.stripe_subscription_id == subscription_id
                ).first()
                
                if assinatura:
                    # Atualiza período
                    assinatura.current_period_end = datetime.fromtimestamp(
                        invoice['lines']['data'][0]['period']['end']
                    )
                    
                    # Marca fatura como paga
                    fatura = db.query(Fatura).filter(
                        Fatura.stripe_invoice_id == invoice['id']
                    ).first()
                    if fatura:
                        fatura.status = 'paid'
                        fatura.data_pagamento = datetime.now()
            
            elif event['type'] == 'invoice.payment_failed':
                invoice = event['data']['object']
                subscription_id = invoice.get('subscription')
                
                assinatura = db.query(Assinatura).filter(
                    Assinatura.stripe_subscription_id == subscription_id
                ).first()
                
                if assinatura:
                    assinatura.status = 'past_due'
            
            elif event['type'] == 'customer.subscription.deleted':
                subscription = event['data']['object']
                
                assinatura = db.query(Assinatura).filter(
                    Assinatura.stripe_subscription_id == subscription['id']
                ).first()
                
                if assinatura:
                    assinatura.status = 'canceled'
                    assinatura.canceled_at = datetime.now()
            
            webhook_log.processado = True
            
        except Exception as e:
            webhook_log.erro = str(e)
            raise
        
        return {'status': 'ok', 'event_type': event['type']}
