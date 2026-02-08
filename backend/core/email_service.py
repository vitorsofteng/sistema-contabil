"""
Serviço de Email usando Resend
Para recuperação de senha, validação de cadastro e notificações
"""

import os
import secrets
from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend não instalado. Emails serão apenas logados.")


class EmailService:
    """Serviço de envio de emails via Resend"""
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("EMAIL_FROM", "Kontabil <onboarding@resend.dev>")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost")
        self.is_production = os.getenv("ENVIRONMENT", "development") == "production"
        
        if RESEND_AVAILABLE and self.api_key:
            resend.api_key = self.api_key
            self.enabled = True
            logger.info(f"✅ Email service habilitado via Resend (from: {self.from_email})")
        else:
            self.enabled = False
            if not self.api_key:
                logger.warning("⚠️ RESEND_API_KEY não configurada. Emails serão simulados.")
    
    def generate_token(self, length: int = 64) -> str:
        """Gera token seguro para verificação/reset"""
        return secrets.token_urlsafe(length)
    
    # =========================================================================
    # VERIFICAÇÃO DE EMAIL (CADASTRO)
    # =========================================================================
    
    def send_email_verification(self, to_email: str, verification_token: str, user_name: str = "Usuário") -> bool:
        """Envia email de verificação de conta após cadastro."""
        verify_link = f"{self.frontend_url}?verify_email={verification_token}"
        
        subject = "Confirme seu email - Kontabil"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #10b981, #059669); padding: 32px; text-align: center; }}
                .header h1 {{ color: white; margin: 0; font-size: 28px; }}
                .header p {{ color: rgba(255,255,255,0.9); margin: 8px 0 0; font-size: 16px; }}
                .content {{ padding: 32px; }}
                .content h2 {{ color: #1e293b; margin: 0 0 16px; }}
                .content p {{ color: #64748b; line-height: 1.6; margin: 0 0 16px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 16px 0; }}
                .footer {{ padding: 24px; text-align: center; color: #94a3b8; font-size: 14px; border-top: 1px solid #e2e8f0; }}
                .warning {{ background: #fef3c7; border: 1px solid #fcd34d; padding: 12px 16px; border-radius: 8px; color: #92400e; font-size: 14px; margin: 16px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Kontabil</h1>
                    <p>Análise Financeira Inteligente</p>
                </div>
                <div class="content">
                    <h2>Bem-vindo, {user_name}! 👋</h2>
                    <p>Obrigado por se cadastrar no Kontabil! Para ativar sua conta, confirme seu email clicando no botão abaixo:</p>
                    
                    <div style="text-align: center;">
                        <a href="{verify_link}" class="button">✓ Confirmar meu email</a>
                    </div>
                    
                    <div class="warning">
                        ⏰ Este link expira em <strong>24 horas</strong>. Após esse prazo, será necessário solicitar um novo email de verificação.
                    </div>
                    
                    <p style="font-size: 13px; color: #94a3b8;">Se você não criou uma conta no Kontabil, ignore este email.</p>
                </div>
                <div class="footer">
                    <p>Kontabil - Análise Financeira Inteligente</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Olá, {user_name}!

Obrigado por se cadastrar no Kontabil!
Para confirmar seu email, acesse: {verify_link}

Este link expira em 24 horas.

Se você não criou esta conta, ignore este email.
---
Kontabil - Análise Financeira Inteligente
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    # =========================================================================
    # RECUPERAÇÃO DE SENHA
    # =========================================================================
    
    def send_password_reset(self, to_email: str, reset_token: str, user_name: str = "Usuário") -> bool:
        """Envia email de recuperação de senha."""
        reset_link = f"{self.frontend_url}?reset_token={reset_token}"
        
        subject = "Recuperação de senha - Kontabil"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #10b981, #059669); padding: 32px; text-align: center; }}
                .header h1 {{ color: white; margin: 0; font-size: 28px; }}
                .header p {{ color: rgba(255,255,255,0.9); margin: 8px 0 0; }}
                .content {{ padding: 32px; }}
                .content h2 {{ color: #1e293b; margin: 0 0 16px; }}
                .content p {{ color: #64748b; line-height: 1.6; margin: 0 0 16px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 16px 0; }}
                .token-box {{ background: #f1f5f9; padding: 16px; border-radius: 8px; font-family: monospace; word-break: break-all; margin: 16px 0; font-size: 14px; color: #475569; }}
                .footer {{ padding: 24px; text-align: center; color: #94a3b8; font-size: 14px; border-top: 1px solid #e2e8f0; }}
                .warning {{ background: #fef3c7; border: 1px solid #fcd34d; padding: 12px 16px; border-radius: 8px; color: #92400e; font-size: 14px; margin: 16px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Kontabil</h1>
                    <p>Análise Financeira Inteligente</p>
                </div>
                <div class="content">
                    <h2>Olá, {user_name}!</h2>
                    <p>Recebemos uma solicitação para redefinir a senha da sua conta.</p>
                    <p>Clique no botão abaixo para criar uma nova senha:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">🔒 Redefinir minha senha</a>
                    </div>
                    
                    <p>Ou copie e cole o token abaixo na página de recuperação:</p>
                    <div class="token-box">{reset_token}</div>
                    
                    <div class="warning">
                        ⚠️ Este link expira em <strong>1 hora</strong>. Se você não solicitou, ignore este email.
                    </div>
                </div>
                <div class="footer">
                    <p>Kontabil - Análise Financeira Inteligente</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Olá, {user_name}!

Para redefinir sua senha, acesse: {reset_link}

Ou use este token: {reset_token}

Este link expira em 1 hora.
Se você não solicitou, ignore este email.
---
Kontabil - Análise Financeira Inteligente
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    # =========================================================================
    # ENVIO BASE
    # =========================================================================
    
    def _send_email(self, to: str, subject: str, html: str, text: str = None) -> bool:
        """Envia email via Resend ou loga se não disponível"""
        
        if not self.enabled:
            logger.info(f"📧 [EMAIL SIMULADO] Para: {to} | Assunto: {subject}")
            print(f"📧 [EMAIL SIMULADO] Para: {to} | Assunto: {subject}")
            print(f"   (Configure RESEND_API_KEY para enviar emails reais)")
            return True
        
        try:
            params = {
                "from": self.from_email,
                "to": [to],
                "subject": subject,
                "html": html,
            }
            
            if text:
                params["text"] = text
            
            response = resend.Emails.send(params)
            logger.info(f"✅ Email enviado para {to}: {response}")
            print(f"✅ Email enviado para {to} via Resend (id: {response.get('id', 'n/a') if isinstance(response, dict) else response})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email para {to}: {e}")
            print(f"❌ Erro ao enviar email para {to}: {e}")
            return False


# Instância global
email_service = EmailService()
