import AuthBranding from './AuthBranding';
import React, { useState } from 'react';
import { AlertCircle, ArrowUpRight, BarChart3, Clock, Eye, Loader2, Lock, Settings, Shield, User, XCircle } from 'lucide-react';
import { BarChart } from 'recharts';
import { useAuth } from '../../contexts/AuthContext';

function LoginPage({ onToggle, onForgot }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isLocked, setIsLocked] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      await login(email, senha);
    } catch (err) {
      const msg = err.message;
      setError(msg);
      if (msg.toLowerCase().includes('bloqueada') || msg.toLowerCase().includes('tentativa')) {
        setIsLocked(msg.toLowerCase().includes('bloqueada'));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-slate-50">
      <AuthBranding />
      
      {/* Form Side */}
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

          <div className="text-center lg:text-left mb-8">
            <h2 className="text-3xl font-bold text-slate-900">Bem-vindo de volta</h2>
            <p className="text-slate-500 mt-2">Entre na sua conta para continuar</p>
          </div>
          
          {error && (
            <div className={`mb-6 p-4 rounded-xl text-sm flex items-start gap-3 ${
              isLocked 
                ? 'bg-amber-50 border border-amber-200 text-amber-800' 
                : 'bg-red-50 border border-red-200 text-red-700'
            }`}>
              {isLocked ? (
                <Clock className="w-5 h-5 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              )}
              <div>
                <p className="font-medium">{isLocked ? 'Conta temporariamente bloqueada' : 'Erro ao entrar'}</p>
                <p className="text-sm opacity-80 mt-1">{error}</p>
              </div>
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
                  disabled={isLocked}
                  className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all disabled:bg-slate-50 disabled:text-slate-500"
                />
                <User className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Senha</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={senha}
                  onChange={e => setSenha(e.target.value)}
                  placeholder="••••••••"
                  required
                  disabled={isLocked}
                  className="w-full px-4 py-3 pl-11 pr-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all disabled:bg-slate-50 disabled:text-slate-500"
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
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="w-4 h-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500" />
                <span className="text-sm text-slate-600">Lembrar de mim</span>
              </label>
              <button type="button" onClick={onForgot} className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
                Esqueci a senha
              </button>
            </div>
            
            <button
              type="submit"
              disabled={loading || isLocked}
              className="w-full py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Entrando...
                </>
              ) : isLocked ? (
                'Conta bloqueada'
              ) : (
                <>
                  Entrar
                  <ArrowUpRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>
          
          <p className="mt-8 text-center text-sm text-slate-500">
            Não tem uma conta?{' '}
            <button onClick={onToggle} className="text-emerald-600 font-semibold hover:text-emerald-700">
              Criar conta grátis
            </button>
          </p>
          
          {/* Trust badges */}
          <div className="mt-8 pt-8 border-t border-slate-200">
            <div className="flex items-center justify-center gap-6 text-slate-400">
              <div className="flex items-center gap-2 text-xs">
                <Shield className="w-4 h-4" />
                <span>Dados criptografados</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <Lock className="w-4 h-4" />
                <span>Acesso seguro</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
