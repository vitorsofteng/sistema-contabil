"""
Serviço de Email usando Resend
Para recuperação de senha e notificações
"""

import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Tentar importar resend
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend não instalado. Emails serão apenas logados.")


class EmailService:
    """Serviço de envio de emails"""
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("EMAIL_FROM", "Kontabil <noreply@kontabil.com.br>")
        self.is_production = os.getenv("ENVIRONMENT", "development") == "production"
        
        if RESEND_AVAILABLE and self.api_key:
            resend.api_key = self.api_key
            self.enabled = True
        else:
            self.enabled = False
            if self.is_production:
                logger.warning("⚠️ Email não configurado em PRODUÇÃO! Configure RESEND_API_KEY.")
    
    def send_password_reset(self, to_email: str, reset_token: str, user_name: str = "Usuário") -> bool:
        """
        Envia email de recuperação de senha.
        
        Args:
            to_email: Email do destinatário
            reset_token: Token de reset
            user_name: Nome do usuário
        
        Returns:
            True se enviado com sucesso
        """
        # URL base do frontend (configurável)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        
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
                .button:hover {{ opacity: 0.9; }}
                .token-box {{ background: #f1f5f9; padding: 16px; border-radius: 8px; font-family: monospace; word-break: break-all; margin: 16px 0; }}
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
                    <p>Recebemos uma solicitação para redefinir a senha da sua conta no Kontabil.</p>
                    <p>Clique no botão abaixo para criar uma nova senha:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">Redefinir minha senha</a>
                    </div>
                    
                    <p>Ou copie e cole o token abaixo na página de recuperação:</p>
                    <div class="token-box">{reset_token}</div>
                    
                    <div class="warning">
                        ⚠️ Este link expira em <strong>1 hora</strong>. Se você não solicitou esta recuperação, ignore este email.
                    </div>
                </div>
                <div class="footer">
                    <p>Este email foi enviado automaticamente pelo Kontabil.</p>
                    <p>Se você não solicitou a recuperação de senha, pode ignorar este email com segurança.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Olá, {user_name}!

Recebemos uma solicitação para redefinir a senha da sua conta no Kontabil.

Para criar uma nova senha, acesse o link abaixo:
{reset_link}

Ou use este token na página de recuperação:
{reset_token}

⚠️ Este link expira em 1 hora.

Se você não solicitou esta recuperação, ignore este email.

---
Kontabil - Análise Financeira Inteligente
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_welcome(self, to_email: str, user_name: str) -> bool:
        """Envia email de boas-vindas"""
        subject = "Bem-vindo ao Kontabil! 🎉"
        
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
                .content {{ padding: 32px; }}
                .content h2 {{ color: #1e293b; margin: 0 0 16px; }}
                .content p {{ color: #64748b; line-height: 1.6; }}
                .feature {{ display: flex; align-items: flex-start; gap: 12px; margin: 16px 0; padding: 16px; background: #f8fafc; border-radius: 8px; }}
                .feature-icon {{ width: 40px; height: 40px; background: #10b981; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; flex-shrink: 0; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; }}
                .footer {{ padding: 24px; text-align: center; color: #94a3b8; font-size: 14px; border-top: 1px solid #e2e8f0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Bem-vindo ao Kontabil!</h1>
                </div>
                <div class="content">
                    <h2>Olá, {user_name}!</h2>
                    <p>Sua conta foi criada com sucesso! Estamos felizes em tê-lo conosco.</p>
                    
                    <p><strong>O que você pode fazer agora:</strong></p>
                    
                    <div class="feature">
                        <div class="feature-icon">📊</div>
                        <div>
                            <strong>Cadastre suas empresas</strong><br>
                            <span style="color: #64748b;">Adicione as empresas que você gerencia</span>
                        </div>
                    </div>
                    
                    <div class="feature">
                        <div class="feature-icon">📁</div>
                        <div>
                            <strong>Importe dados financeiros</strong><br>
                            <span style="color: #64748b;">Upload de planilhas Excel ou CSV</span>
                        </div>
                    </div>
                    
                    <div class="feature">
                        <div class="feature-icon">📈</div>
                        <div>
                            <strong>Analise a saúde financeira</strong><br>
                            <span style="color: #64748b;">Relatórios automáticos com insights</span>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin-top: 24px;">
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}" class="button">Acessar Kontabil</a>
                    </div>
                </div>
                <div class="footer">
                    <p>Precisa de ajuda? Responda este email que teremos prazer em ajudar.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_content)
    
    def _send_email(self, to: str, subject: str, html: str, text: str = None) -> bool:
        """Envia email via Resend ou loga se não disponível"""
        
        if not self.enabled:
            logger.info(f"📧 [EMAIL SIMULADO] Para: {to}")
            logger.info(f"   Assunto: {subject}")
            logger.info(f"   (Configure RESEND_API_KEY para enviar emails reais)")
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
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email para {to}: {e}")
            return False


# Instância global
email_service = EmailService()
