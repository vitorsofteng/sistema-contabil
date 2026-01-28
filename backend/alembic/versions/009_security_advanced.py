"""
Migration 009 - Segurança Avançada (Sprint 2)
Tabelas: audit_logs, user_2fa, user_sessions, password_reset_tokens
"""

from alembic import op
import sqlalchemy as sa

revision = '009_security_advanced'
down_revision = '008_tabelas_auxiliares'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================================================
    # TABELA DE AUDITORIA (2.1)
    # ========================================================================
    op.execute('''
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
    ''')
    
    # Índices para consultas frequentes
    op.execute('CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_audit_ip ON audit_logs(ip_address)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at)')
    
    # ========================================================================
    # TABELA DE 2FA (2.7)
    # ========================================================================
    op.execute('''
        CREATE TABLE IF NOT EXISTS user_2fa (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES contadores(id) ON DELETE CASCADE,
            secret VARCHAR(64) NOT NULL,
            backup_codes_hash VARCHAR(64),
            is_enabled BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP
        )
    ''')
    
    # Tabela de códigos de backup usados
    op.execute('''
        CREATE TABLE IF NOT EXISTS used_backup_codes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES contadores(id) ON DELETE CASCADE,
            code_hash VARCHAR(64) NOT NULL,
            used_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, code_hash)
        )
    ''')
    
    # ========================================================================
    # TABELA DE SESSÕES (2.3, 2.4)
    # ========================================================================
    op.execute('''
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
    ''')
    
    op.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(token_hash)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at)')
    
    # ========================================================================
    # TABELA DE TOKENS DE RESET DE SENHA (2.5)
    # ========================================================================
    op.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES contadores(id) ON DELETE CASCADE,
            token_hash VARCHAR(64) NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT false,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    op.execute('CREATE INDEX IF NOT EXISTS idx_reset_token ON password_reset_tokens(token_hash)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_reset_user ON password_reset_tokens(user_id)')
    
    # ========================================================================
    # TABELA DE BLOQUEIO DE CONTA (2.2)
    # ========================================================================
    op.execute('''
        CREATE TABLE IF NOT EXISTS account_lockouts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES contadores(id) ON DELETE CASCADE,
            ip_address VARCHAR(45),
            failed_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP,
            reason VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    op.execute('CREATE INDEX IF NOT EXISTS idx_lockout_user ON account_lockouts(user_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_lockout_ip ON account_lockouts(ip_address)')
    
    # ========================================================================
    # ADICIONAR CAMPO 2FA NA TABELA DE CONTADORES
    # ========================================================================
    op.execute('''
        ALTER TABLE contadores 
        ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT false
    ''')
    
    op.execute('''
        ALTER TABLE contadores 
        ADD COLUMN IF NOT EXISTS account_locked BOOLEAN DEFAULT false
    ''')
    
    op.execute('''
        ALTER TABLE contadores 
        ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP
    ''')
    
    print("✅ Migration 009 (Segurança Avançada) aplicada com sucesso")


def downgrade():
    op.execute('DROP TABLE IF EXISTS account_lockouts CASCADE')
    op.execute('DROP TABLE IF EXISTS password_reset_tokens CASCADE')
    op.execute('DROP TABLE IF EXISTS user_sessions CASCADE')
    op.execute('DROP TABLE IF EXISTS used_backup_codes CASCADE')
    op.execute('DROP TABLE IF EXISTS user_2fa CASCADE')
    op.execute('DROP TABLE IF EXISTS audit_logs CASCADE')
    
    op.execute('ALTER TABLE contadores DROP COLUMN IF EXISTS two_factor_enabled')
    op.execute('ALTER TABLE contadores DROP COLUMN IF EXISTS account_locked')
    op.execute('ALTER TABLE contadores DROP COLUMN IF EXISTS locked_until')
