#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração do Banco de Dados - PostgreSQL com SQLAlchemy
==========================================================

Suporta:
- PostgreSQL (produção)
- SQLite (desenvolvimento/fallback)
- Connection pooling
- Sessões assíncronas
"""

import os
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

class DatabaseConfig:
    """Configurações do banco de dados."""
    
    # Detecta ambiente
    ENV = os.environ.get('ENV', 'development')
    
    # URLs de conexão
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'contabil')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'contabil123')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'postgres')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'contabil_db')
    
    # URL completa do PostgreSQL
    POSTGRES_URL = os.environ.get(
        'DATABASE_URL',
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    
    # SQLite para fallback/desenvolvimento
    SQLITE_PATH = os.environ.get('SQLITE_PATH', 'kontabil.db')
    SQLITE_URL = f"sqlite:///{SQLITE_PATH}"
    
    # Detecta automaticamente se DATABASE_URL é SQLite
    @classmethod
    def get_database_url(cls) -> str:
        """Retorna URL do banco baseado na configuração."""
        db_url = os.environ.get('DATABASE_URL', '')
        
        # Se DATABASE_URL começa com sqlite, usa direto
        if db_url.startswith('sqlite'):
            return db_url
        
        # Se tem DATABASE_URL válido (postgres), usa
        if db_url and 'postgresql' in db_url:
            return db_url
        
        # Se USE_POSTGRES=true e tem config, tenta postgres
        if cls.USE_POSTGRES and cls.POSTGRES_HOST:
            return cls.POSTGRES_URL
        
        # Fallback para SQLite
        return cls.SQLITE_URL
    
    # Usa PostgreSQL se disponível, senão SQLite
    USE_POSTGRES = os.environ.get('USE_POSTGRES', 'false').lower() == 'true'
    
    # Pool settings (PostgreSQL)
    POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '10'))
    MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', '20'))
    POOL_TIMEOUT = int(os.environ.get('DB_POOL_TIMEOUT', '30'))
    POOL_RECYCLE = int(os.environ.get('DB_POOL_RECYCLE', '1800'))  # 30 min


# =============================================================================
# ENGINE E SESSÃO
# =============================================================================

def create_db_engine():
    """Cria engine do SQLAlchemy com configurações apropriadas."""
    
    database_url = DatabaseConfig.get_database_url()
    is_sqlite = database_url.startswith('sqlite')
    
    if is_sqlite:
        # SQLite - sem pool
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=DatabaseConfig.ENV == 'development'
        )
        
        # Habilita foreign keys no SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        # PostgreSQL - com connection pool
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=DatabaseConfig.POOL_SIZE,
            max_overflow=DatabaseConfig.MAX_OVERFLOW,
            pool_timeout=DatabaseConfig.POOL_TIMEOUT,
            pool_recycle=DatabaseConfig.POOL_RECYCLE,
            pool_pre_ping=True,  # Verifica conexões antes de usar
            echo=DatabaseConfig.ENV == 'development'
        )
    
    return engine


# Engine global
engine = create_db_engine()

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para modelos
Base = declarative_base()


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para injeção de sessão do banco.
    
    Uso com FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager para uso fora do FastAPI.
    
    Uso:
        with get_db_context() as db:
            ...
    """
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
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas.
    
    Em produção, usar migrations do Alembic.
    """
    from db.models import Base
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """Verifica se a conexão com o banco está funcionando."""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Erro de conexão com banco: {e}")
        return False


def get_db_info() -> dict:
    """Retorna informações sobre a configuração do banco."""
    return {
        "engine": "PostgreSQL" if DatabaseConfig.USE_POSTGRES else "SQLite",
        "url": DatabaseConfig.get_database_url().split("@")[-1] if "@" in DatabaseConfig.get_database_url() else DatabaseConfig.get_database_url(),
        "pool_size": DatabaseConfig.POOL_SIZE if DatabaseConfig.USE_POSTGRES else "N/A",
        "environment": DatabaseConfig.ENV
    }
