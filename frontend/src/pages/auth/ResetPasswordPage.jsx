import AuthBranding from './AuthBranding';
import React, { useState } from 'react';
import { AlertCircle, ArrowLeft, BarChart3, Check, CheckCircle, Eye, Loader2, Settings, XCircle } from 'lucide-react';
import { BarChart } from 'recharts';
import { API_URL } from '../../config/api';

function ResetPasswordPage({ token, onBack, onSuccess }) {
  const [senha, setSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [tokenInput, setTokenInput] = useState(token || '');

  const passwordChecks = [
    { label: 'Mínimo 8 caracteres', check: senha.length >= 8 },
    { label: 'Uma letra maiúscula', check: /[A-Z]/.test(senha) },
    { label: 'Uma letra minúscula', check: /[a-z]/.test(senha) },
    { label: 'Um número', check: /\d/.test(senha) },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (senha !== confirmarSenha) {
      setError('As senhas não coincidem');
      return;
    }
    
    if (!passwordChecks.every(c => c.check)) {
      setError('A senha não atende aos requisitos mínimos');
      return;
    }
    
    setLoading(true);
    
    try {
      const res = await fetch(`${API_URL}/auth/reset-senha/confirmar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: tokenInput, nova_senha: senha })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail?.message || data.detail || 'Erro ao redefinir senha');
      }
      
      setSuccess(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex bg-slate-50">
        <AuthBranding />
        
        <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
          <div className="w-full max-w-md text-center">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-8 h-8 text-emerald-600" />
            </div>
            
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Senha alterada!</h2>
            <p className="text-slate-500 mb-6">
              Sua senha foi redefinida com sucesso. Agora você pode fazer login com sua nova senha.
            </p>
            
            <button 
              onClick={onSuccess}
              className="w-full py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all"
            >
              Ir para login
            </button>
          </div>
        </div>
      </div>
    );
  }

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

          <button 
            onClick={onBack}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar para login
          </button>

          <div className="text-center lg:text-left mb-8">
            <h2 className="text-3xl font-bold text-slate-900">Nova senha</h2>
            <p className="text-slate-500 mt-2">
              Digite sua nova senha abaixo.
            </p>
          </div>
          
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <p>{error}</p>
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-5">
            {!token && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Token de recuperação</label>
                <input
                  type="text"
                  value={tokenInput}
                  onChange={e => setTokenInput(e.target.value)}
                  placeholder="Cole o token recebido por email"
                  required
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                />
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Nova senha</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={senha}
                  onChange={e => setSenha(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full px-4 py-3 pl-11 pr-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                />
                <Settings className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <XCircle className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              
              {/* Requisitos de senha */}
              <div className="mt-3 space-y-2">
                {passwordChecks.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div className={`w-4 h-4 rounded-full flex items-center justify-center ${item.check ? 'bg-emerald-500' : 'bg-slate-200'}`}>
                      {item.check && <Check className="w-3 h-3 text-white" />}
                    </div>
                    <span className={`text-xs ${item.check ? 'text-emerald-600' : 'text-slate-500'}`}>{item.label}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Confirmar nova senha</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmarSenha}
                  onChange={e => setConfirmarSenha(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                />
                <Settings className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
              </div>
              {confirmarSenha && senha !== confirmarSenha && (
                <p className="text-red-500 text-xs mt-1">As senhas não coincidem</p>
              )}
            </div>
            
            <button
              type="submit"
              disabled={loading || !passwordChecks.every(c => c.check) || senha !== confirmarSenha}
              className="w-full py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Salvando...
                </>
              ) : (
                'Salvar nova senha'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default ResetPasswordPage;
