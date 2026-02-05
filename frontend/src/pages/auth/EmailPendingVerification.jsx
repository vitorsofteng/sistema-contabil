import React, { useState, useEffect } from 'react';
import { CheckCircle, Mail } from 'lucide-react';
import { API_URL } from '../../config/api';

function EmailPendingVerification({ email, nome, onContinue }) {
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(c => c - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleResend = async () => {
    setResending(true);
    try {
      await fetch(`${API_URL}/auth/reenviar-verificacao`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      setResent(true);
      setCountdown(60);
    } catch (e) {
      // silently fail
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-md text-center">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          {/* Ícone de email */}
          <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Mail className="w-10 h-10 text-emerald-600" />
          </div>
          
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Verifique seu email</h2>
          <p className="text-slate-500 mb-6">
            Enviamos um link de confirmação para:
          </p>
          <div className="bg-slate-50 rounded-xl px-4 py-3 mb-6">
            <p className="font-medium text-slate-900">{email}</p>
          </div>
          
          <p className="text-sm text-slate-500 mb-6">
            Clique no link enviado para ativar sua conta. O link expira em 24 horas.
          </p>

          {/* Divider */}
          <div className="border-t border-slate-200 my-6"></div>

          {/* Reenviar */}
          <div className="mb-4">
            <p className="text-sm text-slate-500 mb-3">Não recebeu o email? Verifique sua pasta de spam ou:</p>
            <button
              onClick={handleResend}
              disabled={resending || countdown > 0}
              className={`w-full px-4 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                countdown > 0 
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                  : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
              }`}
            >
              {resending ? 'Enviando...' : countdown > 0 ? `Reenviar em ${countdown}s` : resent ? 'Reenviar novamente' : 'Reenviar email de verificação'}
            </button>
          </div>

          {resent && countdown > 0 && (
            <div className="bg-emerald-50 text-emerald-700 text-sm p-3 rounded-xl mb-4 flex items-center gap-2 justify-center">
              <CheckCircle className="w-4 h-4" />
              Email reenviado com sucesso!
            </div>
          )}

          {/* Continuar mesmo assim */}
          <button
            onClick={onContinue}
            className="text-sm text-slate-400 hover:text-slate-600 transition-colors underline"
          >
            Continuar sem verificar (poderá verificar depois)
          </button>
        </div>
        
        <p className="text-xs text-slate-400 mt-4">
          Kontabil - Análise Financeira Inteligente
        </p>
      </div>
    </div>
  );
}

export default EmailPendingVerification;
