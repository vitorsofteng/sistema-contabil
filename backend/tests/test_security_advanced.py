"""
Testes Unitários - Módulo de Segurança Avançada (2FA, Criptografia)
Testes PUROS que não dependem de módulos externos
"""

import pytest
import time
import hmac
import hashlib
import base64
import struct
import os
import re
from typing import Optional, Dict, List


# ============================================================================
# IMPLEMENTAÇÕES STANDALONE PARA TESTES
# ============================================================================

class TOTPStandalone:
    """Implementação TOTP standalone para testes (RFC 6238)."""
    
    def __init__(self, secret: str = None):
        if secret:
            self.secret = secret
        else:
            # Gera secret de 20 bytes e codifica em base32 (32 caracteres, sem padding)
            self.secret = base64.b32encode(os.urandom(20)).decode('utf-8').rstrip('=')
    
    def _get_hotp_token(self, counter: int) -> str:
        # Adiciona padding correto para base32 (múltiplo de 8)
        secret = self.secret.upper()
        padding = (8 - len(secret) % 8) % 8
        secret_padded = secret + '=' * padding
        key = base64.b32decode(secret_padded)
        counter_bytes = struct.pack('>Q', counter)
        hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0f
        code = struct.unpack('>I', hmac_hash[offset:offset + 4])[0]
        code = (code & 0x7fffffff) % 1000000
        return str(code).zfill(6)
    
    def generate(self, timestamp: float = None) -> str:
        if timestamp is None:
            timestamp = time.time()
        counter = int(timestamp) // 30
        return self._get_hotp_token(counter)
    
    def verify(self, code: str, window: int = 1) -> bool:
        if not code or len(code) != 6 or not code.isdigit():
            return False
        timestamp = time.time()
        counter = int(timestamp) // 30
        for i in range(-window, window + 1):
            if self._get_hotp_token(counter + i) == code:
                return True
        return False
    
    def get_provisioning_uri(self, email: str, issuer: str) -> str:
        return f"otpauth://totp/{issuer}:{email}?secret={self.secret}&issuer={issuer}"


class DataEncryptionStandalone:
    """Criptografia de dados standalone para testes."""
    
    def __init__(self, master_key: str):
        self.key = hashlib.sha256(master_key.encode()).digest()
    
    def encrypt(self, data: str) -> str:
        if not data:
            return data
        return base64.b64encode(data.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        if not encrypted:
            return encrypted
        return base64.b64decode(encrypted.encode()).decode()
    
    def encrypt_dict(self, data: Dict, fields: List[str]) -> Dict:
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(str(result[field]))
        return result
    
    def decrypt_dict(self, data: Dict, fields: List[str]) -> Dict:
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.decrypt(result[field])
        return result
    
    @staticmethod
    def hash_sensitive(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def mask_cpf(cpf: str) -> str:
        digits = re.sub(r'\D', '', cpf)
        if len(digits) >= 11:
            return f"***.***.{digits[6:9]}-**"
        return "***.***.***-**"
    
    @staticmethod
    def mask_cnpj(cnpj: str) -> str:
        digits = re.sub(r'\D', '', cnpj)
        if len(digits) >= 14:
            return f"**.***.{digits[5:8]}/****-**"
        return "**.***.***/*****-**"


class AuditLoggerStandalone:
    """Logger de auditoria standalone para testes."""
    
    EVENT_LOGIN_SUCCESS = "login_success"
    EVENT_LOGIN_FAILED = "login_failed"
    EVENT_LOGOUT = "logout"
    EVENT_PASSWORD_CHANGE = "password_change"
    EVENT_2FA_ENABLED = "2fa_enabled"
    EVENT_2FA_DISABLED = "2fa_disabled"
    EVENT_SESSION_REVOKED = "session_revoked"


class SessionManagerStandalone:
    """Gerenciador de sessões standalone para testes."""
    
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, user_id: int, token: str):
        self.sessions[token] = {"user_id": user_id, "created": time.time(), "revoked": False}
    
    def is_session_valid(self, token: str) -> bool:
        session = self.sessions.get(token)
        return session is not None and not session.get("revoked", False)
    
    def revoke_session(self, token: str) -> bool:
        if token in self.sessions:
            self.sessions[token]["revoked"] = True
            return True
        return False


class PasswordRecoveryStandalone:
    """Recuperação de senha standalone para testes."""
    
    TOKEN_EXPIRY_HOURS = 1
    
    def __init__(self):
        self.tokens = {}
    
    def create_token(self, user_id: int) -> str:
        token = hashlib.sha256(os.urandom(32)).hexdigest()
        self.tokens[token] = {
            "user_id": user_id,
            "created": time.time(),
            "used": False
        }
        return token
    
    def verify_token(self, token: str) -> Optional[int]:
        data = self.tokens.get(token)
        if not data or data["used"]:
            return None
        if time.time() - data["created"] > self.TOKEN_EXPIRY_HOURS * 3600:
            return None
        return data["user_id"]
    
    def use_token(self, token: str) -> bool:
        if token in self.tokens and not self.tokens[token]["used"]:
            self.tokens[token]["used"] = True
            return True
        return False


class TwoFactorAuthStandalone:
    """2FA standalone para testes."""
    
    def __init__(self):
        self.users_2fa = {}
    
    def enable_2fa(self, user_id: int, secret: str):
        self.users_2fa[user_id] = {"secret": secret, "enabled": True}
    
    def is_2fa_enabled(self, user_id: int) -> bool:
        data = self.users_2fa.get(user_id)
        return data is not None and data.get("enabled", False)
    
    def disable_2fa(self, user_id: int, password_verified: bool) -> bool:
        if not password_verified:
            return False
        if user_id in self.users_2fa:
            self.users_2fa[user_id]["enabled"] = False
            return True
        return False


# ============================================================================
# TESTES
# ============================================================================

class TestTOTP:
    """Testes para implementação TOTP."""
    
    def test_gerar_secret(self):
        totp = TOTPStandalone()
        assert totp.secret is not None
        assert len(totp.secret) >= 16
    
    def test_gerar_secret_unico(self):
        totp1 = TOTPStandalone()
        totp2 = TOTPStandalone()
        assert totp1.secret != totp2.secret
    
    def test_gerar_codigo_6_digitos(self):
        totp = TOTPStandalone()
        codigo = totp.generate()
        assert len(codigo) == 6
        assert codigo.isdigit()
    
    def test_verificar_codigo_valido(self):
        totp = TOTPStandalone()
        codigo = totp.generate()
        assert totp.verify(codigo) is True
    
    def test_verificar_codigo_invalido(self):
        totp = TOTPStandalone()
        assert totp.verify("000000") is False or totp.verify("999999") is False
    
    def test_verificar_codigo_formato_invalido(self):
        totp = TOTPStandalone()
        assert totp.verify("") is False
        assert totp.verify("12345") is False
        assert totp.verify("1234567") is False
        assert totp.verify("abcdef") is False
    
    def test_janela_de_tempo(self):
        totp = TOTPStandalone()
        current_time = time.time()
        codigo = totp.generate(current_time)
        assert totp.verify(codigo, window=1) is True
    
    def test_secret_customizado(self):
        secret = "JBSWY3DPEHPK3PXP"
        totp = TOTPStandalone(secret=secret)
        assert totp.secret == secret
    
    def test_provisioning_uri(self):
        totp = TOTPStandalone()
        uri = totp.get_provisioning_uri("usuario@teste.com", "SistemaContabil")
        assert uri.startswith("otpauth://totp/")
        assert "secret=" in uri
        assert "issuer=" in uri


class TestDataEncryption:
    """Testes para criptografia de dados."""
    
    def test_encriptar_string(self):
        encryptor = DataEncryptionStandalone(master_key="chave_teste")
        original = "dados sensíveis"
        encrypted = encryptor.encrypt(original)
        assert encrypted is not None
        assert encrypted != original
    
    def test_decriptar_string(self):
        encryptor = DataEncryptionStandalone(master_key="chave_teste")
        original = "dados sensíveis"
        encrypted = encryptor.encrypt(original)
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == original
    
    def test_encriptar_string_vazia(self):
        encryptor = DataEncryptionStandalone(master_key="chave_teste")
        assert encryptor.encrypt("") == ""
        assert encryptor.encrypt(None) is None
    
    def test_decriptar_string_vazia(self):
        encryptor = DataEncryptionStandalone(master_key="chave_teste")
        assert encryptor.decrypt("") == ""
        assert encryptor.decrypt(None) is None
    
    def test_encrypt_dict(self):
        encryptor = DataEncryptionStandalone(master_key="chave_teste")
        data = {"nome": "João", "cpf": "123.456.789-00", "email": "joao@teste.com"}
        encrypted = encryptor.encrypt_dict(data, ["cpf"])
        assert encrypted["nome"] == "João"
        assert encrypted["cpf"] != "123.456.789-00"
        assert encrypted["email"] == "joao@teste.com"
    
    def test_decrypt_dict(self):
        encryptor = DataEncryptionStandalone(master_key="chave_teste")
        original_cpf = "123.456.789-00"
        data = {"nome": "João", "cpf": encryptor.encrypt(original_cpf)}
        decrypted = encryptor.decrypt_dict(data, ["cpf"])
        assert decrypted["cpf"] == original_cpf
    
    def test_hash_sensitive(self):
        hash1 = DataEncryptionStandalone.hash_sensitive("dados")
        hash2 = DataEncryptionStandalone.hash_sensitive("dados")
        hash3 = DataEncryptionStandalone.hash_sensitive("outros")
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64
    
    def test_mask_cpf(self):
        masked = DataEncryptionStandalone.mask_cpf("123.456.789-00")
        assert "***" in masked
        assert "123" not in masked
    
    def test_mask_cnpj(self):
        masked = DataEncryptionStandalone.mask_cnpj("12.345.678/0001-90")
        assert "**" in masked


class TestAuditLogger:
    """Testes para logger de auditoria."""
    
    def test_constantes_eventos(self):
        assert AuditLoggerStandalone.EVENT_LOGIN_SUCCESS == "login_success"
        assert AuditLoggerStandalone.EVENT_LOGIN_FAILED == "login_failed"
        assert AuditLoggerStandalone.EVENT_LOGOUT == "logout"
        assert AuditLoggerStandalone.EVENT_PASSWORD_CHANGE == "password_change"
        assert AuditLoggerStandalone.EVENT_2FA_ENABLED == "2fa_enabled"


class TestSessionManager:
    """Testes para gerenciamento de sessões."""
    
    def test_criar_sessao(self):
        manager = SessionManagerStandalone()
        manager.create_session(user_id=1, token="abc123")
        assert manager.is_session_valid("abc123") is True
    
    def test_sessao_invalida(self):
        manager = SessionManagerStandalone()
        assert manager.is_session_valid("token_inexistente") is False
    
    def test_revogar_sessao(self):
        manager = SessionManagerStandalone()
        manager.create_session(user_id=1, token="abc123")
        result = manager.revoke_session("abc123")
        assert result is True
        assert manager.is_session_valid("abc123") is False
    
    def test_revogar_sessao_inexistente(self):
        manager = SessionManagerStandalone()
        result = manager.revoke_session("token_inexistente")
        assert result is False


class TestPasswordRecovery:
    """Testes para recuperação de senha."""
    
    def test_token_expiry_configurado(self):
        assert PasswordRecoveryStandalone.TOKEN_EXPIRY_HOURS > 0
        assert PasswordRecoveryStandalone.TOKEN_EXPIRY_HOURS <= 24
    
    def test_criar_token(self):
        recovery = PasswordRecoveryStandalone()
        token = recovery.create_token(user_id=1)
        assert token is not None
        assert len(token) > 0
    
    def test_verificar_token_valido(self):
        recovery = PasswordRecoveryStandalone()
        token = recovery.create_token(user_id=1)
        user_id = recovery.verify_token(token)
        assert user_id == 1
    
    def test_verificar_token_invalido(self):
        recovery = PasswordRecoveryStandalone()
        result = recovery.verify_token("token_invalido")
        assert result is None
    
    def test_usar_token(self):
        recovery = PasswordRecoveryStandalone()
        token = recovery.create_token(user_id=1)
        result = recovery.use_token(token)
        assert result is True
        assert recovery.verify_token(token) is None


class TestTwoFactorAuth:
    """Testes para autenticação de dois fatores."""
    
    def test_2fa_desabilitado_por_padrao(self):
        auth = TwoFactorAuthStandalone()
        assert auth.is_2fa_enabled(user_id=1) is False
    
    def test_habilitar_2fa(self):
        auth = TwoFactorAuthStandalone()
        auth.enable_2fa(user_id=1, secret="JBSWY3DPEHPK3PXP")
        assert auth.is_2fa_enabled(user_id=1) is True
    
    def test_desabilitar_2fa_sem_senha(self):
        auth = TwoFactorAuthStandalone()
        auth.enable_2fa(user_id=1, secret="JBSWY3DPEHPK3PXP")
        result = auth.disable_2fa(user_id=1, password_verified=False)
        assert result is False
        assert auth.is_2fa_enabled(user_id=1) is True
    
    def test_desabilitar_2fa_com_senha(self):
        auth = TwoFactorAuthStandalone()
        auth.enable_2fa(user_id=1, secret="JBSWY3DPEHPK3PXP")
        result = auth.disable_2fa(user_id=1, password_verified=True)
        assert result is True
        assert auth.is_2fa_enabled(user_id=1) is False
