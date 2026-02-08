import AuthBranding from './AuthBranding';
import React, { useState } from 'react';
import { AlertCircle, ArrowLeft, BarChart3, CheckCircle, Loader2, User } from 'lucide-react';
import { BarChart } from 'recharts';
import { API_URL } from '../../config/api';

function ForgotPasswordPage({ onBack, onTokenReceived }) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [devToken, setDevToken] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const res = await fetch(`${API_URL}/auth/reset-senha`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || 'Erro ao solicitar recuperação');
      }
      
      setSent(true);
      
      // Em desenvolvimento, mostrar token (para testes)
      if (data._dev_token) {
        setDevToken(data._dev_token);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-slate-50">
      <AuthBranding />
      
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center">
              <BarChart3 className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Kontabil</h1>
              <p className="text-emerald-600 text-xs font-medium">Análise Financeira</p>
            </div>
          </div>

          {!sent ? (
            <>
              <button 
                onClick={onBack}
                className="flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-6"
              >
                <ArrowLeft className="w-4 h-4" />
                Voltar para login
              </button>

              <div className="text-center lg:text-left mb-8">
                <h2 className="text-3xl font-bold text-slate-900">Esqueceu sua senha?</h2>
                <p className="text-slate-500 mt-2">
                  Digite seu email e enviaremos instruções para recuperar sua senha.
                </p>
              </div>
              
              {error && (
                <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <p>{error}</p>
                </div>
              )}
              
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
                  <div className="relative">
                    <input
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="seu@email.com"
                      required
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <User className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Enviando...
                    </>
                  ) : (
                    'Enviar instruções'
                  )}
                </button>
              </form>
            </>
          ) : (
            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-8 h-8 text-emerald-600" />
              </div>
              
              <h2 className="text-2xl font-bold text-slate-900 mb-2">Email enviado!</h2>
              <p className="text-slate-500 mb-6">
                Se existe uma conta com o email <strong>{email}</strong>, você receberá instruções para recuperar sua senha.
              </p>
              
              {/* Token de desenvolvimento - REMOVER EM PRODUÇÃO */}
              {devToken && (
                <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl text-left">
                  <p className="text-amber-800 text-sm font-medium mb-2">🔧 Modo Desenvolvimento</p>
                  <p className="text-amber-700 text-xs mb-2">Token de recuperação (não aparece em produção):</p>
                  <code className="block p-2 bg-amber-100 rounded text-xs break-all">{devToken}</code>
                  <button
                    onClick={() => onTokenReceived(devToken)}
                    className="mt-3 w-full py-2 px-4 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    Usar este token para redefinir senha
                  </button>
                </div>
              )}
              
              <button 
                onClick={onBack}
                className="text-emerald-600 font-semibold hover:text-emerald-700"
              >
                Voltar para login
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Página de Redefinir Senha

export default ForgotPasswordPage;
