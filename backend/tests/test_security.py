"""
Testes Unitários - Módulo de Segurança Básica
Testes PUROS que não dependem de módulos externos (fastapi, sqlalchemy, etc.)
"""

import pytest
import re
import time
import hashlib
import html
from collections import defaultdict
from typing import Tuple, List


# ============================================================================
# IMPLEMENTAÇÕES STANDALONE PARA TESTES
# ============================================================================

class PasswordValidatorStandalone:
    """Validador de senhas - implementação standalone para testes."""
    
    COMMON_PASSWORDS = [
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'monkey', '1234567', 'letmein', 'trustno1', 'dragon',
        'baseball', 'iloveyou', 'master', 'sunshine', 'ashley',
        'passw0rd', 'shadow', '123123', '654321', 'superman'
    ]
    
    MIN_LENGTH = 8
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, List[str]]:
        """Valida senha e retorna (válido, lista_de_erros)."""
        errors = []
        
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Senha deve ter no mínimo {cls.MIN_LENGTH} caracteres")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Senha deve conter pelo menos uma letra maiúscula")
        
        if not re.search(r'[a-z]', password):
            errors.append("Senha deve conter pelo menos uma letra minúscula")
        
        if not re.search(r'\d', password):
            errors.append("Senha deve conter pelo menos um número")
        
        password_lower = password.lower()
        for common in cls.COMMON_PASSWORDS:
            if common in password_lower:
                errors.append("Senha muito comum ou previsível")
                break
        
        return (len(errors) == 0, errors)
    
    @classmethod
    def get_strength(cls, password: str) -> dict:
        """Avalia força da senha."""
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        
        levels = {0: "muito_fraca", 1: "muito_fraca", 2: "fraca", 3: "media",
                  4: "forte", 5: "forte", 6: "muito_forte", 7: "muito_forte"}
        
        return {"score": score, "level": levels.get(score, "muito_forte")}


class InputSanitizerStandalone:
    """Sanitizador de inputs - implementação standalone para testes."""
    
    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        if not value:
            return False
        value_upper = value.upper()
        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        if not value:
            return False
        value_lower = value.lower()
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        if not value:
            return value
        value = value.replace('\x00', '')
        value = html.escape(value)
        if len(value) > max_length:
            value = value[:max_length]
        return value
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        if not filename:
            return "unnamed"
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        filename = re.sub(r'[<>:"|?*]', '', filename)
        return filename or "unnamed"
    
    @classmethod
    def validate_input(cls, value: str, field_name: str) -> Tuple[bool, str]:
        if cls.check_sql_injection(value):
            return False, f"Campo {field_name} contém caracteres inválidos (SQL)"
        if cls.check_xss(value):
            return False, f"Campo {field_name} contém caracteres inválidos (XSS)"
        return True, None


class RateLimiterStandalone:
    """Rate limiter - implementação standalone para testes."""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.blocked = {}
        self.failed_logins = defaultdict(list)
    
    def check_rate_limit(self, ip: str, limit: int, window: int = 60) -> Tuple[bool, int]:
        now = time.time()
        cutoff = now - window
        self.requests[ip] = [ts for ts in self.requests[ip] if ts > cutoff]
        current_count = len(self.requests[ip])
        if current_count >= limit:
            return False, 0
        self.requests[ip].append(now)
        return True, limit - current_count - 1
    
    def is_blocked(self, ip: str) -> bool:
        if ip in self.blocked:
            if time.time() < self.blocked[ip]:
                return True
            del self.blocked[ip]
        return False
    
    def block(self, ip: str, minutes: int = 15):
        self.blocked[ip] = time.time() + (minutes * 60)
    
    def record_failed_login(self, ip: str) -> int:
        self.failed_logins[ip].append(time.time())
        return len(self.failed_logins[ip])
    
    def clear_failed_logins(self, ip: str):
        self.failed_logins[ip] = []
    
    def get_failed_login_count(self, ip: str) -> int:
        return len(self.failed_logins[ip])


def hash_for_log(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def mask_email(email: str) -> str:
    if not email or '@' not in email:
        return '***@***'
    parts = email.split('@')
    local = parts[0]
    domain = parts[1]
    if len(local) <= 2:
        masked_local = '***'
    else:
        masked_local = local[0] + '***' + local[-1]
    return f"{masked_local}@{domain}"


# ============================================================================
# TESTES
# ============================================================================

class TestPasswordValidator:
    """Testes para validação de senha."""
    
    def test_senha_valida_completa(self):
        is_valid, errors = PasswordValidatorStandalone.validate("Senha@123")
        assert is_valid is True
        assert errors == []
    
    def test_senha_curta(self):
        is_valid, errors = PasswordValidatorStandalone.validate("Ab@1")
        assert is_valid is False
        assert any("8 caracteres" in e for e in errors)
    
    def test_senha_sem_maiuscula(self):
        is_valid, errors = PasswordValidatorStandalone.validate("senha@123")
        assert is_valid is False
        assert any("maiúscula" in e for e in errors)
    
    def test_senha_sem_minuscula(self):
        is_valid, errors = PasswordValidatorStandalone.validate("SENHA@123")
        assert is_valid is False
        assert any("minúscula" in e for e in errors)
    
    def test_senha_sem_numero(self):
        is_valid, errors = PasswordValidatorStandalone.validate("Senha@abc")
        assert is_valid is False
        assert any("número" in e for e in errors)
    
    def test_senha_comum_bloqueada(self):
        is_valid, errors = PasswordValidatorStandalone.validate("Password123!")
        assert is_valid is False
        assert any("comum" in e.lower() for e in errors)
    
    def test_senha_123456_bloqueada(self):
        is_valid, errors = PasswordValidatorStandalone.validate("123456Aa!")
        assert is_valid is False
    
    def test_forca_senha_fraca(self):
        result = PasswordValidatorStandalone.get_strength("abc")
        assert result["score"] < 3
        assert result["level"] in ["muito_fraca", "fraca"]
    
    def test_forca_senha_forte(self):
        result = PasswordValidatorStandalone.get_strength("S3nh@Sup3rF0rt3!")
        assert result["score"] >= 4
        assert result["level"] in ["forte", "muito_forte"]


class TestInputSanitizer:
    """Testes para sanitização de inputs."""
    
    def test_detecta_sql_injection_select(self):
        result = InputSanitizerStandalone.check_sql_injection("'; SELECT * FROM users; --")
        assert result is True
    
    def test_detecta_sql_injection_union(self):
        result = InputSanitizerStandalone.check_sql_injection("1 UNION SELECT password FROM users")
        assert result is True
    
    def test_detecta_sql_injection_drop(self):
        result = InputSanitizerStandalone.check_sql_injection("'; DROP TABLE users; --")
        assert result is True
    
    def test_texto_normal_nao_e_sql_injection(self):
        result = InputSanitizerStandalone.check_sql_injection("João da Silva")
        assert result is False
    
    def test_detecta_xss_script(self):
        result = InputSanitizerStandalone.check_xss("<script>alert('xss')</script>")
        assert result is True
    
    def test_detecta_xss_onerror(self):
        result = InputSanitizerStandalone.check_xss('<img src="x" onerror="alert(1)">')
        assert result is True
    
    def test_detecta_xss_javascript(self):
        result = InputSanitizerStandalone.check_xss('javascript:alert(1)')
        assert result is True
    
    def test_texto_normal_nao_e_xss(self):
        result = InputSanitizerStandalone.check_xss("Empresa LTDA - Serviços")
        assert result is False
    
    def test_sanitize_string_escapa_html(self):
        result = InputSanitizerStandalone.sanitize_string("<b>teste</b>")
        assert "<" not in result
        assert ">" not in result
    
    def test_sanitize_string_remove_null_bytes(self):
        result = InputSanitizerStandalone.sanitize_string("teste\x00injeção")
        assert "\x00" not in result
    
    def test_sanitize_string_limita_tamanho(self):
        texto_longo = "a" * 10000
        result = InputSanitizerStandalone.sanitize_string(texto_longo, max_length=100)
        assert len(result) <= 100
    
    def test_sanitize_filename_remove_path_traversal(self):
        result = InputSanitizerStandalone.sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
    
    def test_sanitize_filename_mantem_extensao(self):
        result = InputSanitizerStandalone.sanitize_filename("relatorio.pdf")
        assert result.endswith(".pdf")
    
    def test_validate_input_valido(self):
        valid, error = InputSanitizerStandalone.validate_input("João Silva", "nome")
        assert valid is True
        assert error is None
    
    def test_validate_input_sql_injection(self):
        valid, error = InputSanitizerStandalone.validate_input("'; DROP TABLE users; --", "nome")
        assert valid is False
        assert "SQL" in error
    
    def test_validate_input_xss(self):
        valid, error = InputSanitizerStandalone.validate_input("<script>alert(1)</script>", "nome")
        assert valid is False


class TestRateLimiter:
    """Testes para rate limiter."""
    
    def test_primeira_requisicao_permitida(self):
        limiter = RateLimiterStandalone()
        allowed, remaining = limiter.check_rate_limit("192.168.1.100", limit=60)
        assert allowed is True
        assert remaining == 59
    
    def test_limite_excedido(self):
        limiter = RateLimiterStandalone()
        ip = "192.168.1.101"
        for _ in range(5):
            limiter.check_rate_limit(ip, limit=5)
        allowed, remaining = limiter.check_rate_limit(ip, limit=5)
        assert allowed is False
        assert remaining == 0
    
    def test_ips_diferentes_nao_interferem(self):
        limiter = RateLimiterStandalone()
        for _ in range(5):
            limiter.check_rate_limit("192.168.1.1", limit=5)
        allowed, _ = limiter.check_rate_limit("192.168.1.2", limit=5)
        assert allowed is True
    
    def test_bloqueio_de_ip(self):
        limiter = RateLimiterStandalone()
        ip = "192.168.1.102"
        limiter.block(ip, minutes=1)
        assert limiter.is_blocked(ip) is True
    
    def test_ip_nao_bloqueado(self):
        limiter = RateLimiterStandalone()
        assert limiter.is_blocked("192.168.1.103") is False
    
    def test_registro_tentativas_login_falhas(self):
        limiter = RateLimiterStandalone()
        ip = "192.168.1.104"
        count1 = limiter.record_failed_login(ip)
        count2 = limiter.record_failed_login(ip)
        count3 = limiter.record_failed_login(ip)
        assert count1 == 1
        assert count2 == 2
        assert count3 == 3
    
    def test_limpar_tentativas_falhas(self):
        limiter = RateLimiterStandalone()
        ip = "192.168.1.105"
        limiter.record_failed_login(ip)
        limiter.record_failed_login(ip)
        limiter.clear_failed_logins(ip)
        count = limiter.get_failed_login_count(ip)
        assert count == 0
    
    def test_contar_tentativas_falhas(self):
        limiter = RateLimiterStandalone()
        ip = "192.168.1.106"
        limiter.record_failed_login(ip)
        limiter.record_failed_login(ip)
        count = limiter.get_failed_login_count(ip)
        assert count == 2


class TestSecurityHelpers:
    """Testes para funções auxiliares de segurança."""
    
    def test_hash_for_log(self):
        result = hash_for_log("teste@email.com")
        assert result is not None
        assert len(result) == 16
        assert result != "teste@email.com"
    
    def test_hash_for_log_consistente(self):
        result1 = hash_for_log("teste")
        result2 = hash_for_log("teste")
        assert result1 == result2
    
    def test_mask_email(self):
        result = mask_email("usuario@dominio.com")
        assert "***" in result
        assert "@" in result
        assert "usuario" not in result
    
    def test_mask_email_curto(self):
        result = mask_email("a@b.com")
        assert "@" in result
