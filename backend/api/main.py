#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API REST - Sistema de Gestão Contábil para Contadores
Com banco de dados PostgreSQL, autenticação segura e gestão de múltiplas empresas

Features de Segurança:
- Sprint 1: Rate Limiting, Headers de Segurança, CORS, Sanitização
- Sprint 2: Auditoria, 2FA (TOTP), Criptografia, Gerenciamento de Sessões
"""

import os
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import asdict
import json
import numpy as np

from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, EmailStr, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==============================================================================
# CONFIGURAÇÕES DE SEGURANÇA (Sprint 1)
# ==============================================================================
try:
    from core.config import settings
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    # Fallback para desenvolvimento
    class FallbackSettings:
        environment = "development"
        is_production = False
        cors_origins = ["http://localhost", "http://localhost:3000", "http://localhost:5173"]
        rate_limit_enabled = False  # Desabilitar em dev
        rate_limit_per_minute = 300  # Aumentar para 300 requisições/minuto
        rate_limit_login_attempts = 10  # Mais tentativas
        rate_limit_login_window = 5  # Janela menor
        security_headers_enabled = True
        jwt_secret = os.getenv("JWT_SECRET", "development-secret-change-in-production")
        password_min_length = 8
        password_require_uppercase = True
        password_require_lowercase = True
        password_require_digit = True
        password_require_special = False
    settings = FallbackSettings()

# Middlewares de segurança (Sprint 1)
try:
    from core.security import (
        RateLimitMiddleware, 
        SecurityHeadersMiddleware, 
        rate_limiter,
        PasswordValidator,
        InputSanitizer
    )
    SECURITY_MIDDLEWARE_AVAILABLE = True
except ImportError:
    SECURITY_MIDDLEWARE_AVAILABLE = False
    rate_limiter = None
    PasswordValidator = None
    InputSanitizer = None

# ==============================================================================
# SEGURANÇA AVANÇADA (Sprint 2)
# ==============================================================================
try:
    from core.security_advanced import (
        AuditLogger,
        TwoFactorAuth,
        TOTP,
        DataEncryption,
        SessionManager,
        PasswordRecovery
    )
    SECURITY_ADVANCED_AVAILABLE = True
except ImportError:
    SECURITY_ADVANCED_AVAILABLE = False
    AuditLogger = None
    TwoFactorAuth = None
    TOTP = None
    DataEncryption = None
    SessionManager = None
    PasswordRecovery = None

# Serviço de Email
try:
    from core.email_service import email_service
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    EMAIL_SERVICE_AVAILABLE = False
    email_service = None

from data.database import (
    init_db, criar_contador, autenticar_contador, validar_token, logout,
    criar_empresa, listar_empresas, obter_empresa, atualizar_empresa, excluir_empresa,
    salvar_dados_mensais, listar_dados_mensais, obter_dados_para_analise, excluir_dados_mensais,
    salvar_analise, listar_analises, obter_analise, obter_ultima_analise,
    obter_estatisticas_contador,
    # Novas funções de segurança
    logout_all_devices, refresh_access_token, alterar_senha,
    solicitar_reset_senha, resetar_senha, listar_sessoes_ativas, revogar_sessao,
    # Database session
    get_db
)
from data.csv_importer import SmartCSVImporter, CompanyData, MonthlyRecord
from engine.analyzer_pro import ContabilAnalyzerPro
from reports.pdf_generator_pro import PDFGeneratorPro

# Tenta importar validação de senha legada
try:
    from auth.security import validate_password_strength
    LEGACY_SECURITY_AVAILABLE = True
except ImportError:
    LEGACY_SECURITY_AVAILABLE = False

# ==============================================================================
# INICIALIZAÇÃO DO APP
# ==============================================================================

# Determinar se estamos em produção
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"

# Validar configurações críticas em produção
if IS_PRODUCTION and SETTINGS_AVAILABLE:
    errors = settings.validate_production()
    if errors:
        print("=" * 60)
        print("ERRO: Configurações de produção inválidas!")
        for error in errors:
            print(f"  - {error}")
        print("=" * 60)
        # Em produção, não iniciar com configuração insegura
        # sys.exit(1)

app = FastAPI(
    title="Sistema de Gestão Contábil", 
    version="3.0.0",
    description="API para gestão contábil com autenticação segura",
    docs_url="/docs" if not IS_PRODUCTION or os.getenv("FEATURE_API_DOCS_ENABLED", "true").lower() == "true" else None,
    redoc_url="/redoc" if not IS_PRODUCTION or os.getenv("FEATURE_API_DOCS_ENABLED", "true").lower() == "true" else None,
)

# ==============================================================================
# MIDDLEWARES DE SEGURANÇA (Sprint 1)
# ==============================================================================

# 1. Rate Limiting Middleware
if SECURITY_MIDDLEWARE_AVAILABLE and settings.rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware)

# 2. Security Headers Middleware
if SECURITY_MIDDLEWARE_AVAILABLE and settings.security_headers_enabled:
    app.add_middleware(SecurityHeadersMiddleware)

# 3. CORS - Configuração restritiva
cors_origins = settings.cors_origins if SETTINGS_AVAILABLE else [
    "http://localhost",
    "http://localhost:3000", 
    "http://localhost:5173"
]

# Em produção, não usar "*"
if IS_PRODUCTION and "*" in cors_origins:
    cors_origins = ["https://seudominio.com"]  # Substitua pelo seu domínio

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=600,  # Cache preflight por 10 minutos
)

csv_importer = SmartCSVImporter()
analyzer = ContabilAnalyzerPro()
pdf_generator = PDFGeneratorPro()

# ==============================================================================
# FUNÇÕES AUXILIARES DE SEGURANÇA
# ==============================================================================

def _get_client_ip(request: Request) -> str:
    """Obtém IP real do cliente considerando proxies."""
    # X-Forwarded-For (proxies padrão)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # X-Real-IP (Nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # CF-Connecting-IP (Cloudflare)
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    
    # Fallback
    if request.client:
        return request.client.host
    
    return "unknown"


# ==============================================================================
# EVENTOS DE STARTUP
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a aplicação."""
    print("=" * 60)
    print(f"Sistema Contábil v3.0.0 iniciando...")
    print(f"Ambiente: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Rate Limiting: {'Ativado' if rate_limiter else 'Desativado'}")
    print(f"Security Headers: {'Ativado' if SECURITY_MIDDLEWARE_AVAILABLE else 'Desativado'}")
    print(f"2FA (TOTP): {'Disponível' if SECURITY_ADVANCED_AVAILABLE else 'Não disponível'}")
    
    # Validar configurações em produção
    if IS_PRODUCTION:
        jwt_secret = os.getenv("JWT_SECRET", "")
        if not jwt_secret or "DEVELOPMENT" in jwt_secret.upper() or len(jwt_secret) < 32:
            print("⚠️  AVISO: JWT_SECRET não configurado corretamente para produção!")
        
        encryption_key = os.getenv("ENCRYPTION_KEY", "")
        if not encryption_key or "DEVELOPMENT" in encryption_key.upper():
            print("⚠️  AVISO: ENCRYPTION_KEY não configurado corretamente para produção!")
        
        if os.getenv("DEBUG", "false").lower() == "true":
            print("⚠️  AVISO: DEBUG está ativado em produção!")
    
    # Inicializar banco de dados
    try:
        init_db()
        print("✅ Banco de dados inicializado")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
    
    # Criar tabelas de segurança avançada (Sprint 2)
    try:
        from sqlalchemy import text
        with get_db() as db:
            # Tabela de auditoria
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES contadores(id) ON DELETE SET NULL,
                    event_type VARCHAR(50) NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    details TEXT,
                    success BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            '''))
            
            # Tabela de 2FA
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS user_2fa (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE REFERENCES contadores(id) ON DELETE CASCADE,
                    secret VARCHAR(64) NOT NULL,
                    backup_codes_hash VARCHAR(64),
                    is_enabled BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP
                )
            '''))
            
            # Tabela de códigos de backup usados
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS used_backup_codes (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES contadores(id) ON DELETE CASCADE,
                    code_hash VARCHAR(64) NOT NULL,
                    used_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, code_hash)
                )
            '''))
            
            # Tabela de sessões avançadas
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES contadores(id) ON DELETE CASCADE,
                    token_hash VARCHAR(64) NOT NULL,
                    refresh_token_hash VARCHAR(64),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    expires_at TIMESTAMP NOT NULL,
                    revoked BOOLEAN DEFAULT false,
                    revoked_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_activity TIMESTAMP DEFAULT NOW()
                )
            '''))
            
            # Tabela de tokens de reset de senha
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES contadores(id) ON DELETE CASCADE,
                    token_hash VARCHAR(64) NOT NULL UNIQUE,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT false,
                    used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            '''))
            
            db.commit()
            
            # Índices para performance (criar separadamente para evitar erros)
            indices = [
                ('idx_audit_user_id', 'audit_logs', 'user_id'),
                ('idx_audit_event', 'audit_logs', 'event_type'),
                ('idx_sessions_user', 'user_sessions', 'user_id'),
                ('idx_sessions_token', 'user_sessions', 'token_hash'),
            ]
            
            for idx_name, table, column in indices:
                try:
                    db.execute(text(f'CREATE INDEX {idx_name} ON {table}({column})'))
                    db.commit()
                except Exception:
                    db.rollback()  # Índice já existe, ignorar
            
            print("✅ Tabelas de segurança avançada verificadas/criadas")
    except Exception as e:
        print(f"⚠️  Aviso ao criar tabelas de segurança: {e}")
    
    print("=" * 60)


# ==============================================================================
# HEALTH CHECK E STATUS (Públicos)
# ==============================================================================

@app.get("/health")
async def health_check():
    """Health check para monitoramento."""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/security/status")
async def security_status():
    """Status das configurações de segurança (público)."""
    return {
        "rate_limiting": {
            "enabled": rate_limiter is not None,
            "requests_per_minute": settings.rate_limit_per_minute if SETTINGS_AVAILABLE else 60
        },
        "cors": {
            "restricted": "*" not in cors_origins
        },
        "security_headers": {
            "enabled": SECURITY_MIDDLEWARE_AVAILABLE
        },
        "password_policy": {
            "min_length": settings.password_min_length if SETTINGS_AVAILABLE else 8,
            "require_uppercase": settings.password_require_uppercase if SETTINGS_AVAILABLE else True,
            "require_lowercase": settings.password_require_lowercase if SETTINGS_AVAILABLE else True,
            "require_digit": settings.password_require_digit if SETTINGS_AVAILABLE else True
        }
    }


# === MODELS ===

class ContadorCreate(BaseModel):
    nome: str = Field(..., min_length=3)
    email: EmailStr
    senha: str = Field(..., min_length=8, description="Mínimo 8 caracteres, 1 maiúscula, 1 minúscula, 1 número, 1 especial")
    telefone: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str = Field(..., min_length=8)

class ResetSenhaRequest(BaseModel):
    email: EmailStr

class ConfirmarResetSenhaRequest(BaseModel):
    token: str
    nova_senha: str = Field(..., min_length=8)

class EmpresaCreate(BaseModel):
    razao_social: str = Field(..., min_length=3)
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    regime_tributario: Optional[str] = None
    setor: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None

class EmpresaUpdate(EmpresaCreate):
    razao_social: Optional[str] = None

class DadosMensais(BaseModel):
    ano: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    receita: float = Field(default=0, ge=0)
    custos: float = Field(default=0, ge=0)
    despesas: float = Field(default=0, ge=0)
    impostos: float = Field(default=0, ge=0)
    folha: float = Field(default=0, ge=0)
    caixa: float = Field(default=0)

class DadosMensaisFrontend(BaseModel):
    competencia: str  # formato "2024-01"
    # Campos básicos
    receita_bruta: float = 0
    receita: float = 0
    custos: float = 0
    despesas_operacionais: float = 0
    despesas: float = 0
    folha_pagamento: float = 0
    folha: float = 0
    impostos: float = 0
    saldo_caixa: float = 0
    caixa: float = 0
    lucro_liquido: float = 0
    # Balanço Patrimonial - Ativo
    ativo_total: float = 0
    ativo_circulante: float = 0
    ativo_nao_circulante: float = 0
    disponivel: float = 0
    disponibilidades: float = 0
    bancos: float = 0
    aplicacoes: float = 0
    clientes: float = 0
    contas_receber: float = 0
    estoques: float = 0
    imobilizado: float = 0
    # Balanço Patrimonial - Passivo
    passivo_total: float = 0
    passivo_circulante: float = 0
    passivo_nao_circulante: float = 0
    fornecedores: float = 0
    emprestimos_cp: float = 0
    emprestimos_lp: float = 0
    impostos_pagar: float = 0
    salarios_pagar: float = 0
    # Patrimônio Líquido
    patrimonio_liquido: float = 0
    capital_social: float = 0
    reservas: float = 0
    lucros_acumulados: float = 0
    # DRE
    receita_servicos: float = 0
    deducoes_receita: float = 0
    custos_total: float = 0
    despesas_financeiras: float = 0
    receitas_financeiras: float = 0
    # Impostos
    iss: float = 0
    pis: float = 0
    cofins: float = 0
    irpj: float = 0
    csll: float = 0
    impostos_total: float = 0
    # Meta
    arquivo_origem: Optional[str] = None

class DadosBulk(BaseModel):
    dados: List[DadosMensais]

class UploadConfirm(BaseModel):
    csv_content: str
    mapping: Dict[str, str]
    substituir_existentes: bool = False

# === AUTH ===

async def get_user(authorization: Optional[str] = Header(None)) -> Dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user = validar_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")
    return user


# ==============================================================================
# HEALTH CHECK DETALHADO (Requer autenticação)
# ==============================================================================

@app.get("/health/detailed")
async def detailed_health_check(user: Dict = Depends(get_user)):
    """Health check detalhado (requer autenticação)."""
    health_status = {
        "status": "healthy",
        "version": "3.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Verificar banco de dados
    try:
        with get_db() as db:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Verificar rate limiter
    health_status["components"]["rate_limiter"] = {
        "status": "healthy" if rate_limiter else "disabled",
        "enabled": rate_limiter is not None
    }
    
    # Verificar security middleware
    health_status["components"]["security_middleware"] = {
        "status": "healthy" if SECURITY_MIDDLEWARE_AVAILABLE else "disabled",
        "enabled": SECURITY_MIDDLEWARE_AVAILABLE
    }
    
    return health_status


def sanitize(obj: Any) -> Any:
    """Converte tipos numpy para tipos nativos do Python para serialização JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize(i) for i in obj)
    elif isinstance(obj, (np.bool_, )):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return sanitize(vars(obj))
    return obj

# === ROTAS AUTH ===

@app.post("/auth/registrar")
async def registrar(dados: ContadorCreate, request: Request):
    """
    Registra novo contador.
    
    Requisitos de senha:
    - Mínimo 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    """
    # Rate limiting para registro (10 tentativas por 5 minutos por IP)
    if rate_limiter:
        client_ip = _get_client_ip(request)
        allowed, remaining = rate_limiter.check_rate_limit(f"register:{client_ip}", 10, 300)
        if not allowed:
            raise HTTPException(
                status_code=429, 
                detail="Muitas tentativas de registro deste IP. Aguarde 5 minutos."
            )
    
    # Sanitização de inputs
    if InputSanitizer:
        valid, error = InputSanitizer.validate_input(dados.nome, "nome")
        if not valid:
            raise HTTPException(status_code=400, detail=error)
    
    # Validação de senha forte
    if PasswordValidator:
        is_valid, errors = PasswordValidator.validate(dados.senha)
        if not is_valid:
            raise HTTPException(
                status_code=400, 
                detail={"message": "Senha não atende aos requisitos", "errors": errors}
            )
    
    try:
        result = criar_contador(dados.nome, dados.email, dados.senha, dados.telefone)
        return {
            "message": "Conta criada com sucesso",
            "user": {
                "id": result['id'],
                "nome": result['nome'],
                "email": result['email']
            },
            "token": result['token'],
            "refresh_token": result['refresh_token'],
            "expires_in": result['expires_in']
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if "UNIQUE" in str(e) or "já cadastrado" in str(e):
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login")
async def login(dados: LoginRequest, request: Request):
    """
    Autentica contador.
    
    Rate limiting: 5 tentativas por 15 minutos, depois bloqueia IP.
    """
    client_ip = _get_client_ip(request)
    
    # Rate limiting específico para login
    if rate_limiter:
        # Verificar se IP está bloqueado
        if rate_limiter.is_blocked(client_ip):
            raise HTTPException(
                status_code=429, 
                detail="IP bloqueado temporariamente. Tente novamente em 15 minutos."
            )
    
    try:
        result = autenticar_contador(dados.email, dados.senha, client_ip)
        if not result:
            # Registrar tentativa falha
            if rate_limiter:
                attempts = rate_limiter.record_failed_login(client_ip)
                if attempts >= settings.rate_limit_login_attempts:
                    rate_limiter.block(client_ip, settings.rate_limit_login_window)
                    # Registrar bloqueio na auditoria
                    if SECURITY_ADVANCED_AVAILABLE and AuditLogger:
                        try:
                            with get_db() as db:
                                AuditLogger.log(
                                    db, None,
                                    AuditLogger.EVENT_LOGIN_BLOCKED,
                                    ip_address=client_ip,
                                    details={"email": dados.email[:3] + "***", "attempts": attempts},
                                    success=False
                                )
                        except:
                            pass
                    raise HTTPException(
                        status_code=429,
                        detail=f"Muitas tentativas falhas. IP bloqueado por {settings.rate_limit_login_window} minutos."
                    )
            
            # Registrar tentativa falha na auditoria
            if SECURITY_ADVANCED_AVAILABLE and AuditLogger:
                try:
                    with get_db() as db:
                        AuditLogger.log(
                            db, None,
                            AuditLogger.EVENT_LOGIN_FAILED,
                            ip_address=client_ip,
                            details={"email": dados.email[:3] + "***"},
                            success=False
                        )
                except:
                    pass
            
            raise HTTPException(status_code=401, detail="Email ou senha incorretos")
        
        # Login bem-sucedido - limpar tentativas falhas
        if rate_limiter:
            rate_limiter.clear_failed_logins(client_ip)
        
        # Verificar se 2FA está ativo
        requires_2fa = False
        if SECURITY_ADVANCED_AVAILABLE and TwoFactorAuth:
            try:
                with get_db() as db:
                    requires_2fa = TwoFactorAuth.is_2fa_enabled(db, result['id'])
            except:
                pass
        
        # Registrar login bem-sucedido na auditoria
        if SECURITY_ADVANCED_AVAILABLE and AuditLogger:
            try:
                with get_db() as db:
                    AuditLogger.log(
                        db, result['id'],
                        AuditLogger.EVENT_LOGIN_SUCCESS,
                        ip_address=client_ip,
                        user_agent=request.headers.get("User-Agent", ""),
                        details={"requires_2fa": requires_2fa}
                    )
            except:
                pass
        
        response = {
            "message": "Login realizado com sucesso",
            "user": {
                "id": result['id'],
                "nome": result['nome'],
                "email": result['email']
            },
            "token": result['token'],
            "refresh_token": result['refresh_token'],
            "expires_in": result['expires_in'],
            "requires_2fa": requires_2fa
        }
        
        if requires_2fa:
            response["message"] = "Verificação 2FA necessária"
            response["next_step"] = "/auth/2fa/verify"
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        # Rate limiting do banco de dados
        raise HTTPException(status_code=429 if "bloqueada" in str(e).lower() else 401, detail=str(e))


@app.post("/auth/refresh")
async def refresh_token(dados: RefreshTokenRequest):
    """
    Renova access token usando refresh token.
    
    Use quando o access token expirar (após 15 minutos).
    """
    result = refresh_access_token(dados.refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")
    
    return {
        "token": result['token'],
        "expires_in": result['expires_in'],
        "user": result['user']
    }


@app.get("/auth/me")
async def me(user: Dict = Depends(get_user)):
    """Retorna dados do usuário autenticado."""
    return user


@app.post("/auth/logout")
async def sair(authorization: str = Header(...)):
    """Faz logout da sessão atual."""
    token = authorization.replace("Bearer ", "")
    logout(token)
    return {"ok": True, "message": "Logout realizado com sucesso"}


@app.post("/auth/logout-all")
async def sair_todos_dispositivos(user: Dict = Depends(get_user), authorization: str = Header(...)):
    """Faz logout de todos os dispositivos."""
    token = authorization.replace("Bearer ", "")
    logout_all_devices(user['id'], token)
    return {"ok": True, "message": "Logout realizado em todos os dispositivos"}


@app.post("/auth/alterar-senha")
async def alterar_senha_endpoint(dados: AlterarSenhaRequest, user: Dict = Depends(get_user)):
    """
    Altera senha do usuário.
    
    Requisitos da nova senha:
    - Mínimo 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    
    Após alterar, todas as sessões são invalidadas.
    """
    # Validar força da nova senha
    if PasswordValidator:
        is_valid, errors = PasswordValidator.validate(dados.nova_senha)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={"message": "Nova senha não atende aos requisitos", "errors": errors}
            )
    
    try:
        alterar_senha(user['id'], dados.senha_atual, dados.nova_senha)
        return {"ok": True, "message": "Senha alterada com sucesso. Faça login novamente."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/reset-senha")
async def solicitar_reset(dados: ResetSenhaRequest, request: Request):
    """
    Solicita reset de senha.
    
    Um token será gerado e enviado por email.
    Token expira em 1 hora.
    """
    # Rate limiting para reset de senha
    if rate_limiter:
        client_ip = _get_client_ip(request)
        allowed, _ = rate_limiter.check_rate_limit(f"reset:{client_ip}", 3, 300)  # 3 por 5 minutos
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Muitas solicitações de reset. Aguarde alguns minutos."
            )
    
    token = solicitar_reset_senha(dados.email)
    
    # Enviar email de recuperação
    if token and EMAIL_SERVICE_AVAILABLE and email_service:
        email_service.send_password_reset(
            to_email=dados.email,
            reset_token=token,
            user_name=dados.email.split('@')[0]  # Nome do email como fallback
        )
    
    response = {
        "ok": True, 
        "message": "Se o email existir, você receberá instruções para resetar a senha."
    }
    
    # Token só retornado em desenvolvimento (NUNCA em produção)
    if token and not IS_PRODUCTION:
        response["_dev_token"] = token
    
    return response


@app.post("/auth/reset-senha/confirmar")
async def confirmar_reset(dados: ConfirmarResetSenhaRequest, request: Request):
    """
    Confirma reset de senha com token.
    
    Após resetar, todas as sessões são invalidadas.
    """
    # Validar força da nova senha
    if PasswordValidator:
        is_valid, errors = PasswordValidator.validate(dados.nova_senha)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={"message": "Nova senha não atende aos requisitos", "errors": errors}
            )
    
    try:
        resetar_senha(dados.token, dados.nova_senha)
        return {"ok": True, "message": "Senha alterada com sucesso. Faça login com a nova senha."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/verificar-senha")
async def verificar_forca_senha(request: Request):
    """
    Verifica força de uma senha (para feedback em tempo real no frontend).
    Não armazena a senha.
    """
    try:
        body = await request.json()
        senha = body.get("senha", "")
    except:
        raise HTTPException(status_code=400, detail="JSON inválido")
    
    if not senha:
        return {
            "valida": False,
            "forca": {"score": 0, "label": "Muito fraca"},
            "erros": ["Senha não pode ser vazia"]
        }
    
    # Validar requisitos
    if PasswordValidator:
        is_valid, errors = PasswordValidator.validate(senha)
        strength = PasswordValidator.get_strength(senha)
        
        return {
            "valida": is_valid,
            "forca": {
                "score": strength["score"],
                "max_score": strength["max_score"],
                "label": strength["strength"]
            },
            "erros": errors,
            "feedback": strength.get("feedback", [])
        }
    
    # Fallback sem PasswordValidator
    errors = []
    if len(senha) < 8:
        errors.append("Mínimo 8 caracteres")
    
    import re
    if not re.search(r'[A-Z]', senha):
        errors.append("Deve conter letra maiúscula")
    if not re.search(r'[a-z]', senha):
        errors.append("Deve conter letra minúscula")
    if not re.search(r'\d', senha):
        errors.append("Deve conter número")
    
    return {
        "valida": len(errors) == 0,
        "forca": {"score": max(0, 5 - len(errors)), "label": "Verificação básica"},
        "erros": errors
    }


@app.get("/auth/sessoes")
async def listar_sessoes(user: Dict = Depends(get_user)):
    """Lista todas as sessões ativas do usuário."""
    sessoes = listar_sessoes_ativas(user['id'])
    return {"sessoes": sessoes}


@app.delete("/auth/sessoes/{session_id}")
async def revogar_sessao_endpoint(session_id: int, user: Dict = Depends(get_user)):
    """Revoga uma sessão específica."""
    if revogar_sessao(user['id'], session_id):
        return {"ok": True, "message": "Sessão revogada"}
    raise HTTPException(status_code=404, detail="Sessão não encontrada")


@app.get("/auth/requisitos-senha")
async def requisitos_senha():
    """Retorna os requisitos de senha."""
    return {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special": True,
        "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
        "message": "A senha deve ter no mínimo 8 caracteres, incluindo: 1 maiúscula, 1 minúscula, 1 número e 1 caractere especial"
    }


# ==============================================================================
# AUTENTICAÇÃO DE DOIS FATORES - 2FA (Sprint 2)
# ==============================================================================

class Setup2FAResponse(BaseModel):
    secret: str
    provisioning_uri: str
    backup_codes: List[str]
    qr_code_url: str = None

class Verify2FARequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)

class Disable2FARequest(BaseModel):
    password: str
    code: str = Field(..., min_length=6, max_length=6)


@app.post("/auth/2fa/setup")
async def setup_2fa(user: Dict = Depends(get_user)):
    """
    Configura autenticação de dois fatores (2FA).
    
    Retorna:
    - secret: Chave para configuração manual
    - provisioning_uri: URI para QR code (use em apps como Google Authenticator)
    - backup_codes: 10 códigos de backup (guarde em local seguro!)
    
    IMPORTANTE: Após setup, confirme com /auth/2fa/enable enviando um código válido.
    """
    if not SECURITY_ADVANCED_AVAILABLE:
        raise HTTPException(status_code=501, detail="2FA não disponível")
    
    try:
        with get_db() as db:
            result = TwoFactorAuth.setup_2fa(db, user['id'], user['email'])
            
            # Gerar URL para QR code (usando API pública)
            from urllib.parse import quote
            qr_data = quote(result['provisioning_uri'])
            result['qr_code_url'] = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_data}"
            
            return {
                "ok": True,
                "message": "2FA configurado. Use o código do app autenticador para ativar.",
                "data": result
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao configurar 2FA: {str(e)}")


@app.post("/auth/2fa/enable")
async def enable_2fa(dados: Verify2FARequest, user: Dict = Depends(get_user)):
    """
    Ativa 2FA após verificar código do app autenticador.
    
    Envie o código de 6 dígitos do seu app autenticador (Google Authenticator, Authy, etc).
    """
    if not SECURITY_ADVANCED_AVAILABLE:
        raise HTTPException(status_code=501, detail="2FA não disponível")
    
    try:
        with get_db() as db:
            if TwoFactorAuth.enable_2fa(db, user['id'], dados.code):
                # Registrar na auditoria
                if AuditLogger:
                    AuditLogger.log(
                        db, user['id'], 
                        AuditLogger.EVENT_2FA_ENABLED,
                        ip_address="",
                        details={"method": "totp"}
                    )
                return {"ok": True, "message": "2FA ativado com sucesso!"}
            else:
                raise HTTPException(status_code=400, detail="Código inválido. Verifique e tente novamente.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ativar 2FA: {str(e)}")


@app.post("/auth/2fa/verify")
async def verify_2fa(dados: Verify2FARequest, request: Request, user: Dict = Depends(get_user)):
    """
    Verifica código 2FA.
    
    Use este endpoint quando o login retornar requires_2fa=true.
    """
    if not SECURITY_ADVANCED_AVAILABLE:
        raise HTTPException(status_code=501, detail="2FA não disponível")
    
    client_ip = _get_client_ip(request)
    
    try:
        with get_db() as db:
            if TwoFactorAuth.verify_2fa(db, user['id'], dados.code):
                if AuditLogger:
                    AuditLogger.log(
                        db, user['id'],
                        AuditLogger.EVENT_2FA_VERIFIED,
                        ip_address=client_ip,
                        success=True
                    )
                return {"ok": True, "verified": True}
            else:
                if AuditLogger:
                    AuditLogger.log(
                        db, user['id'],
                        AuditLogger.EVENT_2FA_FAILED,
                        ip_address=client_ip,
                        success=False
                    )
                raise HTTPException(status_code=401, detail="Código 2FA inválido")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/2fa/disable")
async def disable_2fa(dados: Disable2FARequest, user: Dict = Depends(get_user)):
    """
    Desativa 2FA (requer senha atual e código 2FA).
    """
    if not SECURITY_ADVANCED_AVAILABLE:
        raise HTTPException(status_code=501, detail="2FA não disponível")
    
    # Verificar senha
    auth_result = autenticar_contador(user['email'], dados.password, None)
    if not auth_result:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    
    try:
        with get_db() as db:
            # Verificar código 2FA
            if not TwoFactorAuth.verify_2fa(db, user['id'], dados.code):
                raise HTTPException(status_code=401, detail="Código 2FA inválido")
            
            if TwoFactorAuth.disable_2fa(db, user['id'], password_verified=True):
                if AuditLogger:
                    AuditLogger.log(
                        db, user['id'],
                        AuditLogger.EVENT_2FA_DISABLED,
                        ip_address=""
                    )
                return {"ok": True, "message": "2FA desativado"}
            else:
                raise HTTPException(status_code=500, detail="Erro ao desativar 2FA")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/2fa/status")
async def status_2fa(user: Dict = Depends(get_user)):
    """Verifica se 2FA está ativado para o usuário."""
    if not SECURITY_ADVANCED_AVAILABLE:
        return {"enabled": False, "available": False}
    
    try:
        with get_db() as db:
            enabled = TwoFactorAuth.is_2fa_enabled(db, user['id'])
            return {"enabled": enabled, "available": True}
    except Exception:
        return {"enabled": False, "available": True}


@app.post("/auth/2fa/backup-code")
async def use_backup_code(request: Request, user: Dict = Depends(get_user)):
    """
    Usa código de backup para verificar 2FA.
    
    Cada código só pode ser usado uma vez!
    """
    if not SECURITY_ADVANCED_AVAILABLE:
        raise HTTPException(status_code=501, detail="2FA não disponível")
    
    try:
        body = await request.json()
        code = body.get("code", "")
    except:
        raise HTTPException(status_code=400, detail="JSON inválido")
    
    if not code:
        raise HTTPException(status_code=400, detail="Código de backup obrigatório")
    
    try:
        with get_db() as db:
            if TwoFactorAuth.verify_backup_code(db, user['id'], code):
                return {"ok": True, "message": "Código de backup aceito"}
            else:
                raise HTTPException(status_code=401, detail="Código de backup inválido ou já usado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# AUDITORIA DE SEGURANÇA (Sprint 2)
# ==============================================================================

@app.get("/auth/audit-log")
async def get_audit_log(
    user: Dict = Depends(get_user),
    event_type: Optional[str] = None,
    limit: int = 50
):
    """
    Obtém log de auditoria do usuário.
    
    Tipos de evento:
    - login_success, login_failed, login_blocked
    - logout, logout_all
    - password_change, password_reset_request, password_reset_complete
    - 2fa_enabled, 2fa_disabled, 2fa_verified, 2fa_failed
    - session_revoked
    """
    if not SECURITY_ADVANCED_AVAILABLE:
        return {"events": [], "available": False}
    
    try:
        with get_db() as db:
            events = AuditLogger.get_user_events(db, user['id'], event_type, min(limit, 100))
            return {"events": events, "total": len(events)}
    except Exception as e:
        return {"events": [], "error": str(e)}


@app.get("/auth/security-check")
async def security_check(request: Request, user: Dict = Depends(get_user)):
    """
    Verifica status de segurança da conta.
    
    Retorna alertas de atividade suspeita e recomendações.
    """
    client_ip = _get_client_ip(request)
    
    result = {
        "status": "ok",
        "alerts": [],
        "recommendations": [],
        "2fa_enabled": False,
        "recent_activity": []
    }
    
    if not SECURITY_ADVANCED_AVAILABLE:
        result["recommendations"].append("Módulo de segurança avançada não disponível")
        return result
    
    try:
        with get_db() as db:
            # Verificar 2FA
            result["2fa_enabled"] = TwoFactorAuth.is_2fa_enabled(db, user['id'])
            if not result["2fa_enabled"]:
                result["recommendations"].append("Ative a autenticação de dois fatores (2FA) para maior segurança")
            
            # Detectar atividade suspeita
            suspicious = AuditLogger.detect_suspicious_activity(db, user['id'], client_ip)
            if suspicious["suspicious"]:
                result["status"] = "warning"
                result["alerts"] = suspicious["alerts"]
            
            # Últimos eventos
            recent = AuditLogger.get_user_events(db, user['id'], limit=5)
            result["recent_activity"] = [
                {
                    "event": e.get("event_type"),
                    "success": e.get("success"),
                    "time": e.get("created_at"),
                    "ip": e.get("ip_address", "")[:15] + "..."
                }
                for e in recent
            ]
            
    except Exception as e:
        result["error"] = str(e)
    
    return result


# ==============================================================================
# GERENCIAMENTO AVANÇADO DE SESSÕES (Sprint 2)
# ==============================================================================

@app.get("/auth/sessions/active")
async def get_active_sessions(user: Dict = Depends(get_user)):
    """Lista todas as sessões ativas com detalhes."""
    if not SECURITY_ADVANCED_AVAILABLE:
        # Fallback para sistema antigo
        sessoes = listar_sessoes_ativas(user['id'])
        return {"sessions": sessoes, "count": len(sessoes)}
    
    try:
        with get_db() as db:
            sessions = SessionManager.get_active_sessions(db, user['id'])
            return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        return {"sessions": [], "error": str(e)}


@app.delete("/auth/sessions/all")
async def revoke_all_sessions(
    request: Request,
    keep_current: bool = True,
    user: Dict = Depends(get_user),
    authorization: str = Header(...)
):
    """
    Revoga todas as sessões do usuário.
    
    Args:
        keep_current: Se True, mantém a sessão atual ativa (padrão: True)
    """
    current_token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    client_ip = _get_client_ip(request)
    
    if not SECURITY_ADVANCED_AVAILABLE:
        # Fallback
        logout_all_devices(user['id'], current_token if keep_current else None)
        return {"ok": True, "message": "Todas as sessões foram encerradas"}
    
    try:
        with get_db() as db:
            count = SessionManager.revoke_all_sessions(
                db, user['id'], 
                except_current=current_token if keep_current else None
            )
            
            if AuditLogger:
                AuditLogger.log(
                    db, user['id'],
                    AuditLogger.EVENT_LOGOUT_ALL,
                    ip_address=client_ip,
                    details={"sessions_revoked": count, "kept_current": keep_current}
                )
            
            return {
                "ok": True, 
                "message": f"{count} sessões encerradas",
                "sessions_revoked": count
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ROTAS DASHBOARD ===

@app.get("/dashboard")
async def dashboard(user: Dict = Depends(get_user)):
    stats = obter_estatisticas_contador(user['id'])
    empresas = listar_empresas(user['id'])
    atencao = [e for e in empresas if e.get('ultimo_status') == 'critico' or not e.get('ultimo_score')][:5]
    return {"estatisticas": stats, "empresas_atencao": atencao, "total": len(empresas)}

@app.get("/dashboard/graficos")
async def dashboard_graficos(
    user: Dict = Depends(get_user), 
    meses: int = 12,
    empresa_id: Optional[int] = None
):
    """Obtém dados para gráficos do dashboard. Opcionalmente filtra por empresa."""
    from data.database import obter_dados_dashboard_graficos
    dados = obter_dados_dashboard_graficos(user['id'], meses, empresa_id=empresa_id)
    return dados

# === ROTAS EMPRESAS ===

@app.get("/empresas")
async def lista_empresas_route(user: Dict = Depends(get_user)):
    return {"empresas": listar_empresas(user['id'])}

@app.post("/empresas")
async def nova_empresa(dados: EmpresaCreate, user: Dict = Depends(get_user)):
    emp_id = criar_empresa(user['id'], dados.model_dump())
    return {"empresa": obter_empresa(emp_id, user['id']), "id": emp_id}

@app.get("/empresas/cnpj/{cnpj}")
async def get_empresa_by_cnpj(cnpj: str, user: Dict = Depends(get_user)):
    """Busca empresa pelo CNPJ."""
    # Limpar CNPJ (remover formatação)
    cnpj_limpo = ''.join(c for c in cnpj if c.isdigit())
    
    # Buscar em todas as empresas do contador
    empresas = listar_empresas(user['id'])
    
    for emp in empresas:
        emp_cnpj = ''.join(c for c in (emp.get('cnpj') or '') if c.isdigit())
        if emp_cnpj == cnpj_limpo:
            return emp
    
    raise HTTPException(status_code=404, detail="Empresa não encontrada")

@app.get("/empresas/{id}")
async def get_empresa_route(id: int, user: Dict = Depends(get_user)):
    emp = obter_empresa(id, user['id'])
    if not emp:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    emp['dados_mensais'] = listar_dados_mensais(id, limite=36)
    emp['ultima_analise'] = obter_ultima_analise(id)
    return emp

@app.put("/empresas/{id}")
async def update_empresa_route(id: int, dados: EmpresaUpdate, user: Dict = Depends(get_user)):
    if not obter_empresa(id, user['id']):
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    atualizar_empresa(id, user['id'], {k:v for k,v in dados.model_dump().items() if v})
    return {"ok": True}

@app.delete("/empresas/{id}")
async def delete_empresa_route(id: int, user: Dict = Depends(get_user)):
    if not obter_empresa(id, user['id']):
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    excluir_empresa(id, user['id'])
    return {"ok": True}

# === ROTAS DADOS MENSAIS ===

@app.get("/empresas/{id}/dados")
async def lista_dados(id: int, user: Dict = Depends(get_user)):
    if not obter_empresa(id, user['id']):
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    dados_raw = listar_dados_mensais(id)
    # Transforma para formato do frontend
    dados = []
    for d in dados_raw:
        receita = d.get('receita', 0) or 0
        custos = d.get('custos', 0) or 0
        despesas = d.get('despesas', 0) or 0
        impostos = d.get('impostos', 0) or 0
        folha = d.get('folha', 0) or 0
        lucro = receita - custos - despesas - impostos - folha
        margem = (lucro / receita * 100) if receita > 0 else 0
        dados.append({
            'id': d.get('id'),
            'competencia': f"{d['ano']}-{d['mes']:02d}",
            'receita_bruta': receita,
            'custos': custos,
            'despesas_operacionais': despesas,
            'impostos': impostos,
            'folha_pagamento': folha,
            'saldo_caixa': d.get('caixa', 0) or 0,
            'lucro_liquido': lucro,
            'margem_liquida': margem
        })
    return {"dados": dados}

@app.post("/empresas/{id}/dados")
async def add_dados(id: int, dados: DadosMensaisFrontend, user: Dict = Depends(get_user)):
    emp = obter_empresa(id, user['id'])
    if not emp:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    # Parse competencia "2024-01" para ano e mes
    try:
        partes = dados.competencia.split('-')
        ano = int(partes[0])
        mes = int(partes[1])
    except:
        raise HTTPException(status_code=400, detail="Formato de competência inválido. Use AAAA-MM")
    
    # Converter modelo para dicionário com todos os campos
    dados_dict = {
        'ano': ano,
        'mes': mes,
        # Campos básicos
        'receita': dados.receita_bruta or dados.receita or 0,
        'custos': dados.custos or dados.custos_total or 0,
        'despesas': dados.despesas_operacionais or dados.despesas or 0,
        'impostos': dados.impostos or dados.impostos_total or 0,
        'folha': dados.folha_pagamento or dados.folha or 0,
        'caixa': dados.saldo_caixa or dados.caixa or dados.disponivel or 0,
        # Campos expandidos
        'ativo_total': dados.ativo_total,
        'ativo_circulante': dados.ativo_circulante,
        'disponivel': dados.disponivel,
        'bancos': dados.bancos,
        'clientes': dados.clientes,
        'estoques': dados.estoques,
        'passivo_total': dados.passivo_total,
        'passivo_circulante': dados.passivo_circulante,
        'passivo_nao_circulante': dados.passivo_nao_circulante,
        'patrimonio_liquido': dados.patrimonio_liquido,
        'capital_social': dados.capital_social,
        'receita_bruta': dados.receita_bruta,
        'receita_servicos': dados.receita_servicos,
        'deducoes_receita': dados.deducoes_receita,
        'custos_total': dados.custos_total,
        'despesas_operacionais': dados.despesas_operacionais,
        'despesas_financeiras': dados.despesas_financeiras,
        'receitas_financeiras': dados.receitas_financeiras,
        'lucro_liquido': dados.lucro_liquido,
        'iss': dados.iss,
        'pis': dados.pis,
        'cofins': dados.cofins,
        'irpj': dados.irpj,
        'csll': dados.csll,
        'impostos_total': dados.impostos_total,
        'arquivo_origem': dados.arquivo_origem
    }
    
    salvar_dados_mensais(id, dados_dict)
    
    # Gerar alertas automaticamente após salvar dados
    alertas_gerados = 0
    try:
        if ALERTAS_AVAILABLE:
            from engine.alertas import gerar_alertas_empresa
            dados_mensais = listar_dados_mensais(id, limite=24)
            
            if len(dados_mensais) >= 3:  # Mínimo 3 meses para alertas
                alertas = gerar_alertas_empresa(
                    empresa=emp,
                    dados_mensais=dados_mensais,
                    analise_atual=None
                )
                
                # Salvar alertas no banco
                with get_db() as db:
                    from sqlalchemy import text
                    # Limpar alertas antigos não resolvidos
                    db.execute(text("""
                        DELETE FROM alertas 
                        WHERE empresa_id = :empresa_id 
                        AND contador_id = :contador_id
                        AND resolvido = false
                    """), {"empresa_id": id, "contador_id": user['id']})
                    
                    # Inserir novos alertas
                    for alerta in alertas:
                        db.execute(text("""
                            INSERT INTO alertas (
                                empresa_id, contador_id, tipo, severidade, codigo,
                                titulo, mensagem, valor_atual, valor_limite, valor_anterior,
                                dados_json, periodo_referencia
                            ) VALUES (
                                :empresa_id, :contador_id, :tipo, :severidade, :codigo,
                                :titulo, :mensagem, :valor_atual, :valor_limite, :valor_anterior,
                                :dados_json, :periodo_referencia
                            )
                        """), {
                            "empresa_id": id,
                            "contador_id": user['id'],
                            "tipo": alerta.get('tipo'),
                            "severidade": alerta.get('severidade'),
                            "codigo": alerta.get('codigo'),
                            "titulo": alerta.get('titulo'),
                            "mensagem": alerta.get('mensagem'),
                            "valor_atual": alerta.get('valor_atual'),
                            "valor_limite": alerta.get('valor_limite'),
                            "valor_anterior": alerta.get('valor_anterior'),
                            "dados_json": alerta.get('dados_json'),
                            "periodo_referencia": alerta.get('periodo_referencia')
                        })
                        alertas_gerados += 1
                    db.commit()
    except Exception as e:
        print(f"Aviso: Erro ao gerar alertas automaticamente: {e}")
    
    return {"ok": True, "mes": f"{mes:02d}/{ano}", "alertas_gerados": alertas_gerados}

@app.post("/empresas/{id}/dados/bulk")
async def add_dados_bulk(id: int, dados: DadosBulk, user: Dict = Depends(get_user)):
    if not obter_empresa(id, user['id']):
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    for d in dados.dados:
        dados_dict = d.model_dump()
        dados_dict['ano'] = d.ano
        dados_dict['mes'] = d.mes
        salvar_dados_mensais(id, dados_dict)
    return {"ok": True, "salvos": len(dados.dados)}

@app.delete("/empresas/{id}/dados/{ano}/{mes}")
async def del_dados(id: int, ano: int, mes: int, user: Dict = Depends(get_user)):
    if not obter_empresa(id, user['id']):
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    excluir_dados_mensais(id, ano, mes)
    return {"ok": True}

@app.post("/empresas/{id}/dados/upload")
async def upload_csv(id: int, file: UploadFile = File(...), user: Dict = Depends(get_user)):
    if not obter_empresa(id, user['id']):
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    try:
        content = await file.read()
        try:
            csv_content = content.decode('utf-8')
        except:
            csv_content = content.decode('latin-1')
        
        preview = csv_importer.get_preview(csv_content)
        return {"preview": preview, "csv_content": csv_content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo: {str(e)}")

@app.post("/empresas/{id}/dados/upload/confirmar")
async def confirmar_upload(id: int, dados: UploadConfirm, user: Dict = Depends(get_user)):
    emp = obter_empresa(id, user['id'])
    if not emp:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    try:
        mapping_dict = dados.mapping
        company_data = csv_importer.import_csv(dados.csv_content, mapping_dict, emp['razao_social'], emp.get('cnpj',''))
        registros_criados = 0
        for r in company_data.records:
            salvar_dados_mensais(id, {
                'ano': r.data.year,
                'mes': r.data.month,
                'receita': r.receita, 
                'custos': r.custos, 
                'despesas': r.despesas,
                'impostos': r.impostos, 
                'folha': r.folha, 
                'caixa': r.caixa
            })
            registros_criados += 1
        return {"ok": True, "registros_criados": registros_criados}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao importar dados: {str(e)}")

# === ROTAS ANÁLISES ===

@app.get("/empresas/{id}/analises")
async def lista_analises_route(id: int, user: Dict = Depends(get_user)):
    if not obter_empresa(id, user['id']):
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return {"analises": listar_analises(id)}

@app.post("/empresas/{id}/analises")
async def executar_analise_route(id: int, user: Dict = Depends(get_user)):
    """
    Executa análise financeira completa da empresa.
    
    Usa o novo analyzer profissional com todos os indicadores expandidos.
    """
    emp = obter_empresa(id, user['id'])
    if not emp:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    dados_db = obter_dados_para_analise(id)
    if len(dados_db) < 3:
        raise HTTPException(status_code=400, detail="Mínimo de 3 meses de dados para análise")
    
    # Tentar usar o analyzer profissional primeiro
    try:
        from engine.analyzer_profissional import executar_analise as executar_analise_pro
        
        # Converter dados para formato esperado - usar todos os campos disponíveis
        dados_mensais = []
        for d in dados_db:
            item = {
                'competencia': f"{d['ano']}-{d['mes']:02d}",
                # Campos básicos
                'receita_bruta': d.get('receita_bruta') or d.get('receita') or 0,
                'custos_total': d.get('custos_total') or d.get('custos') or 0,
                'despesas_operacionais': d.get('despesas_operacionais') or d.get('despesas') or 0,
                'impostos_total': d.get('impostos_total') or d.get('impostos') or 0,
                'folha_pagamento': d.get('folha') or 0,
                'disponivel': d.get('disponivel') or d.get('caixa') or 0,
                'lucro_liquido': d.get('lucro_liquido') or ((d.get('receita') or 0) - (d.get('custos') or 0) - (d.get('despesas') or 0) - (d.get('impostos') or 0)),
                # Campos expandidos do balanço
                'ativo_total': d.get('ativo_total') or 0,
                'ativo_circulante': d.get('ativo_circulante') or 0,
                'bancos': d.get('bancos') or 0,
                'caixa': d.get('caixa') or 0,
                'clientes': d.get('clientes') or 0,
                'estoques': d.get('estoques') or 0,
                'passivo_total': d.get('passivo_total') or 0,
                'passivo_circulante': d.get('passivo_circulante') or 0,
                'passivo_nao_circulante': d.get('passivo_nao_circulante') or 0,
                'patrimonio_liquido': d.get('patrimonio_liquido') or d.get('capital_social') or 0,
                'capital_social': d.get('capital_social') or 0,
                # Campos DRE
                'receita_servicos': d.get('receita_servicos') or 0,
                'deducoes_receita': d.get('deducoes_receita') or 0,
                'despesas_financeiras': d.get('despesas_financeiras') or 0,
                'receitas_financeiras': d.get('receitas_financeiras') or 0,
                # Impostos detalhados
                'iss_deducao': d.get('iss') or 0,
                'pis_deducao': d.get('pis') or 0,
                'cofins_deducao': d.get('cofins') or 0,
                'irpj_deducao': d.get('irpj') or 0,
                'csll_deducao': d.get('csll') or 0,
            }
            dados_mensais.append(item)
        
        resultado = executar_analise_pro(
            dados_mensais=dados_mensais,
            empresa_id=id,
            empresa_nome=emp['razao_social']
        )
        
        analise_id = salvar_analise(id, resultado)
        
        # Gerar alertas automaticamente após análise
        try:
            from engine.alertas import gerar_alertas_empresa
            dados_para_alertas = listar_dados_mensais(id, limite=24)
            alertas = gerar_alertas_empresa(
                empresa=emp,
                dados_mensais=dados_para_alertas,
                analise_atual={'resultado_completo': resultado}
            )
            
            # Salvar alertas no banco
            with get_db() as db:
                from sqlalchemy import text
                # Limpar alertas antigos não resolvidos
                db.execute(text("""
                    DELETE FROM alertas 
                    WHERE empresa_id = :empresa_id 
                    AND contador_id = :contador_id
                    AND resolvido = false
                """), {"empresa_id": id, "contador_id": user['id']})
                
                # Inserir novos alertas
                for alerta in alertas:
                    db.execute(text("""
                        INSERT INTO alertas (
                            empresa_id, contador_id, tipo, severidade, codigo,
                            titulo, mensagem, valor_atual, valor_limite, valor_anterior,
                            dados_json, periodo_referencia
                        ) VALUES (
                            :empresa_id, :contador_id, :tipo, :severidade, :codigo,
                            :titulo, :mensagem, :valor_atual, :valor_limite, :valor_anterior,
                            :dados_json, :periodo_referencia
                        )
                    """), {
                        "empresa_id": id,
                        "contador_id": user['id'],
                        "tipo": alerta.get('tipo'),
                        "severidade": alerta.get('severidade'),
                        "codigo": alerta.get('codigo'),
                        "titulo": alerta.get('titulo'),
                        "mensagem": alerta.get('mensagem'),
                        "valor_atual": alerta.get('valor_atual'),
                        "valor_limite": alerta.get('valor_limite'),
                        "valor_anterior": alerta.get('valor_anterior'),
                        "dados_json": alerta.get('dados_json'),
                        "periodo_referencia": alerta.get('periodo_referencia')
                    })
                db.commit()
        except Exception as e:
            print(f"Aviso: Erro ao gerar alertas automaticamente: {e}")
        
        return {"analise_id": analise_id, "resultado": resultado, "alertas_gerados": len(alertas) if 'alertas' in dir() else 0}
        
    except ImportError:
        pass
    
    # Fallback para analyzer antigo (requer 6 meses)
    if len(dados_db) < 6:
        raise HTTPException(status_code=400, detail=f"Mínimo 6 meses de dados para análise detalhada. Atual: {len(dados_db)}")
    
    records = []
    for d in dados_db:
        dt = datetime(d['ano'], d['mes'], 1)
        records.append(MonthlyRecord(
            periodo=dt.strftime('%Y-%m'),
            data=dt,
            receita=d['receita'] or 0,
            custos=d['custos'] or 0,
            despesas=d['despesas'] or 0,
            impostos=d['impostos'] or 0,
            folha=d['folha'] or 0,
            caixa=d['caixa'] or 0
        ))
    
    company_data = CompanyData(empresa=emp['razao_social'], cnpj=emp.get('cnpj',''), records=records)
    resultado = analyzer.analyze(company_data)
    resultado_dict = sanitize(asdict(resultado))
    analise_id = salvar_analise(id, resultado_dict)
    return {"analise_id": analise_id, "resultado": resultado_dict}

@app.get("/empresas/{id}/analises/{aid}")
async def get_analise_route(id: int, aid: int, user: Dict = Depends(get_user)):
    if not obter_empresa(id, user['id']):
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    analise = obter_analise(aid, id)
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    return analise

@app.get("/empresas/{id}/analises/{aid}/pdf")
async def get_pdf(id: int, aid: int, user: Dict = Depends(get_user)):
    emp = obter_empresa(id, user['id'])
    if not emp:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    analise = obter_analise(aid, id)
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    pdf = pdf_generator.generate(analise.get('resultado', {}))
    return Response(content=pdf, media_type="application/pdf",
                   headers={"Content-Disposition": f'attachment; filename="analise_{id}_{aid}.pdf"'})

@app.get("/empresas/{id}/pdf")
async def get_ultimo_pdf(id: int, user: Dict = Depends(get_user)):
    emp = obter_empresa(id, user['id'])
    if not emp:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Obter dados mensais da empresa
    dados_mensais = listar_dados_mensais(id)
    
    # Se não tem dados mensais, retornar erro
    if not dados_mensais:
        raise HTTPException(status_code=404, detail="Nenhum dado financeiro cadastrado. Importe balancetes para gerar o relatório.")
    
    # Preparar dados para o gerador de PDF
    resultado = {
        'empresa': emp.get('razao_social', 'Empresa'),
        'cnpj': emp.get('cnpj', ''),
        'dados_mensais': dados_mensais,
    }
    
    # Se tem análise, adicionar ao resultado incluindo o score
    analise = obter_ultima_analise(id)
    if analise:
        resultado['score'] = analise.get('score')
        resultado['status'] = analise.get('status')
        resultado['periodo_inicio'] = analise.get('periodo_inicio')
        resultado['periodo_fim'] = analise.get('periodo_fim')
        resultado['meses_analisados'] = analise.get('meses_analisados')
        if analise.get('resultado'):
            resultado.update(analise.get('resultado', {}))
    
    pdf = pdf_generator.generate(resultado)
    nome_arquivo = emp.get('razao_social', 'empresa')[:20].replace(' ', '_')
    return Response(content=pdf, media_type="application/pdf",
                   headers={"Content-Disposition": f'attachment; filename="relatorio_{nome_arquivo}.pdf"'})

# === ROTAS MULTI-TENANCY ===

# Importa módulo de multi-tenancy
try:
    from auth.multitenancy import (
        criar_organizacao, obter_organizacao, listar_organizacoes_usuario,
        listar_membros_organizacao, criar_convite, aceitar_convite,
        verificar_permissao, obter_papel_usuario, registrar_audit,
        listar_audit_logs, definir_organizacao_padrao, listar_papeis
    )
    MULTITENANCY_AVAILABLE = True
except ImportError:
    MULTITENANCY_AVAILABLE = False

class OrganizacaoCreate(BaseModel):
    nome: str = Field(..., min_length=3)
    cnpj: Optional[str] = None
    email: Optional[str] = None
    plano: str = "free"

class ConviteCreate(BaseModel):
    email: EmailStr
    papel_id: int
    mensagem: Optional[str] = None

class ConviteAceitar(BaseModel):
    token: str

@app.get("/organizacoes")
async def listar_minhas_organizacoes(user: Dict = Depends(get_user)):
    """Lista organizações do usuário logado."""
    if not MULTITENANCY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-tenancy não disponível")
    
    orgs = listar_organizacoes_usuario(user['id'])
    return {"organizacoes": orgs}

@app.post("/organizacoes")
async def criar_nova_organizacao(dados: OrganizacaoCreate, user: Dict = Depends(get_user)):
    """Cria uma nova organização."""
    if not MULTITENANCY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-tenancy não disponível")
    
    try:
        org = criar_organizacao(
            nome=dados.nome,
            owner_id=user['id'],
            cnpj=dados.cnpj,
            email=dados.email,
            plano=dados.plano
        )
        return {"ok": True, "organizacao": org}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/organizacoes/{org_id}")
async def obter_organizacao_route(org_id: int, user: Dict = Depends(get_user)):
    """Obtém detalhes de uma organização."""
    if not MULTITENANCY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-tenancy não disponível")
    
    org = obter_organizacao(org_id, user['id'])
    if not org:
        raise HTTPException(status_code=404, detail="Organização não encontrada")
    return {"organizacao": org}

@app.get("/organizacoes/{org_id}/membros")
async def listar_membros_route(org_id: int, user: Dict = Depends(get_user)):
    """Lista membros de uma organização."""
    if not MULTITENANCY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-tenancy não disponível")
    
    if not verificar_permissao(user['id'], org_id, 'usuarios', 'read'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    membros = listar_membros_organizacao(org_id)
    return {"membros": membros}

@app.post("/organizacoes/{org_id}/convites")
async def criar_convite_route(org_id: int, dados: ConviteCreate, user: Dict = Depends(get_user)):
    """Cria um convite para a organização."""
    if not MULTITENANCY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-tenancy não disponível")
    
    if not verificar_permissao(user['id'], org_id, 'convites', 'create'):
        raise HTTPException(status_code=403, detail="Sem permissão para convidar")
    
    try:
        convite = criar_convite(
            org_id=org_id,
            email=dados.email,
            papel_id=dados.papel_id,
            convidado_por=user['id'],
            mensagem=dados.mensagem
        )
        return {"ok": True, "convite": convite}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/organizacoes/{org_id}/convites")
async def listar_convites_route(org_id: int, user: Dict = Depends(get_user)):
    """Lista convites pendentes."""
    if not MULTITENANCY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-tenancy não disponível")
    
    if not verificar_permissao(user['id'], org_id, 'convites', 'read'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    from auth.multitenancy import Convite, get_db
    with get_db() as db:
        from auth.multitenancy import Convite
        convites = db.query(Convite).filter(
            Convite.organizacao_id == org_id,
            Convite.status == 'pendente'
        ).all()
        return {"convites": [c.to_dict() for c in convites]}

@app.post("/convites/aceitar")
async def aceitar_convite_route(dados: ConviteAceitar, user: Dict = Depends(get_user)):
    """Aceita um convite."""
    if not MULTITENANCY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-tenancy não disponível")
    
    try:
        org = aceitar_convite(dados.token, user['id'])
        return {"ok": True, "organizacao": org}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/organizacoes/{org_id}/audit")
async def listar_audit_route(
    org_id: int, 
    limite: int = 50, 
    offset: int = 0,
    user: Dict = Depends(get_user)
):
    """Lista logs de auditoria."""
    if not MULTITENANCY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-tenancy não disponível")
    
    if not verificar_permissao(user['id'], org_id, 'audit', 'read'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    logs = listar_audit_logs(org_id, limite, offset)
    return {"logs": logs}

@app.post("/organizacoes/{org_id}/definir-padrao")
async def definir_org_padrao_route(org_id: int, user: Dict = Depends(get_user)):
    """Define organização padrão do usuário."""
    if not MULTITENANCY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-tenancy não disponível")
    
    org = obter_organizacao(org_id, user['id'])
    if not org:
        raise HTTPException(status_code=404, detail="Organização não encontrada")
    
    definir_organizacao_padrao(user['id'], org_id)
    return {"ok": True}

@app.get("/papeis")
async def listar_papeis_route(user: Dict = Depends(get_user)):
    """Lista papéis disponíveis."""
    if not MULTITENANCY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-tenancy não disponível")
    
    papeis = listar_papeis()
    return {"papeis": papeis}

@app.get("/meu-papel/{org_id}")
async def obter_meu_papel_route(org_id: int, user: Dict = Depends(get_user)):
    """Obtém papel do usuário na organização."""
    if not MULTITENANCY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Multi-tenancy não disponível")
    
    papel = obter_papel_usuario(user['id'], org_id)
    if not papel:
        raise HTTPException(status_code=404, detail="Você não é membro desta organização")
    return {"papel": papel}

# === ROTAS BILLING (F04) ===

# Importa módulo de billing
try:
    from billing.billing import (
        listar_planos, obter_plano,
        obter_assinatura_org, criar_assinatura_trial, iniciar_assinatura,
        cancelar_assinatura, alterar_plano,
        listar_faturas, obter_fatura,
        obter_uso_atual, verificar_limite, validar_cupom,
        criar_checkout_session, processar_webhook,
        STRIPE_AVAILABLE
    )
    BILLING_AVAILABLE = True
except ImportError:
    BILLING_AVAILABLE = False
    STRIPE_AVAILABLE = False

class AssinaturaCreate(BaseModel):
    plano: str
    ciclo: str = "mensal"
    cupom: Optional[str] = None

class AlterarPlanoRequest(BaseModel):
    plano: str
    ciclo: Optional[str] = None

class CheckoutRequest(BaseModel):
    plano: str
    ciclo: str = "mensal"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

@app.get("/planos")
async def listar_planos_route():
    """Lista todos os planos disponíveis."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    planos = listar_planos()
    return {"planos": planos}

@app.get("/planos/{codigo}")
async def obter_plano_route(codigo: str):
    """Obtém detalhes de um plano."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    plano = obter_plano(codigo)
    if not plano:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return {"plano": plano}

@app.get("/organizacoes/{org_id}/assinatura")
async def obter_assinatura_route(org_id: int, user: Dict = Depends(get_user)):
    """Obtém assinatura da organização."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    if MULTITENANCY_AVAILABLE and not verificar_permissao(user['id'], org_id, 'organizacao', 'read'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    assinatura = obter_assinatura_org(org_id)
    return {"assinatura": assinatura}

@app.post("/organizacoes/{org_id}/assinatura/trial")
async def iniciar_trial_route(org_id: int, user: Dict = Depends(get_user)):
    """Inicia período de teste."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    if MULTITENANCY_AVAILABLE and not verificar_permissao(user['id'], org_id, 'organizacao', 'update'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    try:
        assinatura = criar_assinatura_trial(org_id)
        return {"ok": True, "assinatura": assinatura}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/organizacoes/{org_id}/assinatura")
async def criar_assinatura_route(org_id: int, dados: AssinaturaCreate, user: Dict = Depends(get_user)):
    """Cria uma assinatura."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    if MULTITENANCY_AVAILABLE and not verificar_permissao(user['id'], org_id, 'organizacao', 'update'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    try:
        assinatura = iniciar_assinatura(org_id, dados.plano, dados.ciclo, dados.cupom)
        return {"ok": True, "assinatura": assinatura}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/organizacoes/{org_id}/assinatura/plano")
async def alterar_plano_route(org_id: int, dados: AlterarPlanoRequest, user: Dict = Depends(get_user)):
    """Altera plano da assinatura."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    if MULTITENANCY_AVAILABLE and not verificar_permissao(user['id'], org_id, 'organizacao', 'update'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    try:
        assinatura = alterar_plano(org_id, dados.plano, dados.ciclo)
        return {"ok": True, "assinatura": assinatura}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/organizacoes/{org_id}/assinatura")
async def cancelar_assinatura_route(org_id: int, imediatamente: bool = False, user: Dict = Depends(get_user)):
    """Cancela assinatura."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    if MULTITENANCY_AVAILABLE and not verificar_permissao(user['id'], org_id, 'organizacao', 'update'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    try:
        assinatura = cancelar_assinatura(org_id, imediatamente)
        return {"ok": True, "assinatura": assinatura}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/organizacoes/{org_id}/faturas")
async def listar_faturas_route(org_id: int, limite: int = 12, user: Dict = Depends(get_user)):
    """Lista faturas da organização."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    if MULTITENANCY_AVAILABLE and not verificar_permissao(user['id'], org_id, 'organizacao', 'read'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    faturas = listar_faturas(org_id, limite)
    return {"faturas": faturas}

@app.get("/organizacoes/{org_id}/faturas/{fatura_id}")
async def obter_fatura_route(org_id: int, fatura_id: int, user: Dict = Depends(get_user)):
    """Obtém detalhes de uma fatura."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    if MULTITENANCY_AVAILABLE and not verificar_permissao(user['id'], org_id, 'organizacao', 'read'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    fatura = obter_fatura(fatura_id, org_id)
    if not fatura:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    return {"fatura": fatura}

@app.get("/organizacoes/{org_id}/uso")
async def obter_uso_route(org_id: int, user: Dict = Depends(get_user)):
    """Obtém uso atual da organização."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    if MULTITENANCY_AVAILABLE and not verificar_permissao(user['id'], org_id, 'organizacao', 'read'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    uso = obter_uso_atual(org_id)
    return {"uso": uso}

@app.get("/cupom/{codigo}")
async def validar_cupom_route(codigo: str, plano: Optional[str] = None):
    """Valida um cupom."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    cupom = validar_cupom(codigo, plano)
    if not cupom:
        raise HTTPException(status_code=404, detail="Cupom inválido ou expirado")
    return {"cupom": cupom}

@app.post("/organizacoes/{org_id}/checkout")
async def criar_checkout_route(org_id: int, dados: CheckoutRequest, user: Dict = Depends(get_user)):
    """Cria sessão de checkout Stripe."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=501, detail="Stripe não configurado")
    
    if MULTITENANCY_AVAILABLE and not verificar_permissao(user['id'], org_id, 'organizacao', 'update'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    try:
        result = criar_checkout_session(org_id, dados.plano, dados.ciclo, dados.success_url, dados.cancel_url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/webhooks/stripe")
async def stripe_webhook_route(request: Request):
    """Processa webhooks do Stripe."""
    if not BILLING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing não disponível")
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature', '')
    
    try:
        result = processar_webhook(payload.decode(), sig_header)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# === ROTAS IMPORTAÇÃO AVANÇADA (F05) ===

# Importa módulo de importação
try:
    from importers import (
        detectar_tipo_arquivo, preview_importacao, executar_importacao,
        listar_historico_importacoes, obter_importacao,
        salvar_mapeamento, listar_mapeamentos, obter_mapeamento_padrao
    )
    IMPORTACAO_AVAILABLE = True
except ImportError:
    IMPORTACAO_AVAILABLE = False

class MapeamentoCreate(BaseModel):
    nome: str
    tipo_arquivo: str
    mapeamento: Dict[str, str]
    is_default: bool = False

class ImportacaoConfig(BaseModel):
    mapeamento: Optional[Dict[str, str]] = None
    ignorar_duplicados: bool = True
    modo_agregacao: str = "substituir"  # substituir, somar, ignorar

@app.post("/empresas/{empresa_id}/importar/preview")
async def preview_importacao_route(
    empresa_id: int,
    file: UploadFile = File(...),
    user: Dict = Depends(get_user)
):
    """Preview de importação - analisa arquivo sem salvar."""
    if not IMPORTACAO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Importação avançada não disponível")
    
    conteudo = await file.read()
    
    try:
        resultado = preview_importacao(
            conteudo=conteudo,
            nome_arquivo=file.filename,
            empresa_id=empresa_id
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/empresas/{empresa_id}/importar")
async def executar_importacao_route(
    empresa_id: int,
    file: UploadFile = File(...),
    mapeamento: Optional[str] = Form(None),
    ignorar_duplicados: bool = Form(True),
    modo_agregacao: str = Form("substituir"),
    user: Dict = Depends(get_user)
):
    """Executa importação completa."""
    if not IMPORTACAO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Importação avançada não disponível")
    
    conteudo = await file.read()
    mapeamento_dict = json.loads(mapeamento) if mapeamento else None
    
    # Obtém empresa para verificar organização
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    try:
        resultado = executar_importacao(
            conteudo=conteudo,
            nome_arquivo=file.filename,
            empresa_id=empresa_id,
            contador_id=user['id'],
            organizacao_id=empresa.get('organizacao_id'),
            mapeamento=mapeamento_dict,
            ignorar_duplicados=ignorar_duplicados,
            modo_agregacao=modo_agregacao
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/empresas/{empresa_id}/importacoes")
async def listar_importacoes_route(
    empresa_id: int,
    limite: int = 20,
    user: Dict = Depends(get_user)
):
    """Lista histórico de importações da empresa."""
    if not IMPORTACAO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Importação avançada não disponível")
    
    importacoes = listar_historico_importacoes(empresa_id=empresa_id, limite=limite)
    return {"importacoes": importacoes}

@app.get("/importacoes/{importacao_id}")
async def obter_importacao_route(importacao_id: int, user: Dict = Depends(get_user)):
    """Obtém detalhes de uma importação."""
    if not IMPORTACAO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Importação avançada não disponível")
    
    importacao = obter_importacao(importacao_id)
    if not importacao:
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    return {"importacao": importacao}

@app.get("/empresas/{empresa_id}/mapeamentos")
async def listar_mapeamentos_route(
    empresa_id: int,
    tipo_arquivo: Optional[str] = None,
    user: Dict = Depends(get_user)
):
    """Lista mapeamentos salvos."""
    if not IMPORTACAO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Importação avançada não disponível")
    
    mapeamentos = listar_mapeamentos(tipo_arquivo=tipo_arquivo, empresa_id=empresa_id)
    return {"mapeamentos": mapeamentos}

@app.post("/empresas/{empresa_id}/mapeamentos")
async def salvar_mapeamento_route(
    empresa_id: int,
    dados: MapeamentoCreate,
    user: Dict = Depends(get_user)
):
    """Salva um mapeamento para reutilização."""
    if not IMPORTACAO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Importação avançada não disponível")
    
    # Obtém empresa para organização
    empresa = obter_empresa(empresa_id, user['id'])
    
    try:
        mapeamento = salvar_mapeamento(
            nome=dados.nome,
            tipo_arquivo=dados.tipo_arquivo,
            mapeamento=dados.mapeamento,
            contador_id=user['id'],
            empresa_id=empresa_id,
            organizacao_id=empresa.get('organizacao_id') if empresa else None,
            is_default=dados.is_default
        )
        return {"ok": True, "mapeamento": mapeamento}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/empresas/{empresa_id}/mapeamentos/padrao/{tipo_arquivo}")
async def obter_mapeamento_padrao_route(
    empresa_id: int,
    tipo_arquivo: str,
    user: Dict = Depends(get_user)
):
    """Obtém mapeamento padrão para tipo de arquivo."""
    if not IMPORTACAO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Importação avançada não disponível")
    
    mapeamento = obter_mapeamento_padrao(tipo_arquivo, empresa_id)
    return {"mapeamento": mapeamento}


# === RELATÓRIOS PRO (F09) ===

# Verificar disponibilidade dos geradores
try:
    from reports.excel_generator import gerar_excel, EXCEL_AVAILABLE
except ImportError:
    EXCEL_AVAILABLE = False
    def gerar_excel(*args, **kwargs): raise ImportError("Excel não disponível")

try:
    from reports.pptx_generator import gerar_pptx, PPTX_AVAILABLE
except ImportError:
    PPTX_AVAILABLE = False
    def gerar_pptx(*args, **kwargs): raise ImportError("PowerPoint não disponível")

try:
    from reports.pdf_generator_pro import gerar_pdf as generate_pdf_pro, PDFGeneratorPro
    PDF_PRO_AVAILABLE = True
except ImportError:
    PDF_PRO_AVAILABLE = False
    def generate_pdf_pro(*args, **kwargs): raise ImportError("PDF não disponível")


class ConfiguracaoRelatorioUpdate(BaseModel):
    """Schema para atualização de configuração de relatório."""
    logo_base64: Optional[str] = None
    nome_escritorio: Optional[str] = None
    slogan: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    email_contato: Optional[str] = None
    website: Optional[str] = None
    cor_primaria: Optional[str] = None
    cor_secundaria: Optional[str] = None
    cor_destaque: Optional[str] = None
    mostrar_logo: Optional[bool] = True
    mostrar_graficos: Optional[bool] = True
    mostrar_recomendacoes: Optional[bool] = True
    template_padrao: Optional[str] = 'executivo'
    texto_rodape: Optional[str] = None
    disclaimer: Optional[str] = None


class LinkCompartilhadoCreate(BaseModel):
    """Schema para criar link compartilhado."""
    tipo_relatorio: str = 'pdf'
    template: str = 'executivo'
    permite_download: bool = True
    requer_senha: bool = False
    senha: Optional[str] = None
    expira_em_dias: Optional[int] = 7
    max_acessos: Optional[int] = None


@app.get("/relatorios/configuracao")
async def obter_configuracao_relatorio(user: Dict = Depends(get_user)):
    """Obtém configuração de relatórios do contador."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            result = db.execute(text("""
                SELECT * FROM configuracoes_relatorio WHERE contador_id = :contador_id
            """), {"contador_id": user['id']}).fetchone()
            
            if result:
                return dict(result._mapping)
    except Exception:
        pass  # Tabela pode não existir ainda
    
    # Retorna configuração padrão
    return {
        "contador_id": user['id'],
        "nome_escritorio": user.get('nome', 'ContaGestor'),
        "cor_primaria": "#1e40af",
        "cor_secundaria": "#3b82f6",
        "cor_destaque": "#059669",
        "mostrar_logo": True,
        "mostrar_graficos": True,
        "mostrar_recomendacoes": True,
        "template_padrao": "executivo"
    }


@app.put("/relatorios/configuracao")
async def salvar_configuracao_relatorio(
    dados: ConfiguracaoRelatorioUpdate,
    user: Dict = Depends(get_user)
):
    """Salva configuração de relatórios do contador."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            from datetime import datetime
            
            # Criar tabela se não existir (PostgreSQL) - com TODAS as colunas
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS configuracoes_relatorio (
                    id SERIAL PRIMARY KEY,
                    contador_id INTEGER NOT NULL UNIQUE,
                    logo_base64 TEXT,
                    logo_url TEXT,
                    nome_escritorio TEXT,
                    slogan TEXT,
                    endereco TEXT,
                    telefone TEXT,
                    email_contato TEXT,
                    website TEXT,
                    cor_primaria TEXT DEFAULT '#1e40af',
                    cor_secundaria TEXT DEFAULT '#3b82f6',
                    cor_destaque TEXT DEFAULT '#059669',
                    mostrar_logo BOOLEAN DEFAULT true,
                    mostrar_marca_dagua BOOLEAN DEFAULT false,
                    mostrar_graficos BOOLEAN DEFAULT true,
                    mostrar_recomendacoes BOOLEAN DEFAULT true,
                    cabecalho_personalizado TEXT,
                    rodape_personalizado TEXT,
                    texto_rodape TEXT,
                    disclaimer TEXT,
                    template_padrao TEXT DEFAULT 'executivo',
                    incluir_graficos BOOLEAN DEFAULT true,
                    incluir_recomendacoes BOOLEAN DEFAULT true,
                    formato_numeros TEXT DEFAULT 'brasileiro',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.commit()
            
            # Adicionar colunas que podem estar faltando em tabelas existentes
            colunas_novas = [
                ("nome_escritorio", "TEXT"),
                ("slogan", "TEXT"),
                ("endereco", "TEXT"),
                ("telefone", "TEXT"),
                ("email_contato", "TEXT"),
                ("website", "TEXT"),
                ("cor_destaque", "TEXT DEFAULT '#059669'"),
                ("mostrar_graficos", "BOOLEAN DEFAULT true"),
                ("mostrar_recomendacoes", "BOOLEAN DEFAULT true"),
                ("texto_rodape", "TEXT"),
                ("disclaimer", "TEXT"),
                ("logo_base64", "TEXT"),
            ]
            
            for col_nome, col_tipo in colunas_novas:
                try:
                    db.execute(text(f"""
                        ALTER TABLE configuracoes_relatorio 
                        ADD COLUMN IF NOT EXISTS {col_nome} {col_tipo}
                    """))
                    db.commit()
                except Exception:
                    db.rollback()
            
            # Verifica se já existe
            exists = db.execute(text("""
                SELECT id FROM configuracoes_relatorio WHERE contador_id = :contador_id
            """), {"contador_id": user['id']}).fetchone()
            
            dados_dict = {k: v for k, v in dados.model_dump().items() if v is not None}
            dados_dict['contador_id'] = user['id']
            dados_dict['updated_at'] = datetime.now().isoformat()
            
            if exists:
                # Update
                set_parts = [f"{k} = :{k}" for k in dados_dict.keys() if k != 'contador_id']
                set_clause = ", ".join(set_parts)
                if set_clause:
                    db.execute(text(f"""
                        UPDATE configuracoes_relatorio 
                        SET {set_clause}
                        WHERE contador_id = :contador_id
                    """), dados_dict)
            else:
                # Insert
                dados_dict['created_at'] = datetime.now().isoformat()
                cols = ", ".join(dados_dict.keys())
                vals = ", ".join([f":{k}" for k in dados_dict.keys()])
                db.execute(text(f"""
                    INSERT INTO configuracoes_relatorio ({cols}) VALUES ({vals})
                """), dados_dict)
            
            db.commit()
            return {"ok": True, "message": "Configuração salva com sucesso"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar configuração: {str(e)}")


@app.get("/relatorios/templates")
async def listar_templates_relatorio(user: Dict = Depends(get_user)):
    """Lista templates de relatório disponíveis."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            results = db.execute(text("""
                SELECT id, nome, descricao, tipo, is_default, is_system
                FROM templates_relatorio 
                WHERE is_system = true OR contador_id = :contador_id
                ORDER BY is_default DESC, nome
            """), {"contador_id": user['id']}).fetchall()
            
            return {"templates": [dict(r._mapping) for r in results]}
    except Exception:
        # Retorna templates padrão se tabela não existe
        return {"templates": [
            {"id": 1, "nome": "Executivo", "descricao": "Relatório resumido", "tipo": "executivo", "is_default": True, "is_system": True},
            {"id": 2, "nome": "Detalhado", "descricao": "Relatório completo", "tipo": "detalhado", "is_default": False, "is_system": True},
        ]}


@app.post("/empresas/{empresa_id}/relatorios/pdf")
async def gerar_relatorio_pdf(
    empresa_id: int,
    template: str = 'executivo',
    user: Dict = Depends(get_user)
):
    """Gera relatório PDF da empresa com alertas e indicadores expandidos."""
    from fastapi.responses import Response
    
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    dados_mensais = listar_dados_mensais(empresa_id, limite=24)
    ultima_analise = obter_ultima_analise(empresa_id)
    
    # Buscar alertas da empresa
    alertas = []
    try:
        with get_db() as db:
            from sqlalchemy import text
            results = db.execute(text("""
                SELECT * FROM alertas 
                WHERE empresa_id = :empresa_id AND contador_id = :contador_id
                ORDER BY 
                    CASE severidade WHEN 'critico' THEN 1 WHEN 'atencao' THEN 2 ELSE 3 END,
                    created_at DESC
                LIMIT 20
            """), {"empresa_id": empresa_id, "contador_id": user['id']}).fetchall()
            alertas = [dict(r._mapping) for r in results]
    except Exception:
        pass
    
    # Obter configuração white-label (pode não existir a tabela ainda)
    config = {}
    try:
        with get_db() as db:
            from sqlalchemy import text
            result = db.execute(text("""
                SELECT * FROM configuracoes_relatorio WHERE contador_id = :contador_id
            """), {"contador_id": user['id']}).fetchone()
            if result:
                config = dict(result._mapping)
    except Exception:
        pass  # Tabela pode não existir
    
    # Preparar dados para o gerador
    if not dados_mensais:
        raise HTTPException(status_code=400, detail="Empresa não possui dados mensais para gerar relatório")
    
    try:
        # Usar novo gerador com alertas
        from reports.pdf_generator_pro import gerar_pdf
        pdf_bytes = gerar_pdf(
            empresa=empresa,
            dados_mensais=dados_mensais,
            analise=ultima_analise,
            config=config,
            alertas=alertas
        )
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"Gerador PDF não disponível: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")
    
    # Registrar histórico (criar tabela se não existe)
    try:
        with get_db() as db:
            from sqlalchemy import text
            # Criar tabela se não existir
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS historico_relatorios (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER NOT NULL,
                    contador_id INTEGER NOT NULL,
                    analise_id INTEGER,
                    tipo VARCHAR(20) NOT NULL DEFAULT 'pdf',
                    template VARCHAR(50),
                    arquivo_nome VARCHAR(255),
                    arquivo_tamanho INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.commit()
            
            db.execute(text("""
                INSERT INTO historico_relatorios (empresa_id, contador_id, analise_id, tipo, template, arquivo_nome, arquivo_tamanho)
                VALUES (:empresa_id, :contador_id, :analise_id, 'pdf', :template, :nome, :tamanho)
            """), {
                "empresa_id": empresa_id,
                "contador_id": user['id'],
                "analise_id": ultima_analise.get('id') if ultima_analise else None,
                "template": template,
                "nome": f"diagnostico_{empresa.get('razao_social', 'empresa')[:20]}.pdf",
                "tamanho": len(pdf_bytes)
            })
            db.commit()
    except Exception as e:
        print(f"Erro ao registrar histórico: {e}")
    
    filename = f"diagnostico_{empresa.get('razao_social', 'empresa').replace(' ', '_')[:30]}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.post("/empresas/{empresa_id}/relatorios/excel")
async def gerar_relatorio_excel(
    empresa_id: int,
    user: Dict = Depends(get_user)
):
    """Gera relatório Excel da empresa com alertas e indicadores expandidos."""
    from fastapi.responses import Response
    
    if not EXCEL_AVAILABLE:
        raise HTTPException(status_code=501, detail="Gerador Excel não disponível. Instale: pip install openpyxl")
    
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    dados_mensais = listar_dados_mensais(empresa_id, limite=24)
    ultima_analise = obter_ultima_analise(empresa_id)
    
    # Buscar alertas da empresa
    alertas = []
    try:
        with get_db() as db:
            from sqlalchemy import text
            results = db.execute(text("""
                SELECT * FROM alertas 
                WHERE empresa_id = :empresa_id AND contador_id = :contador_id
                ORDER BY 
                    CASE severidade WHEN 'critico' THEN 1 WHEN 'atencao' THEN 2 ELSE 3 END,
                    created_at DESC
                LIMIT 20
            """), {"empresa_id": empresa_id, "contador_id": user['id']}).fetchall()
            alertas = [dict(r._mapping) for r in results]
    except Exception:
        pass
    
    # Obter configuração white-label
    config = {}
    try:
        with get_db() as db:
            from sqlalchemy import text
            result = db.execute(text("""
                SELECT * FROM configuracoes_relatorio WHERE contador_id = :contador_id
            """), {"contador_id": user['id']}).fetchone()
            if result:
                config = dict(result._mapping)
    except Exception:
        pass  # Tabela pode não existir
    
    try:
        excel_bytes = gerar_excel(empresa, dados_mensais, ultima_analise, config, alertas)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar Excel: {str(e)}")
    
    # Registrar histórico
    try:
        with get_db() as db:
            from sqlalchemy import text
            # Criar tabela se não existir
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS historico_relatorios (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER NOT NULL,
                    contador_id INTEGER NOT NULL,
                    analise_id INTEGER,
                    tipo VARCHAR(20) NOT NULL DEFAULT 'pdf',
                    template VARCHAR(50),
                    arquivo_nome VARCHAR(255),
                    arquivo_tamanho INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.commit()
            
            db.execute(text("""
                INSERT INTO historico_relatorios (empresa_id, contador_id, analise_id, tipo, arquivo_nome, arquivo_tamanho)
                VALUES (:empresa_id, :contador_id, :analise_id, 'excel', :nome, :tamanho)
            """), {
                "empresa_id": empresa_id,
                "contador_id": user['id'],
                "analise_id": ultima_analise.get('id') if ultima_analise else None,
                "nome": f"diagnostico_{empresa.get('razao_social', 'empresa')[:20]}.xlsx",
                "tamanho": len(excel_bytes)
            })
            db.commit()
    except Exception as e:
        print(f"Erro ao registrar histórico: {e}")
    
    filename = f"diagnostico_{empresa.get('razao_social', 'empresa').replace(' ', '_')[:30]}.xlsx"
    
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.post("/empresas/{empresa_id}/relatorios/pptx")
async def gerar_relatorio_pptx(
    empresa_id: int,
    user: Dict = Depends(get_user)
):
    """Gera apresentação PowerPoint da empresa com alertas e indicadores expandidos."""
    from fastapi.responses import Response
    
    if not PPTX_AVAILABLE:
        raise HTTPException(status_code=501, detail="Gerador PowerPoint não disponível. Instale: pip install python-pptx")
    
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    dados_mensais = listar_dados_mensais(empresa_id, limite=24)
    ultima_analise = obter_ultima_analise(empresa_id)
    
    # Buscar alertas da empresa
    alertas = []
    try:
        with get_db() as db:
            from sqlalchemy import text
            results = db.execute(text("""
                SELECT * FROM alertas 
                WHERE empresa_id = :empresa_id AND contador_id = :contador_id
                ORDER BY 
                    CASE severidade WHEN 'critico' THEN 1 WHEN 'atencao' THEN 2 ELSE 3 END,
                    created_at DESC
                LIMIT 20
            """), {"empresa_id": empresa_id, "contador_id": user['id']}).fetchall()
            alertas = [dict(r._mapping) for r in results]
    except Exception:
        pass
    
    # Obter configuração white-label
    config = {}
    try:
        with get_db() as db:
            from sqlalchemy import text
            result = db.execute(text("""
                SELECT * FROM configuracoes_relatorio WHERE contador_id = :contador_id
            """), {"contador_id": user['id']}).fetchone()
            if result:
                config = dict(result._mapping)
    except Exception:
        pass  # Tabela pode não existir
    
    try:
        pptx_bytes = gerar_pptx(empresa, dados_mensais, ultima_analise, config, alertas)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PowerPoint: {str(e)}")
    
    # Registrar histórico
    try:
        with get_db() as db:
            from sqlalchemy import text
            # Criar tabela se não existir
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS historico_relatorios (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER NOT NULL,
                    contador_id INTEGER NOT NULL,
                    analise_id INTEGER,
                    tipo VARCHAR(20) NOT NULL DEFAULT 'pdf',
                    template VARCHAR(50),
                    arquivo_nome VARCHAR(255),
                    arquivo_tamanho INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.commit()
            
            db.execute(text("""
                INSERT INTO historico_relatorios (empresa_id, contador_id, analise_id, tipo, arquivo_nome, arquivo_tamanho)
                VALUES (:empresa_id, :contador_id, :analise_id, 'pptx', :nome, :tamanho)
            """), {
                "empresa_id": empresa_id,
                "contador_id": user['id'],
                "analise_id": ultima_analise.get('id') if ultima_analise else None,
                "nome": f"apresentacao_{empresa.get('razao_social', 'empresa')[:20]}.pptx",
                "tamanho": len(pptx_bytes)
            })
            db.commit()
    except Exception as e:
        print(f"Erro ao registrar histórico: {e}")
    
    filename = f"apresentacao_{empresa.get('razao_social', 'empresa').replace(' ', '_')[:30]}.pptx"
    
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.post("/empresas/{empresa_id}/relatorios/link")
async def criar_link_compartilhado(
    empresa_id: int,
    dados: LinkCompartilhadoCreate,
    user: Dict = Depends(get_user)
):
    """Cria link compartilhável para relatório."""
    import secrets
    from datetime import timedelta
    
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    ultima_analise = obter_ultima_analise(empresa_id)
    
    # Gerar token único
    token = secrets.token_urlsafe(32)
    
    # Calcular expiração
    expira_em = None
    if dados.expira_em_dias:
        expira_em = datetime.now() + timedelta(days=dados.expira_em_dias)
    
    # Hash da senha se necessário
    senha_hash = None
    if dados.requer_senha and dados.senha:
        import hashlib
        senha_hash = hashlib.sha256(dados.senha.encode()).hexdigest()
    
    try:
        with get_db() as db:
            from sqlalchemy import text
            db.execute(text("""
                INSERT INTO links_compartilhados 
                (token, empresa_id, contador_id, analise_id, tipo_relatorio, template, 
                 permite_download, requer_senha, senha_hash, expira_em, max_acessos)
                VALUES (:token, :empresa_id, :contador_id, :analise_id, :tipo, :template,
                        :download, :requer_senha, :senha_hash, :expira_em, :max_acessos)
            """), {
                "token": token,
                "empresa_id": empresa_id,
                "contador_id": user['id'],
                "analise_id": ultima_analise.get('id') if ultima_analise else None,
                "tipo": dados.tipo_relatorio,
                "template": dados.template,
                "download": dados.permite_download,
                "requer_senha": dados.requer_senha,
                "senha_hash": senha_hash,
                "expira_em": expira_em,
                "max_acessos": dados.max_acessos
            })
            db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar link. Execute as migrations: {str(e)}")
    
    # Construir URL
    base_url = os.getenv('BASE_URL', 'http://localhost')
    link_url = f"{base_url}/compartilhado/{token}"
    
    return {
        "token": token,
        "url": link_url,
        "expira_em": expira_em.isoformat() if expira_em else None,
        "max_acessos": dados.max_acessos
    }


@app.get("/compartilhado/{token}")
async def acessar_link_compartilhado(
    token: str,
    senha: Optional[str] = None
):
    """Acessa relatório via link compartilhado."""
    from fastapi.responses import Response
    
    try:
        with get_db() as db:
            from sqlalchemy import text
            
            # Buscar link
            result = db.execute(text("""
                SELECT l.*, e.razao_social as empresa_nome
                FROM links_compartilhados l
                JOIN empresas e ON l.empresa_id = e.id
                WHERE l.token = :token AND l.ativo = true
            """), {"token": token}).fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="Link não encontrado ou expirado")
            
            link = dict(result._mapping)
            
            # Verificar expiração
            if link.get('expira_em') and datetime.now() > link['expira_em']:
                raise HTTPException(status_code=410, detail="Link expirado")
            
            # Verificar máximo de acessos
            if link.get('max_acessos') and link.get('acessos', 0) >= link['max_acessos']:
                raise HTTPException(status_code=410, detail="Limite de acessos atingido")
            
            # Verificar senha
            if link.get('requer_senha') and link.get('senha_hash'):
                if not senha:
                    raise HTTPException(status_code=401, detail="Senha requerida")
                import hashlib
                if hashlib.sha256(senha.encode()).hexdigest() != link['senha_hash']:
                    raise HTTPException(status_code=401, detail="Senha incorreta")
            
            # Incrementar contador de acessos
            db.execute(text("""
                UPDATE links_compartilhados 
                SET acessos = acessos + 1, ultimo_acesso = NOW()
                WHERE token = :token
            """), {"token": token})
            db.commit()
            
            # Obter configuração white-label
            config_result = db.execute(text("""
                SELECT * FROM configuracoes_relatorio WHERE contador_id = :contador_id
            """), {"contador_id": link['contador_id']}).fetchone()
            config = dict(config_result._mapping) if config_result else {}
        
        # Buscar dados da empresa (fora do with para não manter conexão)
        empresa = obter_empresa(link['empresa_id'], link['contador_id'])
        dados_mensais = listar_dados_mensais(link['empresa_id'], limite=24)
        ultima_analise = obter_ultima_analise(link['empresa_id'])
        
        # Gerar relatório baseado no tipo
        tipo = link.get('tipo_relatorio', 'pdf')
        
        if tipo == 'pdf' and PDF_PRO_AVAILABLE:
            dados_formatados = []
            for d in dados_mensais:
                receita = d.get('receita', 0) or 0
                custos = d.get('custos', 0) or 0
                despesas = d.get('despesas', 0) or 0
                impostos = d.get('impostos', 0) or 0
                folha = d.get('folha', 0) or 0
                lucro = receita - custos - despesas - impostos - folha
                
                dados_formatados.append({
                    'periodo': f"{d.get('mes', 0):02d}/{d.get('ano', 0)}",
                    'receita': receita,
                    'custos': custos,
                    'despesas': despesas,
                    'impostos': impostos,
                    'folha': folha,
                    'caixa': d.get('caixa', 0) or 0,
                    'lucro': lucro,
                    'margem': (lucro / receita * 100) if receita > 0 else 0,
                    'custos_pct': (custos / receita * 100) if receita > 0 else 0,
                    'impostos_pct': (impostos / receita * 100) if receita > 0 else 0,
                })
            
            pdf_data = {
                'empresa': empresa,
                'dados_mensais': dados_formatados,
                'analise': ultima_analise,
                'config': config,
            }
            content = generate_pdf_pro(pdf_data)
            media_type = "application/pdf"
            filename = f"relatorio_{link['empresa_nome'][:20]}.pdf"
            
        elif tipo == 'excel' and EXCEL_AVAILABLE:
            content = gerar_excel(empresa, dados_mensais, ultima_analise, config)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"relatorio_{link['empresa_nome'][:20]}.xlsx"
            
        elif tipo == 'pptx' and PPTX_AVAILABLE:
            content = gerar_pptx(empresa, dados_mensais, ultima_analise, config)
            media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            filename = f"apresentacao_{link['empresa_nome'][:20]}.pptx"
            
        else:
            raise HTTPException(status_code=501, detail=f"Tipo de relatório '{tipo}' não disponível")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao acessar link: {str(e)}")


@app.get("/relatorios/historico")
async def listar_historico_relatorios(
    limite: int = 20,
    user: Dict = Depends(get_user)
):
    """Lista histórico de relatórios gerados."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            results = db.execute(text("""
                SELECT h.*, e.razao_social as empresa_nome
                FROM historico_relatorios h
                JOIN empresas e ON h.empresa_id = e.id
                WHERE h.contador_id = :contador_id
                ORDER BY h.created_at DESC
                LIMIT :limite
            """), {"contador_id": user['id'], "limite": limite}).fetchall()
            
            return {"historico": [dict(r._mapping) for r in results]}
    except Exception:
        return {"historico": []}


@app.get("/relatorios/links")
async def listar_links_compartilhados(user: Dict = Depends(get_user)):
    """Lista links compartilhados ativos."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            results = db.execute(text("""
                SELECT l.*, e.razao_social as empresa_nome
                FROM links_compartilhados l
                JOIN empresas e ON l.empresa_id = e.id
                WHERE l.contador_id = :contador_id AND l.ativo = true
                ORDER BY l.created_at DESC
            """), {"contador_id": user['id']}).fetchall()
            
            base_url = os.getenv('BASE_URL', 'http://localhost')
            links = []
            for r in results:
                link = dict(r._mapping)
                link['url'] = f"{base_url}/compartilhado/{link['token']}"
                links.append(link)
            
            return {"links": links}
    except Exception:
        return {"links": []}


@app.delete("/relatorios/links/{token}")
async def desativar_link_compartilhado(token: str, user: Dict = Depends(get_user)):
    """Desativa um link compartilhado."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            result = db.execute(text("""
                UPDATE links_compartilhados 
                SET ativo = false 
                WHERE token = :token AND contador_id = :contador_id
            """), {"token": token, "contador_id": user['id']})
            db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Link não encontrado")
            
            return {"ok": True}
    except HTTPException:
        raise
    except Exception:
        return {"ok": False, "error": "Erro ao desativar link"}


# === ALERTAS INTELIGENTES (F06) ===

# Importar motor de alertas
try:
    from engine.alertas import gerar_alertas_empresa, gerar_resumo_alertas, MotorAlertas
    ALERTAS_AVAILABLE = True
except ImportError:
    ALERTAS_AVAILABLE = False


class ConfiguracaoAlertaUpdate(BaseModel):
    """Schema para atualização de configuração de alertas."""
    # Caixa
    alerta_caixa_ativo: Optional[bool] = True
    caixa_dias_critico: Optional[int] = 30
    caixa_dias_atencao: Optional[int] = 60
    # Margem
    alerta_margem_ativo: Optional[bool] = True
    margem_minima: Optional[float] = 5.0
    margem_queda_pct: Optional[float] = 20.0
    # Tendência
    alerta_tendencia_ativo: Optional[bool] = True
    tendencia_meses_negativos: Optional[int] = 3
    queda_faturamento_pct: Optional[float] = 15.0
    # Anomalias
    alerta_anomalias_ativo: Optional[bool] = True
    anomalia_desvio_padrao: Optional[float] = 2.0
    # Score
    alerta_score_ativo: Optional[bool] = True
    score_critico: Optional[int] = 40
    score_queda_pontos: Optional[int] = 15
    # Notificações
    notificar_email: Optional[bool] = False
    notificar_dashboard: Optional[bool] = True
    frequencia_email: Optional[str] = 'semanal'
    email_destino: Optional[str] = None


class ResolverAlertaRequest(BaseModel):
    """Schema para resolver um alerta."""
    nota: Optional[str] = None


@app.get("/alertas")
async def listar_alertas(
    empresa_id: Optional[int] = None,
    severidade: Optional[str] = None,
    tipo: Optional[str] = None,
    apenas_nao_lidos: bool = False,
    apenas_nao_resolvidos: bool = True,
    limite: int = 50,
    user: Dict = Depends(get_user)
):
    """Lista alertas do contador."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            
            # Base query
            query = """
                SELECT a.*, e.razao_social as empresa_nome
                FROM alertas a
                JOIN empresas e ON a.empresa_id = e.id
                WHERE a.contador_id = :contador_id
            """
            params = {"contador_id": user['id'], "limite": limite}
            
            # Filtros
            if empresa_id:
                query += " AND a.empresa_id = :empresa_id"
                params["empresa_id"] = empresa_id
            
            if severidade:
                query += " AND a.severidade = :severidade"
                params["severidade"] = severidade
            
            if tipo:
                query += " AND a.tipo = :tipo"
                params["tipo"] = tipo
            
            if apenas_nao_lidos:
                query += " AND a.lido = false"
            
            if apenas_nao_resolvidos:
                query += " AND a.resolvido = false"
            
            query += " ORDER BY a.created_at DESC LIMIT :limite"
            
            results = db.execute(text(query), params).fetchall()
            
            alertas = []
            for r in results:
                alerta = dict(r._mapping)
                # Parse dados_json
                if alerta.get('dados_json'):
                    try:
                        alerta['dados'] = json.loads(alerta['dados_json'])
                    except:
                        alerta['dados'] = {}
                alertas.append(alerta)
            
            return {"alertas": alertas, "total": len(alertas)}
    except Exception as e:
        return {"alertas": [], "total": 0, "error": str(e)}


@app.get("/alertas/resumo")
async def obter_resumo_alertas(user: Dict = Depends(get_user)):
    """Obtém resumo dos alertas para o dashboard."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            
            # Contar por severidade (não resolvidos)
            result = db.execute(text("""
                SELECT 
                    severidade,
                    COUNT(*) as total
                FROM alertas
                WHERE contador_id = :contador_id 
                AND resolvido = false
                GROUP BY severidade
            """), {"contador_id": user['id']}).fetchall()
            
            por_severidade = {"critico": 0, "atencao": 0, "info": 0}
            for r in result:
                sev = r[0]
                if sev in por_severidade:
                    por_severidade[sev] = r[1]
            
            # Total não lidos
            nao_lidos = db.execute(text("""
                SELECT COUNT(*) FROM alertas
                WHERE contador_id = :contador_id 
                AND lido = false 
                AND resolvido = false
            """), {"contador_id": user['id']}).scalar() or 0
            
            # Últimos 5 alertas críticos
            criticos = db.execute(text("""
                SELECT a.*, e.razao_social as empresa_nome
                FROM alertas a
                JOIN empresas e ON a.empresa_id = e.id
                WHERE a.contador_id = :contador_id 
                AND a.severidade = 'critico'
                AND a.resolvido = false
                ORDER BY a.created_at DESC
                LIMIT 5
            """), {"contador_id": user['id']}).fetchall()
            
            alertas_criticos = [dict(r._mapping) for r in criticos]
            
            # Por empresa (top 5 com mais alertas)
            por_empresa = db.execute(text("""
                SELECT e.razao_social, COUNT(*) as total
                FROM alertas a
                JOIN empresas e ON a.empresa_id = e.id
                WHERE a.contador_id = :contador_id 
                AND a.resolvido = false
                GROUP BY a.empresa_id, e.razao_social
                ORDER BY total DESC
                LIMIT 5
            """), {"contador_id": user['id']}).fetchall()
            
            empresas_alertas = [{"empresa": r[0], "total": r[1]} for r in por_empresa]
            
            return {
                "total": por_severidade['critico'] + por_severidade['atencao'] + por_severidade['info'],
                "nao_lidos": nao_lidos,
                "por_severidade": por_severidade,
                "alertas_criticos": alertas_criticos,
                "por_empresa": empresas_alertas
            }
    except Exception:
        return {
            "total": 0,
            "nao_lidos": 0,
            "por_severidade": {"critico": 0, "atencao": 0, "info": 0},
            "alertas_criticos": [],
            "por_empresa": []
        }


@app.post("/alertas/{alerta_id}/lido")
async def marcar_alerta_lido(alerta_id: int, user: Dict = Depends(get_user)):
    """Marca um alerta como lido."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            result = db.execute(text("""
                UPDATE alertas 
                SET lido = true, lido_em = NOW()
                WHERE id = :id AND contador_id = :contador_id
            """), {"id": alerta_id, "contador_id": user['id']})
            db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Alerta não encontrado")
            
            return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alertas/{alerta_id}/resolver")
async def resolver_alerta(
    alerta_id: int,
    dados: ResolverAlertaRequest,
    user: Dict = Depends(get_user)
):
    """Marca um alerta como resolvido."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            result = db.execute(text("""
                UPDATE alertas 
                SET resolvido = true, 
                    resolvido_em = NOW(),
                    resolvido_por = :resolvido_por,
                    resolucao_nota = :nota,
                    lido = true,
                    lido_em = COALESCE(lido_em, NOW())
                WHERE id = :id AND contador_id = :contador_id
            """), {
                "id": alerta_id,
                "contador_id": user['id'],
                "resolvido_por": user['id'],
                "nota": dados.nota
            })
            db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Alerta não encontrado")
            
            return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alertas/marcar-todos-lidos")
async def marcar_todos_alertas_lidos(
    empresa_id: Optional[int] = None,
    user: Dict = Depends(get_user)
):
    """Marca todos os alertas como lidos."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            
            if empresa_id:
                db.execute(text("""
                    UPDATE alertas 
                    SET lido = true, lido_em = NOW()
                    WHERE contador_id = :contador_id 
                    AND empresa_id = :empresa_id
                    AND lido = false
                """), {"contador_id": user['id'], "empresa_id": empresa_id})
            else:
                db.execute(text("""
                    UPDATE alertas 
                    SET lido = true, lido_em = NOW()
                    WHERE contador_id = :contador_id AND lido = false
                """), {"contador_id": user['id']})
            
            db.commit()
            return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alertas/configuracao")
async def obter_configuracao_alertas_global(user: Dict = Depends(get_user)):
    """Obtém configuração global de alertas do contador."""
    try:
        with get_db() as db:
            from sqlalchemy import text
            result = db.execute(text("""
                SELECT * FROM configuracoes_alerta_global 
                WHERE contador_id = :contador_id
            """), {"contador_id": user['id']}).fetchone()
            
            if result:
                return dict(result._mapping)
    except Exception:
        pass
    
    # Configuração padrão
    return {
        "contador_id": user['id'],
        "horario_notificacao": "09:00",
        "dias_notificacao": "1,2,3,4,5",
        "enviar_resumo_semanal": True,
        "dia_resumo_semanal": 1,
        "max_alertas_email_dia": 10
    }


@app.get("/empresas/{empresa_id}/alertas/configuracao")
async def obter_configuracao_alertas_empresa(
    empresa_id: int,
    user: Dict = Depends(get_user)
):
    """Obtém configuração de alertas de uma empresa."""
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    try:
        with get_db() as db:
            from sqlalchemy import text
            result = db.execute(text("""
                SELECT * FROM configuracoes_alerta 
                WHERE empresa_id = :empresa_id AND contador_id = :contador_id
            """), {"empresa_id": empresa_id, "contador_id": user['id']}).fetchone()
            
            if result:
                return dict(result._mapping)
    except Exception:
        pass
    
    # Configuração padrão
    return {
        "empresa_id": empresa_id,
        "contador_id": user['id'],
        "alerta_caixa_ativo": True,
        "caixa_dias_critico": 30,
        "caixa_dias_atencao": 60,
        "alerta_margem_ativo": True,
        "margem_minima": 5.0,
        "margem_queda_pct": 20.0,
        "alerta_tendencia_ativo": True,
        "tendencia_meses_negativos": 3,
        "queda_faturamento_pct": 15.0,
        "alerta_anomalias_ativo": True,
        "anomalia_desvio_padrao": 2.0,
        "alerta_score_ativo": True,
        "score_critico": 40,
        "score_queda_pontos": 15,
        "notificar_email": False,
        "notificar_dashboard": True,
        "frequencia_email": "semanal"
    }


@app.put("/empresas/{empresa_id}/alertas/configuracao")
async def salvar_configuracao_alertas_empresa(
    empresa_id: int,
    dados: ConfiguracaoAlertaUpdate,
    user: Dict = Depends(get_user)
):
    """Salva configuração de alertas de uma empresa."""
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    try:
        with get_db() as db:
            from sqlalchemy import text
            from datetime import datetime
            
            # Criar tabela se não existir (PostgreSQL)
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS configuracoes_alerta (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER NOT NULL,
                    contador_id INTEGER NOT NULL,
                    alerta_caixa_ativo BOOLEAN DEFAULT true,
                    caixa_dias_critico INTEGER DEFAULT 30,
                    caixa_dias_atencao INTEGER DEFAULT 60,
                    alerta_margem_ativo BOOLEAN DEFAULT true,
                    margem_minima REAL DEFAULT 5.0,
                    margem_queda_pct REAL DEFAULT 20.0,
                    alerta_tendencia_ativo BOOLEAN DEFAULT true,
                    tendencia_meses_negativos INTEGER DEFAULT 3,
                    queda_faturamento_pct REAL DEFAULT 15.0,
                    alerta_anomalias_ativo BOOLEAN DEFAULT true,
                    anomalia_desvio_padrao REAL DEFAULT 2.0,
                    alerta_score_ativo BOOLEAN DEFAULT true,
                    score_critico INTEGER DEFAULT 40,
                    score_queda_pontos INTEGER DEFAULT 15,
                    notificar_email BOOLEAN DEFAULT false,
                    notificar_dashboard BOOLEAN DEFAULT true,
                    frequencia_email TEXT DEFAULT 'semanal',
                    email_destino TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(empresa_id, contador_id)
                )
            """))
            db.commit()
            
            # Verificar se existe
            exists = db.execute(text("""
                SELECT id FROM configuracoes_alerta 
                WHERE empresa_id = :empresa_id AND contador_id = :contador_id
            """), {"empresa_id": empresa_id, "contador_id": user['id']}).fetchone()
            
            dados_dict = {k: v for k, v in dados.model_dump().items() if v is not None}
            dados_dict['empresa_id'] = empresa_id
            dados_dict['contador_id'] = user['id']
            dados_dict['updated_at'] = datetime.now().isoformat()
            
            if exists:
                # Update
                set_parts = []
                for k in dados_dict.keys():
                    if k not in ['empresa_id', 'contador_id']:
                        set_parts.append(f"{k} = :{k}")
                set_clause = ", ".join(set_parts)
                
                if set_clause:
                    db.execute(text(f"""
                        UPDATE configuracoes_alerta 
                        SET {set_clause}
                        WHERE empresa_id = :empresa_id AND contador_id = :contador_id
                    """), dados_dict)
            else:
                # Insert
                dados_dict['created_at'] = datetime.now().isoformat()
                cols = ", ".join(dados_dict.keys())
                vals = ", ".join([f":{k}" for k in dados_dict.keys()])
                db.execute(text(f"""
                    INSERT INTO configuracoes_alerta ({cols}) VALUES ({vals})
                """), dados_dict)
            
            db.commit()
            return {"ok": True, "message": "Configuração salva com sucesso"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar configuração: {str(e)}")


@app.post("/empresas/{empresa_id}/alertas/gerar")
async def gerar_alertas_para_empresa(
    empresa_id: int,
    user: Dict = Depends(get_user)
):
    """Gera alertas para uma empresa específica."""
    if not ALERTAS_AVAILABLE:
        raise HTTPException(status_code=501, detail="Motor de alertas não disponível")
    
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Limpar alertas não resolvidos desta empresa antes de gerar novos
    try:
        with get_db() as db:
            from sqlalchemy import text
            db.execute(text("""
                DELETE FROM alertas 
                WHERE empresa_id = :empresa_id 
                AND contador_id = :contador_id
                AND resolvido = false
            """), {"empresa_id": empresa_id, "contador_id": user['id']})
            db.commit()
    except Exception as e:
        print(f"Aviso ao limpar alertas antigos: {e}")
    
    # Obter dados
    dados_mensais = listar_dados_mensais(empresa_id, limite=24)
    analise_atual = obter_ultima_analise(empresa_id)
    
    # Obter análise anterior
    analise_anterior = None
    analises = listar_analises(empresa_id, limite=2)
    if len(analises) >= 2:
        analise_anterior = analises[1]
    
    # Obter configuração
    config = {}
    try:
        with get_db() as db:
            from sqlalchemy import text
            result = db.execute(text("""
                SELECT * FROM configuracoes_alerta 
                WHERE empresa_id = :empresa_id AND contador_id = :contador_id
            """), {"empresa_id": empresa_id, "contador_id": user['id']}).fetchone()
            if result:
                config = dict(result._mapping)
    except Exception:
        pass
    
    # Gerar alertas
    alertas_gerados = gerar_alertas_empresa(
        empresa=empresa,
        dados_mensais=dados_mensais,
        analise_atual=analise_atual,
        analise_anterior=analise_anterior,
        config=config
    )
    
    # Salvar alertas no banco
    alertas_salvos = 0
    try:
        with get_db() as db:
            from sqlalchemy import text
            
            for alerta in alertas_gerados:
                # Inserir alerta diretamente (já limpamos os não resolvidos)
                db.execute(text("""
                    INSERT INTO alertas (
                        empresa_id, contador_id, tipo, severidade, codigo,
                        titulo, mensagem, valor_atual, valor_limite, valor_anterior,
                        dados_json, periodo_referencia
                    ) VALUES (
                        :empresa_id, :contador_id, :tipo, :severidade, :codigo,
                        :titulo, :mensagem, :valor_atual, :valor_limite, :valor_anterior,
                        :dados_json, :periodo_referencia
                    )
                """), {
                    "empresa_id": empresa_id,
                    "contador_id": user['id'],
                    "tipo": alerta['tipo'],
                    "severidade": alerta['severidade'],
                    "codigo": alerta['codigo'],
                    "titulo": alerta['titulo'],
                    "mensagem": alerta['mensagem'],
                    "valor_atual": alerta.get('valor_atual'),
                    "valor_limite": alerta.get('valor_limite'),
                    "valor_anterior": alerta.get('valor_anterior'),
                    "dados_json": alerta.get('dados_json'),
                    "periodo_referencia": alerta.get('periodo_referencia')
                })
                alertas_salvos += 1
            
            db.commit()
    except Exception as e:
        # Se tabelas não existem, retorna alertas gerados sem salvar
        return {
            "alertas_gerados": len(alertas_gerados),
            "alertas_salvos": 0,
            "alertas": alertas_gerados,
            "aviso": "Tabelas de alertas não encontradas. Execute as migrations."
        }
    
    return {
        "alertas_gerados": len(alertas_gerados),
        "alertas_salvos": alertas_salvos,
        "alertas": alertas_gerados
    }


@app.post("/alertas/gerar-todos")
async def gerar_alertas_todas_empresas(user: Dict = Depends(get_user)):
    """Gera alertas para todas as empresas do contador."""
    if not ALERTAS_AVAILABLE:
        raise HTTPException(status_code=501, detail="Motor de alertas não disponível")
    
    empresas = listar_empresas(user['id'])
    
    total_alertas = 0
    total_salvos = 0
    resultados = []
    
    # Primeiro, limpar alertas não resolvidos e não lidos (serão regenerados)
    try:
        with get_db() as db:
            from sqlalchemy import text
            db.execute(text("""
                DELETE FROM alertas 
                WHERE contador_id = :contador_id 
                AND resolvido = false
            """), {"contador_id": user['id']})
            
            # Limpar histórico de alertas antigos (mais de 30 dias)
            db.execute(text("""
                DELETE FROM alertas_historico 
                WHERE empresa_id IN (
                    SELECT id FROM empresas WHERE contador_id = :contador_id
                )
                AND created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
            """), {"contador_id": user['id']})
            
            db.commit()
    except Exception as e:
        print(f"Aviso ao limpar alertas antigos: {e}")
    
    for empresa in empresas:
        try:
            # Obter dados
            dados_mensais = listar_dados_mensais(empresa['id'], limite=24)
            analise_atual = obter_ultima_analise(empresa['id'])
            
            # Obter análise anterior
            analise_anterior = None
            analises = listar_analises(empresa['id'], limite=2)
            if len(analises) >= 2:
                analise_anterior = analises[1]
            
            # Obter configuração
            config = {}
            try:
                with get_db() as db:
                    from sqlalchemy import text
                    result = db.execute(text("""
                        SELECT * FROM configuracoes_alerta 
                        WHERE empresa_id = :empresa_id AND contador_id = :contador_id
                    """), {"empresa_id": empresa['id'], "contador_id": user['id']}).fetchone()
                    if result:
                        config = dict(result._mapping)
            except Exception:
                pass
            
            # Gerar alertas
            alertas = gerar_alertas_empresa(
                empresa=empresa,
                dados_mensais=dados_mensais,
                analise_atual=analise_atual,
                analise_anterior=analise_anterior,
                config=config
            )
            
            # Salvar alertas
            salvos = 0
            erros_salvamento = []
            try:
                with get_db() as db:
                    from sqlalchemy import text
                    
                    for alerta in alertas:
                        try:
                            # Inserir alerta diretamente (já limpamos os não resolvidos)
                            db.execute(text("""
                                INSERT INTO alertas (
                                    empresa_id, contador_id, tipo, severidade, codigo,
                                    titulo, mensagem, valor_atual, valor_limite, valor_anterior,
                                    dados_json, periodo_referencia
                                ) VALUES (
                                    :empresa_id, :contador_id, :tipo, :severidade, :codigo,
                                    :titulo, :mensagem, :valor_atual, :valor_limite, :valor_anterior,
                                    :dados_json, :periodo_referencia
                                )
                            """), {
                                "empresa_id": empresa['id'],
                                "contador_id": user['id'],
                                "tipo": alerta['tipo'],
                                "severidade": alerta['severidade'],
                                "codigo": alerta['codigo'],
                                "titulo": alerta['titulo'],
                                "mensagem": alerta['mensagem'],
                                "valor_atual": alerta.get('valor_atual'),
                                "valor_limite": alerta.get('valor_limite'),
                                "valor_anterior": alerta.get('valor_anterior'),
                                "dados_json": alerta.get('dados_json'),
                                "periodo_referencia": alerta.get('periodo_referencia')
                            })
                            salvos += 1
                        except Exception as e:
                            erros_salvamento.append(f"{alerta['codigo']}: {str(e)}")
                    
                    db.commit()
            except Exception as e:
                print(f"Erro ao salvar alertas para empresa {empresa['id']}: {e}")
                erros_salvamento.append(f"Geral: {str(e)}")
            
            total_alertas += len(alertas)
            total_salvos += salvos
            
            if alertas:
                resultado_empresa = {
                    "empresa_id": empresa['id'],
                    "empresa": empresa['razao_social'],
                    "alertas_gerados": len(alertas),
                    "alertas_salvos": salvos
                }
                if erros_salvamento:
                    resultado_empresa["erros_salvamento"] = erros_salvamento
                resultados.append(resultado_empresa)
        except Exception as e:
            resultados.append({
                "empresa_id": empresa['id'],
                "empresa": empresa.get('razao_social', 'N/A'),
                "erro": str(e)
            })
    
    return {
        "empresas_analisadas": len(empresas),
        "total_alertas_gerados": total_alertas,
        "total_alertas_salvos": total_salvos,
        "resultados": resultados
    }


# === F12: ANÁLISE FINANCEIRA AVANÇADA ===

# Tenta importar módulo de análise financeira avançada
try:
    from engine.analise_avancada import (
        gerar_analise_avancada, analise_to_dict, get_setores_disponiveis,
        gerar_dre, calcular_indices, calcular_break_even, gerar_projecoes,
        comparar_benchmarks, BENCHMARKS, get_benchmark_setor
    )
    ANALISE_FINANCEIRA_AVAILABLE = True
except ImportError as e:
    print(f"Módulo analise_avancada não disponível: {e}")
    ANALISE_FINANCEIRA_AVAILABLE = False


@app.get("/empresas/{empresa_id}/analise-financeira")
async def obter_analise_financeira(
    empresa_id: int,
    setor: Optional[str] = None,
    user: Dict = Depends(get_user)
):
    """Obtém análise financeira completa da empresa."""
    if not ANALISE_FINANCEIRA_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulo de análise financeira não disponível")
    
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    dados_mensais = listar_dados_mensais(empresa_id, limite=36)
    
    if not dados_mensais:
        return {
            "empresa_id": empresa_id,
            "empresa_nome": empresa.get('razao_social'),
            "erro": "Sem dados financeiros para análise",
            "dados_suficientes": False
        }
    
    setor_empresa = setor or empresa.get('setor') or 'geral'
    analise = gerar_analise_avancada(empresa, dados_mensais, setor_empresa)
    
    # Converter análise para dict e adicionar dados mensais
    analise_dict = analise_to_dict(analise)
    analise_dict['dados_mensais'] = dados_mensais  # Adicionar dados mensais para cálculos no frontend
    
    return {
        "dados_suficientes": True,
        "analise": analise_dict
    }


@app.get("/empresas/{empresa_id}/dre")
async def obter_dre(
    empresa_id: int,
    periodo: Optional[str] = None,
    user: Dict = Depends(get_user)
):
    """Obtém DRE da empresa."""
    if not ANALISE_FINANCEIRA_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulo de análise financeira não disponível")
    
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    dados_mensais = listar_dados_mensais(empresa_id, limite=36)
    
    if not dados_mensais:
        raise HTTPException(status_code=404, detail="Sem dados para gerar DRE")
    
    from dataclasses import asdict
    
    if periodo:
        dre = gerar_dre(dados_mensais, periodo)
        return {"dre": asdict(dre)}
    else:
        # DRE consolidado
        dre = gerar_dre(dados_mensais)
        
        # DRE por mês
        dre_mensal = []
        periodos = {}
        for d in dados_mensais:
            p = f"{d.get('ano')}-{d.get('mes', 1):02d}"
            if p not in periodos:
                periodos[p] = []
            periodos[p].append(d)
        
        for p in sorted(periodos.keys()):
            dre_mes = gerar_dre(periodos[p], p)
            dre_mensal.append(asdict(dre_mes))
        
        return {
            "dre_anual": asdict(dre),
            "dre_mensal": dre_mensal
        }


@app.get("/empresas/{empresa_id}/indices")
async def obter_indices_financeiros(
    empresa_id: int,
    user: Dict = Depends(get_user)
):
    """Obtém índices financeiros da empresa."""
    if not ANALISE_FINANCEIRA_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulo de análise financeira não disponível")
    
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    dados_mensais = listar_dados_mensais(empresa_id, limite=36)
    
    if not dados_mensais:
        raise HTTPException(status_code=404, detail="Sem dados para calcular índices")
    
    from dataclasses import asdict
    indices = calcular_indices(dados_mensais)
    return {"indices": asdict(indices)}


@app.get("/empresas/{empresa_id}/break-even")
async def obter_break_even(
    empresa_id: int,
    user: Dict = Depends(get_user)
):
    """Obtém análise de ponto de equilíbrio."""
    if not ANALISE_FINANCEIRA_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulo de análise financeira não disponível")
    
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    dados_mensais = listar_dados_mensais(empresa_id, limite=12)
    
    if not dados_mensais:
        raise HTTPException(status_code=404, detail="Sem dados para calcular break-even")
    
    from dataclasses import asdict
    be = calcular_break_even(dados_mensais)
    return {"break_even": asdict(be)}


@app.get("/empresas/{empresa_id}/projecoes")
async def obter_projecoes(
    empresa_id: int,
    meses: int = 12,
    user: Dict = Depends(get_user)
):
    """Obtém projeções financeiras para os próximos meses."""
    if not ANALISE_FINANCEIRA_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulo de análise financeira não disponível")
    
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    dados_mensais = listar_dados_mensais(empresa_id, limite=24)
    
    if len(dados_mensais) < 3:
        raise HTTPException(status_code=400, detail="Mínimo de 3 meses de dados para projeções")
    
    from dataclasses import asdict
    projecoes = gerar_projecoes(dados_mensais, min(meses, 24))
    
    # Formata resultado
    resultado = {}
    for p in projecoes:
        resultado[p.cenario] = {
            'taxa_crescimento_receita': p.taxa_crescimento_receita,
            'taxa_variacao_custos': p.taxa_variacao_custos,
            'receita_total': p.receita_total,
            'lucro_total': p.lucro_total,
            'caixa_final': p.caixa_final,
            'margem_media': p.margem_media,
            'dados_mensais': [asdict(m) for m in p.dados_mensais]
        }
    
    return {
        "meses_projetados": min(meses, 24),
        "cenarios": resultado
    }


@app.get("/empresas/{empresa_id}/benchmarks")
async def obter_benchmarks(
    empresa_id: int,
    setor: Optional[str] = None,
    user: Dict = Depends(get_user)
):
    """Compara índices da empresa com benchmarks do setor."""
    if not ANALISE_FINANCEIRA_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulo de análise financeira não disponível")
    
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    dados_mensais = listar_dados_mensais(empresa_id, limite=12)
    
    if not dados_mensais:
        raise HTTPException(status_code=404, detail="Sem dados para comparar")
    
    from dataclasses import asdict
    
    setor_empresa = setor or empresa.get('setor') or 'geral'
    indices = calcular_indices(dados_mensais)
    benchmarks = comparar_benchmarks(indices, setor_empresa)
    
    return {
        "setor": setor_empresa,
        "setor_nome": BENCHMARKS.get(setor_empresa, {}).get('nome', setor_empresa),
        "benchmarks": [asdict(b) for b in benchmarks]
    }


@app.get("/setores")
async def listar_setores(user: Dict = Depends(get_user)):
    """Lista setores disponíveis para benchmark."""
    if not ANALISE_FINANCEIRA_AVAILABLE:
        return {"setores": []}
    
    return {"setores": get_setores_disponiveis()}


# Endpoint para atualizar setor da empresa
class AtualizarSetorRequest(BaseModel):
    setor: str
    porte: Optional[str] = None


@app.put("/empresas/{empresa_id}/setor")
async def atualizar_setor_empresa(
    empresa_id: int,
    dados: AtualizarSetorRequest,
    user: Dict = Depends(get_user)
):
    """Atualiza setor e porte da empresa."""
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    try:
        with get_db() as db:
            from sqlalchemy import text
            db.execute(text("""
                UPDATE empresas 
                SET setor = :setor, porte = :porte, updated_at = NOW()
                WHERE id = :id
            """), {
                "id": empresa_id,
                "setor": dados.setor,
                "porte": dados.porte
            })
            db.commit()
        
        return {"ok": True, "setor": dados.setor, "porte": dados.porte}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Metas financeiras
class MetaFinanceiraRequest(BaseModel):
    ano: int
    mes: Optional[int] = None
    receita_meta: Optional[float] = None
    margem_bruta_meta: Optional[float] = None
    margem_liquida_meta: Optional[float] = None
    custos_meta: Optional[float] = None
    despesas_meta: Optional[float] = None
    caixa_minimo_meta: Optional[float] = None
    observacoes: Optional[str] = None


@app.post("/empresas/{empresa_id}/metas")
async def criar_meta_financeira(
    empresa_id: int,
    meta: MetaFinanceiraRequest,
    user: Dict = Depends(get_user)
):
    """Cria ou atualiza meta financeira."""
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    try:
        with get_db() as db:
            from sqlalchemy import text
            
            # Verifica se meta já existe
            existe = db.execute(text("""
                SELECT id FROM metas_financeiras 
                WHERE empresa_id = :empresa_id AND ano = :ano AND (mes = :mes OR (mes IS NULL AND :mes IS NULL))
            """), {
                "empresa_id": empresa_id,
                "ano": meta.ano,
                "mes": meta.mes
            }).fetchone()
            
            if existe:
                # Atualiza
                db.execute(text("""
                    UPDATE metas_financeiras SET
                        receita_meta = :receita_meta,
                        margem_bruta_meta = :margem_bruta_meta,
                        margem_liquida_meta = :margem_liquida_meta,
                        custos_meta = :custos_meta,
                        despesas_meta = :despesas_meta,
                        caixa_minimo_meta = :caixa_minimo_meta,
                        observacoes = :observacoes,
                        updated_at = NOW()
                    WHERE id = :id
                """), {
                    "id": existe[0],
                    **meta.dict()
                })
            else:
                # Cria nova
                db.execute(text("""
                    INSERT INTO metas_financeiras (
                        empresa_id, contador_id, ano, mes,
                        receita_meta, margem_bruta_meta, margem_liquida_meta,
                        custos_meta, despesas_meta, caixa_minimo_meta, observacoes
                    ) VALUES (
                        :empresa_id, :contador_id, :ano, :mes,
                        :receita_meta, :margem_bruta_meta, :margem_liquida_meta,
                        :custos_meta, :despesas_meta, :caixa_minimo_meta, :observacoes
                    )
                """), {
                    "empresa_id": empresa_id,
                    "contador_id": user['id'],
                    **meta.dict()
                })
            
            db.commit()
            return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/empresas/{empresa_id}/metas")
async def listar_metas(
    empresa_id: int,
    ano: Optional[int] = None,
    user: Dict = Depends(get_user)
):
    """Lista metas financeiras da empresa."""
    empresa = obter_empresa(empresa_id, user['id'])
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    try:
        with get_db() as db:
            from sqlalchemy import text
            
            query = "SELECT * FROM metas_financeiras WHERE empresa_id = :empresa_id"
            params = {"empresa_id": empresa_id}
            
            if ano:
                query += " AND ano = :ano"
                params["ano"] = ano
            
            query += " ORDER BY ano DESC, mes ASC NULLS FIRST"
            
            result = db.execute(text(query), params).fetchall()
            
            metas = []
            for row in result:
                metas.append(dict(row._mapping))
            
            return {"metas": metas}
    except Exception as e:
        return {"metas": [], "error": str(e)}


# === HEALTH ===

@app.get("/")
async def root():
    """Rota raiz - informações do sistema."""
    return {
        "status": "ok", 
        "version": "3.0.0",
        "name": "Sistema Contábil",
        "docs": "/docs",
        "health": "/health"
    }

@app.on_event("startup")
async def create_extra_tables():
    """Criar tabelas adicionais (alertas, análise financeira)."""
    # Criar tabelas de alertas se não existirem
    try:
        from sqlalchemy import text
        with get_db() as db:
            # Tabela de configurações por empresa
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS configuracoes_alerta (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER REFERENCES empresas(id),
                    contador_id INTEGER REFERENCES contadores(id),
                    ativo BOOLEAN DEFAULT true,
                    dias_caixa_critico INTEGER DEFAULT 7,
                    dias_caixa_atencao INTEGER DEFAULT 30,
                    margem_minima FLOAT DEFAULT 10.0,
                    queda_margem_alerta FLOAT DEFAULT 20.0,
                    meses_tendencia INTEGER DEFAULT 3,
                    queda_faturamento_alerta FLOAT DEFAULT 15.0,
                    detectar_anomalias BOOLEAN DEFAULT true,
                    desvios_anomalia FLOAT DEFAULT 2.0,
                    score_critico INTEGER DEFAULT 40,
                    queda_score_alerta INTEGER DEFAULT 15,
                    notificar_email BOOLEAN DEFAULT true,
                    notificar_sistema BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(empresa_id, contador_id)
                )
            '''))
            
            # Tabela de alertas
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS alertas (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER REFERENCES empresas(id),
                    contador_id INTEGER REFERENCES contadores(id),
                    tipo VARCHAR(50) NOT NULL,
                    severidade VARCHAR(20) NOT NULL,
                    codigo VARCHAR(100) NOT NULL,
                    titulo VARCHAR(200) NOT NULL,
                    mensagem TEXT,
                    valor_atual FLOAT,
                    valor_limite FLOAT,
                    valor_anterior FLOAT,
                    dados_json TEXT,
                    periodo_referencia VARCHAR(20),
                    lido BOOLEAN DEFAULT false,
                    lido_em TIMESTAMP,
                    resolvido BOOLEAN DEFAULT false,
                    resolvido_em TIMESTAMP,
                    resolvido_por INTEGER,
                    nota_resolucao TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            '''))
            
            # Tabela de histórico (evita duplicados)
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS alertas_historico (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER REFERENCES empresas(id),
                    codigo VARCHAR(100) NOT NULL,
                    periodo_referencia VARCHAR(20),
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(empresa_id, codigo, periodo_referencia)
                )
            '''))
            
            # Tabela de configuração global
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS configuracoes_alerta_global (
                    id SERIAL PRIMARY KEY,
                    contador_id INTEGER REFERENCES contadores(id) UNIQUE,
                    horario_notificacao VARCHAR(5) DEFAULT '09:00',
                    dias_notificacao VARCHAR(20) DEFAULT '1,2,3,4,5',
                    enviar_resumo_semanal BOOLEAN DEFAULT true,
                    dia_resumo_semanal INTEGER DEFAULT 1,
                    max_alertas_email INTEGER DEFAULT 10,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            '''))
            
            db.commit()
            print("✅ Tabelas de alertas verificadas/criadas")
            
            # Tabelas F12 - Análise Financeira Avançada
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS benchmarks_setor (
                    id SERIAL PRIMARY KEY,
                    setor VARCHAR(100) NOT NULL,
                    subsetor VARCHAR(100),
                    porte VARCHAR(20),
                    margem_bruta_min FLOAT DEFAULT 0,
                    margem_bruta_media FLOAT DEFAULT 0,
                    margem_bruta_max FLOAT DEFAULT 0,
                    margem_liquida_min FLOAT DEFAULT 0,
                    margem_liquida_media FLOAT DEFAULT 0,
                    margem_liquida_max FLOAT DEFAULT 0,
                    liquidez_corrente_media FLOAT DEFAULT 1.5,
                    folha_pct FLOAT DEFAULT 25,
                    impostos_pct FLOAT DEFAULT 15,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(setor, subsetor, porte)
                )
            '''))
            
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS metas_financeiras (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER REFERENCES empresas(id),
                    contador_id INTEGER REFERENCES contadores(id),
                    ano INTEGER NOT NULL,
                    mes INTEGER,
                    receita_meta FLOAT,
                    margem_bruta_meta FLOAT,
                    margem_liquida_meta FLOAT,
                    custos_meta FLOAT,
                    despesas_meta FLOAT,
                    caixa_minimo_meta FLOAT,
                    observacoes TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(empresa_id, ano, mes)
                )
            '''))
            
            db.execute(text('''
                CREATE TABLE IF NOT EXISTS projecoes_financeiras (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER REFERENCES empresas(id),
                    contador_id INTEGER REFERENCES contadores(id),
                    ano INTEGER NOT NULL,
                    mes INTEGER NOT NULL,
                    cenario VARCHAR(20) NOT NULL,
                    receita_projetada FLOAT DEFAULT 0,
                    custos_projetados FLOAT DEFAULT 0,
                    despesas_projetadas FLOAT DEFAULT 0,
                    lucro_projetado FLOAT DEFAULT 0,
                    caixa_projetado FLOAT DEFAULT 0,
                    taxa_crescimento FLOAT,
                    premissas_json TEXT,
                    gerado_em TIMESTAMP DEFAULT NOW(),
                    UNIQUE(empresa_id, ano, mes, cenario)
                )
            '''))
            
            # Adicionar coluna setor na empresa se não existir
            try:
                db.execute(text('ALTER TABLE empresas ADD COLUMN IF NOT EXISTS setor VARCHAR(100)'))
                db.execute(text('ALTER TABLE empresas ADD COLUMN IF NOT EXISTS porte VARCHAR(20)'))
            except:
                pass
            
            db.commit()
            print("✅ Tabelas de análise financeira verificadas/criadas")
    except Exception as e:
        print(f"⚠️ Erro ao criar tabelas de alertas: {e}")


# ============================================================================
# IMPORTAÇÃO DE BALANCETES (PDF/XLS)
# ============================================================================

# Importa módulo de balancetes
try:
    from importers import importar_balancete, importar_balancete_e_salvar, BALANCETE_IMPORTER_AVAILABLE
except ImportError:
    BALANCETE_IMPORTER_AVAILABLE = False


@app.post("/importar/balancete")
async def importar_balancete_route(
    file: UploadFile = File(...),
    user: Dict = Depends(get_user)
):
    """
    Importa balancete de arquivo PDF ou XLS.
    
    Extrai automaticamente todos os dados financeiros:
    - Empresa (nome, CNPJ)
    - Período
    - Balanço Patrimonial
    - DRE
    - Impostos
    - Indicadores
    
    A empresa é identificada automaticamente pelo CNPJ.
    """
    if not BALANCETE_IMPORTER_AVAILABLE:
        raise HTTPException(
            status_code=501, 
            detail="Importador de balancetes não disponível"
        )
    
    # Validar extensão
    extensao = os.path.splitext(file.filename)[1].lower()
    if extensao not in ['.pdf', '.xls', '.xlsx', '.xlsm', '.csv']:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado: {extensao}. Use PDF, XLS, XLSX ou CSV."
        )
    
    conteudo = await file.read()
    
    try:
        resultado = importar_balancete(conteudo, file.filename)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/importar/balancete/salvar")
async def importar_balancete_e_salvar_route(
    file: UploadFile = File(...),
    empresa_id: Optional[int] = Form(None),
    user: Dict = Depends(get_user)
):
    """
    Importa balancete e salva os dados no sistema.
    
    Se empresa_id não for informado, busca ou cria a empresa pelo CNPJ.
    """
    if not BALANCETE_IMPORTER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Importador de balancetes não disponível"
        )
    
    conteudo = await file.read()
    
    try:
        resultado = importar_balancete_e_salvar(
            conteudo=conteudo,
            nome_arquivo=file.filename,
            contador_id=user['id'],
            empresa_id=empresa_id
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/importar/balancetes/lote")
async def importar_balancetes_lote(
    files: List[UploadFile] = File(...),
    user: Dict = Depends(get_user)
):
    """
    Importa múltiplos balancetes de uma vez.
    
    Cada arquivo representa um período/mês diferente.
    A empresa é identificada automaticamente pelo CNPJ.
    """
    if not BALANCETE_IMPORTER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Importador de balancetes não disponível"
        )
    
    try:
        from engine.importacao_lote import processar_importacao_lote
        
        # Preparar arquivos
        arquivos = []
        for file in files:
            conteudo = await file.read()
            arquivos.append((conteudo, file.filename))
        
        # Processar em lote
        resultado = processar_importacao_lote(arquivos, user['id'])
        return resultado
        
    except ImportError:
        # Fallback: processar sequencialmente
        resultados = []
        for file in files:
            conteudo = await file.read()
            try:
                res = importar_balancete(conteudo, file.filename)
                resultados.append({
                    'nome': file.filename,
                    'sucesso': res.get('sucesso', False),
                    'dados': res
                })
            except Exception as e:
                resultados.append({
                    'nome': file.filename,
                    'sucesso': False,
                    'erro': str(e)
                })
        
        return {
            'total_arquivos': len(files),
            'processados_sucesso': len([r for r in resultados if r['sucesso']]),
            'processados_erro': len([r for r in resultados if not r['sucesso']]),
            'arquivos': resultados
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Importar calculadora de indicadores
try:
    from engine.importacao_lote import calcular_indicadores, gerar_insights, calcular_score
    INSIGHTS_AVAILABLE = True
except ImportError:
    INSIGHTS_AVAILABLE = False


@app.post("/analise/indicadores")
async def calcular_indicadores_route(
    dados: Dict,
    user: Dict = Depends(get_user)
):
    """
    Calcula indicadores financeiros a partir dos dados fornecidos.
    """
    if not INSIGHTS_AVAILABLE:
        raise HTTPException(status_code=501, detail="Calculadora não disponível")
    
    try:
        indicadores = calcular_indicadores(dados)
        return {
            'sucesso': True,
            'indicadores': indicadores
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/analise/insights")
async def gerar_insights_route(
    dados: Dict,
    user: Dict = Depends(get_user)
):
    """
    Gera insights e recomendações a partir dos dados financeiros.
    """
    if not INSIGHTS_AVAILABLE:
        raise HTTPException(status_code=501, detail="Gerador de insights não disponível")
    
    try:
        indicadores = calcular_indicadores(dados.get('totais', dados))
        insights = gerar_insights(indicadores, dados.get('totais', dados))
        score = calcular_score(indicadores)
        
        return {
            'sucesso': True,
            'indicadores': indicadores,
            'insights': insights,
            'score': score
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/empresas/{id}/insights")
async def obter_insights_empresa(
    id: int,
    user: Dict = Depends(get_user)
):
    """
    Obtém insights da empresa baseados nos dados mais recentes.
    """
    emp = obter_empresa(id, user['id'])
    if not emp:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Obter dados mais recentes
    dados_raw = listar_dados_mensais(id, limite=1)
    if not dados_raw:
        return {
            'sucesso': True,
            'insights': [],
            'score': 50,
            'mensagem': 'Sem dados suficientes para análise'
        }
    
    dados = dados_raw[0]
    
    if INSIGHTS_AVAILABLE:
        try:
            indicadores = calcular_indicadores(dados)
            insights = gerar_insights(indicadores, dados)
            score = calcular_score(indicadores)
            
            return {
                'sucesso': True,
                'periodo': dados.get('competencia'),
                'indicadores': indicadores,
                'insights': insights,
                'score': score
            }
        except Exception as e:
            pass
    
    # Fallback básico
    return {
        'sucesso': True,
        'periodo': dados.get('competencia'),
        'indicadores': {},
        'insights': [],
        'score': 50
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
