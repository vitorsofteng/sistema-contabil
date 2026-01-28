"""
Módulo de Auditoria e Segurança Avançada - Sprint 2
Implementa: Auditoria de login, 2FA (TOTP), Criptografia de dados sensíveis
"""

import os
import base64
import hashlib
import hmac
import struct
import time
import secrets
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# ============================================================================
# AUDITORIA DE LOGIN (2.1)
# ============================================================================

class AuditLogger:
    """Logger de auditoria para eventos de segurança."""
    
    # Tipos de eventos
    EVENT_LOGIN_SUCCESS = "login_success"
    EVENT_LOGIN_FAILED = "login_failed"
    EVENT_LOGIN_BLOCKED = "login_blocked"
    EVENT_LOGOUT = "logout"
    EVENT_LOGOUT_ALL = "logout_all"
    EVENT_PASSWORD_CHANGE = "password_change"
    EVENT_PASSWORD_RESET_REQUEST = "password_reset_request"
    EVENT_PASSWORD_RESET_COMPLETE = "password_reset_complete"
    EVENT_2FA_ENABLED = "2fa_enabled"
    EVENT_2FA_DISABLED = "2fa_disabled"
    EVENT_2FA_VERIFIED = "2fa_verified"
    EVENT_2FA_FAILED = "2fa_failed"
    EVENT_SESSION_REVOKED = "session_revoked"
    EVENT_ACCOUNT_LOCKED = "account_locked"
    EVENT_ACCOUNT_UNLOCKED = "account_unlocked"
    EVENT_SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    @staticmethod
    def log(
        db_session,
        user_id: Optional[int],
        event_type: str,
        ip_address: str,
        user_agent: str = None,
        details: Dict = None,
        success: bool = True
    ):
        """Registra evento de auditoria no banco de dados."""
        from sqlalchemy import text
        
        try:
            db_session.execute(text("""
                INSERT INTO audit_logs (
                    user_id, event_type, ip_address, user_agent, 
                    details, success, created_at
                ) VALUES (
                    :user_id, :event_type, :ip_address, :user_agent,
                    :details, :success, :created_at
                )
            """), {
                "user_id": user_id,
                "event_type": event_type,
                "ip_address": ip_address,
                "user_agent": user_agent or "",
                "details": str(details) if details else None,
                "success": success,
                "created_at": datetime.now().isoformat()
            })
            db_session.commit()
        except Exception as e:
            print(f"Erro ao registrar auditoria: {e}")
    
    @staticmethod
    def get_user_events(
        db_session,
        user_id: int,
        event_type: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Retorna eventos de auditoria de um usuário."""
        from sqlalchemy import text
        
        try:
            if event_type:
                result = db_session.execute(text("""
                    SELECT * FROM audit_logs 
                    WHERE user_id = :user_id AND event_type = :event_type
                    ORDER BY created_at DESC
                    LIMIT :limit
                """), {"user_id": user_id, "event_type": event_type, "limit": limit})
            else:
                result = db_session.execute(text("""
                    SELECT * FROM audit_logs 
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """), {"user_id": user_id, "limit": limit})
            
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception:
            return []
    
    @staticmethod
    def get_failed_logins(
        db_session,
        ip_address: str,
        minutes: int = 15
    ) -> int:
        """Conta tentativas de login falhas de um IP."""
        from sqlalchemy import text
        
        try:
            cutoff = (datetime.now() - timedelta(minutes=minutes)).isoformat()
            result = db_session.execute(text("""
                SELECT COUNT(*) as count FROM audit_logs 
                WHERE ip_address = :ip 
                AND event_type = :event_type
                AND created_at > :cutoff
                AND success = false
            """), {
                "ip": ip_address,
                "event_type": AuditLogger.EVENT_LOGIN_FAILED,
                "cutoff": cutoff
            })
            row = result.fetchone()
            return row.count if row else 0
        except Exception:
            return 0
    
    @staticmethod
    def detect_suspicious_activity(
        db_session,
        user_id: int,
        current_ip: str
    ) -> Dict:
        """Detecta atividade suspeita baseada em padrões."""
        from sqlalchemy import text
        
        alerts = []
        
        try:
            # Verificar logins de IPs diferentes nas últimas 24h
            result = db_session.execute(text("""
                SELECT DISTINCT ip_address FROM audit_logs
                WHERE user_id = :user_id
                AND event_type = :event_type
                AND success = true
                AND created_at > :cutoff
            """), {
                "user_id": user_id,
                "event_type": AuditLogger.EVENT_LOGIN_SUCCESS,
                "cutoff": (datetime.now() - timedelta(hours=24)).isoformat()
            })
            
            unique_ips = [row.ip_address for row in result.fetchall()]
            
            if len(unique_ips) > 3:
                alerts.append({
                    "type": "multiple_ips",
                    "message": f"Login de {len(unique_ips)} IPs diferentes nas últimas 24h",
                    "severity": "medium"
                })
            
            # Verificar se é um IP novo
            result = db_session.execute(text("""
                SELECT COUNT(*) as count FROM audit_logs
                WHERE user_id = :user_id
                AND ip_address = :ip
                AND event_type = :event_type
                AND success = true
            """), {
                "user_id": user_id,
                "ip": current_ip,
                "event_type": AuditLogger.EVENT_LOGIN_SUCCESS
            })
            
            row = result.fetchone()
            if row and row.count == 0:
                alerts.append({
                    "type": "new_ip",
                    "message": f"Primeiro login deste IP: {current_ip}",
                    "severity": "low"
                })
            
            # Verificar tentativas falhas recentes
            failed_count = AuditLogger.get_failed_logins(db_session, current_ip, 60)
            if failed_count >= 3:
                alerts.append({
                    "type": "failed_attempts",
                    "message": f"{failed_count} tentativas falhas na última hora",
                    "severity": "high"
                })
            
        except Exception as e:
            print(f"Erro ao detectar atividade suspeita: {e}")
        
        return {
            "suspicious": len(alerts) > 0,
            "alerts": alerts
        }


# ============================================================================
# TWO-FACTOR AUTHENTICATION - TOTP (2.7)
# ============================================================================

class TOTP:
    """Implementação de Time-based One-Time Password (RFC 6238)."""
    
    def __init__(self, secret: str = None, digits: int = 6, interval: int = 30):
        """
        Inicializa TOTP.
        
        Args:
            secret: Chave secreta em base32. Se None, gera uma nova.
            digits: Número de dígitos do código (padrão: 6)
            interval: Intervalo em segundos (padrão: 30)
        """
        self.secret = secret or self.generate_secret()
        self.digits = digits
        self.interval = interval
    
    @staticmethod
    def generate_secret(length: int = 32) -> str:
        """Gera uma chave secreta aleatória em base32."""
        random_bytes = secrets.token_bytes(length)
        return base64.b32encode(random_bytes).decode('utf-8').rstrip('=')
    
    def _get_counter(self, timestamp: float = None) -> int:
        """Calcula o contador baseado no timestamp."""
        if timestamp is None:
            timestamp = time.time()
        return int(timestamp // self.interval)
    
    def _hotp(self, counter: int) -> str:
        """Gera HOTP para um contador específico."""
        # Decodificar secret de base32
        secret_bytes = base64.b32decode(self.secret + '=' * (8 - len(self.secret) % 8))
        
        # Converter contador para bytes (8 bytes, big-endian)
        counter_bytes = struct.pack('>Q', counter)
        
        # Calcular HMAC-SHA1
        hmac_hash = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
        
        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0F
        binary = struct.unpack('>I', hmac_hash[offset:offset + 4])[0] & 0x7FFFFFFF
        
        # Gerar código com N dígitos
        otp = binary % (10 ** self.digits)
        return str(otp).zfill(self.digits)
    
    def generate(self, timestamp: float = None) -> str:
        """Gera código TOTP atual."""
        counter = self._get_counter(timestamp)
        return self._hotp(counter)
    
    def verify(self, code: str, window: int = 1) -> bool:
        """
        Verifica código TOTP.
        
        Args:
            code: Código a verificar
            window: Janela de tolerância (padrão: 1 = ±30 segundos)
        
        Returns:
            True se código válido
        """
        if not code or len(code) != self.digits:
            return False
        
        current_counter = self._get_counter()
        
        # Verificar janela de tempo
        for offset in range(-window, window + 1):
            if self._hotp(current_counter + offset) == code:
                return True
        
        return False
    
    def get_provisioning_uri(self, account_name: str, issuer: str = "Sistema Contabil") -> str:
        """
        Gera URI para configurar app autenticador.
        
        Formato: otpauth://totp/ISSUER:ACCOUNT?secret=SECRET&issuer=ISSUER
        """
        from urllib.parse import quote
        
        label = f"{issuer}:{account_name}"
        params = f"secret={self.secret}&issuer={quote(issuer)}&algorithm=SHA1&digits={self.digits}&period={self.interval}"
        
        return f"otpauth://totp/{quote(label)}?{params}"


class TwoFactorAuth:
    """Gerenciador de autenticação de dois fatores."""
    
    @staticmethod
    def setup_2fa(db_session, user_id: int, email: str) -> Dict:
        """
        Configura 2FA para um usuário.
        Retorna secret e URI para QR code.
        """
        from sqlalchemy import text
        
        # Gerar novo secret
        totp = TOTP()
        secret = totp.secret
        
        # Gerar códigos de backup
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        backup_codes_hash = hashlib.sha256(
            ','.join(backup_codes).encode()
        ).hexdigest()
        
        # Salvar secret (ainda não ativado)
        try:
            db_session.execute(text("""
                INSERT INTO user_2fa (user_id, secret, backup_codes_hash, is_enabled, created_at)
                VALUES (:user_id, :secret, :backup_hash, false, :created_at)
                ON CONFLICT (user_id) DO UPDATE SET
                    secret = :secret,
                    backup_codes_hash = :backup_hash,
                    is_enabled = false,
                    updated_at = :created_at
            """), {
                "user_id": user_id,
                "secret": secret,
                "backup_hash": backup_codes_hash,
                "created_at": datetime.now().isoformat()
            })
            db_session.commit()
        except Exception as e:
            print(f"Erro ao configurar 2FA: {e}")
            raise
        
        return {
            "secret": secret,
            "provisioning_uri": totp.get_provisioning_uri(email),
            "backup_codes": backup_codes
        }
    
    @staticmethod
    def enable_2fa(db_session, user_id: int, code: str) -> bool:
        """
        Ativa 2FA após verificar código.
        Deve ser chamado após setup_2fa com código do app autenticador.
        """
        from sqlalchemy import text
        
        try:
            # Obter secret
            result = db_session.execute(text("""
                SELECT secret FROM user_2fa WHERE user_id = :user_id
            """), {"user_id": user_id})
            
            row = result.fetchone()
            if not row:
                return False
            
            # Verificar código
            totp = TOTP(secret=row.secret)
            if not totp.verify(code):
                return False
            
            # Ativar 2FA
            db_session.execute(text("""
                UPDATE user_2fa SET is_enabled = true, updated_at = :updated_at
                WHERE user_id = :user_id
            """), {"user_id": user_id, "updated_at": datetime.now().isoformat()})
            db_session.commit()
            
            return True
        except Exception as e:
            print(f"Erro ao ativar 2FA: {e}")
            return False
    
    @staticmethod
    def disable_2fa(db_session, user_id: int, password_verified: bool = False) -> bool:
        """Desativa 2FA (requer verificação de senha)."""
        from sqlalchemy import text
        
        if not password_verified:
            return False
        
        try:
            db_session.execute(text("""
                UPDATE user_2fa SET is_enabled = false, updated_at = :updated_at
                WHERE user_id = :user_id
            """), {"user_id": user_id, "updated_at": datetime.now().isoformat()})
            db_session.commit()
            return True
        except Exception:
            return False
    
    @staticmethod
    def verify_2fa(db_session, user_id: int, code: str) -> bool:
        """Verifica código 2FA."""
        from sqlalchemy import text
        
        try:
            result = db_session.execute(text("""
                SELECT secret, is_enabled FROM user_2fa 
                WHERE user_id = :user_id AND is_enabled = true
            """), {"user_id": user_id})
            
            row = result.fetchone()
            if not row:
                return False
            
            totp = TOTP(secret=row.secret)
            return totp.verify(code)
        except Exception:
            return False
    
    @staticmethod
    def is_2fa_enabled(db_session, user_id: int) -> bool:
        """Verifica se usuário tem 2FA ativado."""
        from sqlalchemy import text
        
        try:
            result = db_session.execute(text("""
                SELECT is_enabled FROM user_2fa 
                WHERE user_id = :user_id
            """), {"user_id": user_id})
            
            row = result.fetchone()
            return row.is_enabled if row else False
        except Exception:
            return False
    
    @staticmethod
    def verify_backup_code(db_session, user_id: int, code: str) -> bool:
        """
        Verifica código de backup.
        Cada código só pode ser usado uma vez.
        """
        from sqlalchemy import text
        
        try:
            # Verificar se código já foi usado
            result = db_session.execute(text("""
                SELECT id FROM used_backup_codes 
                WHERE user_id = :user_id AND code_hash = :code_hash
            """), {
                "user_id": user_id,
                "code_hash": hashlib.sha256(code.upper().encode()).hexdigest()
            })
            
            if result.fetchone():
                return False  # Código já usado
            
            # Marcar código como usado
            db_session.execute(text("""
                INSERT INTO used_backup_codes (user_id, code_hash, used_at)
                VALUES (:user_id, :code_hash, :used_at)
            """), {
                "user_id": user_id,
                "code_hash": hashlib.sha256(code.upper().encode()).hexdigest(),
                "used_at": datetime.now().isoformat()
            })
            db_session.commit()
            
            return True
        except Exception:
            return False


# ============================================================================
# CRIPTOGRAFIA DE DADOS SENSÍVEIS (2.8)
# ============================================================================

class DataEncryption:
    """Criptografia de dados sensíveis em repouso."""
    
    def __init__(self, master_key: str = None):
        """
        Inicializa encriptador.
        
        Args:
            master_key: Chave mestra. Se None, usa variável de ambiente.
        """
        self.master_key = master_key or os.getenv(
            "ENCRYPTION_KEY",
            "DEVELOPMENT_KEY_CHANGE_IN_PRODUCTION_32CHARS"
        )
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """Obtém instância Fernet com chave derivada."""
        if self._fernet is None:
            # Derivar chave usando PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'contabil_system_salt_v1',  # Salt fixo (em produção, usar salt por registro)
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, data: str) -> str:
        """
        Encripta string.
        
        Returns:
            String encriptada em base64
        """
        if not data:
            return data
        
        fernet = self._get_fernet()
        encrypted = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decripta string.
        
        Returns:
            String original
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            fernet = self._get_fernet()
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            print(f"Erro ao decriptar: {e}")
            return None
    
    def encrypt_dict(self, data: Dict, fields: List[str]) -> Dict:
        """
        Encripta campos específicos de um dicionário.
        
        Args:
            data: Dicionário com dados
            fields: Lista de campos a encriptar
        
        Returns:
            Dicionário com campos encriptados
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(str(result[field]))
        return result
    
    def decrypt_dict(self, data: Dict, fields: List[str]) -> Dict:
        """
        Decripta campos específicos de um dicionário.
        
        Args:
            data: Dicionário com dados encriptados
            fields: Lista de campos a decriptar
        
        Returns:
            Dicionário com campos decriptados
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                decrypted = self.decrypt(str(result[field]))
                if decrypted is not None:
                    result[field] = decrypted
        return result
    
    @staticmethod
    def hash_sensitive(data: str) -> str:
        """
        Gera hash de dado sensível (one-way).
        Útil para comparação sem decriptação.
        """
        if not data:
            return None
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def mask_cpf(cpf: str) -> str:
        """Mascara CPF para exibição."""
        if not cpf or len(cpf) < 11:
            return "***.***.***-**"
        clean = ''.join(filter(str.isdigit, cpf))
        return f"***.{clean[3:6]}.***-{clean[9:11]}"
    
    @staticmethod
    def mask_cnpj(cnpj: str) -> str:
        """Mascara CNPJ para exibição."""
        if not cnpj or len(cnpj) < 14:
            return "**.***.***/****..**"
        clean = ''.join(filter(str.isdigit, cnpj))
        return f"**.{clean[2:5]}.{clean[5:8]}/****.{clean[12:14]}"


# ============================================================================
# GERENCIAMENTO DE SESSÕES AVANÇADO (2.3, 2.4)
# ============================================================================

class SessionManager:
    """Gerenciamento avançado de sessões."""
    
    @staticmethod
    def create_session(
        db_session,
        user_id: int,
        token: str,
        refresh_token: str,
        ip_address: str,
        user_agent: str = None,
        expires_at: datetime = None
    ) -> int:
        """Cria nova sessão no banco."""
        from sqlalchemy import text
        
        if expires_at is None:
            expires_at = datetime.now() + timedelta(days=7)
        
        try:
            result = db_session.execute(text("""
                INSERT INTO user_sessions (
                    user_id, token_hash, refresh_token_hash, ip_address, 
                    user_agent, expires_at, created_at, last_activity
                ) VALUES (
                    :user_id, :token_hash, :refresh_hash, :ip,
                    :user_agent, :expires_at, :created_at, :created_at
                )
                RETURNING id
            """), {
                "user_id": user_id,
                "token_hash": hashlib.sha256(token.encode()).hexdigest(),
                "refresh_hash": hashlib.sha256(refresh_token.encode()).hexdigest(),
                "ip": ip_address,
                "user_agent": user_agent or "",
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now().isoformat()
            })
            db_session.commit()
            row = result.fetchone()
            return row.id if row else None
        except Exception as e:
            print(f"Erro ao criar sessão: {e}")
            return None
    
    @staticmethod
    def get_active_sessions(db_session, user_id: int) -> List[Dict]:
        """Lista sessões ativas de um usuário."""
        from sqlalchemy import text
        
        try:
            result = db_session.execute(text("""
                SELECT id, ip_address, user_agent, created_at, last_activity
                FROM user_sessions
                WHERE user_id = :user_id 
                AND expires_at > :now
                AND revoked = false
                ORDER BY last_activity DESC
            """), {
                "user_id": user_id,
                "now": datetime.now().isoformat()
            })
            
            sessions = []
            for row in result.fetchall():
                sessions.append({
                    "id": row.id,
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent,
                    "created_at": row.created_at,
                    "last_activity": row.last_activity
                })
            return sessions
        except Exception:
            return []
    
    @staticmethod
    def revoke_session(db_session, session_id: int, user_id: int) -> bool:
        """Revoga uma sessão específica."""
        from sqlalchemy import text
        
        try:
            result = db_session.execute(text("""
                UPDATE user_sessions 
                SET revoked = true, revoked_at = :revoked_at
                WHERE id = :session_id AND user_id = :user_id
            """), {
                "session_id": session_id,
                "user_id": user_id,
                "revoked_at": datetime.now().isoformat()
            })
            db_session.commit()
            return result.rowcount > 0
        except Exception:
            return False
    
    @staticmethod
    def revoke_all_sessions(db_session, user_id: int, except_current: str = None) -> int:
        """Revoga todas as sessões de um usuário."""
        from sqlalchemy import text
        
        try:
            if except_current:
                current_hash = hashlib.sha256(except_current.encode()).hexdigest()
                result = db_session.execute(text("""
                    UPDATE user_sessions 
                    SET revoked = true, revoked_at = :revoked_at
                    WHERE user_id = :user_id 
                    AND revoked = false
                    AND token_hash != :current_hash
                """), {
                    "user_id": user_id,
                    "revoked_at": datetime.now().isoformat(),
                    "current_hash": current_hash
                })
            else:
                result = db_session.execute(text("""
                    UPDATE user_sessions 
                    SET revoked = true, revoked_at = :revoked_at
                    WHERE user_id = :user_id AND revoked = false
                """), {
                    "user_id": user_id,
                    "revoked_at": datetime.now().isoformat()
                })
            db_session.commit()
            return result.rowcount
        except Exception:
            return 0
    
    @staticmethod
    def update_activity(db_session, token: str):
        """Atualiza última atividade da sessão."""
        from sqlalchemy import text
        
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            db_session.execute(text("""
                UPDATE user_sessions 
                SET last_activity = :now
                WHERE token_hash = :token_hash AND revoked = false
            """), {
                "token_hash": token_hash,
                "now": datetime.now().isoformat()
            })
            db_session.commit()
        except Exception:
            pass
    
    @staticmethod
    def is_session_valid(db_session, token: str) -> bool:
        """Verifica se sessão está válida."""
        from sqlalchemy import text
        
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            result = db_session.execute(text("""
                SELECT id FROM user_sessions
                WHERE token_hash = :token_hash
                AND revoked = false
                AND expires_at > :now
            """), {
                "token_hash": token_hash,
                "now": datetime.now().isoformat()
            })
            return result.fetchone() is not None
        except Exception:
            return False
    
    @staticmethod
    def cleanup_expired_sessions(db_session) -> int:
        """Remove sessões expiradas."""
        from sqlalchemy import text
        
        try:
            result = db_session.execute(text("""
                DELETE FROM user_sessions 
                WHERE expires_at < :now OR revoked = true
            """), {"now": (datetime.now() - timedelta(days=30)).isoformat()})
            db_session.commit()
            return result.rowcount
        except Exception:
            return 0


# ============================================================================
# RECUPERAÇÃO DE SENHA SEGURA (2.5)
# ============================================================================

class PasswordRecovery:
    """Gerenciamento de recuperação de senha."""
    
    TOKEN_EXPIRY_HOURS = 1
    
    @staticmethod
    def create_reset_token(db_session, user_id: int, email: str) -> str:
        """Cria token de reset de senha."""
        from sqlalchemy import text
        
        # Gerar token único
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(hours=PasswordRecovery.TOKEN_EXPIRY_HOURS)
        
        try:
            # Invalidar tokens anteriores
            db_session.execute(text("""
                UPDATE password_reset_tokens 
                SET used = true 
                WHERE user_id = :user_id AND used = false
            """), {"user_id": user_id})
            
            # Criar novo token
            db_session.execute(text("""
                INSERT INTO password_reset_tokens (
                    user_id, token_hash, expires_at, created_at
                ) VALUES (
                    :user_id, :token_hash, :expires_at, :created_at
                )
            """), {
                "user_id": user_id,
                "token_hash": token_hash,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now().isoformat()
            })
            db_session.commit()
            
            return token
        except Exception as e:
            print(f"Erro ao criar token de reset: {e}")
            return None
    
    @staticmethod
    def verify_reset_token(db_session, token: str) -> Optional[int]:
        """
        Verifica token de reset.
        Retorna user_id se válido, None caso contrário.
        """
        from sqlalchemy import text
        
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            result = db_session.execute(text("""
                SELECT user_id FROM password_reset_tokens
                WHERE token_hash = :token_hash
                AND used = false
                AND expires_at > :now
            """), {
                "token_hash": token_hash,
                "now": datetime.now().isoformat()
            })
            
            row = result.fetchone()
            return row.user_id if row else None
        except Exception:
            return None
    
    @staticmethod
    def use_reset_token(db_session, token: str) -> bool:
        """Marca token como usado."""
        from sqlalchemy import text
        
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            result = db_session.execute(text("""
                UPDATE password_reset_tokens 
                SET used = true, used_at = :used_at
                WHERE token_hash = :token_hash AND used = false
            """), {
                "token_hash": token_hash,
                "used_at": datetime.now().isoformat()
            })
            db_session.commit()
            return result.rowcount > 0
        except Exception:
            return False


# Instâncias globais
audit_logger = AuditLogger()
data_encryption = DataEncryption()
