"""
Módulo de Segurança - Sprint 1
Implementa: Rate Limiting, Headers de Segurança, Sanitização, Validação de Senha
"""

import re
import time
import html
import hashlib
from typing import Dict, Optional, Callable, Tuple, List
from collections import defaultdict
from functools import wraps

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Importar configurações
try:
    from core.config import settings
except ImportError:
    class FallbackSettings:
        rate_limit_enabled = True
        rate_limit_per_minute = 60
        rate_limit_login_per_minute = 5
        rate_limit_login_window = 15
        security_headers_enabled = True
        hsts_enabled = True
        hsts_max_age = 31536000
        is_production = False
        password_min_length = 8
        password_require_uppercase = True
        password_require_lowercase = True
        password_require_digit = True
        password_require_special = False
    settings = FallbackSettings()


# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """Rate limiter em memória com suporte a bloqueio de IP."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.blocked: Dict[str, float] = {}
        self.failed_logins: Dict[str, list] = defaultdict(list)
        self.last_cleanup = time.time()
    
    def _cleanup(self):
        """Remove registros antigos periodicamente."""
        now = time.time()
        if now - self.last_cleanup < 60:
            return
        
        cutoff = now - 120
        for key in list(self.requests.keys()):
            self.requests[key] = [(ts, c) for ts, c in self.requests[key] if ts > cutoff]
            if not self.requests[key]:
                del self.requests[key]
        
        for key in list(self.failed_logins.keys()):
            self.failed_logins[key] = [ts for ts in self.failed_logins[key] if ts > cutoff]
            if not self.failed_logins[key]:
                del self.failed_logins[key]
        
        for ip in list(self.blocked.keys()):
            if now > self.blocked[ip]:
                del self.blocked[ip]
        
        self.last_cleanup = now
    
    def is_blocked(self, ip: str) -> bool:
        """Verifica se IP está bloqueado."""
        if ip in self.blocked:
            if time.time() < self.blocked[ip]:
                return True
            del self.blocked[ip]
        return False
    
    def block(self, ip: str, minutes: int = 15):
        """Bloqueia IP por N minutos."""
        self.blocked[ip] = time.time() + (minutes * 60)
    
    def check_rate_limit(self, ip: str, limit: int, window: int = 60) -> Tuple[bool, int]:
        """Verifica rate limit. Retorna (permitido, restantes)."""
        self._cleanup()
        
        if self.is_blocked(ip):
            return False, 0
        
        now = time.time()
        cutoff = now - window
        self.requests[ip] = [(ts, c) for ts, c in self.requests[ip] if ts > cutoff]
        total = sum(c for _, c in self.requests[ip])
        
        if total >= limit:
            return False, 0
        
        self.requests[ip].append((now, 1))
        return True, limit - total - 1
    
    def record_failed_login(self, ip: str) -> int:
        """Registra tentativa de login falha. Retorna total de tentativas."""
        now = time.time()
        window = settings.rate_limit_login_window * 60
        self.failed_logins[ip] = [ts for ts in self.failed_logins[ip] if ts > now - window]
        self.failed_logins[ip].append(now)
        return len(self.failed_logins[ip])
    
    def clear_failed_logins(self, ip: str):
        """Limpa tentativas após login bem-sucedido."""
        if ip in self.failed_logins:
            del self.failed_logins[ip]
    
    def get_failed_login_count(self, ip: str) -> int:
        """Retorna número de tentativas falhas."""
        now = time.time()
        window = settings.rate_limit_login_window * 60
        self.failed_logins[ip] = [ts for ts in self.failed_logins[ip] if ts > now - window]
        return len(self.failed_logins[ip])


# Instância global
rate_limiter = RateLimiter()


# ============================================================================
# MIDDLEWARES
# ============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting."""
    
    # Endpoints que NÃO devem ter rate limit do middleware (tratados internamente ou alta frequência)
    SKIP_MIDDLEWARE_LIMIT = [
        "/auth/registrar", "/auth/login", "/health", "/docs", "/openapi.json",
        "/dashboard", "/empresas", "/graficos", "/alertas", "/relatorios"
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # Ignorar requisições OPTIONS (preflight CORS)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Ignorar requisições GET comuns (são menos críticas)
        if request.method == "GET":
            return await call_next(request)
        
        ip = self._get_client_ip(request)
        path = request.url.path
        
        # Verificar se IP está bloqueado
        if rate_limiter.is_blocked(ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "IP bloqueado temporariamente. Tente novamente mais tarde."},
                headers={"Retry-After": str(settings.rate_limit_login_window * 60)}
            )
        
        # Pular rate limit do middleware para endpoints que tratam internamente
        if any(skip in path for skip in self.SKIP_MIDDLEWARE_LIMIT):
            return await call_next(request)
        
        # Limite geral: 300 por minuto (mais generoso)
        limit = settings.rate_limit_per_minute
        
        allowed, remaining = rate_limiter.check_rate_limit(ip, limit)
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitas requisições. Aguarde um momento."},
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        if request.client:
            return request.client.host
        return "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware que adiciona headers de segurança."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        if not settings.security_headers_enabled:
            return response
        
        # Prevenir clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevenir MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS (apenas em produção com HTTPS)
        if settings.hsts_enabled and settings.is_production:
            response.headers["Strict-Transport-Security"] = f"max-age={settings.hsts_max_age}; includeSubDomains"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' http://localhost:* ws://localhost:*; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redireciona HTTP para HTTPS em produção."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.is_production:
            return await call_next(request)
        
        proto = request.headers.get("X-Forwarded-Proto", "http")
        if proto == "https":
            return await call_next(request)
        
        url = str(request.url).replace("http://", "https://", 1)
        return Response(status_code=301, headers={"Location": url})


# ============================================================================
# VALIDAÇÃO DE SENHA
# ============================================================================

class PasswordValidator:
    """Validador de força de senha."""
    
    # Senhas comuns proibidas
    COMMON_PASSWORDS = {
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'senha', 'senha123', 'admin', 'administrator', 'letmein',
        'welcome', 'monkey', 'dragon', 'master', 'login', '111111',
        'password1', 'senha@123', 'mudar123', 'teste123'
    }
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, List[str]]:
        """Valida senha. Retorna (válida, lista_de_erros)."""
        errors = []
        
        if len(password) < settings.password_min_length:
            errors.append(f"Mínimo {settings.password_min_length} caracteres")
        
        if settings.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Deve conter letra maiúscula")
        
        if settings.password_require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Deve conter letra minúscula")
        
        if settings.password_require_digit and not re.search(r'\d', password):
            errors.append("Deve conter número")
        
        if settings.password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Deve conter caractere especial (!@#$%^&*)")
        
        if password.lower() in cls.COMMON_PASSWORDS:
            errors.append("Senha muito comum")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_strength(cls, password: str) -> Dict:
        """Analisa força da senha."""
        score = 0
        
        if len(password) >= 8: score += 1
        if len(password) >= 12: score += 1
        if len(password) >= 16: score += 1
        if re.search(r'[a-z]', password): score += 1
        if re.search(r'[A-Z]', password): score += 1
        if re.search(r'\d', password): score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password): score += 1
        
        # Penalidades
        if re.search(r'(.)\1{2,}', password): score -= 1
        if password.lower() in cls.COMMON_PASSWORDS: score -= 2
        
        score = max(0, min(5, score))
        labels = {0: "Muito fraca", 1: "Fraca", 2: "Regular", 3: "Boa", 4: "Forte", 5: "Muito forte"}
        
        return {"score": score, "max_score": 5, "strength": labels[score]}


# ============================================================================
# SANITIZAÇÃO DE INPUTS
# ============================================================================

class InputSanitizer:
    """Sanitização de inputs contra XSS e SQL Injection."""
    
    SQL_PATTERNS = [
        r"(\s|^)(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)(\s|$)",
        r"--", r";(\s|$)", r"'(\s|$)", r"(\s|^)OR(\s|$).*=", r"EXEC(\s|$)"
    ]
    
    XSS_PATTERNS = [
        r"<script", r"javascript:", r"on\w+\s*=", r"<iframe", r"<object",
        r"<embed", r"document\.", r"window\.", r"eval\(", r"alert\("
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 10000) -> str:
        """Sanitiza string."""
        if not value:
            return value
        value = value[:max_length]
        value = html.escape(value)
        value = value.replace('\x00', '')
        return ' '.join(value.split())
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Verifica padrões de SQL injection."""
        if not value:
            return False
        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value.upper(), re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        """Verifica padrões de XSS."""
        if not value:
            return False
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value.lower(), re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def validate_input(cls, value: str, field_name: str = "campo") -> Tuple[bool, Optional[str]]:
        """Valida input. Retorna (válido, erro)."""
        if not value:
            return True, None
        if cls.check_sql_injection(value):
            return False, f"Caracteres não permitidos em {field_name}"
        if cls.check_xss(value):
            return False, f"Conteúdo não permitido em {field_name}"
        return True, None
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitiza nome de arquivo."""
        if not filename:
            return "arquivo"
        filename = filename.replace("..", "").replace("/", "").replace("\\", "")
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        return filename[:200] or "arquivo"


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def get_client_ip(request: Request) -> str:
    """Obtém IP real do cliente."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"


def hash_for_log(value: str) -> str:
    """Hash de valor para logs (privacidade)."""
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def mask_email(email: str) -> str:
    """Mascara email para logs."""
    if not email or '@' not in email:
        return "***"
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked = '*' * len(local)
    else:
        masked = local[0] + '*' * (len(local) - 2) + local[-1]
    return f"{masked}@{domain}"
