#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelos de Multi-Tenancy - Sistema Contábil
============================================

Organizações, Papéis, Permissões, Convites e Audit Log
"""

import json
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, Index, UniqueConstraint, func, and_, or_, desc
)
from sqlalchemy.orm import relationship, Session

# Importa Base do database principal
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import Base, get_db


# =============================================================================
# MODELO: Organização
# =============================================================================

class Organizacao(Base):
    """Modelo de organização (escritório contábil)."""
    __tablename__ = 'organizacoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    cnpj = Column(String(20))
    email = Column(String(255))
    telefone = Column(String(50))
    endereco = Column(String(500))
    cidade = Column(String(100))
    estado = Column(String(2))
    logo_url = Column(String(500))
    cor_primaria = Column(String(7), default='#3B82F6')
    
    # Plano e limites
    plano = Column(String(50), default='free')
    max_usuarios = Column(Integer, default=1)
    max_empresas = Column(Integer, default=5)
    ativo = Column(Boolean, default=True)
    trial_ends_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)
    
    # Relacionamentos
    membros = relationship("MembroOrganizacao", back_populates="organizacao")
    convites = relationship("Convite", back_populates="organizacao")
    audit_logs = relationship("AuditLog", back_populates="organizacao")
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nome': self.nome,
            'slug': self.slug,
            'cnpj': self.cnpj,
            'email': self.email,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'cidade': self.cidade,
            'estado': self.estado,
            'logo_url': self.logo_url,
            'cor_primaria': self.cor_primaria,
            'plano': self.plano,
            'max_usuarios': self.max_usuarios,
            'max_empresas': self.max_empresas,
            'ativo': self.ativo,
            'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# MODELO: Papel
# =============================================================================

class Papel(Base):
    """Modelo de papel (role)."""
    __tablename__ = 'papeis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False)
    descricao = Column(String(255))
    nivel = Column(Integer, default=0)  # 0=cliente, 10=assistente, 20=contador, 30=admin, 99=owner
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    permissoes = relationship("Permissao", back_populates="papel")
    membros = relationship("MembroOrganizacao", back_populates="papel")
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'nivel': self.nivel,
            'is_system': self.is_system
        }


# =============================================================================
# MODELO: Membro da Organização
# =============================================================================

class MembroOrganizacao(Base):
    """Modelo de membro da organização."""
    __tablename__ = 'membros_organizacao'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organizacao_id = Column(Integer, ForeignKey('organizacoes.id'), nullable=False)
    contador_id = Column(Integer, ForeignKey('contadores.id'), nullable=False)
    papel_id = Column(Integer, ForeignKey('papeis.id'), nullable=False)
    is_default = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    organizacao = relationship("Organizacao", back_populates="membros")
    papel = relationship("Papel", back_populates="membros")
    
    __table_args__ = (
        UniqueConstraint('organizacao_id', 'contador_id', name='uq_membro_org_contador'),
        Index('idx_membros_org', 'organizacao_id'),
        Index('idx_membros_contador', 'contador_id'),
    )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'organizacao_id': self.organizacao_id,
            'contador_id': self.contador_id,
            'papel_id': self.papel_id,
            'papel_nome': self.papel.nome if self.papel else None,
            'is_default': self.is_default,
            'ativo': self.ativo,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }


# =============================================================================
# MODELO: Permissão
# =============================================================================

class Permissao(Base):
    """Modelo de permissão."""
    __tablename__ = 'permissoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    papel_id = Column(Integer, ForeignKey('papeis.id'), nullable=False)
    recurso = Column(String(50), nullable=False)
    acao = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    papel = relationship("Papel", back_populates="permissoes")
    
    __table_args__ = (
        UniqueConstraint('papel_id', 'recurso', 'acao', name='uq_permissao'),
    )


# =============================================================================
# MODELO: Convite
# =============================================================================

class Convite(Base):
    """Modelo de convite."""
    __tablename__ = 'convites'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organizacao_id = Column(Integer, ForeignKey('organizacoes.id'), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    papel_id = Column(Integer, ForeignKey('papeis.id'), nullable=False)
    token = Column(String(100), unique=True, nullable=False, index=True)
    convidado_por = Column(Integer, ForeignKey('contadores.id'), nullable=False)
    mensagem = Column(Text)
    status = Column(String(20), default='pendente')
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    organizacao = relationship("Organizacao", back_populates="convites")
    papel = relationship("Papel")
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'organizacao_id': self.organizacao_id,
            'organizacao_nome': self.organizacao.nome if self.organizacao else None,
            'email': self.email,
            'papel_id': self.papel_id,
            'papel_nome': self.papel.nome if self.papel else None,
            'status': self.status,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# MODELO: Audit Log
# =============================================================================

class AuditLog(Base):
    """Modelo de log de auditoria."""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organizacao_id = Column(Integer, ForeignKey('organizacoes.id'))
    contador_id = Column(Integer, ForeignKey('contadores.id'))
    acao = Column(String(50), nullable=False)
    recurso = Column(String(50), nullable=False)
    recurso_id = Column(Integer)
    detalhes = Column(Text)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    organizacao = relationship("Organizacao", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_org', 'organizacao_id'),
        Index('idx_audit_contador', 'contador_id'),
        Index('idx_audit_acao', 'acao'),
        Index('idx_audit_recurso', 'recurso', 'recurso_id'),
        Index('idx_audit_created', 'created_at'),
    )
    
    def to_dict(self) -> dict:
        detalhes_dict = {}
        if self.detalhes:
            try:
                detalhes_dict = json.loads(self.detalhes)
            except:
                pass
        
        return {
            'id': self.id,
            'organizacao_id': self.organizacao_id,
            'contador_id': self.contador_id,
            'acao': self.acao,
            'recurso': self.recurso,
            'recurso_id': self.recurso_id,
            'detalhes': detalhes_dict,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# FUNÇÕES DE SERVIÇO
# =============================================================================

def gerar_slug(nome: str) -> str:
    """Gera slug único a partir do nome."""
    import re
    slug = nome.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug[:50]


def criar_organizacao(
    nome: str,
    owner_id: int,
    cnpj: str = None,
    email: str = None,
    plano: str = 'free'
) -> Dict:
    """Cria uma nova organização e adiciona o owner."""
    
    with get_db() as db:
        # Gera slug único
        base_slug = gerar_slug(nome)
        slug = base_slug
        counter = 1
        while db.query(Organizacao).filter(Organizacao.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Define limites por plano
        limites = {
            'free': {'usuarios': 1, 'empresas': 5},
            'starter': {'usuarios': 3, 'empresas': 20},
            'pro': {'usuarios': 10, 'empresas': 100},
            'enterprise': {'usuarios': 999, 'empresas': 9999}
        }
        
        limite = limites.get(plano, limites['free'])
        
        # Cria organização
        org = Organizacao(
            nome=nome,
            slug=slug,
            cnpj=cnpj,
            email=email,
            plano=plano,
            max_usuarios=limite['usuarios'],
            max_empresas=limite['empresas'],
            trial_ends_at=datetime.now() + timedelta(days=14) if plano == 'free' else None
        )
        db.add(org)
        db.flush()
        
        # Busca papel owner
        papel_owner = db.query(Papel).filter(Papel.nome == 'owner').first()
        
        # Adiciona owner como membro
        membro = MembroOrganizacao(
            organizacao_id=org.id,
            contador_id=owner_id,
            papel_id=papel_owner.id,
            is_default=True
        )
        db.add(membro)
        
        # Log
        log = AuditLog(
            organizacao_id=org.id,
            contador_id=owner_id,
            acao='create',
            recurso='organizacao',
            recurso_id=org.id,
            detalhes=json.dumps({'nome': nome, 'plano': plano})
        )
        db.add(log)
        
        return org.to_dict()


def obter_organizacao(org_id: int, user_id: int = None) -> Optional[Dict]:
    """Obtém uma organização."""
    
    with get_db() as db:
        org = db.query(Organizacao).filter(
            Organizacao.id == org_id,
            Organizacao.deleted_at.is_(None)
        ).first()
        
        if not org:
            return None
        
        # Verifica se usuário tem acesso
        if user_id:
            membro = db.query(MembroOrganizacao).filter(
                MembroOrganizacao.organizacao_id == org_id,
                MembroOrganizacao.contador_id == user_id,
                MembroOrganizacao.ativo == True
            ).first()
            
            if not membro:
                return None
        
        org_dict = org.to_dict()
        
        # Conta membros e empresas
        org_dict['total_membros'] = db.query(MembroOrganizacao).filter(
            MembroOrganizacao.organizacao_id == org_id,
            MembroOrganizacao.ativo == True
        ).count()
        
        from data.database import Empresa
        org_dict['total_empresas'] = db.query(Empresa).filter(
            Empresa.organizacao_id == org_id,
            Empresa.ativo == True,
            Empresa.deleted_at.is_(None)
        ).count()
        
        return org_dict


def listar_organizacoes_usuario(user_id: int) -> List[Dict]:
    """Lista organizações do usuário."""
    
    with get_db() as db:
        membros = db.query(MembroOrganizacao).filter(
            MembroOrganizacao.contador_id == user_id,
            MembroOrganizacao.ativo == True
        ).all()
        
        result = []
        for m in membros:
            if m.organizacao and not m.organizacao.deleted_at:
                org_dict = m.organizacao.to_dict()
                org_dict['papel'] = m.papel.nome if m.papel else None
                org_dict['papel_nivel'] = m.papel.nivel if m.papel else 0
                org_dict['is_default'] = m.is_default
                result.append(org_dict)
        
        return result


def listar_membros_organizacao(org_id: int) -> List[Dict]:
    """Lista membros de uma organização."""
    
    with get_db() as db:
        from data.database import Contador
        
        membros = db.query(MembroOrganizacao, Contador).join(
            Contador, MembroOrganizacao.contador_id == Contador.id
        ).filter(
            MembroOrganizacao.organizacao_id == org_id,
            MembroOrganizacao.ativo == True
        ).all()
        
        result = []
        for m, c in membros:
            result.append({
                'id': m.id,
                'contador_id': c.id,
                'nome': c.nome,
                'email': c.email,
                'papel_id': m.papel_id,
                'papel_nome': m.papel.nome if m.papel else None,
                'papel_nivel': m.papel.nivel if m.papel else 0,
                'is_default': m.is_default,
                'joined_at': m.joined_at.isoformat() if m.joined_at else None
            })
        
        return sorted(result, key=lambda x: -x['papel_nivel'])


def criar_convite(
    org_id: int,
    email: str,
    papel_id: int,
    convidado_por: int,
    mensagem: str = None
) -> Dict:
    """Cria um convite."""
    
    with get_db() as db:
        # Verifica se já existe convite pendente
        existing = db.query(Convite).filter(
            Convite.organizacao_id == org_id,
            Convite.email == email,
            Convite.status == 'pendente',
            Convite.expires_at > datetime.now()
        ).first()
        
        if existing:
            raise ValueError("Já existe um convite pendente para este email")
        
        # Verifica se usuário já é membro
        from data.database import Contador
        contador = db.query(Contador).filter(Contador.email == email).first()
        if contador:
            membro = db.query(MembroOrganizacao).filter(
                MembroOrganizacao.organizacao_id == org_id,
                MembroOrganizacao.contador_id == contador.id
            ).first()
            if membro:
                raise ValueError("Este usuário já é membro da organização")
        
        # Cria convite
        convite = Convite(
            organizacao_id=org_id,
            email=email,
            papel_id=papel_id,
            token=secrets.token_urlsafe(32),
            convidado_por=convidado_por,
            mensagem=mensagem,
            expires_at=datetime.now() + timedelta(days=7)
        )
        db.add(convite)
        
        # Log
        log = AuditLog(
            organizacao_id=org_id,
            contador_id=convidado_por,
            acao='create',
            recurso='convite',
            recurso_id=convite.id,
            detalhes=json.dumps({'email': email, 'papel_id': papel_id})
        )
        db.add(log)
        
        db.flush()
        return convite.to_dict()


def aceitar_convite(token: str, user_id: int) -> Dict:
    """Aceita um convite."""
    
    with get_db() as db:
        convite = db.query(Convite).filter(
            Convite.token == token,
            Convite.status == 'pendente',
            Convite.expires_at > datetime.now()
        ).first()
        
        if not convite:
            raise ValueError("Convite inválido ou expirado")
        
        # Verifica se email confere
        from data.database import Contador
        contador = db.query(Contador).filter(Contador.id == user_id).first()
        if not contador or contador.email != convite.email:
            raise ValueError("Este convite não é para você")
        
        # Verifica se já é membro
        existing = db.query(MembroOrganizacao).filter(
            MembroOrganizacao.organizacao_id == convite.organizacao_id,
            MembroOrganizacao.contador_id == user_id
        ).first()
        
        if existing:
            existing.ativo = True
            existing.papel_id = convite.papel_id
        else:
            membro = MembroOrganizacao(
                organizacao_id=convite.organizacao_id,
                contador_id=user_id,
                papel_id=convite.papel_id
            )
            db.add(membro)
        
        # Atualiza convite
        convite.status = 'aceito'
        convite.accepted_at = datetime.now()
        
        # Log
        log = AuditLog(
            organizacao_id=convite.organizacao_id,
            contador_id=user_id,
            acao='accept',
            recurso='convite',
            recurso_id=convite.id
        )
        db.add(log)
        
        return convite.organizacao.to_dict()


def verificar_permissao(user_id: int, org_id: int, recurso: str, acao: str) -> bool:
    """Verifica se usuário tem permissão."""
    
    with get_db() as db:
        membro = db.query(MembroOrganizacao).filter(
            MembroOrganizacao.organizacao_id == org_id,
            MembroOrganizacao.contador_id == user_id,
            MembroOrganizacao.ativo == True
        ).first()
        
        if not membro:
            return False
        
        permissao = db.query(Permissao).filter(
            Permissao.papel_id == membro.papel_id,
            Permissao.recurso == recurso,
            Permissao.acao == acao
        ).first()
        
        return permissao is not None


def obter_papel_usuario(user_id: int, org_id: int) -> Optional[Dict]:
    """Obtém papel do usuário na organização."""
    
    with get_db() as db:
        membro = db.query(MembroOrganizacao).filter(
            MembroOrganizacao.organizacao_id == org_id,
            MembroOrganizacao.contador_id == user_id,
            MembroOrganizacao.ativo == True
        ).first()
        
        if not membro:
            return None
        
        return membro.papel.to_dict() if membro.papel else None


def registrar_audit(
    org_id: int,
    user_id: int,
    acao: str,
    recurso: str,
    recurso_id: int = None,
    detalhes: dict = None,
    ip: str = None,
    user_agent: str = None
):
    """Registra uma ação no audit log."""
    
    with get_db() as db:
        log = AuditLog(
            organizacao_id=org_id,
            contador_id=user_id,
            acao=acao,
            recurso=recurso,
            recurso_id=recurso_id,
            detalhes=json.dumps(detalhes) if detalhes else None,
            ip_address=ip,
            user_agent=user_agent
        )
        db.add(log)


def listar_audit_logs(org_id: int, limite: int = 50, offset: int = 0) -> List[Dict]:
    """Lista logs de auditoria."""
    
    with get_db() as db:
        from data.database import Contador
        
        logs = db.query(AuditLog, Contador).outerjoin(
            Contador, AuditLog.contador_id == Contador.id
        ).filter(
            AuditLog.organizacao_id == org_id
        ).order_by(
            desc(AuditLog.created_at)
        ).offset(offset).limit(limite).all()
        
        result = []
        for log, contador in logs:
            log_dict = log.to_dict()
            log_dict['usuario_nome'] = contador.nome if contador else 'Sistema'
            result.append(log_dict)
        
        return result


def definir_organizacao_padrao(user_id: int, org_id: int):
    """Define organização padrão do usuário."""
    
    with get_db() as db:
        # Remove padrão anterior
        db.query(MembroOrganizacao).filter(
            MembroOrganizacao.contador_id == user_id
        ).update({"is_default": False})
        
        # Define nova padrão
        db.query(MembroOrganizacao).filter(
            MembroOrganizacao.contador_id == user_id,
            MembroOrganizacao.organizacao_id == org_id
        ).update({"is_default": True})


def listar_papeis() -> List[Dict]:
    """Lista todos os papéis."""
    
    with get_db() as db:
        papeis = db.query(Papel).order_by(desc(Papel.nivel)).all()
        return [p.to_dict() for p in papeis]
