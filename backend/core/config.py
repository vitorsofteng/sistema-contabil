"""
Configuração Centralizada - Sprint 1
Carrega variáveis de ambiente com valores padrão seguros.
"""

import os
from typing import List
from functools import lru_cache


class Settings:
    """Configurações do sistema carregadas de variáveis de ambiente."""
    
    def __init__(self):
        # Ambiente
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Aplicação
        self.app_name = os.getenv("APP_NAME", "Sistema Contábil")
        self.app_version = os.getenv("APP_VERSION", "3.0.0")
        self.base_url = os.getenv("BASE_URL", "http://localhost")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost")
        self.api_url = os.getenv("API_URL", "http://localhost:8000")
        
        # JWT
        self.jwt_secret = os.getenv("JWT_SECRET", "DEVELOPMENT_SECRET_CHANGE_IN_PRODUCTION")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.jwt_refresh_token_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # Senhas
        self.bcrypt_rounds = int(os.getenv("BCRYPT_ROUNDS", "12"))
        self.password_min_length = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
        self.password_require_uppercase = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
        self.password_require_lowercase = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
        self.password_require_digit = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
        self.password_require_special = os.getenv("PASSWORD_REQUIRE_SPECIAL", "false").lower() == "true"
        
        # Rate Limiting - valores mais generosos para desenvolvimento
        self.rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "300"))
        self.rate_limit_login_per_minute = int(os.getenv("RATE_LIMIT_LOGIN_ATTEMPTS", "20"))
        self.rate_limit_login_attempts = int(os.getenv("RATE_LIMIT_LOGIN_ATTEMPTS", "20"))
        self.rate_limit_login_window = int(os.getenv("RATE_LIMIT_LOGIN_WINDOW_MINUTES", "5"))
        
        # CORS
        cors_str = os.getenv("CORS_ORIGINS", "http://localhost,http://localhost:3000,http://localhost:5173")
        self.cors_origins = [o.strip() for o in cors_str.split(",") if o.strip()]
        
        # Headers de Segurança
        self.security_headers_enabled = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
        self.hsts_enabled = os.getenv("HSTS_ENABLED", "true").lower() == "true"
        self.hsts_max_age = int(os.getenv("HSTS_MAX_AGE", "31536000"))
        
        # Banco de dados
        self.database_url = os.getenv("DATABASE_URL", "postgresql://contabil:contabil123@db:5432/contabil")
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    def validate_production(self) -> List[str]:
        """Valida configurações críticas para produção."""
        errors = []
        if self.is_production:
            if "DEVELOPMENT" in self.jwt_secret.upper() or "CHANGE" in self.jwt_secret.upper():
                errors.append("JWT_SECRET deve ser alterado em produção")
            if len(self.jwt_secret) < 32:
                errors.append("JWT_SECRET deve ter pelo menos 32 caracteres")
            if self.debug:
                errors.append("DEBUG deve ser false em produção")
            if "*" in str(self.cors_origins):
                errors.append("CORS_ORIGINS não pode conter '*' em produção")
        return errors


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
