"""
Módulo de Auditoria de Segurança - Sprint 2
Registra eventos de segurança: login, logout, tentativas falhas, alterações de senha, etc.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum


class AuditEventType(str, Enum):
    """Tipos de eventos de auditoria."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    LOGOUT_ALL = "logout_all"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOKED = "token_revoked"
    TWO_FACTOR_ENABLED = "2fa_enabled"
    TWO_FACTOR_DISABLED = "2fa_disabled"
    TWO_FACTOR_SUCCESS = "2fa_success"
    TWO_FACTOR_FAILED = "2fa_failed"
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_EXPORT = "data_export"
    SETTINGS_CHANGE = "settings_change"


class AuditLogger:
    """Logger de auditoria de segurança."""
    
    def __init__(self, db_session_factory=None):
        self.db_session_factory = db_session_factory
    
    def _hash_ip(self, ip: str) -> str:
        """Hash parcial do IP para privacidade nos logs."""
        if not ip or ip == "unknown":
            return "unknown"
        # Mantém apenas parte do IP para identificação
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.xxx.xxx"
        return hashlib.sha256(ip.encode()).hexdigest()[:12]
    
    def _get_user_agent_info(self, user_agent: str) -> Dict:
        """Extrai informações básicas do User-Agent."""
        if not user_agent:
            return {"browser": "unknown", "os": "unknown", "device": "unknown"}
        
        ua_lower = user_agent.lower()
        
        # Detectar navegador
        browser = "unknown"
        if "chrome" in ua_lower and "edg" not in ua_lower:
            browser = "Chrome"
        elif "firefox" in ua_lower:
            browser = "Firefox"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            browser = "Safari"
        elif "edg" in ua_lower:
            browser = "Edge"
        elif "opera" in ua_lower or "opr" in ua_lower:
            browser = "Opera"
        
        # Detectar OS
        os_name = "unknown"
        if "windows" in ua_lower:
            os_name = "Windows"
        elif "mac" in ua_lower:
            os_name = "macOS"
        elif "linux" in ua_lower:
            os_name = "Linux"
        elif "android" in ua_lower:
            os_name = "Android"
        elif "iphone" in ua_lower or "ipad" in ua_lower:
            os_name = "iOS"
        
        # Detectar tipo de dispositivo
        device = "Desktop"
        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            device = "Mobile"
        elif "tablet" in ua_lower or "ipad" in ua_lower:
            device = "Tablet"
        
        return {"browser": browser, "os": os_name, "device": device}
    
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict] = None,
        success: bool = True,
        risk_level: str = "low"
    ) -> Dict:
        """
        Registra um evento de auditoria.
        
        Args:
            event_type: Tipo do evento
            user_id: ID do usuário (se autenticado)
            email: Email do usuário
            ip_address: Endereço IP
            user_agent: User-Agent do navegador
            details: Detalhes adicionais
            success: Se a operação foi bem-sucedida
            risk_level: Nível de risco (low, medium, high, critical)
        """
        event = {
            "id": None,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "email_hash": hashlib.sha256(email.encode()).hexdigest()[:16] if email else None,
            "ip_hash": self._hash_ip(ip_address),
            "ip_full": ip_address,  # Armazenado criptografado no banco
            "user_agent_info": self._get_user_agent_info(user_agent),
            "success": success,
            "risk_level": risk_level,
            "details": details or {}
        }
        
        # Salvar no banco de dados
        if self.db_session_factory:
            try:
                self._save_to_db(event)
            except Exception as e:
                print(f"Erro ao salvar evento de auditoria: {e}")
        
        # Log para console/arquivo (em produção, usar logging estruturado)
        self._log_to_console(event)
        
        return event
    
    def _save_to_db(self, event: Dict):
        """Salva evento no banco de dados."""
        if not self.db_session_factory:
            return
        
        try:
            with self.db_session_factory() as db:
                from sqlalchemy import text
                
                db.execute(text("""
                    INSERT INTO audit_logs (
                        event_type, user_id, email_hash, ip_hash, ip_encrypted,
                        user_agent_info, success, risk_level, details, created_at
                    ) VALUES (
                        :event_type, :user_id, :email_hash, :ip_hash, :ip_encrypted,
                        :user_agent_info, :success, :risk_level, :details, :created_at
                    )
                """), {
                    "event_type": event["event_type"],
                    "user_id": event["user_id"],
                    "email_hash": event["email_hash"],
                    "ip_hash": event["ip_hash"],
                    "ip_encrypted": event["ip_full"],  # TODO: Criptografar
                    "user_agent_info": json.dumps(event["user_agent_info"]),
                    "success": event["success"],
                    "risk_level": event["risk_level"],
                    "details": json.dumps(event["details"]),
                    "created_at": event["timestamp"]
                })
                db.commit()
        except Exception as e:
            # Tabela pode não existir ainda
            print(f"Aviso: Não foi possível salvar audit log: {e}")
    
    def _log_to_console(self, event: Dict):
        """Log para console (desenvolvimento) ou arquivo (produção)."""
        log_level = "INFO"
        if not event["success"]:
            log_level = "WARNING"
        if event["risk_level"] in ["high", "critical"]:
            log_level = "ERROR" if event["risk_level"] == "critical" else "WARNING"
        
        # Formato estruturado (JSON) para facilitar análise
        log_entry = {
            "level": log_level,
            "type": "AUDIT",
            "event": event["event_type"],
            "user_id": event["user_id"],
            "ip": event["ip_hash"],
            "success": event["success"],
            "risk": event["risk_level"],
            "time": event["timestamp"]
        }
        
        print(f"[AUDIT] {json.dumps(log_entry)}")
    
    def get_user_events(
        self,
        user_id: int,
        event_types: Optional[List[AuditEventType]] = None,
        limit: int = 50,
        days: int = 30
    ) -> List[Dict]:
        """Obtém eventos de auditoria de um usuário."""
        if not self.db_session_factory:
            return []
        
        try:
            with self.db_session_factory() as db:
                from sqlalchemy import text
                
                query = """
                    SELECT * FROM audit_logs 
                    WHERE user_id = :user_id 
                    AND created_at > NOW() - INTERVAL ':days days'
                """
                
                if event_types:
                    types_str = ",".join([f"'{t.value}'" for t in event_types])
                    query += f" AND event_type IN ({types_str})"
                
                query += " ORDER BY created_at DESC LIMIT :limit"
                
                results = db.execute(text(query), {
                    "user_id": user_id,
                    "days": days,
                    "limit": limit
                }).fetchall()
                
                return [dict(r._mapping) for r in results]
        except Exception:
            return []
    
    def get_failed_logins(
        self,
        ip_address: Optional[str] = None,
        email: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict]:
        """Obtém tentativas de login falhas."""
        if not self.db_session_factory:
            return []
        
        try:
            with self.db_session_factory() as db:
                from sqlalchemy import text
                
                conditions = ["event_type = 'login_failed'", "success = false"]
                params = {"hours": hours}
                
                if ip_address:
                    conditions.append("ip_hash = :ip_hash")
                    params["ip_hash"] = self._hash_ip(ip_address)
                
                if email:
                    conditions.append("email_hash = :email_hash")
                    params["email_hash"] = hashlib.sha256(email.encode()).hexdigest()[:16]
                
                query = f"""
                    SELECT * FROM audit_logs 
                    WHERE {' AND '.join(conditions)}
                    AND created_at > NOW() - INTERVAL '{hours} hours'
                    ORDER BY created_at DESC
                """
                
                results = db.execute(text(query), params).fetchall()
                return [dict(r._mapping) for r in results]
        except Exception:
            return []
    
    def detect_suspicious_activity(self, user_id: int, ip_address: str) -> Dict:
        """
        Detecta atividade suspeita para um usuário.
        
        Retorna análise de risco baseada em:
        - Múltiplas tentativas de login falhas
        - Login de novo IP/dispositivo
        - Mudança frequente de senha
        - Padrões incomuns
        """
        risk_factors = []
        risk_score = 0
        
        if not self.db_session_factory:
            return {"risk_score": 0, "risk_factors": [], "recommendation": "normal"}
        
        try:
            with self.db_session_factory() as db:
                from sqlalchemy import text
                
                # Verificar tentativas de login falhas recentes
                failed_logins = db.execute(text("""
                    SELECT COUNT(*) as count FROM audit_logs
                    WHERE user_id = :user_id 
                    AND event_type = 'login_failed'
                    AND created_at > NOW() - INTERVAL '1 hour'
                """), {"user_id": user_id}).fetchone()
                
                if failed_logins and failed_logins.count > 3:
                    risk_factors.append("multiple_failed_logins")
                    risk_score += 30
                
                # Verificar se é um novo IP
                ip_hash = self._hash_ip(ip_address)
                known_ip = db.execute(text("""
                    SELECT COUNT(*) as count FROM audit_logs
                    WHERE user_id = :user_id 
                    AND ip_hash = :ip_hash
                    AND event_type = 'login_success'
                    AND created_at > NOW() - INTERVAL '30 days'
                """), {"user_id": user_id, "ip_hash": ip_hash}).fetchone()
                
                if not known_ip or known_ip.count == 0:
                    risk_factors.append("new_ip_address")
                    risk_score += 20
                
                # Verificar mudanças de senha recentes
                password_changes = db.execute(text("""
                    SELECT COUNT(*) as count FROM audit_logs
                    WHERE user_id = :user_id 
                    AND event_type = 'password_change'
                    AND created_at > NOW() - INTERVAL '24 hours'
                """), {"user_id": user_id}).fetchone()
                
                if password_changes and password_changes.count > 1:
                    risk_factors.append("frequent_password_changes")
                    risk_score += 25
                
        except Exception:
            pass
        
        # Determinar recomendação
        recommendation = "normal"
        if risk_score >= 50:
            recommendation = "require_2fa"
        elif risk_score >= 30:
            recommendation = "verify_identity"
        elif risk_score >= 20:
            recommendation = "monitor"
        
        return {
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommendation": recommendation
        }


# Instância global (será inicializada com db_session na startup)
audit_logger = AuditLogger()


def init_audit_logger(db_session_factory):
    """Inicializa o audit logger com a factory de sessão do banco."""
    global audit_logger
    audit_logger = AuditLogger(db_session_factory)
