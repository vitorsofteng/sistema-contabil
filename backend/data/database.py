#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Banco de Dados - Sistema Contábil com SQLAlchemy
================================================

Suporta:
- PostgreSQL (produção)
- SQLite (fallback/desenvolvimento)
- Connection pooling
- Soft delete
- Timestamps automáticos

Versão: 2.0 (F02 - PostgreSQL)
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, Index, event, func, and_, or_, desc, text
)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.pool import QueuePool

# =============================================================================
# CONFIGURAÇÃO DO BANCO
# =============================================================================

class DatabaseConfig:
    """Configurações do banco de dados."""
    
    ENV = os.environ.get('ENV', 'development')
    USE_POSTGRES = os.environ.get('USE_POSTGRES', 'false').lower() == 'true'
    
    # PostgreSQL
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'contabil')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'contabil123')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'postgres')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'contabil_db')
    
    DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    
    # SQLite fallback
    SQLITE_PATH = os.environ.get('SQLITE_PATH', 'data/contabil.db')
    SQLITE_URL = f"sqlite:///{SQLITE_PATH}"
    
    # Pool (PostgreSQL)
    POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '10'))
    MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', '20'))
    
    @classmethod
    def get_url(cls):
        if cls.USE_POSTGRES:
            return cls.DATABASE_URL
        # Cria diretório para SQLite se necessário
        db_dir = os.path.dirname(cls.SQLITE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        return cls.SQLITE_URL


# =============================================================================
# ENGINE E SESSÃO
# =============================================================================

def create_db_engine():
    """Cria engine SQLAlchemy."""
    url = DatabaseConfig.get_url()
    is_sqlite = url.startswith('sqlite')
    
    if is_sqlite:
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False
        )
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=DatabaseConfig.POOL_SIZE,
            max_overflow=DatabaseConfig.MAX_OVERFLOW,
            pool_pre_ping=True,
            echo=False
        )
    
    return engine


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@contextmanager
def get_db():
    """Context manager para sessão do banco."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# =============================================================================
# MODELOS
# =============================================================================

class Contador(Base):
    """Modelo de contador (usuário)."""
    __tablename__ = 'contadores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    telefone = Column(String(50))
    crc = Column(String(50))
    ativo = Column(Boolean, default=True)
    
    # Segurança
    password_changed_at = Column(DateTime)
    reset_token = Column(String(500))
    reset_token_expires = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)
    
    # Relacionamentos
    empresas = relationship("Empresa", back_populates="contador")
    sessoes = relationship("Sessao", back_populates="contador")


class Sessao(Base):
    """Modelo de sessão."""
    __tablename__ = 'sessoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contador_id = Column(Integer, ForeignKey('contadores.id'), nullable=False)
    token_jti = Column(String(100), unique=True, nullable=False, index=True)
    refresh_token_jti = Column(String(100), unique=True, index=True)
    device_info = Column(String(500))
    ip_address = Column(String(50))
    expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime, default=func.now())
    
    contador = relationship("Contador", back_populates="sessoes")


class Empresa(Base):
    """Modelo de empresa."""
    __tablename__ = 'empresas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contador_id = Column(Integer, ForeignKey('contadores.id'), nullable=False, index=True)
    organizacao_id = Column(Integer, ForeignKey('organizacoes.id'), nullable=True, index=True)
    razao_social = Column(String(255), nullable=False)
    nome_fantasia = Column(String(255))
    cnpj = Column(String(20), index=True)
    inscricao_estadual = Column(String(50))
    regime_tributario = Column(String(50))
    setor = Column(String(100))
    endereco = Column(String(500))
    cidade = Column(String(100))
    estado = Column(String(2))
    telefone = Column(String(50))
    email = Column(String(255))
    contato_nome = Column(String(255))
    observacoes = Column(Text)
    ativo = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)
    
    contador = relationship("Contador", back_populates="empresas")
    dados_mensais = relationship("DadosMensal", back_populates="empresa", cascade="all, delete-orphan")
    analises = relationship("Analise", back_populates="empresa", cascade="all, delete-orphan")


class DadosMensal(Base):
    """Modelo de dados mensais - expandido para balancetes completos."""
    __tablename__ = 'dados_mensais'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False, index=True)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    
    # Campos básicos (compatibilidade)
    receita = Column(Float, default=0)
    custos = Column(Float, default=0)
    despesas = Column(Float, default=0)
    impostos = Column(Float, default=0)
    folha = Column(Float, default=0)
    caixa = Column(Float, default=0)
    
    # Campos expandidos - Balanço Patrimonial
    ativo_total = Column(Float, default=0)
    ativo_circulante = Column(Float, default=0)
    disponivel = Column(Float, default=0)
    bancos = Column(Float, default=0)
    clientes = Column(Float, default=0)
    estoques = Column(Float, default=0)
    ativo_nao_circulante = Column(Float, default=0)
    imobilizado = Column(Float, default=0)
    
    passivo_total = Column(Float, default=0)
    passivo_circulante = Column(Float, default=0)
    fornecedores = Column(Float, default=0)
    obrigacoes_trabalhistas = Column(Float, default=0)
    obrigacoes_tributarias = Column(Float, default=0)
    emprestimos_cp = Column(Float, default=0)
    passivo_nao_circulante = Column(Float, default=0)
    emprestimos_lp = Column(Float, default=0)
    
    patrimonio_liquido = Column(Float, default=0)
    capital_social = Column(Float, default=0)
    lucros_acumulados = Column(Float, default=0)
    
    # Campos expandidos - DRE
    receita_bruta = Column(Float, default=0)
    receita_servicos = Column(Float, default=0)
    deducoes_receita = Column(Float, default=0)
    receita_liquida = Column(Float, default=0)
    custos_total = Column(Float, default=0)
    lucro_bruto = Column(Float, default=0)
    despesas_operacionais = Column(Float, default=0)
    despesas_financeiras = Column(Float, default=0)
    receitas_financeiras = Column(Float, default=0)
    lucro_liquido = Column(Float, default=0)
    
    # Impostos detalhados
    iss = Column(Float, default=0)
    pis = Column(Float, default=0)
    cofins = Column(Float, default=0)
    irpj = Column(Float, default=0)
    csll = Column(Float, default=0)
    impostos_total = Column(Float, default=0)
    
    # Metadados
    observacoes = Column(Text)
    arquivo_origem = Column(String(255))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)
    
    empresa = relationship("Empresa", back_populates="dados_mensais")
    
    __table_args__ = (
        Index('idx_dados_empresa_periodo', 'empresa_id', 'ano', 'mes'),
    )


class Analise(Base):
    """Modelo de análise."""
    __tablename__ = 'analises'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False, index=True)
    data_analise = Column(DateTime, default=func.now())
    periodo_inicio = Column(String(10))
    periodo_fim = Column(String(10))
    meses_analisados = Column(Integer)
    score = Column(Integer)
    score_confianca = Column(Float)
    status = Column(String(20))
    resultado_json = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    empresa = relationship("Empresa", back_populates="analises")


class LoginAttempt(Base):
    """Modelo de tentativas de login."""
    __tablename__ = 'login_attempts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(50))
    success = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class TokenBlacklist(Base):
    """Modelo de blacklist de tokens."""
    __tablename__ = 'token_blacklist'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String(100), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    reason = Column(String(100))
    created_at = Column(DateTime, default=func.now())


# =============================================================================
# INICIALIZAÇÃO
# =============================================================================

def init_db():
    """Cria todas as tabelas."""
    Base.metadata.create_all(bind=engine)
    print(f"✓ Banco inicializado: {'PostgreSQL' if DatabaseConfig.USE_POSTGRES else 'SQLite'}")


# =============================================================================
# SEGURANÇA
# =============================================================================

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from auth.security import (
        hash_password, verify_password, validate_password_strength,
        create_access_token, create_refresh_token, decode_access_token,
        decode_refresh_token, create_reset_token, AuthConfig
    )
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    def hash_password(s): return hashlib.sha256(s.encode()).hexdigest()
    def verify_password(p, h): return hashlib.sha256(p.encode()).hexdigest() == h


# =============================================================================
# RATE LIMITING
# =============================================================================

def registrar_tentativa_login(identifier: str, ip: str, success: bool):
    """Registra tentativa de login."""
    with get_db() as db:
        attempt = LoginAttempt(identifier=identifier, ip_address=ip, success=success)
        db.add(attempt)


def verificar_bloqueio_login(identifier: str):
    """Verifica se está bloqueado."""
    with get_db() as db:
        cutoff = datetime.now() - timedelta(minutes=15)
        
        failed = db.query(func.count(LoginAttempt.id)).filter(
            LoginAttempt.identifier == identifier,
            LoginAttempt.success == False,
            LoginAttempt.created_at > cutoff
        ).scalar()
        
        max_attempts = 5
        
        if failed >= max_attempts:
            last = db.query(LoginAttempt).filter(
                LoginAttempt.identifier == identifier,
                LoginAttempt.success == False
            ).order_by(desc(LoginAttempt.created_at)).first()
            
            if last:
                unlock = last.created_at + timedelta(minutes=15)
                if unlock > datetime.now():
                    remaining = int((unlock - datetime.now()).total_seconds())
                    return True, 0, remaining
        
        return False, max_attempts - failed, 0


def limpar_tentativas_login(identifier: str):
    """Limpa tentativas após login."""
    with get_db() as db:
        db.query(LoginAttempt).filter(LoginAttempt.identifier == identifier).delete()


# =============================================================================
# TOKEN BLACKLIST
# =============================================================================

def adicionar_token_blacklist(jti: str, expires_at: datetime, reason: str = None):
    """Adiciona token à blacklist."""
    with get_db() as db:
        existing = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
        if not existing:
            blacklist = TokenBlacklist(jti=jti, expires_at=expires_at, reason=reason)
            db.add(blacklist)


def verificar_token_blacklist(jti: str) -> bool:
    """Verifica se token está na blacklist."""
    with get_db() as db:
        return db.query(TokenBlacklist).filter(
            TokenBlacklist.jti == jti,
            TokenBlacklist.expires_at > datetime.now()
        ).first() is not None


# =============================================================================
# CONTADORES (USUÁRIOS)
# =============================================================================

def criar_contador(nome: str, email: str, senha: str, telefone: str = None, crc: str = None) -> dict:
    """Cria um novo contador."""
    
    if BCRYPT_AVAILABLE:
        validation = validate_password_strength(senha)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))
    
    with get_db() as db:
        # Verifica se email existe
        existing = db.query(Contador).filter(
            Contador.email == email,
            Contador.deleted_at.is_(None)
        ).first()
        
        if existing:
            raise ValueError("Email já cadastrado")
        
        # Cria contador
        contador = Contador(
            nome=nome,
            email=email,
            senha_hash=hash_password(senha),
            telefone=telefone,
            crc=crc,
            password_changed_at=datetime.now()
        )
        db.add(contador)
        db.flush()
        
        # Gera tokens
        if BCRYPT_AVAILABLE:
            access_token = create_access_token({"sub": str(contador.id)})
            refresh_token = create_refresh_token({"sub": str(contador.id)})
            access_payload = decode_access_token(access_token)
            refresh_payload = decode_refresh_token(refresh_token)
            
            sessao = Sessao(
                contador_id=contador.id,
                token_jti=access_payload['jti'],
                refresh_token_jti=refresh_payload['jti'],
                expires_at=datetime.utcnow() + timedelta(minutes=15),
                refresh_expires_at=datetime.utcnow() + timedelta(days=7)
            )
        else:
            access_token = secrets.token_urlsafe(32)
            refresh_token = secrets.token_urlsafe(32)
            
            sessao = Sessao(
                contador_id=contador.id,
                token_jti=access_token,
                refresh_token_jti=refresh_token,
                expires_at=datetime.now() + timedelta(minutes=15),
                refresh_expires_at=datetime.now() + timedelta(days=7)
            )
        
        db.add(sessao)
        
        return {
            'id': contador.id,
            'nome': contador.nome,
            'email': contador.email,
            'telefone': contador.telefone,
            'crc': contador.crc,
            'token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 900
        }


def autenticar_contador(email: str, senha: str, ip: str = None) -> Optional[Dict]:
    """Autentica um contador."""
    
    is_locked, remaining, seconds = verificar_bloqueio_login(email)
    if is_locked:
        raise ValueError(f"Conta bloqueada. Tente novamente em {seconds // 60 + 1} minutos.")
    
    with get_db() as db:
        contador = db.query(Contador).filter(
            Contador.email == email,
            Contador.ativo == True,
            Contador.deleted_at.is_(None)
        ).first()
        
        if not contador:
            registrar_tentativa_login(email, ip, False)
            return None
        
        if not verify_password(senha, contador.senha_hash):
            registrar_tentativa_login(email, ip, False)
            _, remaining, _ = verificar_bloqueio_login(email)
            if remaining <= 2:
                raise ValueError(f"Senha incorreta. {remaining} tentativa(s) restante(s).")
            return None
        
        limpar_tentativas_login(email)
        registrar_tentativa_login(email, ip, True)
        
        if BCRYPT_AVAILABLE:
            access_token = create_access_token({"sub": str(contador.id)})
            refresh_token = create_refresh_token({"sub": str(contador.id)})
            access_payload = decode_access_token(access_token)
            refresh_payload = decode_refresh_token(refresh_token)
            
            sessao = Sessao(
                contador_id=contador.id,
                token_jti=access_payload['jti'],
                refresh_token_jti=refresh_payload['jti'],
                ip_address=ip,
                expires_at=datetime.utcnow() + timedelta(minutes=15),
                refresh_expires_at=datetime.utcnow() + timedelta(days=7)
            )
        else:
            access_token = secrets.token_urlsafe(32)
            refresh_token = secrets.token_urlsafe(32)
            
            sessao = Sessao(
                contador_id=contador.id,
                token_jti=access_token,
                refresh_token_jti=refresh_token,
                ip_address=ip,
                expires_at=datetime.now() + timedelta(minutes=15),
                refresh_expires_at=datetime.now() + timedelta(days=7)
            )
        
        db.add(sessao)
        
        return {
            'id': contador.id,
            'nome': contador.nome,
            'email': contador.email,
            'telefone': contador.telefone,
            'crc': contador.crc,
            'token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 900
        }


def validar_token(token: str) -> Optional[Dict]:
    """Valida token e retorna dados do contador."""
    
    if BCRYPT_AVAILABLE:
        payload = decode_access_token(token)
        if not payload:
            return None
        jti = payload.get('jti')
        
        if verificar_token_blacklist(jti):
            return None
    else:
        jti = token
    
    with get_db() as db:
        sessao = db.query(Sessao).filter(
            Sessao.token_jti == jti,
            Sessao.is_active == True
        ).first()
        
        if not sessao:
            return None
        
        contador = db.query(Contador).filter(
            Contador.id == sessao.contador_id,
            Contador.ativo == True,
            Contador.deleted_at.is_(None)
        ).first()
        
        if not contador:
            return None
        
        sessao.last_used_at = datetime.now()
        
        return {
            'id': contador.id,
            'nome': contador.nome,
            'email': contador.email,
            'telefone': contador.telefone,
            'crc': contador.crc
        }


def logout(token: str):
    """Faz logout."""
    if BCRYPT_AVAILABLE:
        payload = decode_access_token(token)
        if payload:
            jti = payload['jti']
            exp = datetime.utcfromtimestamp(payload.get('exp', 0))
            adicionar_token_blacklist(jti, exp, "logout")
            
            with get_db() as db:
                db.query(Sessao).filter(Sessao.token_jti == jti).update({"is_active": False})
    else:
        with get_db() as db:
            db.query(Sessao).filter(Sessao.token_jti == token).update({"is_active": False})


def logout_all_devices(user_id: int, current_token: str = None):
    """Logout de todos os dispositivos."""
    current_jti = None
    if current_token and BCRYPT_AVAILABLE:
        payload = decode_access_token(current_token)
        current_jti = payload.get('jti') if payload else None
    
    with get_db() as db:
        sessoes = db.query(Sessao).filter(
            Sessao.contador_id == user_id,
            Sessao.is_active == True
        ).all()
        
        for s in sessoes:
            if current_jti and s.token_jti == current_jti:
                continue
            
            if s.token_jti:
                adicionar_token_blacklist(s.token_jti, s.expires_at or datetime.now() + timedelta(hours=1), "logout_all")
            s.is_active = False


def refresh_access_token(refresh_token: str) -> Optional[Dict]:
    """Renova access token."""
    if not BCRYPT_AVAILABLE:
        return None
    
    payload = decode_refresh_token(refresh_token)
    if not payload:
        return None
    
    jti = payload.get('jti')
    if verificar_token_blacklist(jti):
        return None
    
    with get_db() as db:
        sessao = db.query(Sessao).filter(
            Sessao.refresh_token_jti == jti,
            Sessao.is_active == True
        ).first()
        
        if not sessao:
            return None
        
        contador = db.query(Contador).filter(
            Contador.id == sessao.contador_id,
            Contador.ativo == True
        ).first()
        
        if not contador:
            return None
        
        new_token = create_access_token({"sub": str(contador.id)})
        new_payload = decode_access_token(new_token)
        
        sessao.token_jti = new_payload['jti']
        sessao.expires_at = datetime.utcnow() + timedelta(minutes=15)
        sessao.last_used_at = datetime.now()
        
        return {
            'token': new_token,
            'expires_in': 900,
            'user': {
                'id': contador.id,
                'nome': contador.nome,
                'email': contador.email
            }
        }


def alterar_senha(user_id: int, senha_atual: str, nova_senha: str) -> bool:
    """Altera senha."""
    if BCRYPT_AVAILABLE:
        validation = validate_password_strength(nova_senha)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))
    
    with get_db() as db:
        contador = db.query(Contador).filter(Contador.id == user_id).first()
        if not contador:
            raise ValueError("Usuário não encontrado")
        
        if not verify_password(senha_atual, contador.senha_hash):
            raise ValueError("Senha atual incorreta")
        
        contador.senha_hash = hash_password(nova_senha)
        contador.password_changed_at = datetime.now()
        contador.updated_at = datetime.now()
    
    logout_all_devices(user_id)
    return True


def solicitar_reset_senha(email: str) -> Optional[str]:
    """Gera token para reset."""
    with get_db() as db:
        contador = db.query(Contador).filter(
            Contador.email == email,
            Contador.ativo == True
        ).first()
        
        if not contador:
            return None
        
        if BCRYPT_AVAILABLE:
            reset_token = create_reset_token(contador.id)
        else:
            reset_token = secrets.token_urlsafe(32)
        
        contador.reset_token = reset_token
        contador.reset_token_expires = datetime.now() + timedelta(hours=1)
        
        return reset_token


def resetar_senha(token: str, nova_senha: str) -> bool:
    """Reseta senha com token."""
    if BCRYPT_AVAILABLE:
        validation = validate_password_strength(nova_senha)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))
    
    with get_db() as db:
        contador = db.query(Contador).filter(
            Contador.reset_token == token,
            Contador.reset_token_expires > datetime.now(),
            Contador.ativo == True
        ).first()
        
        if not contador:
            raise ValueError("Token inválido ou expirado")
        
        contador.senha_hash = hash_password(nova_senha)
        contador.reset_token = None
        contador.reset_token_expires = None
        contador.password_changed_at = datetime.now()
    
    logout_all_devices(contador.id)
    return True


def listar_sessoes_ativas(user_id: int) -> List[Dict]:
    """Lista sessões ativas."""
    with get_db() as db:
        sessoes = db.query(Sessao).filter(
            Sessao.contador_id == user_id,
            Sessao.is_active == True
        ).order_by(desc(Sessao.last_used_at)).all()
        
        return [{
            'id': s.id,
            'device_info': s.device_info,
            'ip_address': s.ip_address,
            'created_at': s.created_at.isoformat() if s.created_at else None,
            'last_used_at': s.last_used_at.isoformat() if s.last_used_at else None
        } for s in sessoes]


def revogar_sessao(user_id: int, session_id: int) -> bool:
    """Revoga sessão específica."""
    with get_db() as db:
        sessao = db.query(Sessao).filter(
            Sessao.id == session_id,
            Sessao.contador_id == user_id
        ).first()
        
        if not sessao:
            return False
        
        if sessao.token_jti:
            adicionar_token_blacklist(sessao.token_jti, sessao.expires_at or datetime.now() + timedelta(hours=1), "revoked")
        
        sessao.is_active = False
        return True


# =============================================================================
# EMPRESAS
# =============================================================================

def criar_empresa(contador_id: int, dados: Dict) -> int:
    """Cria uma nova empresa."""
    with get_db() as db:
        empresa = Empresa(
            contador_id=contador_id,
            razao_social=dados.get('razao_social'),
            nome_fantasia=dados.get('nome_fantasia'),
            cnpj=dados.get('cnpj'),
            inscricao_estadual=dados.get('inscricao_estadual'),
            regime_tributario=dados.get('regime_tributario'),
            setor=dados.get('setor'),
            endereco=dados.get('endereco'),
            cidade=dados.get('cidade'),
            estado=dados.get('estado'),
            telefone=dados.get('telefone'),
            email=dados.get('email'),
            contato_nome=dados.get('contato_nome'),
            observacoes=dados.get('observacoes')
        )
        db.add(empresa)
        db.flush()
        return empresa.id


def listar_empresas(contador_id: int, apenas_ativas: bool = True) -> List[Dict]:
    """Lista empresas do contador."""
    with get_db() as db:
        query = db.query(Empresa).filter(
            Empresa.contador_id == contador_id,
            Empresa.deleted_at.is_(None)
        )
        
        if apenas_ativas:
            query = query.filter(Empresa.ativo == True)
        
        empresas = query.order_by(Empresa.razao_social).all()
        
        result = []
        for emp in empresas:
            # Conta meses
            meses = db.query(func.count(DadosMensal.id)).filter(
                DadosMensal.empresa_id == emp.id,
                DadosMensal.deleted_at.is_(None)
            ).scalar()
            
            # Última análise
            ultima = db.query(Analise).filter(
                Analise.empresa_id == emp.id
            ).order_by(desc(Analise.data_analise)).first()
            
            # Normalizar status para o frontend
            ultimo_status = None
            if ultima and ultima.score is not None:
                score = ultima.score or 0
                if score >= 70:
                    ultimo_status = 'saudavel'
                elif score >= 40:
                    ultimo_status = 'atencao'
                else:
                    ultimo_status = 'critico'
            
            result.append({
                'id': emp.id,
                'contador_id': emp.contador_id,
                'razao_social': emp.razao_social,
                'nome_fantasia': emp.nome_fantasia,
                'cnpj': emp.cnpj,
                'inscricao_estadual': emp.inscricao_estadual,
                'regime_tributario': emp.regime_tributario,
                'setor': emp.setor,
                'endereco': emp.endereco,
                'cidade': emp.cidade,
                'estado': emp.estado,
                'telefone': emp.telefone,
                'email': emp.email,
                'contato_nome': emp.contato_nome,
                'observacoes': emp.observacoes,
                'ativo': emp.ativo,
                'created_at': emp.created_at.isoformat() if emp.created_at else None,
                'meses_dados': meses,
                'ultimo_score': ultima.score if ultima else None,
                'ultimo_status': ultimo_status
            })
        
        return result


def obter_empresa(empresa_id: int, contador_id: int) -> Optional[Dict]:
    """Obtém uma empresa."""
    with get_db() as db:
        emp = db.query(Empresa).filter(
            Empresa.id == empresa_id,
            Empresa.contador_id == contador_id,
            Empresa.deleted_at.is_(None)
        ).first()
        
        if not emp:
            return None
        
        return {
            'id': emp.id,
            'contador_id': emp.contador_id,
            'razao_social': emp.razao_social,
            'nome_fantasia': emp.nome_fantasia,
            'cnpj': emp.cnpj,
            'inscricao_estadual': emp.inscricao_estadual,
            'regime_tributario': emp.regime_tributario,
            'setor': emp.setor,
            'endereco': emp.endereco,
            'cidade': emp.cidade,
            'estado': emp.estado,
            'telefone': emp.telefone,
            'email': emp.email,
            'contato_nome': emp.contato_nome,
            'observacoes': emp.observacoes,
            'ativo': emp.ativo
        }


def atualizar_empresa(empresa_id: int, contador_id: int, dados: Dict):
    """Atualiza uma empresa."""
    with get_db() as db:
        emp = db.query(Empresa).filter(
            Empresa.id == empresa_id,
            Empresa.contador_id == contador_id,
            Empresa.deleted_at.is_(None)
        ).first()
        
        if not emp:
            return False
        
        for key, value in dados.items():
            if hasattr(emp, key) and value is not None:
                setattr(emp, key, value)
        
        return True


def excluir_empresa(empresa_id: int, contador_id: int):
    """Exclui empresa (soft delete)."""
    with get_db() as db:
        emp = db.query(Empresa).filter(
            Empresa.id == empresa_id,
            Empresa.contador_id == contador_id
        ).first()
        
        if not emp:
            return False
        
        emp.deleted_at = datetime.now()
        emp.ativo = False
        return True


# =============================================================================
# DADOS MENSAIS
# =============================================================================

def salvar_dados_mensais(empresa_id: int, dados: Dict) -> int:
    """Salva ou atualiza dados mensais - suporta campos expandidos."""
    with get_db() as db:
        existing = db.query(DadosMensal).filter(
            DadosMensal.empresa_id == empresa_id,
            DadosMensal.ano == dados['ano'],
            DadosMensal.mes == dados['mes'],
            DadosMensal.deleted_at.is_(None)
        ).first()
        
        if existing:
            for key, value in dados.items():
                if hasattr(existing, key) and key not in ['id', 'empresa_id', 'created_at']:
                    setattr(existing, key, value)
            return existing.id
        else:
            dado = DadosMensal(
                empresa_id=empresa_id,
                ano=dados['ano'],
                mes=dados['mes'],
                # Campos básicos
                receita=dados.get('receita', 0),
                custos=dados.get('custos', 0),
                despesas=dados.get('despesas', 0),
                impostos=dados.get('impostos', 0),
                folha=dados.get('folha', 0),
                caixa=dados.get('caixa', 0),
                # Campos expandidos - Balanço
                ativo_total=dados.get('ativo_total', 0),
                ativo_circulante=dados.get('ativo_circulante', 0),
                disponivel=dados.get('disponivel', 0),
                bancos=dados.get('bancos', 0),
                clientes=dados.get('clientes', 0),
                estoques=dados.get('estoques', 0),
                passivo_total=dados.get('passivo_total', 0),
                passivo_circulante=dados.get('passivo_circulante', 0),
                passivo_nao_circulante=dados.get('passivo_nao_circulante', 0),
                patrimonio_liquido=dados.get('patrimonio_liquido', 0),
                capital_social=dados.get('capital_social', 0),
                # Campos expandidos - DRE
                receita_bruta=dados.get('receita_bruta', 0),
                receita_servicos=dados.get('receita_servicos', 0),
                deducoes_receita=dados.get('deducoes_receita', 0),
                custos_total=dados.get('custos_total', 0),
                despesas_operacionais=dados.get('despesas_operacionais', 0),
                despesas_financeiras=dados.get('despesas_financeiras', 0),
                receitas_financeiras=dados.get('receitas_financeiras', 0),
                lucro_liquido=dados.get('lucro_liquido', 0),
                # Impostos
                iss=dados.get('iss', dados.get('iss_deducao', 0)),
                pis=dados.get('pis', dados.get('pis_deducao', 0)),
                cofins=dados.get('cofins', dados.get('cofins_deducao', 0)),
                irpj=dados.get('irpj', dados.get('irpj_deducao', 0)),
                csll=dados.get('csll', dados.get('csll_deducao', 0)),
                impostos_total=dados.get('impostos_total', 0),
                # Meta
                observacoes=dados.get('observacoes'),
                arquivo_origem=dados.get('arquivo_origem')
            )
            db.add(dado)
            db.flush()
            return dado.id


def listar_dados_mensais(empresa_id: int, limite: int = 36) -> List[Dict]:
    """Lista dados mensais com campos expandidos."""
    with get_db() as db:
        dados = db.query(DadosMensal).filter(
            DadosMensal.empresa_id == empresa_id,
            DadosMensal.deleted_at.is_(None)
        ).order_by(desc(DadosMensal.ano), desc(DadosMensal.mes)).limit(limite).all()
        
        result = []
        for d in dados:
            item = {
                'id': d.id,
                'empresa_id': d.empresa_id,
                'ano': d.ano,
                'mes': d.mes,
                'competencia': f"{d.ano}-{d.mes:02d}",
                'receita': d.receita,
                'custos': d.custos,
                'despesas': d.despesas,
                'impostos': d.impostos,
                'folha': d.folha,
                'caixa': d.caixa,
                'observacoes': d.observacoes
            }
            
            # Adicionar campos expandidos se existirem
            campos_expandidos = [
                'ativo_total', 'ativo_circulante', 'disponivel', 'bancos', 'clientes',
                'estoques', 'passivo_total', 'passivo_circulante', 'passivo_nao_circulante',
                'patrimonio_liquido', 'capital_social', 'receita_bruta', 'receita_servicos',
                'deducoes_receita', 'custos_total', 'despesas_operacionais',
                'despesas_financeiras', 'receitas_financeiras', 'lucro_liquido',
                'iss', 'pis', 'cofins', 'irpj', 'csll', 'impostos_total'
            ]
            
            for campo in campos_expandidos:
                valor = getattr(d, campo, None)
                if valor is not None:
                    item[campo] = valor
            
            result.append(item)
        
        return result


def obter_dados_para_analise(empresa_id: int) -> List[Dict]:
    """Obtém dados para análise - inclui campos expandidos."""
    with get_db() as db:
        dados = db.query(DadosMensal).filter(
            DadosMensal.empresa_id == empresa_id,
            DadosMensal.deleted_at.is_(None)
        ).order_by(DadosMensal.ano, DadosMensal.mes).all()
        
        result = []
        for d in dados:
            item = {
                'ano': d.ano,
                'mes': d.mes,
                # Campos básicos
                'receita': d.receita or 0,
                'custos': d.custos or 0,
                'despesas': d.despesas or 0,
                'impostos': d.impostos or 0,
                'folha': d.folha or 0,
                'caixa': d.caixa or 0,
            }
            
            # Campos expandidos (se existirem)
            campos_expandidos = [
                'ativo_total', 'ativo_circulante', 'disponivel', 'bancos', 'clientes',
                'estoques', 'ativo_nao_circulante', 'imobilizado',
                'passivo_total', 'passivo_circulante', 'fornecedores',
                'obrigacoes_trabalhistas', 'obrigacoes_tributarias',
                'emprestimos_cp', 'passivo_nao_circulante', 'emprestimos_lp',
                'patrimonio_liquido', 'capital_social', 'lucros_acumulados',
                'receita_bruta', 'receita_servicos', 'deducoes_receita',
                'receita_liquida', 'custos_total', 'lucro_bruto',
                'despesas_operacionais', 'despesas_financeiras', 'receitas_financeiras',
                'lucro_liquido', 'iss', 'pis', 'cofins', 'irpj', 'csll', 'impostos_total'
            ]
            
            for campo in campos_expandidos:
                valor = getattr(d, campo, None)
                if valor is not None:
                    item[campo] = valor
            
            result.append(item)
        
        return result


def excluir_dados_mensais(empresa_id: int, ano: int, mes: int):
    """Exclui dados mensais (soft delete)."""
    with get_db() as db:
        dado = db.query(DadosMensal).filter(
            DadosMensal.empresa_id == empresa_id,
            DadosMensal.ano == ano,
            DadosMensal.mes == mes
        ).first()
        
        if not dado:
            return False
        
        dado.deleted_at = datetime.now()
        return True


# =============================================================================
# ANÁLISES
# =============================================================================

def salvar_analise(empresa_id: int, resultado: Dict) -> int:
    """Salva uma análise."""
    with get_db() as db:
        analise = Analise(
            empresa_id=empresa_id,
            periodo_inicio=resultado.get('periodo_inicio'),
            periodo_fim=resultado.get('periodo_fim'),
            meses_analisados=resultado.get('meses_analisados'),
            score=resultado.get('score'),
            score_confianca=resultado.get('score_confianca'),
            status=resultado.get('status'),
            resultado_json=json.dumps(resultado)
        )
        db.add(analise)
        db.flush()
        return analise.id


def listar_analises(empresa_id: int, limite: int = 10) -> List[Dict]:
    """Lista análises."""
    with get_db() as db:
        analises = db.query(Analise).filter(
            Analise.empresa_id == empresa_id
        ).order_by(desc(Analise.data_analise)).limit(limite).all()
        
        result = []
        for a in analises:
            resultado = {}
            if a.resultado_json:
                try:
                    resultado = json.loads(a.resultado_json)
                except:
                    pass
            
            score_det = resultado.get('score_detalhado', {})
            
            result.append({
                'id': a.id,
                'empresa_id': a.empresa_id,
                'data_analise': a.data_analise.isoformat() if a.data_analise else None,
                'periodo_inicio': a.periodo_inicio,
                'periodo_fim': a.periodo_fim,
                'meses_analisados': a.meses_analisados,
                'score': a.score,
                'score_confianca': a.score_confianca,
                'status': a.status,
                'score_tendencia': score_det.get('tendencia', 0),
                'score_margem': score_det.get('margem', 0),
                'score_caixa': score_det.get('caixa', 0),
                'score_estabilidade': score_det.get('estabilidade', 0),
                'score_anomalias': score_det.get('anomalias', 0),
                'insights': resultado.get('insights', []),
                'recomendacao_principal': resultado.get('recomendacao_principal', ''),
                'resultado_completo': resultado
            })
        
        return result


def obter_analise(analise_id: int, empresa_id: int) -> Optional[Dict]:
    """Obtém uma análise."""
    with get_db() as db:
        a = db.query(Analise).filter(
            Analise.id == analise_id,
            Analise.empresa_id == empresa_id
        ).first()
        
        if not a:
            return None
        
        resultado = {}
        if a.resultado_json:
            try:
                resultado = json.loads(a.resultado_json)
            except:
                pass
        
        score_det = resultado.get('score_detalhado', {})
        
        return {
            'id': a.id,
            'empresa_id': a.empresa_id,
            'data_analise': a.data_analise.isoformat() if a.data_analise else None,
            'periodo_inicio': a.periodo_inicio,
            'periodo_fim': a.periodo_fim,
            'meses_analisados': a.meses_analisados,
            'score': a.score,
            'score_confianca': a.score_confianca,
            'status': a.status,
            'score_tendencia': score_det.get('tendencia', 0),
            'score_margem': score_det.get('margem', 0),
            'score_caixa': score_det.get('caixa', 0),
            'score_estabilidade': score_det.get('estabilidade', 0),
            'score_anomalias': score_det.get('anomalias', 0),
            'insights': resultado.get('insights', []),
            'recomendacao_principal': resultado.get('recomendacao_principal', ''),
            'resultado_completo': resultado,
            'resultado': resultado
        }


def obter_ultima_analise(empresa_id: int) -> Optional[Dict]:
    """Obtém última análise."""
    with get_db() as db:
        a = db.query(Analise).filter(
            Analise.empresa_id == empresa_id
        ).order_by(desc(Analise.data_analise)).first()
        
        if not a:
            return None
        
        return obter_analise(a.id, empresa_id)


# =============================================================================
# ESTATÍSTICAS
# =============================================================================

def obter_estatisticas_contador(contador_id: int) -> Dict:
    """Obtém estatísticas do contador."""
    with get_db() as db:
        total = db.query(func.count(Empresa.id)).filter(
            Empresa.contador_id == contador_id,
            Empresa.ativo == True,
            Empresa.deleted_at.is_(None)
        ).scalar()
        
        empresas = listar_empresas(contador_id)
        
        saudaveis = sum(1 for e in empresas if e.get('ultimo_status') == 'saudavel')
        atencao = sum(1 for e in empresas if e.get('ultimo_status') == 'atencao')
        criticos = sum(1 for e in empresas if e.get('ultimo_status') == 'critico')
        sem_analise = sum(1 for e in empresas if not e.get('ultimo_status'))
        
        return {
            'total_empresas': total,
            'empresas_saudaveis': saudaveis,
            'empresas_atencao': atencao,
            'empresas_criticas': criticos,
            'empresas_sem_analise': sem_analise
        }


def obter_dados_dashboard_graficos(contador_id: int, meses: int = 12, empresa_id: int = None) -> Dict:
    """Obtém dados agregados para gráficos do dashboard. 
    
    Args:
        contador_id: ID do contador
        meses: Número de meses para análise
        empresa_id: Se fornecido, filtra apenas essa empresa
    """
    from datetime import datetime, date
    from collections import defaultdict
    
    with get_db() as db:
        # Lista empresas do contador
        query = db.query(Empresa).filter(
            Empresa.contador_id == contador_id,
            Empresa.ativo == True,
            Empresa.deleted_at.is_(None)
        )
        
        # Filtra por empresa específica se fornecido
        if empresa_id:
            query = query.filter(Empresa.id == empresa_id)
        
        empresas = query.all()
        
        if not empresas:
            return {
                'faturamento_mensal': [],
                'composicao_despesas': [],
                'fluxo_caixa': [],
                'top_empresas_faturamento': [],
                'top_empresas_score': [],
                'comparativo_mensal': {},
                'totais': {}
            }
        
        empresa_ids = [e.id for e in empresas]
        
        # Busca dados mensais de todas as empresas
        dados = db.query(DadosMensal).filter(
            DadosMensal.empresa_id.in_(empresa_ids)
        ).order_by(DadosMensal.ano.desc(), DadosMensal.mes.desc()).all()
        
        # Agrupa por mês
        dados_por_mes = defaultdict(lambda: {
            'receita': 0, 'custos': 0, 'despesas': 0, 
            'impostos': 0, 'folha': 0, 'caixa': 0
        })
        
        # Dados por empresa para ranking
        dados_por_empresa = defaultdict(lambda: {'receita_total': 0, 'meses': 0})
        
        for d in dados:
            periodo = f"{d.ano}-{d.mes:02d}"
            dados_por_mes[periodo]['receita'] += d.receita or 0
            dados_por_mes[periodo]['custos'] += d.custos or 0
            dados_por_mes[periodo]['despesas'] += d.despesas or 0
            dados_por_mes[periodo]['impostos'] += d.impostos or 0
            dados_por_mes[periodo]['folha'] += d.folha or 0
            dados_por_mes[periodo]['caixa'] += d.caixa or 0
            
            dados_por_empresa[d.empresa_id]['receita_total'] += d.receita or 0
            dados_por_empresa[d.empresa_id]['meses'] += 1
        
        # Ordena períodos e pega últimos N meses
        periodos_ordenados = sorted(dados_por_mes.keys(), reverse=True)[:meses]
        periodos_ordenados.reverse()  # Do mais antigo para o mais recente
        
        # 1. Faturamento mensal (linha do tempo)
        faturamento_mensal = []
        for periodo in periodos_ordenados:
            d = dados_por_mes[periodo]
            faturamento_mensal.append({
                'periodo': periodo,
                'mes': periodo[5:7] + '/' + periodo[2:4],  # MM/YY
                'receita': round(d['receita'], 2),
                'custos': round(d['custos'], 2),
                'despesas': round(d['despesas'], 2),
                'lucro': round(d['receita'] - d['custos'] - d['despesas'] - d['impostos'] - d['folha'], 2)
            })
        
        # 2. Composição de despesas (pizza) - último mês com dados
        composicao_despesas = []
        if periodos_ordenados:
            ultimo_mes = dados_por_mes[periodos_ordenados[-1]]
            total_saidas = ultimo_mes['custos'] + ultimo_mes['despesas'] + ultimo_mes['impostos'] + ultimo_mes['folha']
            if total_saidas > 0:
                composicao_despesas = [
                    {'nome': 'Custos', 'valor': round(ultimo_mes['custos'], 2), 'cor': '#ef4444'},
                    {'nome': 'Despesas', 'valor': round(ultimo_mes['despesas'], 2), 'cor': '#f97316'},
                    {'nome': 'Impostos', 'valor': round(ultimo_mes['impostos'], 2), 'cor': '#eab308'},
                    {'nome': 'Folha', 'valor': round(ultimo_mes['folha'], 2), 'cor': '#22c55e'},
                ]
        
        # 3. Fluxo de caixa mensal
        fluxo_caixa = []
        for periodo in periodos_ordenados:
            d = dados_por_mes[periodo]
            entradas = d['receita']
            saidas = d['custos'] + d['despesas'] + d['impostos'] + d['folha']
            fluxo_caixa.append({
                'periodo': periodo,
                'mes': periodo[5:7] + '/' + periodo[2:4],
                'entradas': round(entradas, 2),
                'saidas': round(saidas, 2),
                'saldo': round(entradas - saidas, 2)
            })
        
        # 4. Top 5 empresas por faturamento (só mostra se não filtrou por empresa)
        top_empresas_faturamento = []
        if not empresa_id:
            for emp in empresas:
                if emp.id in dados_por_empresa:
                    receita = dados_por_empresa[emp.id]['receita_total']
                    media = receita / max(dados_por_empresa[emp.id]['meses'], 1)
                    top_empresas_faturamento.append({
                        'id': emp.id,
                        'nome': emp.razao_social[:25] + '...' if len(emp.razao_social) > 25 else emp.razao_social,
                        'faturamento_total': round(receita, 2),
                        'media_mensal': round(media, 2)
                    })
            top_empresas_faturamento.sort(key=lambda x: x['faturamento_total'], reverse=True)
            top_empresas_faturamento = top_empresas_faturamento[:5]
        
        # 5. Top 5 empresas por score (só mostra se não filtrou por empresa)
        top_empresas_score = []
        if not empresa_id:
            for emp in empresas:
                # Busca última análise da empresa
                ultima_analise = db.query(Analise).filter(
                    Analise.empresa_id == emp.id
                ).order_by(Analise.data_analise.desc()).first()
                
                if ultima_analise and ultima_analise.score:
                    top_empresas_score.append({
                        'id': emp.id,
                        'nome': emp.razao_social[:25] + '...' if len(emp.razao_social) > 25 else emp.razao_social,
                        'score': ultima_analise.score,
                        'status': ultima_analise.status
                    })
            top_empresas_score.sort(key=lambda x: x['score'], reverse=True)
            top_empresas_score = top_empresas_score[:5]
        
        # 6. Comparativo mês atual vs anterior
        comparativo = {}
        if len(periodos_ordenados) >= 2:
            atual = dados_por_mes[periodos_ordenados[-1]]
            anterior = dados_por_mes[periodos_ordenados[-2]]
            
            def calc_variacao(novo, antigo):
                if antigo == 0:
                    return 100 if novo > 0 else 0
                return round(((novo - antigo) / antigo) * 100, 1)
            
            comparativo = {
                'periodo_atual': periodos_ordenados[-1],
                'periodo_anterior': periodos_ordenados[-2],
                'receita': {
                    'atual': round(atual['receita'], 2),
                    'anterior': round(anterior['receita'], 2),
                    'variacao': calc_variacao(atual['receita'], anterior['receita'])
                },
                'custos': {
                    'atual': round(atual['custos'], 2),
                    'anterior': round(anterior['custos'], 2),
                    'variacao': calc_variacao(atual['custos'], anterior['custos'])
                },
                'despesas': {
                    'atual': round(atual['despesas'], 2),
                    'anterior': round(anterior['despesas'], 2),
                    'variacao': calc_variacao(atual['despesas'], anterior['despesas'])
                },
                'lucro': {
                    'atual': round(atual['receita'] - atual['custos'] - atual['despesas'] - atual['impostos'] - atual['folha'], 2),
                    'anterior': round(anterior['receita'] - anterior['custos'] - anterior['despesas'] - anterior['impostos'] - anterior['folha'], 2),
                    'variacao': calc_variacao(
                        atual['receita'] - atual['custos'] - atual['despesas'] - atual['impostos'] - atual['folha'],
                        anterior['receita'] - anterior['custos'] - anterior['despesas'] - anterior['impostos'] - anterior['folha']
                    )
                }
            }
        
        # 7. Totais consolidados
        totais = {
            'receita_total': sum(d['receita'] for d in dados_por_mes.values()),
            'custos_total': sum(d['custos'] for d in dados_por_mes.values()),
            'despesas_total': sum(d['despesas'] for d in dados_por_mes.values()),
            'impostos_total': sum(d['impostos'] for d in dados_por_mes.values()),
            'folha_total': sum(d['folha'] for d in dados_por_mes.values()),
        }
        totais['lucro_total'] = totais['receita_total'] - totais['custos_total'] - totais['despesas_total'] - totais['impostos_total'] - totais['folha_total']
        
        if totais['receita_total'] > 0:
            totais['margem_media'] = round((totais['lucro_total'] / totais['receita_total']) * 100, 1)
        else:
            totais['margem_media'] = 0
        
        return {
            'faturamento_mensal': faturamento_mensal,
            'composicao_despesas': composicao_despesas,
            'fluxo_caixa': fluxo_caixa,
            'top_empresas_faturamento': top_empresas_faturamento,
            'top_empresas_score': top_empresas_score,
            'comparativo_mensal': comparativo,
            'totais': {k: round(v, 2) for k, v in totais.items()}
        }
