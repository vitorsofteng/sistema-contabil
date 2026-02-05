#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Segurança - Autenticação Robusta
==========================================

Features:
- Bcrypt para hash de senhas (com fallback para SHA256)
- JWT com Access Token (15min) + Refresh Token (7 dias)
- Rate Limiting para proteção contra brute force
- Validação de senha forte
- Blacklist de tokens (logout)
"""

import os
import re
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Bibliotecas de segurança são OBRIGATÓRIAS
try:
    from passlib.context import CryptContext
    from jose import JWTError, jwt
    CRYPTO_AVAILABLE = True
except ImportError:
    raise RuntimeError(
        "ERRO FATAL: Bibliotecas de criptografia não encontradas. "
        "Execute: pip install passlib python-jose[cryptography] bcrypt"
    )


# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

class AuthConfig:
    """Configurações de autenticação."""
    
    # JWT - chaves DEVEM ser definidas via variáveis de ambiente
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    REFRESH_SECRET_KEY = os.environ.get('REFRESH_SECRET_KEY', '')
    
    # Validação: falha ruidosamente se não configurado (exceto dev local)
    _env = os.environ.get('ENVIRONMENT', 'development')
    if _env != 'development' and (not SECRET_KEY or len(SECRET_KEY) < 32):
        raise RuntimeError(
            "ERRO FATAL: SECRET_KEY não definida ou muito curta. "
            "Gere com: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )
    if not SECRET_KEY:
        # Fallback FIXO para desenvolvimento local (não aleatório!)
        SECRET_KEY = 'dev-only-secret-key-do-not-use-in-production-1234567890'
    if not REFRESH_SECRET_KEY:
        REFRESH_SECRET_KEY = 'dev-only-refresh-key-do-not-use-in-production-1234567890'
    
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas
    REFRESH_TOKEN_EXPIRE_DAYS = 30     # 30 dias
    
    # Rate Limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    
    # Senha
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Reset de senha
    RESET_TOKEN_EXPIRE_HOURS = 1


# =============================================================================
# PASSWORD HASHING
# =============================================================================

if CRYPTO_AVAILABLE:
    # Contexto de criptografia com bcrypt
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=12
    )
    
    def hash_password(password: str) -> str:
        """Gera hash da senha usando bcrypt."""
        return pwd_context.hash(password)
    
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha confere com o hash."""
        try:
            # Tenta bcrypt primeiro
            if hashed_password.startswith('$2'):
                return pwd_context.verify(plain_password, hashed_password)
            # Fallback para SHA256 (senhas antigas)
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
        except Exception:
            return False
    
    def needs_rehash(hashed_password: str) -> bool:
        """Verifica se o hash precisa ser atualizado."""
        if not hashed_password.startswith('$2'):
            return True  # SHA256 precisa migrar para bcrypt
        return pwd_context.needs_update(hashed_password)




# =============================================================================
# VALIDAÇÃO DE SENHA
# =============================================================================

@dataclass
class PasswordValidationResult:
    """Resultado da validação de senha."""
    valid: bool
    errors: list


def validate_password_strength(password: str) -> PasswordValidationResult:
    """
    Valida a força da senha.
    
    Requisitos:
    - Mínimo 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial
    """
    errors = []
    
    if len(password) < AuthConfig.MIN_PASSWORD_LENGTH:
        errors.append(f"Senha deve ter no mínimo {AuthConfig.MIN_PASSWORD_LENGTH} caracteres")
    
    if AuthConfig.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        errors.append("Senha deve conter pelo menos 1 letra maiúscula")
    
    if AuthConfig.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        errors.append("Senha deve conter pelo menos 1 letra minúscula")
    
    if AuthConfig.REQUIRE_DIGIT and not re.search(r'\d', password):
        errors.append("Senha deve conter pelo menos 1 número")
    
    if AuthConfig.REQUIRE_SPECIAL:
        pattern = f'[{re.escape(AuthConfig.SPECIAL_CHARS)}]'
        if not re.search(pattern, password):
            errors.append("Senha deve conter pelo menos 1 caractere especial (!@#$%^&*...)")
    
    return PasswordValidationResult(valid=len(errors) == 0, errors=errors)


# =============================================================================
# JWT TOKENS
# =============================================================================

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"


if CRYPTO_AVAILABLE:
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Cria um access token JWT."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.ACCESS.value,
            "jti": secrets.token_urlsafe(16)
        })
        
        return jwt.encode(to_encode, AuthConfig.SECRET_KEY, algorithm=AuthConfig.ALGORITHM)

    def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Cria um refresh token JWT."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=AuthConfig.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.REFRESH.value,
            "jti": secrets.token_urlsafe(16)
        })
        
        return jwt.encode(to_encode, AuthConfig.REFRESH_SECRET_KEY, algorithm=AuthConfig.ALGORITHM)

    def create_reset_token(user_id: int) -> str:
        """Cria um token para reset de senha."""
        expire = datetime.utcnow() + timedelta(hours=AuthConfig.RESET_TOKEN_EXPIRE_HOURS)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.RESET_PASSWORD.value,
            "jti": secrets.token_urlsafe(16)
        }
        
        return jwt.encode(to_encode, AuthConfig.SECRET_KEY, algorithm=AuthConfig.ALGORITHM)

    def decode_access_token(token: str) -> Optional[Dict]:
        """Decodifica e valida um access token."""
        try:
            payload = jwt.decode(token, AuthConfig.SECRET_KEY, algorithms=[AuthConfig.ALGORITHM])
            if payload.get("type") != TokenType.ACCESS.value:
                return None
            return payload
        except JWTError:
            return None

    def decode_refresh_token(token: str) -> Optional[Dict]:
        """Decodifica e valida um refresh token."""
        try:
            payload = jwt.decode(token, AuthConfig.REFRESH_SECRET_KEY, algorithms=[AuthConfig.ALGORITHM])
            if payload.get("type") != TokenType.REFRESH.value:
                return None
            return payload
        except JWTError:
            return None

    def decode_reset_token(token: str) -> Optional[Dict]:
        """Decodifica e valida um token de reset de senha."""
        try:
            payload = jwt.decode(token, AuthConfig.SECRET_KEY, algorithms=[AuthConfig.ALGORITHM])
            if payload.get("type") != TokenType.RESET_PASSWORD.value:
                return None
            return payload
        except JWTError:
            return None




# =============================================================================
# RATE LIMITING (Em memória - para produção usar Redis)
# =============================================================================

class RateLimiter:
    """Rate limiter em memória para proteção contra brute force."""
    
    def __init__(self):
        self._attempts: Dict[str, Dict] = {}
    
    def _clean_expired(self):
        """Remove entradas expiradas."""
        now = datetime.utcnow()
        expired = [
            key for key, val in self._attempts.items()
            if val.get("locked_until") and val["locked_until"] < now
        ]
        for key in expired:
            del self._attempts[key]
    
    def is_locked(self, identifier: str) -> Tuple[bool, Optional[int]]:
        """Verifica se o identificador está bloqueado."""
        self._clean_expired()
        
        if identifier not in self._attempts:
            return False, None
        
        entry = self._attempts[identifier]
        locked_until = entry.get("locked_until")
        
        if locked_until and locked_until > datetime.utcnow():
            remaining = int((locked_until - datetime.utcnow()).total_seconds())
            return True, remaining
        
        return False, None
    
    def record_attempt(self, identifier: str, success: bool) -> Tuple[bool, Optional[int]]:
        """Registra uma tentativa de login."""
        self._clean_expired()
        
        if success:
            if identifier in self._attempts:
                del self._attempts[identifier]
            return False, None
        
        if identifier not in self._attempts:
            self._attempts[identifier] = {"attempts": 0, "locked_until": None}
        
        self._attempts[identifier]["attempts"] += 1
        attempts = self._attempts[identifier]["attempts"]
        
        if attempts >= AuthConfig.MAX_LOGIN_ATTEMPTS:
            locked_until = datetime.utcnow() + timedelta(minutes=AuthConfig.LOCKOUT_DURATION_MINUTES)
            self._attempts[identifier]["locked_until"] = locked_until
            return True, AuthConfig.LOCKOUT_DURATION_MINUTES * 60
        
        return False, None
    
    def get_remaining_attempts(self, identifier: str) -> int:
        """Retorna tentativas restantes."""
        if identifier not in self._attempts:
            return AuthConfig.MAX_LOGIN_ATTEMPTS
        
        used = self._attempts[identifier].get("attempts", 0)
        return max(0, AuthConfig.MAX_LOGIN_ATTEMPTS - used)
    
    def reset(self, identifier: str):
        """Reseta contagem para um identificador."""
        if identifier in self._attempts:
            del self._attempts[identifier]


# Instância global do rate limiter
rate_limiter = RateLimiter()


# =============================================================================
# TOKEN BLACKLIST
# =============================================================================

class TokenBlacklist:
    """Blacklist de tokens para logout."""
    
    def __init__(self):
        self._blacklist: Dict[str, datetime] = {}
    
    def _clean_expired(self):
        """Remove tokens expirados da blacklist."""
        now = datetime.utcnow()
        expired = [jti for jti, exp in self._blacklist.items() if exp < now]
        for jti in expired:
            del self._blacklist[jti]
    
    def add(self, jti: str, exp: datetime):
        """Adiciona token à blacklist."""
        self._clean_expired()
        self._blacklist[jti] = exp
    
    def is_blacklisted(self, jti: str) -> bool:
        """Verifica se token está na blacklist."""
        self._clean_expired()
        return jti in self._blacklist


# Instância global da blacklist
token_blacklist = TokenBlacklist()


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def generate_session_id() -> str:
    """Gera ID único para sessão."""
    return secrets.token_urlsafe(32)


def mask_email(email: str) -> str:
    """Mascara email para exibição segura."""
    if not email or "@" not in email:
        return "***"
    
    local, domain = email.split("@")
    domain_parts = domain.split(".")
    
    masked_local = local[0] + "***" if len(local) > 0 else "***"
    masked_domain = domain_parts[0][0] + "***" if len(domain_parts[0]) > 0 else "***"
    
    return f"{masked_local}@{masked_domain}.{domain_parts[-1]}"
