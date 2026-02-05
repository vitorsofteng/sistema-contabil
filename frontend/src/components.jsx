import React, { useState, useEffect, createContext, useContext, useRef } from 'react';
import { 
  BarChart3, Building2, Users, AlertTriangle, TrendingUp, TrendingDown, 
  Plus, Search, Filter, MoreVertical, Bell, LogOut, Settings, User,
  ChevronRight, ArrowUpRight, ArrowDownRight, Minus, FileText, Upload,
  Calendar, DollarSign, PieChart as PieChartIcon, Activity, RefreshCw, Download, Eye,
  Edit, Trash2, CheckCircle, XCircle, Clock, Menu, X, Home, FileSpreadsheet,
  ChevronDown, AlertCircle, Info, Loader2, Check, ArrowLeft, Target, Lightbulb,
  Award, Shield, Lock
} from 'lucide-react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || '/api';

// ============================================================================
// CONTEXT - Auth
// ============================================================================

const AuthContext = createContext(null);

// Decodifica payload do JWT (sem verificar assinatura - só para ler expiração)
function decodeJWT(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(window.atob(base64));
    return payload;
  } catch {
    return null;
  }
}

// Verifica se token está próximo de expirar (menos de 30 minutos)
function isTokenExpiringSoon(token, minutesBefore = 30) {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) return true;
  const expiresAt = payload.exp * 1000; // converter para ms
  const now = Date.now();
  const threshold = minutesBefore * 60 * 1000;
  return (expiresAt - now) < threshold;
}

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refresh_token'));
  const [loading, setLoading] = useState(true);
  
  // Mutex para evitar múltiplos refreshes simultâneos
  const refreshingRef = useRef(false);
  const refreshPromiseRef = useRef(null);

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  // Refresh proativo - verifica a cada 5 minutos se precisa renovar
  useEffect(() => {
    if (!token || !refreshToken) return;
    
    const checkAndRefresh = async () => {
      if (isTokenExpiringSoon(token, 30)) {
        console.log('🔄 Token expirando em breve, renovando proativamente...');
        await tryRefreshToken();
      }
    };
    
    // Verifica imediatamente
    checkAndRefresh();
    
    // Verifica a cada 5 minutos
    const interval = setInterval(checkAndRefresh, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [token, refreshToken]);

  const fetchUser = async () => {
    try {
      // Se token está expirando, renova primeiro
      let currentToken = token;
      if (isTokenExpiringSoon(token, 5)) {
        const refreshed = await tryRefreshToken();
        if (refreshed) {
          currentToken = localStorage.getItem('token');
        }
      }
      
      const res = await fetch(`${API_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${currentToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else if (res.status === 401 && refreshToken) {
        const refreshed = await tryRefreshToken();
        if (refreshed) {
          // Tenta novamente com novo token
          const newToken = localStorage.getItem('token');
          const retryRes = await fetch(`${API_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${newToken}` }
          });
          if (retryRes.ok) {
            const data = await retryRes.json();
            setUser(data);
          } else {
            logout();
          }
        } else {
          logout();
        }
      } else {
        logout();
      }
    } catch (err) {
      console.error('Erro ao buscar usuário:', err);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const tryRefreshToken = async () => {
    // Se já está refreshando, aguarda a promise existente
    if (refreshingRef.current && refreshPromiseRef.current) {
      console.log('⏳ Refresh já em andamento, aguardando...');
      return refreshPromiseRef.current;
    }
    
    refreshingRef.current = true;
    
    refreshPromiseRef.current = (async () => {
      try {
        const currentRefreshToken = localStorage.getItem('refresh_token');
        if (!currentRefreshToken) {
          return false;
        }
        
        const res = await fetch(`${API_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: currentRefreshToken })
        });
        
        if (res.ok) {
          const data = await res.json();
          localStorage.setItem('token', data.token);
          setToken(data.token);
          if (data.user) {
            setUser(data.user);
          }
          console.log('✅ Token renovado com sucesso');
          return true;
        }
        console.warn('❌ Falha ao renovar token:', res.status);
        return false;
      } catch (err) {
        console.error('❌ Erro ao renovar token:', err);
        return false;
      } finally {
        refreshingRef.current = false;
        refreshPromiseRef.current = null;
      }
    })();
    
    return refreshPromiseRef.current;
  };

  const login = async (email, senha) => {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, senha })
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.detail || 'Erro ao fazer login');
    }
    
    localStorage.setItem('token', data.token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setToken(data.token);
    setRefreshToken(data.refresh_token);
    setUser(data.user);
    return data;
  };

  const register = async (dados) => {
    const res = await fetch(`${API_URL}/auth/registrar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados)
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.detail || 'Erro ao registrar');
    }
    
    localStorage.setItem('token', data.token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setToken(data.token);
    setRefreshToken(data.refresh_token);
    setUser(data.user);
    return data;
  };

  const logout = async () => {
    const currentToken = localStorage.getItem('token');
    if (currentToken) {
      try {
        await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${currentToken}` }
        });
      } catch {}
    }
    
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setRefreshToken(null);
    setUser(null);
  };

  const api = async (path, options = {}) => {
    let currentToken = localStorage.getItem('token');
    
    // Se token está expirando, renova antes de fazer a requisição
    if (currentToken && isTokenExpiringSoon(currentToken, 5)) {
      const refreshed = await tryRefreshToken();
      if (refreshed) {
        currentToken = localStorage.getItem('token');
      }
    }
    
    const headers = {
      'Authorization': `Bearer ${currentToken}`,
      ...options.headers
    };
    
    if (!(options.body instanceof FormData) && !options.headers?.hasOwnProperty('Content-Type')) {
      headers['Content-Type'] = 'application/json';
    }
    
    let res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers
    });
    
    // Se ainda assim deu 401, tenta refresh e retry
    if (res.status === 401) {
      const currentRefreshToken = localStorage.getItem('refresh_token');
      if (currentRefreshToken) {
        const refreshed = await tryRefreshToken();
        if (refreshed) {
          const newToken = localStorage.getItem('token');
          const retryHeaders = {
            'Authorization': `Bearer ${newToken}`,
            ...options.headers
          };
          if (!(options.body instanceof FormData) && !options.headers?.hasOwnProperty('Content-Type')) {
            retryHeaders['Content-Type'] = 'application/json';
          }
          res = await fetch(`${API_URL}${path}`, {
            ...options,
            headers: retryHeaders
          });
        } else {
          logout();
          throw new Error('Sessão expirada. Faça login novamente.');
        }
      } else {
        logout();
        throw new Error('Sessão expirada. Faça login novamente.');
      }
    }
    
    return res;
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, api }}>
      {children}
    </AuthContext.Provider>
  );
}

const useAuth = () => useContext(AuthContext);

// ============================================================================
// CONTEXT - Theme (Cores dinâmicas)
// ============================================================================

const ThemeContext = createContext(null);

function ThemeProvider({ children }) {
  const { token } = useAuth() || {};
  const [theme, setTheme] = useState({
    cor_primaria: '#1e40af',
    cor_secundaria: '#3b82f6',
    cor_destaque: '#059669',
    nome_escritorio: ''
  });
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (token) {
      loadTheme();
    }
  }, [token]);

  useEffect(() => {
    // Aplicar cores como CSS variables
    const root = document.documentElement;
    root.style.setProperty('--cor-primaria', theme.cor_primaria);
    root.style.setProperty('--cor-secundaria', theme.cor_secundaria);
    root.style.setProperty('--cor-destaque', theme.cor_destaque);
    
    // Converter hex para RGB para usar com opacity
    const hexToRgb = (hex) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '30, 64, 175';
    };
    
    root.style.setProperty('--cor-primaria-rgb', hexToRgb(theme.cor_primaria));
    root.style.setProperty('--cor-secundaria-rgb', hexToRgb(theme.cor_secundaria));
  }, [theme]);

  const loadTheme = async () => {
    try {
      const res = await fetch(`${API_URL}/relatorios/configuracao`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTheme(prev => ({
          ...prev,
          cor_primaria: data.cor_primaria || '#1e40af',
          cor_secundaria: data.cor_secundaria || '#3b82f6',
          cor_destaque: data.cor_destaque || '#059669',
          nome_escritorio: data.nome_escritorio || ''
        }));
      }
    } catch (err) {
      console.error('Erro ao carregar tema:', err);
    }
    setLoaded(true);
  };

  const updateTheme = (newTheme) => {
    setTheme(prev => ({ ...prev, ...newTheme }));
  };

  return (
    <ThemeContext.Provider value={{ theme, updateTheme, loadTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

const useTheme = () => useContext(ThemeContext);

// ============================================================================
// COMPONENTS - UI
// ============================================================================

function Card({ children, className = '', onClick }) {
  return (
    <div 
      className={`bg-white rounded-xl border border-slate-200 shadow-sm ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

function Button({ children, variant = 'primary', size = 'md', disabled, loading, className = '', style = {}, ...props }) {
  const themeCtx = useTheme();
  const theme = themeCtx?.theme || {};
  
  const baseClasses = 'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all disabled:cursor-not-allowed';
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  };
  
  // Estilos dinâmicos para variante primary
  const getVariantStyles = () => {
    if (variant === 'primary') {
      return {
        backgroundColor: theme.cor_primaria || '#1e40af',
        color: 'white',
        ...style
      };
    }
    return style;
  };
  
  const variants = {
    primary: 'text-white hover:brightness-110 disabled:opacity-50',
    secondary: 'bg-slate-100 text-slate-700 hover:bg-slate-200',
    danger: 'bg-red-600 text-white hover:bg-red-700',
    ghost: 'text-slate-600 hover:bg-slate-100',
    success: 'bg-emerald-600 text-white hover:bg-emerald-700',
  };
  
  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      style={getVariantStyles()}
      {...props}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  );
}

function Input({ label, error, className = '', ...props }) {
  return (
    <div className={className}>
      {label && <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>}
      <input
        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors ${error ? 'border-red-500' : 'border-slate-300'}`}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}

function Select({ label, options, children, className = '', ...props }) {
  return (
    <div className={className}>
      {label && <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>}
      <select
        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        {...props}
      >
        {children ? children : (options || []).map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
}

function Badge({ children, variant = 'default', size = 'sm' }) {
  const variants = {
    default: 'bg-slate-100 text-slate-700',
    success: 'bg-emerald-100 text-emerald-700',
    warning: 'bg-amber-100 text-amber-700',
    danger: 'bg-red-100 text-red-700',
    info: 'bg-blue-100 text-blue-700',
  };
  
  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  };
  
  return (
    <span className={`inline-flex items-center font-medium rounded-full ${variants[variant]} ${sizes[size]}`}>
      {children}
    </span>
  );
}

function StatusBadge({ status }) {
  const config = {
    // Formato antigo
    saudavel: { label: 'Saudável', variant: 'success' },
    atencao: { label: 'Atenção', variant: 'warning' },
    critico: { label: 'Crítico', variant: 'danger' },
    // Formato novo (analyzer profissional)
    'Excelente': { label: 'Excelente', variant: 'success' },
    'Bom': { label: 'Bom', variant: 'success' },
    'Regular': { label: 'Regular', variant: 'warning' },
    'Atenção': { label: 'Atenção', variant: 'warning' },
    'Crítico': { label: 'Crítico', variant: 'danger' },
  };
  
  const { label, variant } = config[status] || { label: status || 'N/A', variant: 'default' };
  return <Badge variant={variant}>{label}</Badge>;
}

function ScoreCircle({ score, size = 'md' }) {
  const color = score >= 70 ? 'text-emerald-600' : score >= 40 ? 'text-amber-600' : 'text-red-600';
  const bgColor = score >= 70 ? 'bg-emerald-50' : score >= 40 ? 'bg-amber-50' : 'bg-red-50';
  
  const sizes = {
    sm: 'w-10 h-10 text-sm',
    md: 'w-14 h-14 text-lg',
    lg: 'w-20 h-20 text-2xl',
  };
  
  return (
    <div className={`${sizes[size]} ${bgColor} rounded-full flex items-center justify-center font-bold ${color}`}>
      {score ?? '—'}
    </div>
  );
}

function Modal({ isOpen, onClose, title, children, size = 'md' }) {
  if (!isOpen) return null;
  
  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };
  
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative min-h-full flex items-center justify-center p-4">
        <div className={`relative bg-white rounded-xl shadow-xl w-full ${sizes[size]}`}>
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
            <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg">
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>
          <div className="p-4">{children}</div>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="text-center py-12">
      <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <Icon className="w-8 h-8 text-slate-400" />
      </div>
      <h3 className="text-lg font-medium text-slate-900 mb-1">{title}</h3>
      <p className="text-slate-500 mb-4">{description}</p>
      {action}
    </div>
  );
}

function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600 mx-auto mb-4" />
        <p className="text-slate-600">Carregando...</p>
      </div>
    </div>
  );
}

// ============================================================================
// PAGES - Auth
// ============================================================================

// ============================================================================
// AUTH PAGES - DESIGN PROFISSIONAL
// ============================================================================

function AuthBranding() {
  const features = [
    { icon: BarChart3, title: 'Análise Financeira', desc: 'DRE, índices e projeções automáticas' },
    { icon: TrendingUp, title: 'Gestão Inteligente', desc: 'Alertas e recomendações em tempo real' },
    { icon: FileText, title: 'Relatórios Profissionais', desc: 'PDF, Excel e apresentações prontas' },
    { icon: Building2, title: 'Multi-empresas', desc: 'Gerencie todas as empresas em um só lugar' },
  ];

  return (
    <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-96 h-96 bg-emerald-500 rounded-full filter blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-500 rounded-full filter blur-3xl translate-x-1/2 translate-y-1/2"></div>
      </div>
      
      {/* Grid Pattern */}
      <div className="absolute inset-0 opacity-5">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      <div className="relative z-10 flex flex-col justify-between p-12 w-full">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
            <BarChart3 className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Kontabil</h1>
            <p className="text-emerald-400 text-sm font-medium">Análise Financeira Inteligente</p>
          </div>
        </div>

        {/* Main Content */}
        <div className="space-y-8">
          <div>
            <h2 className="text-4xl font-bold text-white leading-tight">
              Simplifique sua
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                gestão financeira
              </span>
            </h2>
            <p className="mt-4 text-slate-400 text-lg max-w-md">
              Análise financeira avançada, relatórios automáticos e insights inteligentes para sua empresa crescer.
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-2 gap-4">
            {features.map((feature, idx) => (
              <div key={idx} className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10 hover:bg-white/10 transition-colors">
                <feature.icon className="w-8 h-8 text-emerald-400 mb-3" />
                <h3 className="font-semibold text-white text-sm">{feature.title}</h3>
                <p className="text-slate-400 text-xs mt-1">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-emerald-400">✓</div>
              <div className="text-slate-400 text-xs">Gratuito</div>
            </div>
            <div className="w-px h-8 bg-slate-700"></div>
            <div className="text-center">
              <div className="text-2xl font-bold text-emerald-400">✓</div>
              <div className="text-slate-400 text-xs">Sem cartão</div>
            </div>
            <div className="w-px h-8 bg-slate-700"></div>
            <div className="text-center">
              <div className="text-2xl font-bold text-emerald-400">✓</div>
              <div className="text-slate-400 text-xs">Fácil de usar</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

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

function RegisterPage({ onToggle }) {
  const { register } = useAuth();
  const [form, setForm] = useState({ 
    nome: '', 
    email: '', 
    senha: '', 
    telefone: '',
    escritorio: '',
    cnpj: '',
    crc: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [step, setStep] = useState(1);
  
  const passwordChecks = {
    length: form.senha.length >= 8,
    uppercase: /[A-Z]/.test(form.senha),
    lowercase: /[a-z]/.test(form.senha),
    number: /\d/.test(form.senha),
    special: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(form.senha),
  };
  const passwordStrength = Object.values(passwordChecks).filter(Boolean).length;
  const isPasswordValid = passwordStrength >= 4;

  const getStrengthColor = () => {
    if (passwordStrength <= 1) return 'bg-red-500';
    if (passwordStrength <= 2) return 'bg-orange-500';
    if (passwordStrength <= 3) return 'bg-yellow-500';
    if (passwordStrength <= 4) return 'bg-lime-500';
    return 'bg-emerald-500';
  };

  const getStrengthText = () => {
    if (passwordStrength <= 1) return 'Muito fraca';
    if (passwordStrength <= 2) return 'Fraca';
    if (passwordStrength <= 3) return 'Média';
    if (passwordStrength <= 4) return 'Forte';
    return 'Muito forte';
  };

  // Formatar CNPJ
  const formatCNPJ = (value) => {
    const numbers = value.replace(/\D/g, '').slice(0, 14);
    return numbers.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
                  .replace(/(\d{2})(\d{3})(\d{3})(\d{4})/, '$1.$2.$3/$4')
                  .replace(/(\d{2})(\d{3})(\d{3})/, '$1.$2.$3')
                  .replace(/(\d{2})(\d{3})/, '$1.$2');
  };

  // Formatar telefone
  const formatPhone = (value) => {
    const numbers = value.replace(/\D/g, '').slice(0, 11);
    if (numbers.length <= 10) {
      return numbers.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3')
                    .replace(/(\d{2})(\d{4})/, '($1) $2');
    }
    return numbers.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3')
                  .replace(/(\d{2})(\d{5})/, '($1) $2');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!isPasswordValid) {
      setError('A senha precisa ter pelo menos 4 requisitos atendidos');
      return;
    }
    
    setLoading(true);
    
    try {
      // Enviar dados completos
      await register({
        nome: form.nome,
        email: form.email,
        senha: form.senha,
        telefone: form.telefone,
        escritorio: form.escritorio,
        cnpj: form.cnpj.replace(/\D/g, ''),
        crc: form.crc
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const canProceedStep1 = form.nome.trim().length >= 3 && form.email.includes('@');
  const canProceedStep2 = form.escritorio.trim().length >= 2;

  const stepTitles = {
    1: { title: 'Dados Pessoais', subtitle: 'Informações do responsável pela conta' },
    2: { title: 'Dados do Escritório', subtitle: 'Informações do seu escritório contábil' },
    3: { title: 'Criar Senha', subtitle: 'Defina uma senha segura para sua conta' }
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

          <div className="text-center lg:text-left mb-6">
            <div className="flex items-center gap-2 text-emerald-600 text-sm font-medium mb-2">
              <span className="w-6 h-6 rounded-full bg-emerald-100 flex items-center justify-center text-xs">
                {step}
              </span>
              <span>Etapa {step} de 3</span>
            </div>
            <h2 className="text-3xl font-bold text-slate-900">{stepTitles[step].title}</h2>
            <p className="text-slate-500 mt-2">{stepTitles[step].subtitle}</p>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center gap-2 mb-8">
            <div className={`flex-1 h-1.5 rounded-full transition-colors ${step >= 1 ? 'bg-emerald-500' : 'bg-slate-200'}`}></div>
            <div className={`flex-1 h-1.5 rounded-full transition-colors ${step >= 2 ? 'bg-emerald-500' : 'bg-slate-200'}`}></div>
            <div className={`flex-1 h-1.5 rounded-full transition-colors ${step >= 3 ? 'bg-emerald-500' : 'bg-slate-200'}`}></div>
          </div>
          
          {error && (
            <div className="mb-6 p-4 rounded-xl text-sm flex items-start gap-3 bg-red-50 border border-red-200 text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">Erro ao criar conta</p>
                <p className="text-sm opacity-80 mt-1">{error}</p>
              </div>
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* ETAPA 1: Dados Pessoais */}
            {step === 1 && (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Nome completo <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={form.nome}
                      onChange={e => setForm({...form, nome: e.target.value})}
                      placeholder="Seu nome completo"
                      required
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <User className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-slate-500 mt-1.5">Nome do contador ou responsável pela conta</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Email profissional <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="email"
                      value={form.email}
                      onChange={e => setForm({...form, email: e.target.value})}
                      placeholder="contador@escritorio.com.br"
                      required
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <FileText className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-slate-500 mt-1.5">Será usado para login e comunicações importantes</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Telefone / WhatsApp
                  </label>
                  <div className="relative">
                    <input
                      type="tel"
                      value={form.telefone}
                      onChange={e => setForm({...form, telefone: formatPhone(e.target.value)})}
                      placeholder="(11) 99999-9999"
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <Activity className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => canProceedStep1 && setStep(2)}
                  disabled={!canProceedStep1}
                  className="w-full py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  Continuar
                  <ChevronRight className="w-5 h-5" />
                </button>
              </>
            )}

            {/* ETAPA 2: Dados do Escritório */}
            {step === 2 && (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Nome do Escritório <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={form.escritorio}
                      onChange={e => setForm({...form, escritorio: e.target.value})}
                      placeholder="Nome do seu escritório contábil"
                      required
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <Building2 className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-slate-500 mt-1.5">Razão social ou nome fantasia do escritório</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    CNPJ do Escritório
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={form.cnpj}
                      onChange={e => setForm({...form, cnpj: formatCNPJ(e.target.value)})}
                      placeholder="00.000.000/0000-00"
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <FileText className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Registro CRC
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={form.crc}
                      onChange={e => setForm({...form, crc: e.target.value.toUpperCase()})}
                      placeholder="CRC-SP 123456/O-7"
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <Award className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-slate-500 mt-1.5">Registro no Conselho Regional de Contabilidade (opcional)</p>
                </div>

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="flex-1 py-3 px-4 border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-100 transition-all flex items-center justify-center gap-2"
                  >
                    <ArrowLeft className="w-5 h-5" />
                    Voltar
                  </button>
                  <button
                    type="button"
                    onClick={() => canProceedStep2 && setStep(3)}
                    disabled={!canProceedStep2}
                    className="flex-1 py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    Continuar
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </>
            )}

            {/* ETAPA 3: Senha */}
            {step === 3 && (
              <>
                {/* Resumo dos dados */}
                <div className="bg-slate-100 rounded-xl p-4 mb-2">
                  <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-2">Resumo do cadastro</p>
                  <div className="space-y-1.5 text-sm">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-700">{form.nome}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-700">{form.escritorio}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-700">{form.email}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Criar senha <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={form.senha}
                      onChange={e => setForm({...form, senha: e.target.value})}
                      placeholder="••••••••"
                      required
                      className="w-full px-4 py-3 pl-11 pr-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <Lock className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                      {showPassword ? <XCircle className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  
                  {/* Password Strength Indicator */}
                  {form.senha && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-slate-500">Força da senha</span>
                        <span className={`text-xs font-medium ${
                          passwordStrength >= 4 ? 'text-emerald-600' : 
                          passwordStrength >= 3 ? 'text-lime-600' : 
                          passwordStrength >= 2 ? 'text-yellow-600' : 'text-red-600'
                        }`}>{getStrengthText()}</span>
                      </div>
                      <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map(i => (
                          <div key={i} className={`flex-1 h-1.5 rounded-full ${i <= passwordStrength ? getStrengthColor() : 'bg-slate-200'}`}></div>
                        ))}
                      </div>
                      
                      <div className="mt-4 grid grid-cols-2 gap-2">
                        {[
                          { check: passwordChecks.length, label: '8+ caracteres' },
                          { check: passwordChecks.uppercase, label: 'Maiúscula' },
                          { check: passwordChecks.lowercase, label: 'Minúscula' },
                          { check: passwordChecks.number, label: 'Número' },
                          { check: passwordChecks.special, label: 'Especial (!@#)' },
                        ].map((item, idx) => (
                          <div key={idx} className="flex items-center gap-2">
                            <div className={`w-4 h-4 rounded-full flex items-center justify-center ${item.check ? 'bg-emerald-500' : 'bg-slate-200'}`}>
                              {item.check && <Check className="w-3 h-3 text-white" />}
                            </div>
                            <span className={`text-xs ${item.check ? 'text-emerald-600' : 'text-slate-500'}`}>{item.label}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setStep(2)}
                    className="flex-1 py-3 px-4 border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-100 transition-all flex items-center justify-center gap-2"
                  >
                    <ArrowLeft className="w-5 h-5" />
                    Voltar
                  </button>
                  <button
                    type="submit"
                    disabled={loading || !isPasswordValid}
                    className="flex-1 py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Criando...
                      </>
                    ) : (
                      <>
                        Criar conta
                        <Check className="w-5 h-5" />
                      </>
                    )}
                  </button>
                </div>
              </>
            )}
          </form>
          
          {/* Info box */}
          <div className="mt-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-emerald-800">Plano gratuito inclui:</p>
                <ul className="text-emerald-700 mt-1 space-y-0.5 text-xs">
                  <li>• Até 5 empresas cadastradas</li>
                  <li>• Importação de balancetes ilimitada</li>
                  <li>• Relatórios em PDF e Excel</li>
                  <li>• Suporte por email</li>
                </ul>
              </div>
            </div>
          </div>
          
          <p className="mt-6 text-center text-sm text-slate-500">
            Já tem uma conta?{' '}
            <button onClick={onToggle} className="text-emerald-600 font-semibold hover:text-emerald-700">
              Fazer login
            </button>
          </p>

          <p className="mt-4 text-center text-xs text-slate-400">
            Ao criar uma conta, você concorda com nossos{' '}
            <a href="#" className="text-emerald-600 hover:underline">Termos de Uso</a>
            {' '}e{' '}
            <a href="#" className="text-emerald-600 hover:underline">Política de Privacidade</a>
          </p>
        </div>
      </div>
    </div>
  );
}

function AuthPages() {
  const [page, setPage] = useState('login'); // login, register, forgot, reset
  const [resetToken, setResetToken] = useState('');
  
  if (page === 'forgot') {
    return <ForgotPasswordPage onBack={() => setPage('login')} onTokenReceived={(token) => { setResetToken(token); setPage('reset'); }} />;
  }
  
  if (page === 'reset') {
    return <ResetPasswordPage token={resetToken} onBack={() => setPage('login')} onSuccess={() => setPage('login')} />;
  }
  
  if (page === 'register') {
    return <RegisterPage onToggle={() => setPage('login')} />;
  }
  
  return <LoginPage onToggle={() => setPage('register')} onForgot={() => setPage('forgot')} />;
}

// Página de Esqueci Minha Senha
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

// ============================================================================
// LAYOUT
// ============================================================================

function Sidebar({ currentPage, onNavigate, collapsed, onToggle }) {
  const { user, logout } = useAuth();
  const themeCtx = useTheme();
  const theme = themeCtx?.theme || {};
  
  const menuItems = [
    { id: 'dashboard', icon: Home, label: 'Dashboard' },
    { id: 'empresas', icon: Building2, label: 'Empresas' },
    { id: 'alertas', icon: Bell, label: 'Alertas' },
    { id: 'importacao', icon: Upload, label: 'Importação' },
    { id: 'relatorios', icon: FileText, label: 'Relatórios' },
  ];

  // Estilo dinâmico baseado no tema
  const sidebarStyle = {
    background: theme.cor_primaria 
      ? `linear-gradient(180deg, ${theme.cor_primaria} 0%, ${adjustBrightness(theme.cor_primaria, -30)} 100%)`
      : 'linear-gradient(180deg, #1e40af 0%, #1e3a8a 100%)'
  };
  
  const activeItemStyle = {
    backgroundColor: theme.cor_secundaria || '#3b82f6'
  };

  return (
    <aside 
      className={`fixed left-0 top-0 h-full text-white transition-all z-40 ${collapsed ? 'w-16' : 'w-64'}`}
      style={sidebarStyle}
    >
      <div className="flex items-center justify-between p-4 border-b border-white/20">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <BarChart3 className="w-8 h-8 text-white/90" />
            <span className="font-bold text-lg">{theme.nome_escritorio || 'Kontabil'}</span>
          </div>
        )}
        <button onClick={onToggle} className="p-1.5 hover:bg-white/10 rounded-lg">
          <Menu className="w-5 h-5" />
        </button>
      </div>
      
      <nav className="p-2 space-y-1">
        {menuItems.map(item => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
              currentPage === item.id 
                ? 'text-white' 
                : 'text-white/70 hover:bg-white/10'
            }`}
            style={currentPage === item.id ? activeItemStyle : {}}
          >
            <item.icon className="w-5 h-5" />
            {!collapsed && <span>{item.label}</span>}
          </button>
        ))}
      </nav>
      
      <div className="absolute bottom-0 left-0 right-0 p-2 border-t border-white/20">
        {!collapsed && (
          <div className="px-3 py-2 mb-2">
            <p className="text-sm font-medium truncate">{user?.nome}</p>
            <p className="text-xs text-white/60 truncate">{user?.email}</p>
          </div>
        )}
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10"
        >
          <LogOut className="w-5 h-5" />
          {!collapsed && <span>Sair</span>}
        </button>
      </div>
    </aside>
  );
}

// Função auxiliar para ajustar brilho de cor hex
function adjustBrightness(hex, percent) {
  if (!hex) return '#1e3a8a';
  hex = hex.replace('#', '');
  const num = parseInt(hex, 16);
  const r = Math.min(255, Math.max(0, (num >> 16) + percent));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + percent));
  const b = Math.min(255, Math.max(0, (num & 0x0000FF) + percent));
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
}

function Header({ title, subtitle, actions }) {
  return (
    <header className="mb-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
          {subtitle && <p className="text-slate-500 mt-1">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </header>
  );
}

// ============================================================================
// PAGES - Dashboard Avançado (F08)
// ============================================================================

const CORES_GRAFICO = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

function formatarMoeda(valor) {
  if (valor === null || valor === undefined) return 'R$ 0';
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatarMoedaCurta(valor) {
  if (valor === null || valor === undefined) return '0';
  if (valor >= 1000000) return `${(valor / 1000000).toFixed(1)}M`;
  if (valor >= 1000) return `${(valor / 1000).toFixed(0)}K`;
  return valor.toFixed(0);
}

function DashboardPage({ onNavigate }) {
  const { api } = useAuth();
  const [stats, setStats] = useState(null);
  const [empresas, setEmpresas] = useState([]);
  const [graficos, setGraficos] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('visao-geral');
  const [empresaFiltro, setEmpresaFiltro] = useState('todas');

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (empresas.length > 0) {
      loadGraficos();
    }
  }, [empresaFiltro]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [dashRes, empRes, grafRes] = await Promise.all([
        api('/dashboard'),
        api('/empresas'),
        api('/dashboard/graficos?meses=12')
      ]);
      
      if (dashRes.ok) {
        const data = await dashRes.json();
        setStats(data.estatisticas);
      }
      if (empRes.ok) {
        const data = await empRes.json();
        setEmpresas(data.empresas || []);
      }
      if (grafRes.ok) {
        const data = await grafRes.json();
        setGraficos(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadGraficos = async () => {
    try {
      const url = empresaFiltro === 'todas' 
        ? '/dashboard/graficos?meses=12' 
        : `/dashboard/graficos?meses=12&empresa_id=${empresaFiltro}`;
      const res = await api(url);
      if (res.ok) {
        const data = await res.json();
        setGraficos(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <LoadingScreen />;

  const tabs = [
    { id: 'visao-geral', label: 'Visão Geral', icon: Home },
    { id: 'graficos', label: 'Gráficos', icon: BarChart3 },
    { id: 'empresas', label: 'Empresas', icon: Building2 },
  ];

  const empresaSelecionadaNome = empresaFiltro === 'todas' 
    ? 'Todas as empresas' 
    : empresas.find(e => e.id === parseInt(empresaFiltro))?.razao_social || 'Empresa';

  return (
    <div>
      <Header 
        title="Dashboard" 
        subtitle="Visão geral do seu portfólio"
        actions={
          <Button onClick={loadData} variant="secondary" size="sm">
            <RefreshCw className="w-4 h-4" /> Atualizar
          </Button>
        }
      />
      
      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-100 p-1 rounded-lg w-fit">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id 
                ? 'bg-white text-slate-900 shadow-sm' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab: Visão Geral */}
      {activeTab === 'visao-geral' && (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total de Empresas</p>
                  <p className="text-2xl font-bold text-slate-900">{stats?.total_empresas || 0}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Saudáveis</p>
                  <p className="text-2xl font-bold text-green-600">{stats?.empresas_saudaveis || 0}</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Em Atenção</p>
                  <p className="text-2xl font-bold text-amber-600">{stats?.empresas_atencao || 0}</p>
                </div>
                <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-amber-600" />
                </div>
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Críticas</p>
                  <p className="text-2xl font-bold text-red-600">{stats?.empresas_criticas || 0}</p>
                </div>
                <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                  <XCircle className="w-6 h-6 text-red-600" />
                </div>
              </div>
            </Card>
          </div>

          {/* Comparativo Mensal */}
          {graficos?.comparativo_mensal?.periodo_atual && (
            <Card className="p-6 mb-6">
              <h3 className="font-semibold text-slate-900 mb-4">
                Comparativo: {graficos.comparativo_mensal.periodo_atual} vs {graficos.comparativo_mensal.periodo_anterior}
              </h3>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {['receita', 'custos', 'despesas', 'lucro'].map(campo => {
                  const dados = graficos.comparativo_mensal[campo];
                  const isPositive = campo === 'lucro' || campo === 'receita' 
                    ? dados?.variacao > 0 
                    : dados?.variacao < 0;
                  return (
                    <div key={campo} className="bg-slate-50 p-4 rounded-lg">
                      <p className="text-sm text-slate-500 capitalize mb-1">{campo}</p>
                      <p className="text-xl font-bold text-slate-900">
                        {formatarMoeda(dados?.atual)}
                      </p>
                      <div className={`flex items-center gap-1 text-sm mt-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                        {dados?.variacao > 0 ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : dados?.variacao < 0 ? (
                          <TrendingDown className="w-4 h-4" />
                        ) : (
                          <Minus className="w-4 h-4" />
                        )}
                        <span>{dados?.variacao > 0 ? '+' : ''}{dados?.variacao}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* Totais Consolidados */}
          {graficos?.totais && (
            <div className="grid md:grid-cols-3 gap-4 mb-6">
              <Card className="p-4 bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                <p className="text-blue-100 text-sm">Receita Total (12 meses)</p>
                <p className="text-2xl font-bold">{formatarMoeda(graficos.totais.receita_total)}</p>
              </Card>
              <Card className="p-4 bg-gradient-to-br from-green-500 to-green-600 text-white">
                <p className="text-green-100 text-sm">Lucro Total (12 meses)</p>
                <p className="text-2xl font-bold">{formatarMoeda(graficos.totais.lucro_total)}</p>
              </Card>
              <Card className="p-4 bg-gradient-to-br from-purple-500 to-purple-600 text-white">
                <p className="text-purple-100 text-sm">Margem Média</p>
                <p className="text-2xl font-bold">{graficos.totais.margem_media}%</p>
              </Card>
            </div>
          )}

          {/* Mini gráfico de faturamento */}
          {graficos?.faturamento_mensal?.length > 0 && (
            <Card className="p-6 mb-6">
              <h3 className="font-semibold text-slate-900 mb-4">Faturamento (12 meses)</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={graficos.faturamento_mensal}>
                    <defs>
                      <linearGradient id="colorReceita" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="mes" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                    <YAxis tickFormatter={formatarMoedaCurta} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                    <Tooltip formatter={(val) => formatarMoeda(val)} />
                    <Area type="monotone" dataKey="receita" stroke="#3b82f6" strokeWidth={2} fill="url(#colorReceita)" name="Receita" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}
        </>
      )}

      {/* Tab: Gráficos */}
      {activeTab === 'graficos' && (
        <div className="space-y-6">
          {/* Filtro de Empresa */}
          <Card className="p-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Filter className="w-5 h-5 text-slate-500" />
                <span className="font-medium text-slate-700">Filtrar por empresa:</span>
              </div>
              <select
                value={empresaFiltro}
                onChange={(e) => setEmpresaFiltro(e.target.value)}
                className="px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white min-w-[200px]"
              >
                <option value="todas">📊 Todas as empresas (consolidado)</option>
                {empresas.map(emp => (
                  <option key={emp.id} value={emp.id}>🏢 {emp.razao_social}</option>
                ))}
              </select>
              {empresaFiltro !== 'todas' && (
                <button 
                  onClick={() => setEmpresaFiltro('todas')}
                  className="text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1"
                >
                  <X className="w-4 h-4" /> Limpar filtro
                </button>
              )}
            </div>
            {empresaFiltro !== 'todas' && (
              <p className="mt-2 text-sm text-emerald-600 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Exibindo dados de: <strong>{empresaSelecionadaNome}</strong>
              </p>
            )}
          </Card>

          {/* Faturamento vs Lucro */}
          {graficos?.faturamento_mensal?.length > 0 && (
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-900">Faturamento vs Lucro</h3>
                <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">{empresaSelecionadaNome}</span>
              </div>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={graficos.faturamento_mensal}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="mes" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                    <YAxis tickFormatter={formatarMoedaCurta} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                    <Tooltip formatter={(val) => formatarMoeda(val)} />
                    <Legend />
                    <Line type="monotone" dataKey="receita" stroke="#3b82f6" strokeWidth={2} name="Receita" dot={{ fill: '#3b82f6' }} />
                    <Line type="monotone" dataKey="lucro" stroke="#22c55e" strokeWidth={2} name="Lucro" dot={{ fill: '#22c55e' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Composição de Despesas */}
            {graficos?.composicao_despesas?.length > 0 && (
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-900">Composição de Despesas</h3>
                  <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">Último mês</span>
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={graficos.composicao_despesas}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={3}
                        dataKey="valor"
                        nameKey="nome"
                        label={false}
                      >
                        {graficos.composicao_despesas.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.cor || CORES_GRAFICO[index % CORES_GRAFICO.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(val) => formatarMoeda(val)} />
                      <Legend 
                        layout="vertical" 
                        align="right" 
                        verticalAlign="middle"
                        formatter={(value) => <span className="text-sm text-slate-600">{value}</span>}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex flex-wrap gap-3 justify-center mt-2">
                  {graficos.composicao_despesas.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.cor || CORES_GRAFICO[idx % CORES_GRAFICO.length] }} />
                      <span className="text-slate-600">{formatarMoeda(item.valor)}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Fluxo de Caixa */}
            {graficos?.fluxo_caixa?.length > 0 && (
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-900">Fluxo de Caixa</h3>
                  <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">{empresaSelecionadaNome}</span>
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={graficos.fluxo_caixa}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="mes" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                      <YAxis tickFormatter={formatarMoedaCurta} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                      <Tooltip formatter={(val) => formatarMoeda(val)} />
                      <Legend />
                      <Bar dataKey="entradas" fill="#22c55e" name="Entradas" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="saidas" fill="#ef4444" name="Saídas" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            )}
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Top Empresas por Faturamento */}
            {graficos?.top_empresas_faturamento?.length > 0 && empresaFiltro === 'todas' && (
              <Card className="p-6">
                <h3 className="font-semibold text-slate-900 mb-4">Top 5 Empresas por Faturamento</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={graficos.top_empresas_faturamento} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis type="number" tickFormatter={formatarMoedaCurta} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                      <YAxis dataKey="nome" type="category" tick={{ fontSize: 11 }} stroke="#94a3b8" width={100} />
                      <Tooltip formatter={(val) => formatarMoeda(val)} />
                      <Bar dataKey="faturamento_total" fill="#3b82f6" name="Faturamento" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            )}

            {/* Top Empresas por Score */}
            {graficos?.top_empresas_score?.length > 0 && empresaFiltro === 'todas' && (
              <Card className="p-6">
                <h3 className="font-semibold text-slate-900 mb-4">Top 5 Empresas por Score</h3>
                <div className="space-y-3">
                  {graficos.top_empresas_score.map((emp, idx) => (
                    <div key={emp.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                      <span className="text-lg font-bold text-slate-400 w-6">{idx + 1}</span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-900 truncate">{emp.nome}</p>
                        <StatusBadge status={emp.status} />
                      </div>
                      <ScoreCircle score={emp.score} size="md" />
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Se filtrou por empresa, mostra dados detalhados */}
            {empresaFiltro !== 'todas' && (
              <Card className="p-6 lg:col-span-2">
                <h3 className="font-semibold text-slate-900 mb-4">Resumo da Empresa</h3>
                {graficos?.totais ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <p className="text-sm text-blue-600 mb-1">Receita Total</p>
                      <p className="text-xl font-bold text-blue-700">{formatarMoeda(graficos.totais.receita_total)}</p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <p className="text-sm text-green-600 mb-1">Lucro Total</p>
                      <p className="text-xl font-bold text-green-700">{formatarMoeda(graficos.totais.lucro_total)}</p>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <p className="text-sm text-purple-600 mb-1">Margem Média</p>
                      <p className="text-xl font-bold text-purple-700">{graficos.totais.margem_media}%</p>
                    </div>
                    <div className="bg-amber-50 p-4 rounded-lg">
                      <p className="text-sm text-amber-600 mb-1">Meses com Dados</p>
                      <p className="text-xl font-bold text-amber-700">{graficos?.faturamento_mensal?.length || 0}</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-500">Nenhum dado encontrado para esta empresa</p>
                )}
              </Card>
            )}
          </div>

          {/* Sem dados */}
          {(!graficos?.faturamento_mensal?.length) && (
            <Card className="p-8">
              <EmptyState 
                icon={BarChart3}
                title="Sem dados para gráficos"
                description="Importe dados financeiros das suas empresas para visualizar os gráficos"
              />
            </Card>
          )}
        </div>
      )}

      {/* Tab: Empresas */}
      {activeTab === 'empresas' && (
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900">Suas Empresas</h3>
            <Button size="sm" onClick={() => onNavigate('nova-empresa')}>
              <Plus className="w-4 h-4" /> Nova Empresa
            </Button>
          </div>
          
          {empresas.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-slate-500 border-b">
                    <th className="pb-3 font-medium">Empresa</th>
                    <th className="pb-3 font-medium">Score</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Meses</th>
                    <th className="pb-3 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {empresas.map(emp => (
                    <tr 
                      key={emp.id} 
                      className="border-b last:border-0 hover:bg-slate-50 cursor-pointer"
                      onClick={() => onNavigate('empresa', emp.id)}
                    >
                      <td className="py-3">
                        <p className="font-medium text-slate-900">{emp.razao_social}</p>
                        {emp.cnpj && <p className="text-sm text-slate-500">{emp.cnpj}</p>}
                      </td>
                      <td className="py-3">
                        <ScoreCircle score={emp.ultimo_score} size="sm" />
                      </td>
                      <td className="py-3">
                        {emp.ultimo_status ? <StatusBadge status={emp.ultimo_status} /> : <span className="text-slate-400">—</span>}
                      </td>
                      <td className="py-3 text-sm text-slate-500">
                        {emp.meses_dados || 0} meses
                      </td>
                      <td className="py-3">
                        <ChevronRight className="w-5 h-5 text-slate-400" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState 
              icon={Building2}
              title="Nenhuma empresa cadastrada"
              description="Cadastre sua primeira empresa para começar"
              action={
                <Button onClick={() => onNavigate('nova-empresa')}>
                  <Plus className="w-4 h-4" /> Cadastrar Empresa
                </Button>
              }
            />
          )}
        </Card>
      )}
    </div>
  );
}

// ============================================================================
// TOAST - Notificações
// ============================================================================

const ToastContext = createContext(null);

function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const toastIdRef = useRef(0);

  const addToast = (message, type = 'info', duration = 4000) => {
    const id = `toast-${++toastIdRef.current}-${Date.now()}`;
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  };

  const toast = {
    success: (msg) => addToast(msg, 'success'),
    error: (msg) => addToast(msg, 'error'),
    warning: (msg) => addToast(msg, 'warning'),
    info: (msg) => addToast(msg, 'info'),
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map(t => (
          <div 
            key={t.id}
            className={`
              px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 min-w-[300px] animate-slide-in
              ${t.type === 'success' ? 'bg-green-500 text-white' : ''}
              ${t.type === 'error' ? 'bg-red-500 text-white' : ''}
              ${t.type === 'warning' ? 'bg-yellow-500 text-white' : ''}
              ${t.type === 'info' ? 'bg-blue-500 text-white' : ''}
            `}
          >
            {t.type === 'success' && <CheckCircle className="w-5 h-5 flex-shrink-0" />}
            {t.type === 'error' && <XCircle className="w-5 h-5 flex-shrink-0" />}
            {t.type === 'warning' && <AlertTriangle className="w-5 h-5 flex-shrink-0" />}
            {t.type === 'info' && <Info className="w-5 h-5 flex-shrink-0" />}
            <span className="text-sm font-medium">{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
}

// ============================================================================
// LOADING OVERLAY
// ============================================================================

function LoadingOverlay({ message = 'Processando...' }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 flex flex-col items-center gap-4 shadow-xl">
        <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
        <p className="text-gray-700 font-medium">{message}</p>
      </div>
    </div>
  );
}

// ============================================================================
// MULTI-TENANCY COMPONENTS
// ============================================================================

const OrganizationContext = createContext(null);

function OrganizationProvider({ children }) {
  const { api, user } = useAuth();
  const [organizations, setOrganizations] = useState([]);
  const [currentOrg, setCurrentOrg] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadOrganizations();
    }
  }, [user]);

  const loadOrganizations = async () => {
    try {
      const res = await api('/organizacoes');
      if (res.ok) {
        const data = await res.json();
        const orgs = data.organizacoes || [];
        setOrganizations(orgs);
        
        // Define organização padrão ou primeira
        const defaultOrg = orgs.find(o => o.is_default) || orgs[0];
        if (defaultOrg && !currentOrg) {
          setCurrentOrg(defaultOrg);
        }
      }
    } catch (err) {
      console.error('Erro ao carregar organizações:', err);
    } finally {
      setLoading(false);
    }
  };

  const switchOrganization = (org) => {
    setCurrentOrg(org);
    localStorage.setItem('currentOrgId', org.id);
  };

  const createOrganization = async (data) => {
    const res = await api('/organizacoes', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    if (res.ok) {
      await loadOrganizations();
      return await res.json();
    }
    throw new Error('Erro ao criar organização');
  };

  return (
    <OrganizationContext.Provider value={{
      organizations,
      currentOrg,
      loading,
      switchOrganization,
      createOrganization,
      refreshOrganizations: loadOrganizations
    }}>
      {children}
    </OrganizationContext.Provider>
  );
}

function useOrganization() {
  const context = useContext(OrganizationContext);
  if (!context) {
    return { organizations: [], currentOrg: null, loading: false };
  }
  return context;
}

function OrganizationSelector() {
  const { organizations, currentOrg, switchOrganization, createOrganization } = useOrganization();
  const [open, setOpen] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [creating, setCreating] = useState(false);

  if (!organizations || organizations.length === 0) {
    return null;
  }

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    
    setCreating(true);
    try {
      await createOrganization({ nome: newOrgName });
      setNewOrgName('');
      setShowCreate(false);
    } catch (err) {
      alert('Erro ao criar organização');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors"
      >
        <Building2 className="w-4 h-4 text-slate-600" />
        <span className="text-sm font-medium text-slate-700 max-w-[150px] truncate">
          {currentOrg?.nome || 'Selecionar'}
        </span>
        <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg shadow-lg border border-slate-200 z-50">
          <div className="p-2 border-b border-slate-100">
            <p className="text-xs text-slate-500 font-medium px-2">ORGANIZAÇÕES</p>
          </div>
          
          <div className="max-h-60 overflow-y-auto">
            {organizations.map(org => (
              <button
                key={org.id}
                onClick={() => {
                  switchOrganization(org);
                  setOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-3 py-2 hover:bg-slate-50 transition-colors ${
                  currentOrg?.id === org.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  currentOrg?.id === org.id ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'
                }`}>
                  {org.nome.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-slate-800">{org.nome}</p>
                  <p className="text-xs text-slate-500">{org.papel || 'Membro'}</p>
                </div>
                {currentOrg?.id === org.id && (
                  <CheckCircle className="w-4 h-4 text-blue-600" />
                )}
              </button>
            ))}
          </div>

          <div className="p-2 border-t border-slate-100">
            {!showCreate ? (
              <button
                onClick={() => setShowCreate(true)}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                Nova Organização
              </button>
            ) : (
              <form onSubmit={handleCreate} className="flex gap-2">
                <input
                  type="text"
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                  placeholder="Nome da organização"
                  className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={creating}
                  className="px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Criar'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function TeamMembersPage() {
  const { api } = useAuth();
  const { currentOrg } = useOrganization();
  const toast = useToast();
  const [members, setMembers] = useState([]);
  const [papeis, setPapeis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [invitePapel, setInvitePapel] = useState('');
  const [inviting, setInviting] = useState(false);

  useEffect(() => {
    if (currentOrg) {
      loadMembers();
      loadPapeis();
    }
  }, [currentOrg]);

  const loadMembers = async () => {
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/membros`);
      if (res.ok) {
        const data = await res.json();
        setMembers(data.membros || []);
      }
    } catch (err) {
      toast.error('Erro ao carregar membros');
    } finally {
      setLoading(false);
    }
  };

  const loadPapeis = async () => {
    try {
      const res = await api('/papeis');
      if (res.ok) {
        const data = await res.json();
        setPapeis(data.papeis || []);
      }
    } catch (err) {
      console.error('Erro ao carregar papéis:', err);
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail || !invitePapel) return;

    setInviting(true);
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/convites`, {
        method: 'POST',
        body: JSON.stringify({ email: inviteEmail, papel_id: parseInt(invitePapel) })
      });
      if (res.ok) {
        toast.success('Convite enviado!');
        setShowInvite(false);
        setInviteEmail('');
        setInvitePapel('');
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Erro ao enviar convite');
      }
    } catch (err) {
      toast.error('Erro ao enviar convite');
    } finally {
      setInviting(false);
    }
  };

  if (!currentOrg) {
    return (
      <div className="p-6">
        <Card className="p-8 text-center">
          <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Selecione uma organização</p>
        </Card>
      </div>
    );
  }

  if (loading) return <LoadingScreen />;

  return (
    <div>
      <Header 
        title="Equipe" 
        subtitle={`${members.length} membro(s) em ${currentOrg.nome}`}
        actions={
          <Button onClick={() => setShowInvite(true)}>
            <Plus className="w-4 h-4" /> Convidar
          </Button>
        }
      />

      <div className="grid gap-4">
        {members.map(m => (
          <Card key={m.id} className="p-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                {m.nome?.charAt(0).toUpperCase() || '?'}
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-slate-800">{m.nome}</h3>
                <p className="text-sm text-slate-500">{m.email}</p>
              </div>
              <Badge variant={m.papel_nivel >= 30 ? 'success' : m.papel_nivel >= 20 ? 'warning' : 'default'}>
                {m.papel_nome}
              </Badge>
            </div>
          </Card>
        ))}
      </div>

      <Modal isOpen={showInvite} onClose={() => setShowInvite(false)} title="Convidar Membro">
        <form onSubmit={handleInvite} className="space-y-4">
          <Input
            label="Email"
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="email@exemplo.com"
            required
          />
          <Select
            label="Papel"
            value={invitePapel}
            onChange={(e) => setInvitePapel(e.target.value)}
            required
          >
            <option value="">Selecione um papel</option>
            {papeis.filter(p => p.nivel < 99).map(p => (
              <option key={p.id} value={p.id}>{p.nome} - {p.descricao}</option>
            ))}
          </Select>
          <div className="flex gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={() => setShowInvite(false)} className="flex-1">
              Cancelar
            </Button>
            <Button type="submit" disabled={inviting} className="flex-1">
              {inviting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Enviar Convite'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

function AuditLogPage() {
  const { api } = useAuth();
  const { currentOrg } = useOrganization();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentOrg) {
      loadLogs();
    }
  }, [currentOrg]);

  const loadLogs = async () => {
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/audit?limite=100`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
      }
    } catch (err) {
      console.error('Erro ao carregar logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (acao) => {
    switch (acao) {
      case 'create': return <Plus className="w-4 h-4 text-green-600" />;
      case 'update': return <Edit className="w-4 h-4 text-blue-600" />;
      case 'delete': return <Trash2 className="w-4 h-4 text-red-600" />;
      case 'login': return <User className="w-4 h-4 text-purple-600" />;
      default: return <Activity className="w-4 h-4 text-slate-600" />;
    }
  };

  if (!currentOrg) {
    return (
      <div className="p-6">
        <Card className="p-8 text-center">
          <Activity className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Selecione uma organização</p>
        </Card>
      </div>
    );
  }

  if (loading) return <LoadingScreen />;

  return (
    <div>
      <Header 
        title="Logs de Auditoria" 
        subtitle={`Atividades em ${currentOrg.nome}`}
      />

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Ação</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Recurso</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Usuário</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Data</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map(log => (
                <tr key={log.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {getActionIcon(log.acao)}
                      <span className="text-sm font-medium text-slate-700 capitalize">{log.acao}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600 capitalize">{log.recurso}</td>
                  <td className="px-4 py-3 text-sm text-slate-600">{log.usuario_nome}</td>
                  <td className="px-4 py-3 text-sm text-slate-500">
                    {new Date(log.created_at).toLocaleString('pt-BR')}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400 font-mono">{log.ip_address || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

// ============================================================================
// BILLING COMPONENTS (F04)
// ============================================================================

function PlanosPage({ onSelectPlan }) {
  const { api } = useAuth();
  const { currentOrg, refreshOrganizations } = useOrganization();
  const toast = useToast();
  const [planos, setPlanos] = useState([]);
  const [assinatura, setAssinatura] = useState(null);
  const [loading, setLoading] = useState(true);
  const [ciclo, setCiclo] = useState('mensal');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    loadPlanos();
    if (currentOrg) loadAssinatura();
  }, [currentOrg]);

  const loadPlanos = async () => {
    try {
      const res = await api('/planos');
      if (res.ok) {
        const data = await res.json();
        setPlanos(data.planos || []);
      }
    } catch (err) {
      toast.error('Erro ao carregar planos');
    } finally {
      setLoading(false);
    }
  };

  const loadAssinatura = async () => {
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/assinatura`);
      if (res.ok) {
        const data = await res.json();
        setAssinatura(data.assinatura);
      }
    } catch (err) {
      console.error('Erro ao carregar assinatura:', err);
    }
  };

  const handleSelectPlan = async (plano) => {
    if (!currentOrg) {
      toast.error('Selecione uma organização primeiro');
      return;
    }

    setProcessing(true);
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/assinatura`, {
        method: 'POST',
        body: JSON.stringify({ plano: plano.codigo, ciclo })
      });
      
      if (res.ok) {
        toast.success(`Plano ${plano.nome} ativado!`);
        loadAssinatura();
        refreshOrganizations();
        if (onSelectPlan) onSelectPlan(plano);
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Erro ao selecionar plano');
      }
    } catch (err) {
      toast.error('Erro ao processar solicitação');
    } finally {
      setProcessing(false);
    }
  };

  const handleStartTrial = async () => {
    if (!currentOrg) {
      toast.error('Selecione uma organização primeiro');
      return;
    }

    setProcessing(true);
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/assinatura/trial`, {
        method: 'POST'
      });
      
      if (res.ok) {
        toast.success('Período de teste iniciado!');
        loadAssinatura();
        refreshOrganizations();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Erro ao iniciar teste');
      }
    } catch (err) {
      toast.error('Erro ao iniciar período de teste');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) return <LoadingScreen />;

  const planoAtual = assinatura?.plano?.codigo || 'free';

  return (
    <div>
      <Header 
        title="Planos e Preços" 
        subtitle="Escolha o plano ideal para seu escritório"
      />

      {/* Status atual */}
      {assinatura && (
        <Card className="p-4 mb-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Plano atual</p>
              <p className="text-xl font-bold text-slate-800">{assinatura.plano?.nome || 'Gratuito'}</p>
              {assinatura.is_trialing && (
                <p className="text-sm text-orange-600">
                  ⏰ {assinatura.dias_restantes_trial} dias restantes de teste
                </p>
              )}
            </div>
            <Badge variant={assinatura.is_active ? 'success' : 'warning'}>
              {assinatura.status_label}
            </Badge>
          </div>
        </Card>
      )}

      {/* Toggle mensal/anual */}
      <div className="flex justify-center mb-8">
        <div className="bg-slate-100 p-1 rounded-xl inline-flex">
          <button
            onClick={() => setCiclo('mensal')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
              ciclo === 'mensal' 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            Mensal
          </button>
          <button
            onClick={() => setCiclo('anual')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
              ciclo === 'anual' 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            Anual <span className="text-green-600 text-xs ml-1">-17%</span>
          </button>
        </div>
      </div>

      {/* Cards de planos */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {planos.map(plano => {
          const preco = ciclo === 'mensal' ? plano.preco_mensal : plano.preco_anual / 12;
          const isAtual = plano.codigo === planoAtual;
          const isPopular = plano.codigo === 'pro';

          return (
            <Card 
              key={plano.id} 
              className={`p-6 relative ${isPopular ? 'border-2 border-blue-500 shadow-lg' : ''} ${isAtual ? 'ring-2 ring-green-500' : ''}`}
            >
              {isPopular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                    POPULAR
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-slate-800">{plano.nome}</h3>
                <p className="text-sm text-slate-500 mt-1">{plano.descricao}</p>
                
                <div className="mt-4">
                  <span className="text-4xl font-bold text-slate-800">
                    R$ {preco.toFixed(0)}
                  </span>
                  <span className="text-slate-500">/mês</span>
                </div>
                
                {ciclo === 'anual' && plano.economia_anual > 0 && (
                  <p className="text-sm text-green-600 mt-1">
                    Economia de R$ {plano.economia_anual.toFixed(0)}/ano
                  </p>
                )}
              </div>

              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>{plano.limites.usuarios} usuário(s)</span>
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>{plano.limites.empresas} empresa(s)</span>
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>{plano.limites.analises_mes} análises/mês</span>
                </li>
                {plano.features.api && (
                  <li className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Acesso API</span>
                  </li>
                )}
                {plano.features.whitelabel && (
                  <li className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>White-label</span>
                  </li>
                )}
                {plano.features.suporte_prioritario && (
                  <li className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Suporte prioritário</span>
                  </li>
                )}
              </ul>

              {isAtual ? (
                <Button disabled className="w-full" variant="secondary">
                  Plano Atual
                </Button>
              ) : plano.codigo === 'free' ? (
                <Button 
                  className="w-full" 
                  variant="secondary"
                  disabled={processing}
                >
                  Gratuito
                </Button>
              ) : (
                <Button 
                  onClick={() => handleSelectPlan(plano)}
                  className="w-full"
                  disabled={processing}
                >
                  {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Assinar'}
                </Button>
              )}
            </Card>
          );
        })}
      </div>

      {/* CTA Trial */}
      {planoAtual === 'free' && !assinatura?.is_trialing && (
        <Card className="p-6 mt-8 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-center">
          <h3 className="text-2xl font-bold mb-2">Teste grátis por 14 dias</h3>
          <p className="text-purple-100 mb-4">
            Experimente o plano Profissional sem compromisso
          </p>
          <Button 
            onClick={handleStartTrial}
            disabled={processing}
            className="bg-white text-purple-600 hover:bg-purple-50"
          >
            {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Começar teste grátis'}
          </Button>
        </Card>
      )}
    </div>
  );
}

function FaturasPage() {
  const { api } = useAuth();
  const { currentOrg } = useOrganization();
  const [faturas, setFaturas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentOrg) loadFaturas();
  }, [currentOrg]);

  const loadFaturas = async () => {
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/faturas`);
      if (res.ok) {
        const data = await res.json();
        setFaturas(data.faturas || []);
      }
    } catch (err) {
      console.error('Erro ao carregar faturas:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      paid: 'text-green-600 bg-green-50',
      pending: 'text-yellow-600 bg-yellow-50',
      failed: 'text-red-600 bg-red-50',
      refunded: 'text-purple-600 bg-purple-50'
    };
    return colors[status] || 'text-slate-600 bg-slate-50';
  };

  if (!currentOrg) {
    return (
      <div className="p-6">
        <Card className="p-8 text-center">
          <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Selecione uma organização</p>
        </Card>
      </div>
    );
  }

  if (loading) return <LoadingScreen />;

  return (
    <div>
      <Header 
        title="Faturas" 
        subtitle={`Histórico de pagamentos de ${currentOrg.nome}`}
      />

      {faturas.length === 0 ? (
        <Card className="p-8 text-center">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Nenhuma fatura encontrada</p>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Número</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Período</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Valor</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Vencimento</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {faturas.map(fatura => (
                  <tr key={fatura.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 text-sm font-medium text-slate-800">
                      {fatura.numero}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {fatura.periodo_inicio && new Date(fatura.periodo_inicio).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="px-4 py-3 text-sm font-semibold text-slate-800">
                      {fatura.valor_formatado}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(fatura.status)}`}>
                        {fatura.status_label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-500">
                      {new Date(fatura.data_vencimento).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="px-4 py-3">
                      {fatura.pdf_url && (
                        <a 
                          href={fatura.pdf_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                        >
                          <Download className="w-4 h-4 inline mr-1" />
                          PDF
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

function UsoPage() {
  const { api } = useAuth();
  const { currentOrg } = useOrganization();
  const [uso, setUso] = useState(null);
  const [assinatura, setAssinatura] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentOrg) {
      loadUso();
      loadAssinatura();
    }
  }, [currentOrg]);

  const loadUso = async () => {
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/uso`);
      if (res.ok) {
        const data = await res.json();
        setUso(data.uso);
      }
    } catch (err) {
      console.error('Erro ao carregar uso:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadAssinatura = async () => {
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/assinatura`);
      if (res.ok) {
        const data = await res.json();
        setAssinatura(data.assinatura);
      }
    } catch (err) {
      console.error('Erro ao carregar assinatura:', err);
    }
  };

  if (!currentOrg) {
    return (
      <div className="p-6">
        <Card className="p-8 text-center">
          <BarChart3 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Selecione uma organização</p>
        </Card>
      </div>
    );
  }

  if (loading) return <LoadingScreen />;

  const limites = assinatura?.plano?.limites || {};

  const calcPercent = (atual, max) => Math.min(100, (atual / max) * 100);

  const UsageBar = ({ label, atual, max, icon: Icon }) => {
    const percent = calcPercent(atual, max);
    const isNearLimit = percent >= 80;

    return (
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <div className="flex items-center gap-2">
            <Icon className="w-4 h-4 text-slate-500" />
            <span className="text-sm font-medium text-slate-700">{label}</span>
          </div>
          <span className={`text-sm ${isNearLimit ? 'text-orange-600 font-semibold' : 'text-slate-500'}`}>
            {atual} / {max}
          </span>
        </div>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full transition-all ${
              isNearLimit ? 'bg-orange-500' : 'bg-blue-500'
            }`}
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <div>
      <Header 
        title="Uso e Limites" 
        subtitle={`Consumo de ${currentOrg.nome} em ${uso?.periodo || 'mês atual'}`}
      />

      <div className="grid md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="font-semibold text-slate-800 mb-4">Recursos</h3>
          
          <UsageBar 
            label="Empresas" 
            atual={uso?.empresas_ativas || 0} 
            max={limites.empresas || 5}
            icon={Building2}
          />
          <UsageBar 
            label="Usuários" 
            atual={uso?.usuarios_ativos || 0} 
            max={limites.usuarios || 1}
            icon={Users}
          />
          <UsageBar 
            label="Análises" 
            atual={uso?.analises_realizadas || 0} 
            max={limites.analises_mes || 10}
            icon={BarChart3}
          />
          <UsageBar 
            label="Storage (MB)" 
            atual={uso?.storage_usado_mb?.toFixed(1) || 0} 
            max={limites.storage_mb || 100}
            icon={FileText}
          />
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold text-slate-800 mb-4">Atividade</h3>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center py-3 border-b border-slate-100">
              <span className="text-slate-600">Relatórios gerados</span>
              <span className="font-semibold text-slate-800">{uso?.relatorios_gerados || 0}</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-slate-100">
              <span className="text-slate-600">Chamadas API</span>
              <span className="font-semibold text-slate-800">{uso?.api_calls || 0}</span>
            </div>
            <div className="flex justify-between items-center py-3">
              <span className="text-slate-600">Período</span>
              <span className="font-semibold text-slate-800">{uso?.periodo || '-'}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

// ============================================================================
// RELATÓRIOS PRO (F09)
// ============================================================================

function RelatoriosPage({ onNavigate }) {
  const { api } = useAuth();
  const toast = useToast();
  const themeCtx = useTheme();
  
  const [activeTab, setActiveTab] = useState('gerar');
  const [empresas, setEmpresas] = useState([]);
  const [empresaSelecionada, setEmpresaSelecionada] = useState(null);
  const [config, setConfig] = useState({
    nome_escritorio: '',
    cor_primaria: '#1e40af',
    cor_secundaria: '#3b82f6',
    cor_destaque: '#059669',
    mostrar_logo: true,
    mostrar_graficos: true,
    mostrar_recomendacoes: true,
    template_padrao: 'executivo',
    telefone: '',
    email_contato: '',
    website: '',
    texto_rodape: ''
  });
  const [historico, setHistorico] = useState([]);
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [gerando, setGerando] = useState(null);
  
  // Modal para criar link
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [linkConfig, setLinkConfig] = useState({
    tipo_relatorio: 'pdf',
    template: 'executivo',
    permite_download: true,
    requer_senha: false,
    senha: '',
    expira_em_dias: 7,
    max_acessos: null
  });
  const [linkCriado, setLinkCriado] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [empRes, configRes, histRes, linksRes] = await Promise.all([
        api('/empresas'),
        api('/relatorios/configuracao'),
        api('/relatorios/historico?limite=10'),
        api('/relatorios/links')
      ]);
      
      if (empRes.ok) {
        const data = await empRes.json();
        setEmpresas(data.empresas || []);
      }
      
      if (configRes.ok) {
        const data = await configRes.json();
        setConfig(prev => ({ ...prev, ...data }));
      }
      
      if (histRes.ok) {
        const data = await histRes.json();
        setHistorico(data.historico || []);
      }
      
      if (linksRes.ok) {
        const data = await linksRes.json();
        setLinks(data.links || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const salvarConfiguracao = async () => {
    try {
      const res = await api('/relatorios/configuracao', {
        method: 'PUT',
        body: JSON.stringify(config)
      });
      
      if (res.ok) {
        toast.success('Configuração salva com sucesso!');
        
        // Atualizar tema global imediatamente
        if (themeCtx?.updateTheme) {
          themeCtx.updateTheme({
            cor_primaria: config.cor_primaria,
            cor_secundaria: config.cor_secundaria,
            cor_destaque: config.cor_destaque,
            nome_escritorio: config.nome_escritorio
          });
        }
      } else {
        toast.error('Erro ao salvar configuração');
      }
    } catch (err) {
      toast.error('Erro ao salvar');
    }
  };

  const gerarRelatorio = async (tipo) => {
    if (!empresaSelecionada) {
      toast.warning('Selecione uma empresa');
      return;
    }
    
    setGerando(tipo);
    
    try {
      const res = await api(`/empresas/${empresaSelecionada}/relatorios/${tipo}`, {
        method: 'POST'
      });
      
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        const extensoes = { pdf: 'pdf', excel: 'xlsx', pptx: 'pptx' };
        const empresa = empresas.find(e => e.id === empresaSelecionada);
        a.download = `relatorio_${empresa?.razao_social?.substring(0, 20) || 'empresa'}.${extensoes[tipo]}`;
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        toast.success(`Relatório ${tipo.toUpperCase()} gerado!`);
        loadData(); // Atualiza histórico
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Erro ao gerar relatório');
      }
    } catch (err) {
      toast.error('Erro ao gerar relatório');
    } finally {
      setGerando(null);
    }
  };

  const criarLink = async () => {
    if (!empresaSelecionada) {
      toast.warning('Selecione uma empresa');
      return;
    }
    
    try {
      const res = await api(`/empresas/${empresaSelecionada}/relatorios/link`, {
        method: 'POST',
        body: JSON.stringify(linkConfig)
      });
      
      if (res.ok) {
        const data = await res.json();
        setLinkCriado(data);
        toast.success('Link criado com sucesso!');
        loadData();
      } else {
        toast.error('Erro ao criar link');
      }
    } catch (err) {
      toast.error('Erro ao criar link');
    }
  };

  const desativarLink = async (token) => {
    try {
      const res = await api(`/relatorios/links/${token}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Link desativado');
        loadData();
      }
    } catch (err) {
      toast.error('Erro ao desativar link');
    }
  };

  const copiarLink = (url) => {
    navigator.clipboard.writeText(url);
    toast.success('Link copiado!');
  };

  if (loading) return <LoadingScreen />;

  return (
    <div>
      <Header 
        title="Relatórios" 
        subtitle="Gere relatórios profissionais em PDF, Excel e PowerPoint"
      />

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-100 p-1 rounded-lg w-fit">
        {[
          { id: 'gerar', label: 'Gerar Relatório' },
          { id: 'config', label: 'Configuração' },
          { id: 'historico', label: 'Histórico' },
          { id: 'links', label: 'Links' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id 
                ? 'bg-white text-slate-900 shadow-sm' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab: Gerar Relatório */}
      {activeTab === 'gerar' && (
        <div className="space-y-6">
          {/* Seleção de empresa */}
          <Card className="p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Selecione a Empresa</h3>
            <select
              value={empresaSelecionada || ''}
              onChange={(e) => setEmpresaSelecionada(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Selecione...</option>
              {empresas.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.razao_social}</option>
              ))}
            </select>
          </Card>

          {/* Tipos de relatório */}
          {empresaSelecionada && (
            <div className="grid md:grid-cols-3 gap-4">
              {/* PDF */}
              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="text-center">
                  <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <FileText className="w-8 h-8 text-red-600" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">Relatório PDF</h3>
                  <p className="text-sm text-slate-500 mb-4">Relatório financeiro completo com análises</p>
                  <Button 
                    onClick={() => gerarRelatorio('pdf')}
                    disabled={gerando === 'pdf'}
                    className="w-full"
                  >
                    {gerando === 'pdf' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                    {gerando === 'pdf' ? 'Gerando...' : 'Baixar PDF'}
                  </Button>
                </div>
              </Card>

              {/* Excel */}
              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <FileSpreadsheet className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">Planilha Excel</h3>
                  <p className="text-sm text-slate-500 mb-4">Dados e indicadores em formato editável</p>
                  <Button 
                    onClick={() => gerarRelatorio('excel')}
                    disabled={gerando === 'excel'}
                    variant="secondary"
                    className="w-full"
                  >
                    {gerando === 'excel' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                    {gerando === 'excel' ? 'Gerando...' : 'Baixar Excel'}
                  </Button>
                </div>
              </Card>

              {/* PowerPoint */}
              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="text-center">
                  <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <PieChartIcon className="w-8 h-8 text-orange-600" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">Apresentação</h3>
                  <p className="text-sm text-slate-500 mb-4">Slides prontos para apresentar ao cliente</p>
                  <Button 
                    onClick={() => gerarRelatorio('pptx')}
                    disabled={gerando === 'pptx'}
                    variant="secondary"
                    className="w-full"
                  >
                    {gerando === 'pptx' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                    {gerando === 'pptx' ? 'Gerando...' : 'Baixar PPTX'}
                  </Button>
                </div>
              </Card>
            </div>
          )}

          {/* Link compartilhável */}
          {empresaSelecionada && (
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-900">Link Compartilhável</h3>
                <Button size="sm" variant="secondary" onClick={() => setShowLinkModal(true)}>
                  <Plus className="w-4 h-4" /> Criar Link
                </Button>
              </div>
              <p className="text-sm text-slate-500">
                Crie um link temporário para compartilhar o relatório com seu cliente, sem necessidade de login.
              </p>
            </Card>
          )}
        </div>
      )}

      {/* Tab: Configuração */}
      {activeTab === 'config' && (
        <Card className="p-6">
          <h3 className="font-semibold text-slate-900 mb-6">Personalização (White-Label)</h3>
          
          <div className="grid md:grid-cols-2 gap-6">
            {/* Nome do escritório */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Nome do Escritório</label>
              <input
                type="text"
                value={config.nome_escritorio}
                onChange={(e) => setConfig({ ...config, nome_escritorio: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                placeholder="Seu Escritório Contábil"
              />
            </div>

            {/* Telefone */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Telefone</label>
              <input
                type="text"
                value={config.telefone}
                onChange={(e) => setConfig({ ...config, telefone: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                placeholder="(11) 99999-9999"
              />
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email de Contato</label>
              <input
                type="email"
                value={config.email_contato}
                onChange={(e) => setConfig({ ...config, email_contato: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                placeholder="contato@escritorio.com"
              />
            </div>

            {/* Website */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Website</label>
              <input
                type="text"
                value={config.website}
                onChange={(e) => setConfig({ ...config, website: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                placeholder="www.seuescritorio.com.br"
              />
            </div>

            {/* Cores */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Cor Primária</label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={config.cor_primaria}
                  onChange={(e) => setConfig({ ...config, cor_primaria: e.target.value })}
                  className="w-12 h-10 border border-slate-200 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={config.cor_primaria}
                  onChange={(e) => setConfig({ ...config, cor_primaria: e.target.value })}
                  className="flex-1 px-3 py-2 border border-slate-200 rounded-lg"
                />
              </div>
            </div>

            {/* Cor secundária */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Cor Secundária</label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={config.cor_secundaria}
                  onChange={(e) => setConfig({ ...config, cor_secundaria: e.target.value })}
                  className="w-12 h-10 border border-slate-200 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={config.cor_secundaria}
                  onChange={(e) => setConfig({ ...config, cor_secundaria: e.target.value })}
                  className="flex-1 px-3 py-2 border border-slate-200 rounded-lg"
                />
              </div>
            </div>

            {/* Texto do rodapé */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">Texto do Rodapé</label>
              <textarea
                value={config.texto_rodape}
                onChange={(e) => setConfig({ ...config, texto_rodape: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                rows={2}
                placeholder="Texto personalizado para aparecer no rodapé dos relatórios"
              />
            </div>

            {/* Opções */}
            <div className="md:col-span-2 space-y-3">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.mostrar_graficos}
                  onChange={(e) => setConfig({ ...config, mostrar_graficos: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm text-slate-700">Incluir gráficos nos relatórios</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.mostrar_recomendacoes}
                  onChange={(e) => setConfig({ ...config, mostrar_recomendacoes: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm text-slate-700">Incluir recomendações e plano de ação</span>
              </label>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t flex justify-end">
            <Button onClick={salvarConfiguracao}>
              <Check className="w-4 h-4" /> Salvar Configuração
            </Button>
          </div>
        </Card>
      )}

      {/* Tab: Histórico */}
      {activeTab === 'historico' && (
        <Card className="p-6">
          <h3 className="font-semibold text-slate-900 mb-4">Histórico de Relatórios</h3>
          
          {historico.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-slate-500 border-b">
                    <th className="pb-3 font-medium">Empresa</th>
                    <th className="pb-3 font-medium">Tipo</th>
                    <th className="pb-3 font-medium">Data</th>
                    <th className="pb-3 font-medium">Tamanho</th>
                  </tr>
                </thead>
                <tbody>
                  {historico.map(item => (
                    <tr key={item.id} className="border-b last:border-0">
                      <td className="py-3 font-medium">{item.empresa_nome}</td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          item.tipo === 'pdf' ? 'bg-red-100 text-red-700' :
                          item.tipo === 'excel' ? 'bg-green-100 text-green-700' :
                          'bg-orange-100 text-orange-700'
                        }`}>
                          {item.tipo?.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 text-sm text-slate-500">
                        {new Date(item.created_at).toLocaleDateString('pt-BR')}
                      </td>
                      <td className="py-3 text-sm text-slate-500">
                        {item.arquivo_tamanho ? `${(item.arquivo_tamanho / 1024).toFixed(0)} KB` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState 
              icon={FileText}
              title="Nenhum relatório gerado"
              description="Gere seu primeiro relatório na aba 'Gerar Relatório'"
            />
          )}
        </Card>
      )}

      {/* Tab: Links */}
      {activeTab === 'links' && (
        <Card className="p-6">
          <h3 className="font-semibold text-slate-900 mb-4">Links Compartilháveis Ativos</h3>
          
          {links.length > 0 ? (
            <div className="space-y-4">
              {links.map(link => (
                <div key={link.id} className="p-4 border border-slate-200 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">{link.empresa_nome}</p>
                      <p className="text-sm text-slate-500 mt-1">
                        Tipo: {link.tipo_relatorio?.toUpperCase()} | 
                        Acessos: {link.acessos}{link.max_acessos ? `/${link.max_acessos}` : ''}
                      </p>
                      {link.expira_em && (
                        <p className="text-xs text-slate-400 mt-1">
                          Expira em: {new Date(link.expira_em).toLocaleDateString('pt-BR')}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="secondary" onClick={() => copiarLink(link.url)}>
                        Copiar Link
                      </Button>
                      <Button size="sm" variant="danger" onClick={() => desativarLink(link.token)}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="mt-2 p-2 bg-slate-50 rounded text-sm text-slate-600 break-all">
                    {link.url}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState 
              icon={FileText}
              title="Nenhum link ativo"
              description="Crie links compartilháveis para enviar relatórios aos seus clientes"
            />
          )}
        </Card>
      )}

      {/* Modal criar link */}
      {showLinkModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg">Criar Link Compartilhável</h3>
              <button onClick={() => { setShowLinkModal(false); setLinkCriado(null); }}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            {linkCriado ? (
              <div className="space-y-4">
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-green-800 font-medium mb-2">Link criado com sucesso!</p>
                  <p className="text-sm text-green-700 break-all">{linkCriado.url}</p>
                </div>
                <Button className="w-full" onClick={() => copiarLink(linkCriado.url)}>
                  Copiar Link
                </Button>
                <Button className="w-full" variant="secondary" onClick={() => { setShowLinkModal(false); setLinkCriado(null); }}>
                  Fechar
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Tipo de Relatório</label>
                  <select
                    value={linkConfig.tipo_relatorio}
                    onChange={(e) => setLinkConfig({ ...linkConfig, tipo_relatorio: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                  >
                    <option value="pdf">PDF</option>
                    <option value="excel">Excel</option>
                    <option value="pptx">PowerPoint</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Expira em (dias)</label>
                  <input
                    type="number"
                    value={linkConfig.expira_em_dias || ''}
                    onChange={(e) => setLinkConfig({ ...linkConfig, expira_em_dias: e.target.value ? parseInt(e.target.value) : null })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                    placeholder="Ex: 7 (deixe vazio para não expirar)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Máximo de acessos</label>
                  <input
                    type="number"
                    value={linkConfig.max_acessos || ''}
                    onChange={(e) => setLinkConfig({ ...linkConfig, max_acessos: e.target.value ? parseInt(e.target.value) : null })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                    placeholder="Ex: 10 (deixe vazio para ilimitado)"
                  />
                </div>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={linkConfig.requer_senha}
                    onChange={(e) => setLinkConfig({ ...linkConfig, requer_senha: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm text-slate-700">Proteger com senha</span>
                </label>

                {linkConfig.requer_senha && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Senha</label>
                    <input
                      type="password"
                      value={linkConfig.senha}
                      onChange={(e) => setLinkConfig({ ...linkConfig, senha: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                    />
                  </div>
                )}

                <div className="flex gap-2 pt-2">
                  <Button className="flex-1" onClick={criarLink}>
                    Criar Link
                  </Button>
                  <Button variant="secondary" onClick={() => setShowLinkModal(false)}>
                    Cancelar
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// ALERTAS INTELIGENTES (F06)
// ============================================================================

function AlertasPage({ onNavigate }) {
  const { api } = useAuth();
  const toast = useToast();
  
  const [tab, setTab] = useState('alertas');
  const [alertas, setAlertas] = useState([]);
  const [resumo, setResumo] = useState({
    total: 0,
    nao_lidos: 0,
    por_severidade: { critico: 0, atencao: 0, info: 0 },
    alertas_criticos: [],
    por_empresa: []
  });
  const [empresas, setEmpresas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [gerando, setGerando] = useState(false);
  
  // Filtros
  const [filtroEmpresa, setFiltroEmpresa] = useState('');
  const [filtroSeveridade, setFiltroSeveridade] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('');
  const [apenasNaoLidos, setApenasNaoLidos] = useState(false);
  
  // Configuração de empresa selecionada
  const [empresaSelecionada, setEmpresaSelecionada] = useState(null);
  const [configEmpresa, setConfigEmpresa] = useState(null);
  const [salvandoConfig, setSalvandoConfig] = useState(false);
  
  useEffect(() => {
    loadData();
  }, []);
  
  useEffect(() => {
    loadAlertas();
  }, [filtroEmpresa, filtroSeveridade, filtroTipo, apenasNaoLidos]);
  
  const loadData = async () => {
    setLoading(true);
    try {
      const [resResumo, resEmpresas] = await Promise.all([
        api('/alertas/resumo'),
        api('/empresas')
      ]);
      
      // Parse JSON das respostas
      const dataResumo = await resResumo.json();
      const dataEmpresas = await resEmpresas.json();
      
      // Garantir estrutura do resumo
      setResumo({
        total: dataResumo?.total || 0,
        nao_lidos: dataResumo?.nao_lidos || 0,
        por_severidade: {
          critico: dataResumo?.por_severidade?.critico || 0,
          atencao: dataResumo?.por_severidade?.atencao || 0,
          info: dataResumo?.por_severidade?.info || 0
        },
        alertas_criticos: dataResumo?.alertas_criticos || [],
        por_empresa: dataResumo?.por_empresa || []
      });
      // Garantir que empresas seja array
      const listaEmpresas = dataEmpresas?.empresas || dataEmpresas;
      setEmpresas(Array.isArray(listaEmpresas) ? listaEmpresas : []);
    } catch (err) {
      console.error(err);
    }
    await loadAlertas();
    setLoading(false);
  };
  
  const loadAlertas = async () => {
    try {
      let url = '/alertas?limite=100';
      if (filtroEmpresa) url += `&empresa_id=${filtroEmpresa}`;
      if (filtroSeveridade) url += `&severidade=${filtroSeveridade}`;
      if (filtroTipo) url += `&tipo=${filtroTipo}`;
      if (apenasNaoLidos) url += '&apenas_nao_lidos=true';
      
      const res = await api(url);
      const data = await res.json();
      // Garantir que alertas seja array
      const listaAlertas = data?.alertas || data;
      setAlertas(Array.isArray(listaAlertas) ? listaAlertas : []);
    } catch (err) {
      console.error(err);
      setAlertas([]);
    }
  };
  
  const loadConfigEmpresa = async (empresaId) => {
    try {
      const res = await api(`/empresas/${empresaId}/alertas/configuracao`);
      const data = await res.json();
      setConfigEmpresa(data);
    } catch (err) {
      console.error(err);
      setConfigEmpresa(null);
    }
  };
  
  const gerarAlertasTodos = async () => {
    setGerando(true);
    try {
      const res = await api('/alertas/gerar-todos', { method: 'POST' });
      const data = await res.json();
      toast.success(`${data.total_alertas_salvos || 0} novos alertas gerados!`);
      await loadData();
    } catch (err) {
      toast.error('Erro ao gerar alertas');
    }
    setGerando(false);
  };
  
  // Helper para garantir estrutura do resumo
  const parseResumo = (res) => ({
    total: res?.total || 0,
    nao_lidos: res?.nao_lidos || 0,
    por_severidade: {
      critico: res?.por_severidade?.critico || 0,
      atencao: res?.por_severidade?.atencao || 0,
      info: res?.por_severidade?.info || 0
    },
    alertas_criticos: res?.alertas_criticos || [],
    por_empresa: res?.por_empresa || []
  });
  
  const gerarAlertasEmpresa = async (empresaId) => {
    setGerando(true);
    try {
      const res = await api(`/empresas/${empresaId}/alertas/gerar`, { method: 'POST' });
      const data = await res.json();
      toast.success(`${data.alertas_salvos || 0} novos alertas gerados!`);
      await loadAlertas();
      const resResumo = await api('/alertas/resumo');
      const dataResumo = await resResumo.json();
      setResumo(parseResumo(dataResumo));
    } catch (err) {
      toast.error('Erro ao gerar alertas');
    }
    setGerando(false);
  };
  
  const marcarLido = async (alertaId) => {
    try {
      await api(`/alertas/${alertaId}/lido`, { method: 'POST' });
      await loadAlertas();
      const resResumo = await api('/alertas/resumo');
      const dataResumo = await resResumo.json();
      setResumo(parseResumo(dataResumo));
    } catch (err) {
      toast.error('Erro ao marcar como lido');
    }
  };
  
  const resolverAlerta = async (alertaId, nota = '') => {
    try {
      await api(`/alertas/${alertaId}/resolver`, { 
        method: 'POST',
        body: JSON.stringify({ nota })
      });
      toast.success('Alerta resolvido!');
      await loadAlertas();
      const resResumo = await api('/alertas/resumo');
      const dataResumo = await resResumo.json();
      setResumo(parseResumo(dataResumo));
    } catch (err) {
      toast.error('Erro ao resolver alerta');
    }
  };
  
  const marcarTodosLidos = async () => {
    try {
      await api('/alertas/marcar-todos-lidos', { method: 'POST' });
      toast.success('Todos os alertas marcados como lidos');
      await loadAlertas();
      const resResumo = await api('/alertas/resumo');
      const dataResumo = await resResumo.json();
      setResumo(parseResumo(dataResumo));
    } catch (err) {
      toast.error('Erro ao marcar alertas');
    }
  };
  
  const salvarConfigEmpresa = async () => {
    if (!empresaSelecionada || !configEmpresa) return;
    
    setSalvandoConfig(true);
    try {
      await api(`/empresas/${empresaSelecionada}/alertas/configuracao`, {
        method: 'PUT',
        body: JSON.stringify(configEmpresa)
      });
      toast.success('Configuração salva!');
    } catch (err) {
      toast.error('Erro ao salvar configuração');
    }
    setSalvandoConfig(false);
  };
  
  const getSeveridadeStyle = (sev) => {
    switch (sev) {
      case 'critico': return 'bg-red-100 text-red-800 border-red-200';
      case 'atencao': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getSeveridadeIcon = (sev) => {
    switch (sev) {
      case 'critico': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'atencao': return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'info': return <Info className="w-5 h-5 text-blue-500" />;
      default: return <Bell className="w-5 h-5 text-gray-500" />;
    }
  };
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }
  
  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alertas Inteligentes</h1>
          <p className="text-gray-500">Monitore a saúde financeira das suas empresas</p>
        </div>
        <button
          onClick={gerarAlertasTodos}
          disabled={gerando}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {gerando ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          Verificar Todas
        </button>
      </div>
      
      {/* Cards de Resumo */}
      {resumo && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total de Alertas</p>
                <p className="text-2xl font-bold">{resumo.total || 0}</p>
              </div>
              <Bell className="w-8 h-8 text-gray-400" />
            </div>
          </Card>
          
          <Card className={`p-4 ${(resumo.por_severidade?.critico || 0) > 0 ? 'border-red-300 bg-red-50' : ''}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Críticos</p>
                <p className="text-2xl font-bold text-red-600">{resumo.por_severidade?.critico || 0}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </div>
          </Card>
          
          <Card className={`p-4 ${(resumo.por_severidade?.atencao || 0) > 0 ? 'border-yellow-300 bg-yellow-50' : ''}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Atenção</p>
                <p className="text-2xl font-bold text-yellow-600">{resumo.por_severidade?.atencao || 0}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-yellow-400" />
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Não Lidos</p>
                <p className="text-2xl font-bold text-blue-600">{resumo.nao_lidos || 0}</p>
              </div>
              <Eye className="w-8 h-8 text-blue-400" />
            </div>
          </Card>
        </div>
      )}
      
      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-4">
          {[
            { id: 'alertas', label: 'Alertas', icon: Bell },
            { id: 'configuracao', label: 'Configuração', icon: Settings },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                tab === t.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <t.icon className="w-4 h-4" />
              {t.label}
            </button>
          ))}
        </nav>
      </div>
      
      {/* Tab: Alertas */}
      {tab === 'alertas' && (
        <div className="space-y-4">
          {/* Filtros */}
          <Card className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <select
                value={filtroEmpresa}
                onChange={(e) => setFiltroEmpresa(e.target.value)}
                className="px-3 py-2 border rounded-lg"
              >
                <option value="">Todas as empresas</option>
                {(empresas || []).map(e => (
                  <option key={e.id} value={e.id}>{e.razao_social}</option>
                ))}
              </select>
              
              <select
                value={filtroSeveridade}
                onChange={(e) => setFiltroSeveridade(e.target.value)}
                className="px-3 py-2 border rounded-lg"
              >
                <option value="">Todas as severidades</option>
                <option value="critico">🔴 Crítico</option>
                <option value="atencao">🟡 Atenção</option>
                <option value="info">🔵 Informativo</option>
              </select>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={apenasNaoLidos}
                  onChange={(e) => setApenasNaoLidos(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">Apenas não lidos</span>
              </label>
              
              <div className="flex-1" />
              
              <button
                onClick={marcarTodosLidos}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Marcar todos como lidos
              </button>
            </div>
          </Card>
          
          {/* Lista de Alertas */}
          <div className="space-y-3">
            {(!alertas || alertas.length === 0) ? (
              <Card className="p-8 text-center">
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900">Nenhum alerta encontrado</h3>
                <p className="text-gray-500 mt-1">Todas as empresas estão com a saúde financeira em dia!</p>
              </Card>
            ) : (
              (alertas || []).map(alerta => (
                <Card 
                  key={alerta.id} 
                  className={`p-4 border-l-4 ${
                    alerta.severidade === 'critico' ? 'border-l-red-500' :
                    alerta.severidade === 'atencao' ? 'border-l-yellow-500' :
                    'border-l-blue-500'
                  } ${!alerta.lido ? 'bg-blue-50/30' : ''}`}
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 mt-1">
                      {getSeveridadeIcon(alerta.severidade)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getSeveridadeStyle(alerta.severidade)}`}>
                          {alerta.severidade?.toUpperCase()}
                        </span>
                        <span className="text-sm text-gray-500">{alerta.empresa_nome}</span>
                        {!alerta.lido && (
                          <span className="w-2 h-2 bg-blue-500 rounded-full" title="Não lido" />
                        )}
                      </div>
                      
                      <h4 className="font-medium text-gray-900">{alerta.titulo}</h4>
                      <p className="text-sm text-gray-600 mt-1">{alerta.mensagem}</p>
                      
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>{formatDate(alerta.created_at)}</span>
                        {alerta.periodo_referencia && (
                          <span>Período: {alerta.periodo_referencia}</span>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {!alerta.lido && (
                        <button
                          onClick={() => marcarLido(alerta.id)}
                          className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50"
                          title="Marcar como lido"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => resolverAlerta(alerta.id)}
                        className="p-2 text-gray-400 hover:text-green-600 rounded-lg hover:bg-green-50"
                        title="Resolver alerta"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}
      
      {/* Tab: Configuração */}
      {tab === 'configuracao' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Lista de Empresas */}
          <Card className="p-4">
            <h3 className="font-medium mb-4">Selecione uma empresa</h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {(empresas || []).map(e => (
                <button
                  key={e.id}
                  onClick={() => {
                    setEmpresaSelecionada(e.id);
                    loadConfigEmpresa(e.id);
                  }}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    empresaSelecionada === e.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium">{e.razao_social}</div>
                  <div className="text-sm text-gray-500">{e.cnpj || 'Sem CNPJ'}</div>
                </button>
              ))}
            </div>
          </Card>
          
          {/* Configuração da Empresa */}
          <Card className="lg:col-span-2 p-6">
            {!empresaSelecionada ? (
              <div className="text-center py-8 text-gray-500">
                <Settings className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Selecione uma empresa para configurar os alertas</p>
              </div>
            ) : !configEmpresa ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="font-medium text-lg">Configuração de Alertas</h3>
                  <button
                    onClick={() => gerarAlertasEmpresa(empresaSelecionada)}
                    disabled={gerando}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
                  >
                    {gerando ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                    Verificar Agora
                  </button>
                </div>
                
                {/* Alertas de Caixa */}
                <div className="border rounded-lg p-4 bg-gradient-to-r from-amber-50 to-white">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                        <DollarSign className="w-5 h-5 text-amber-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">Alertas de Caixa</h4>
                        <p className="text-xs text-gray-500">Monitora a saúde financeira de curto prazo</p>
                      </div>
                    </div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={configEmpresa.alerta_caixa_ativo}
                        onChange={(e) => setConfigEmpresa({...configEmpresa, alerta_caixa_ativo: e.target.checked})}
                        className="rounded text-amber-600 focus:ring-amber-500"
                      />
                      <span className="text-sm font-medium">Ativo</span>
                    </label>
                  </div>
                  {configEmpresa.alerta_caixa_ativo && (
                    <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="w-4 h-4 text-red-500" />
                          <label className="text-sm font-medium text-gray-700">Dias crítico</label>
                        </div>
                        <input
                          type="number"
                          value={configEmpresa.caixa_dias_critico}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, caixa_dias_critico: parseInt(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">⚠️ Alerta CRÍTICO se o caixa cobrir menos de X dias de operação</p>
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <AlertCircle className="w-4 h-4 text-yellow-500" />
                          <label className="text-sm font-medium text-gray-700">Dias atenção</label>
                        </div>
                        <input
                          type="number"
                          value={configEmpresa.caixa_dias_atencao}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, caixa_dias_atencao: parseInt(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">📢 Alerta de ATENÇÃO se caixa cobrir menos de X dias</p>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Alertas de Margem */}
                <div className="border rounded-lg p-4 bg-gradient-to-r from-green-50 to-white">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                        <TrendingUp className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">Alertas de Margem</h4>
                        <p className="text-xs text-gray-500">Acompanha a lucratividade da empresa</p>
                      </div>
                    </div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={configEmpresa.alerta_margem_ativo}
                        onChange={(e) => setConfigEmpresa({...configEmpresa, alerta_margem_ativo: e.target.checked})}
                        className="rounded text-green-600 focus:ring-green-500"
                      />
                      <span className="text-sm font-medium">Ativo</span>
                    </label>
                  </div>
                  {configEmpresa.alerta_margem_ativo && (
                    <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <Target className="w-4 h-4 text-green-600" />
                          <label className="text-sm font-medium text-gray-700">Margem mínima (%)</label>
                        </div>
                        <input
                          type="number"
                          step="0.1"
                          value={configEmpresa.margem_minima}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, margem_minima: parseFloat(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">📉 Alerta se margem líquida ficar abaixo de X%</p>
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <TrendingDown className="w-4 h-4 text-red-500" />
                          <label className="text-sm font-medium text-gray-700">Queda máxima (%)</label>
                        </div>
                        <input
                          type="number"
                          step="0.1"
                          value={configEmpresa.margem_queda_pct}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, margem_queda_pct: parseFloat(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">📊 Alerta se margem cair mais de X% vs mês anterior</p>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Alertas de Score */}
                <div className="border rounded-lg p-4 bg-gradient-to-r from-blue-50 to-white">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Activity className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">Alertas de Score</h4>
                        <p className="text-xs text-gray-500">Monitora a pontuação geral de saúde financeira</p>
                      </div>
                    </div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={configEmpresa.alerta_score_ativo}
                        onChange={(e) => setConfigEmpresa({...configEmpresa, alerta_score_ativo: e.target.checked})}
                        className="rounded text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm font-medium">Ativo</span>
                    </label>
                  </div>
                  {configEmpresa.alerta_score_ativo && (
                    <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="w-4 h-4 text-red-500" />
                          <label className="text-sm font-medium text-gray-700">Score crítico</label>
                        </div>
                        <input
                          type="number"
                          value={configEmpresa.score_critico}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, score_critico: parseInt(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">🔴 Alerta CRÍTICO se score ficar abaixo de X pontos (0-100)</p>
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <TrendingDown className="w-4 h-4 text-orange-500" />
                          <label className="text-sm font-medium text-gray-700">Queda máxima (pontos)</label>
                        </div>
                        <input
                          type="number"
                          value={configEmpresa.score_queda_pontos}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, score_queda_pontos: parseInt(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">📉 Alerta se score cair mais de X pontos vs análise anterior</p>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Botão Salvar */}
                <div className="flex justify-end pt-4 border-t">
                  <button
                    onClick={salvarConfigEmpresa}
                    disabled={salvandoConfig}
                    className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 font-medium shadow-lg shadow-emerald-200"
                  >
                    {salvandoConfig ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                    Salvar Configuração
                  </button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// IMPORTAÇÃO AVANÇADA (F05)
// ============================================================================

function ImportacaoAvancadaPage({ empresaId, onSuccess }) {
  const { api } = useAuth();
  const toast = useToast();
  const fileInputRef = useRef(null);
  
  const [step, setStep] = useState('upload'); // upload, preview, mapping, importing, done
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [mapeamento, setMapeamento] = useState({});
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [historico, setHistorico] = useState([]);
  const [showHistorico, setShowHistorico] = useState(false);
  const [config, setConfig] = useState({
    ignorar_duplicados: true,
    modo_agregacao: 'substituir'
  });

  useEffect(() => {
    if (empresaId) loadHistorico();
  }, [empresaId]);

  const loadHistorico = async () => {
    try {
      const res = await api(`/empresas/${empresaId}/importacoes?limite=10`);
      if (res.ok) {
        const data = await res.json();
        setHistorico(data.importacoes || []);
      }
    } catch (err) {
      console.error('Erro ao carregar histórico:', err);
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setStep('upload');
      setPreview(null);
      setResultado(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setStep('upload');
      setPreview(null);
      setResultado(null);
    }
  };

  const handlePreview = async () => {
    if (!file) return;
    
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await fetch(`/api/empresas/${empresaId}/importar/preview`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });
      
      if (res.ok) {
        const data = await res.json();
        setPreview(data);
        setMapeamento(data.mapeamento_sugerido || {});
        setStep('preview');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Erro ao analisar arquivo');
      }
    } catch (err) {
      toast.error('Erro ao processar arquivo');
    } finally {
      setLoading(false);
    }
  };

  const handleImportar = async () => {
    if (!file) return;
    
    setLoading(true);
    setStep('importing');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mapeamento', JSON.stringify(mapeamento));
    formData.append('ignorar_duplicados', config.ignorar_duplicados);
    formData.append('modo_agregacao', config.modo_agregacao);
    
    try {
      const res = await fetch(`/api/empresas/${empresaId}/importar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });
      
      const data = await res.json();
      
      if (res.ok && data.sucesso) {
        setResultado(data);
        setStep('done');
        toast.success(`Importação concluída: ${data.registros_importados} registros`);
        loadHistorico();
        if (onSuccess) onSuccess();
      } else {
        setResultado(data);
        setStep('done');
        toast.error(data.erro || 'Importação concluída com erros');
      }
    } catch (err) {
      toast.error('Erro ao importar dados');
      setStep('preview');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setMapeamento({});
    setResultado(null);
    setStep('upload');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const camposSistema = [
    { key: 'data', label: 'Data/Período', required: true },
    { key: 'receita', label: 'Receita' },
    { key: 'custos', label: 'Custos' },
    { key: 'despesas', label: 'Despesas' },
    { key: 'impostos', label: 'Impostos' },
    { key: 'folha', label: 'Folha de Pagamento' },
    { key: 'caixa', label: 'Saldo Caixa' }
  ];

  const getTipoIcon = (tipo) => {
    const icons = {
      'csv': '📊',
      'xlsx': '📗',
      'ofx': '🏦',
      'xml_nfe': '📄'
    };
    return icons[tipo] || '📁';
  };

  const getStatusColor = (status) => {
    const colors = {
      'sucesso': 'bg-green-100 text-green-700',
      'parcial': 'bg-yellow-100 text-yellow-700',
      'erro': 'bg-red-100 text-red-700',
      'processando': 'bg-blue-100 text-blue-700'
    };
    return colors[status] || 'bg-slate-100 text-slate-700';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Importação Avançada</h2>
          <p className="text-sm text-slate-500">Suporte a CSV, Excel, OFX e XML NFe</p>
        </div>
        <Button variant="secondary" onClick={() => setShowHistorico(!showHistorico)}>
          <Clock className="w-4 h-4 mr-2" />
          Histórico
        </Button>
      </div>

      {/* Histórico */}
      {showHistorico && (
        <Card className="p-4">
          <h3 className="font-semibold text-slate-800 mb-3">Importações Recentes</h3>
          {historico.length === 0 ? (
            <p className="text-slate-500 text-sm">Nenhuma importação realizada</p>
          ) : (
            <div className="space-y-2">
              {historico.map(imp => (
                <div key={imp.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{getTipoIcon(imp.tipo_arquivo)}</span>
                    <div>
                      <p className="font-medium text-slate-800 text-sm">{imp.nome_arquivo}</p>
                      <p className="text-xs text-slate-500">
                        {new Date(imp.created_at).toLocaleString('pt-BR')} • {imp.periodo}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(imp.status)}`}>
                      {imp.status_label}
                    </span>
                    <span className="text-sm text-slate-600">
                      {imp.registros_importados}/{imp.total_registros}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Upload Area */}
      {step === 'upload' && (
        <Card 
          className="p-8 border-2 border-dashed border-slate-300 hover:border-blue-400 transition-colors cursor-pointer"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.ofx,.qif,.xml"
            onChange={handleFileSelect}
            className="hidden"
          />
          
          <div className="text-center">
            <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-lg font-medium text-slate-700 mb-2">
              {file ? file.name : 'Arraste um arquivo ou clique para selecionar'}
            </p>
            <p className="text-sm text-slate-500">
              Formatos: CSV, OFX (extrato bancário), XML (NFe)
            </p>
            
            {file && (
              <div className="mt-4 flex justify-center gap-3">
                <Button onClick={(e) => { e.stopPropagation(); handlePreview(); }} disabled={loading}>
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
                  Analisar Arquivo
                </Button>
                <Button variant="secondary" onClick={(e) => { e.stopPropagation(); handleReset(); }}>
                  Cancelar
                </Button>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Preview */}
      {step === 'preview' && preview && (
        <div className="space-y-4">
          {/* Info do arquivo */}
          <Card className="p-4">
            <div className="flex items-center gap-4">
              <span className="text-3xl">{getTipoIcon(preview.tipo_arquivo)}</span>
              <div className="flex-1">
                <p className="font-semibold text-slate-800">{file?.name}</p>
                <p className="text-sm text-slate-500">
                  {preview.total_registros} registros • Período: {preview.periodo_inicio} a {preview.periodo_fim}
                </p>
              </div>
              <div className="flex gap-2">
                <Badge variant={preview.registros_validos > 0 ? 'success' : 'warning'}>
                  {preview.registros_validos} válidos
                </Badge>
                {preview.registros_duplicados > 0 && (
                  <Badge variant="warning">{preview.registros_duplicados} duplicados</Badge>
                )}
                {preview.registros_erro > 0 && (
                  <Badge variant="danger">{preview.registros_erro} erros</Badge>
                )}
              </div>
            </div>
          </Card>

          {/* Mapeamento de colunas */}
          <Card className="p-4">
            <h3 className="font-semibold text-slate-800 mb-4">Mapeamento de Colunas</h3>
            <p className="text-sm text-slate-500 mb-4">
              Relacione as colunas do arquivo com os campos do sistema
            </p>
            
            <div className="grid md:grid-cols-2 gap-4">
              {camposSistema.map(campo => (
                <div key={campo.key}>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    {campo.label} {campo.required && <span className="text-red-500">*</span>}
                  </label>
                  <select
                    value={mapeamento[campo.key] || ''}
                    onChange={(e) => setMapeamento({...mapeamento, [campo.key]: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">-- Não mapear --</option>
                    {preview.colunas_detectadas?.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </Card>

          {/* Preview de dados */}
          <Card className="p-4">
            <h3 className="font-semibold text-slate-800 mb-4">Preview dos Dados</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-slate-600">Linha</th>
                    <th className="px-3 py-2 text-left font-medium text-slate-600">Período</th>
                    <th className="px-3 py-2 text-right font-medium text-slate-600">Receita</th>
                    <th className="px-3 py-2 text-right font-medium text-slate-600">Custos</th>
                    <th className="px-3 py-2 text-right font-medium text-slate-600">Despesas</th>
                    <th className="px-3 py-2 text-center font-medium text-slate-600">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {preview.preview?.slice(0, 10).map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="px-3 py-2 text-slate-500">{row.linha}</td>
                      <td className="px-3 py-2">{row.ano}/{String(row.mes).padStart(2, '0')}</td>
                      <td className="px-3 py-2 text-right text-green-600">
                        {row.receita?.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                      </td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {row.custos?.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                      </td>
                      <td className="px-3 py-2 text-right text-orange-600">
                        {row.despesas?.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {row.erro ? (
                          <span className="text-red-500 text-xs">{row.erro}</span>
                        ) : row.is_duplicado ? (
                          <Badge variant="warning">Duplicado</Badge>
                        ) : (
                          <Badge variant="success">OK</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Configurações */}
          <Card className="p-4">
            <h3 className="font-semibold text-slate-800 mb-4">Configurações</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.ignorar_duplicados}
                  onChange={(e) => setConfig({...config, ignorar_duplicados: e.target.checked})}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <span className="text-sm text-slate-700">Ignorar registros duplicados</span>
              </label>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Modo de Agregação
                </label>
                <select
                  value={config.modo_agregacao}
                  onChange={(e) => setConfig({...config, modo_agregacao: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                >
                  <option value="substituir">Substituir dados existentes</option>
                  <option value="somar">Somar aos dados existentes</option>
                  <option value="ignorar">Ignorar se já existir</option>
                </select>
              </div>
            </div>
          </Card>

          {/* Erros */}
          {preview.erros?.length > 0 && (
            <Card className="p-4 border-red-200 bg-red-50">
              <h3 className="font-semibold text-red-800 mb-2 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Erros Encontrados ({preview.erros.length})
              </h3>
              <ul className="text-sm text-red-700 space-y-1">
                {preview.erros.slice(0, 5).map((err, idx) => (
                  <li key={idx}>Linha {err.linha}: {err.erro}</li>
                ))}
                {preview.erros.length > 5 && (
                  <li className="text-red-500">... e mais {preview.erros.length - 5} erros</li>
                )}
              </ul>
            </Card>
          )}

          {/* Ações */}
          <div className="flex gap-3">
            <Button onClick={handleImportar} disabled={loading || !mapeamento.data}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Check className="w-4 h-4 mr-2" />}
              Importar {preview.registros_validos} Registros
            </Button>
            <Button variant="secondary" onClick={handleReset}>
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {/* Importing */}
      {step === 'importing' && (
        <Card className="p-8 text-center">
          <Loader2 className="w-12 h-12 text-blue-500 mx-auto mb-4 animate-spin" />
          <p className="text-lg font-medium text-slate-700">Importando dados...</p>
          <p className="text-sm text-slate-500">Isso pode levar alguns segundos</p>
        </Card>
      )}

      {/* Done */}
      {step === 'done' && resultado && (
        <Card className="p-6">
          <div className="text-center mb-6">
            {resultado.sucesso ? (
              <>
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Check className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-800 mb-2">Importação Concluída!</h3>
              </>
            ) : (
              <>
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <AlertCircle className="w-8 h-8 text-red-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-800 mb-2">Importação com Problemas</h3>
              </>
            )}
          </div>

          <div className="grid md:grid-cols-4 gap-4 mb-6">
            <div className="bg-slate-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-slate-800">{resultado.total_registros || 0}</p>
              <p className="text-sm text-slate-500">Total</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-green-600">{resultado.registros_importados || 0}</p>
              <p className="text-sm text-slate-500">Importados</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-yellow-600">{resultado.registros_duplicados || 0}</p>
              <p className="text-sm text-slate-500">Duplicados</p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-red-600">{resultado.registros_erro || 0}</p>
              <p className="text-sm text-slate-500">Erros</p>
            </div>
          </div>

          {resultado.periodo_inicio && (
            <p className="text-sm text-slate-600 text-center mb-4">
              Período: {resultado.periodo_inicio} a {resultado.periodo_fim}
            </p>
          )}

          {resultado.erros?.length > 0 && (
            <div className="bg-red-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold text-red-800 mb-2">Erros:</h4>
              <ul className="text-sm text-red-700 space-y-1">
                {resultado.erros.slice(0, 5).map((err, idx) => (
                  <li key={idx}>{err.periodo || `Linha ${err.linha}`}: {err.erro}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex justify-center gap-3">
            <Button onClick={handleReset}>
              <Upload className="w-4 h-4 mr-2" />
              Nova Importação
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}

// Componente de importação simplificado para modal
function ImportUploadModal({ isOpen, onClose, empresaId, onSuccess }) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Importar Dados" size="xl">
      <ImportacaoAvancadaPage 
        empresaId={empresaId} 
        onSuccess={() => { onSuccess?.(); onClose(); }}
      />
    </Modal>
  );
}

// === F12: ANÁLISE FINANCEIRA AVANÇADA ===

// Componente de Índices de Liquidez Completo
function IndicesLiquidezTab({ analise, formatMoney, formatPct }) {
  const [periodoCalculo, setPeriodoCalculo] = useState('mensal');
  const [abaIndices, setAbaIndices] = useState('liquidez');
  const [mesSelecionado, setMesSelecionado] = useState(null);
  
  // Dados do período - usar índices já calculados pelo backend
  const dados = analise?.indices || {};
  const dre = analise?.dre || {};
  const dadosMensais = analise?.dados_mensais || [];
  
  // Período atual dos dados
  const periodoInfo = dados.periodo || dre.periodo || '';
  
  // Extrair meses disponíveis para seleção
  const mesesDisponiveis = dadosMensais.length > 0 
    ? dadosMensais.map(d => ({ 
        label: `${String(d.mes || 1).padStart(2, '0')}/${d.ano}`, 
        ano: d.ano, 
        mes: d.mes,
        dados: d 
      })).sort((a, b) => (b.ano - a.ano) || (b.mes - a.mes))
    : [];
  
  // Último mês disponível
  const ultimoMes = mesesDisponiveis[0] || null;
  const mesAtual = mesSelecionado || ultimoMes;
  
  // Dados do mês selecionado (para modo mensal)
  const dadosMes = mesAtual?.dados || {};
  
  // Calcular valores baseado no período selecionado
  const calcularIndicesPeriodo = () => {
    if (periodoCalculo === 'mensal' && dadosMes) {
      // Usar dados do mês selecionado
      const ac = dadosMes.ativo_circulante || dados.ativo_circulante || 0;
      const pc = dadosMes.passivo_circulante || dados.passivo_circulante || 0;
      const est = dadosMes.estoques || dados.estoques || 0;
      const disp = dadosMes.disponibilidades || dadosMes.caixa || dados.disponibilidades || 0;
      const anc = dadosMes.ativo_nao_circulante || dados.ativo_nao_circulante || 0;
      const pnc = dadosMes.passivo_nao_circulante || dados.passivo_nao_circulante || 0;
      const cr = dadosMes.clientes || dadosMes.contas_receber || dados.contas_receber || 0;
      const forn = dadosMes.fornecedores || dados.fornecedores || 0;
      const pl = dadosMes.patrimonio_liquido || dados.patrimonio_liquido || 0;
      const at = dadosMes.ativo_total || dados.ativo_total || (ac + anc) || 0;
      const realizavelLp = dadosMes.realizavel_lp || 0;
      
      // Dados de DRE do mês
      const receita = dadosMes.receita || dadosMes.receita_bruta || 0;
      const lucro = dadosMes.lucro_liquido || 0;
      const custos = dadosMes.custos || dadosMes.custos_total || 0;
      
      // Margem bruta do mês
      const receitaLiq = receita - (dadosMes.deducoes_receita || receita * 0.10);
      const lucroBruto = receitaLiq - custos;
      const margemBruta = receita > 0 ? (lucroBruto / receita * 100) : (dados.margem_bruta || 0);
      
      // Margem operacional do mês
      const despesas = dadosMes.despesas || dadosMes.despesas_operacionais || 0;
      const folha = dadosMes.folha || dadosMes.despesas_pessoal || 0;
      const lucroOp = lucroBruto - despesas - folha;
      const margemOp = receita > 0 ? (lucroOp / receita * 100) : (dados.margem_operacional || 0);
      
      return {
        ativoCirculante: ac,
        passivoCirculante: pc,
        estoques: est,
        disponibilidades: disp,
        ativoNaoCirculante: anc,
        passivoNaoCirculante: pnc,
        contasReceber: cr,
        fornecedores: forn,
        patrimonioLiquido: pl,
        ativoTotal: at,
        receita,
        lucro,
        // Índices calculados
        liquidezCorrente: pc > 0 ? ac / pc : 0,
        liquidezSeca: pc > 0 ? (ac - est) / pc : 0,
        liquidezImediata: pc > 0 ? disp / pc : 0,
        // Liquidez Geral: usa Realizável LP se disponível, senão apenas AC (conservador)
        liquidezGeral: (pc + pnc) > 0 ? (ac + realizavelLp) / (pc + pnc) : 0,
        liquidezCaixa: pc > 0 ? disp / pc : 0,
        liquidezOperacional: forn > 0 ? (cr + est) / forn : 0,
        liquidezAjustada: pc > 0 ? (disp + cr * 0.7 + est * 0.3) / pc : 0,
        ncg: (cr + est) - forn,
        saldoTesouraria: disp - ((cr + est) - forn),
        capitalGiro: ac - pc,
        // Rentabilidade
        roe: pl > 0 ? (lucro / pl * 100) : 0,
        roa: at > 0 ? (lucro / at * 100) : 0,
        giroAtivo: at > 0 ? receita / at : 0,
        margemBruta: margemBruta,
        margemOperacional: margemOp,
        margemLiquida: receita > 0 ? (lucro / receita * 100) : 0,
      };
    } else {
      // Modo Anual - usar dados do backend (já calcula corretamente com desacumulação)
      // Balanço: usa última posição do ano
      const anoAtual = ultimoMes?.ano || new Date().getFullYear();
      const dadosAno = dadosMensais.filter(d => d.ano === anoAtual);
      
      if (dadosAno.length === 0) {
        // Fallback para dados do backend
        return {
          ativoCirculante: dados.ativo_circulante || 0,
          passivoCirculante: dados.passivo_circulante || 0,
          estoques: dados.estoques || 0,
          disponibilidades: dados.disponibilidades || 0,
          ativoNaoCirculante: dados.ativo_nao_circulante || 0,
          passivoNaoCirculante: dados.passivo_nao_circulante || 0,
          contasReceber: dados.contas_receber || 0,
          fornecedores: dados.fornecedores || 0,
          patrimonioLiquido: dados.patrimonio_liquido || 0,
          ativoTotal: dados.ativo_total || 0,
          receita: 0, lucro: 0,
          liquidezCorrente: dados.liquidez_corrente || 0,
          liquidezSeca: dados.liquidez_seca || 0,
          liquidezImediata: dados.liquidez_imediata || 0,
          liquidezGeral: dados.liquidez_geral || 0,
          liquidezCaixa: dados.liquidez_caixa || 0,
          liquidezOperacional: dados.liquidez_operacional || 0,
          liquidezAjustada: dados.liquidez_ajustada || 0,
          ncg: dados.ncg || 0,
          saldoTesouraria: dados.saldo_tesouraria || 0,
          capitalGiro: dados.capital_giro || 0,
          roe: dados.roe || 0,
          roa: dados.roa || 0,
          giroAtivo: dados.giro_ativo || 0,
          margemBruta: dados.margem_bruta || 0,
          margemOperacional: dados.margem_operacional || 0,
          margemLiquida: dados.margem_liquida || 0,
        };
      }
      
      // Ordenar e pegar último mês para dados de balanço
      const dadosAnoSorted = [...dadosAno].sort((a, b) => (a.mes || 0) - (b.mes || 0));
      const ultimoDadosAno = dadosAnoSorted[dadosAnoSorted.length - 1] || {};
      
      const ac = ultimoDadosAno.ativo_circulante || dados.ativo_circulante || 0;
      const pc = ultimoDadosAno.passivo_circulante || dados.passivo_circulante || 0;
      const est = ultimoDadosAno.estoques || dados.estoques || 0;
      const disp = ultimoDadosAno.disponibilidades || ultimoDadosAno.caixa || dados.disponibilidades || 0;
      const anc = ultimoDadosAno.ativo_nao_circulante || dados.ativo_nao_circulante || 0;
      const pnc = ultimoDadosAno.passivo_nao_circulante || dados.passivo_nao_circulante || 0;
      const cr = ultimoDadosAno.clientes || ultimoDadosAno.contas_receber || dados.contas_receber || 0;
      const forn = ultimoDadosAno.fornecedores || dados.fornecedores || 0;
      const pl = ultimoDadosAno.patrimonio_liquido || dados.patrimonio_liquido || 0;
      const at = ultimoDadosAno.ativo_total || dados.ativo_total || (ac + anc) || 0;
      const realizavelLp = ultimoDadosAno.realizavel_lp || 0;
      
      // ============================================================
      // TOTAIS ANUAIS - TRATAR VALORES ACUMULADOS
      // ============================================================
      // Detectar se dados são acumulados (receitas crescem monotonicamente)
      const receitas = dadosAnoSorted.map(d => d.receita || d.receita_bruta || 0);
      const receitasPositivas = receitas.filter(r => r > 0);
      let acumulados = dadosAnoSorted.some(d => d._valores_acumulados);
      
      if (!acumulados && receitasPositivas.length >= 2) {
        const crescente = receitasPositivas.every((r, i) => i === 0 || r >= receitasPositivas[i-1]);
        if (crescente && receitasPositivas[0] > 0) {
          const crescimento = (receitasPositivas[receitasPositivas.length - 1] - receitasPositivas[0]) / receitasPositivas[0];
          if (crescimento > 0.5) acumulados = true;
        }
      }
      
      let receitaAnual, lucroAnual;
      
      if (acumulados) {
        // Para acumulados: último mês já tem o total do ano
        receitaAnual = ultimoDadosAno.receita || ultimoDadosAno.receita_bruta || 0;
        lucroAnual = ultimoDadosAno.lucro_liquido || 0;
      } else {
        // Para mensais: somar
        receitaAnual = dadosAno.reduce((sum, d) => sum + (d.receita || d.receita_bruta || 0), 0);
        lucroAnual = dadosAno.reduce((sum, d) => sum + (d.lucro_liquido || 0), 0);
      }
      
      return {
        ativoCirculante: ac,
        passivoCirculante: pc,
        estoques: est,
        disponibilidades: disp,
        ativoNaoCirculante: anc,
        passivoNaoCirculante: pnc,
        contasReceber: cr,
        fornecedores: forn,
        patrimonioLiquido: pl,
        ativoTotal: at,
        receita: receitaAnual,
        lucro: lucroAnual,
        // Índices de liquidez (balanço - posição final do ano)
        liquidezCorrente: pc > 0 ? ac / pc : 0,
        liquidezSeca: pc > 0 ? (ac - est) / pc : 0,
        liquidezImediata: pc > 0 ? disp / pc : 0,
        // Liquidez Geral: usa Realizável LP se disponível, senão apenas AC (conservador)
        liquidezGeral: (pc + pnc) > 0 ? (ac + realizavelLp) / (pc + pnc) : 0,
        liquidezCaixa: pc > 0 ? disp / pc : 0,
        liquidezOperacional: forn > 0 ? (cr + est) / forn : 0,
        liquidezAjustada: pc > 0 ? (disp + cr * 0.7 + est * 0.3) / pc : 0,
        ncg: (cr + est) - forn,
        saldoTesouraria: disp - ((cr + est) - forn),
        capitalGiro: ac - pc,
        // Rentabilidade (anualizada, corrigida)
        roe: pl > 0 ? (lucroAnual / pl * 100) : 0,
        roa: at > 0 ? (lucroAnual / at * 100) : 0,
        giroAtivo: at > 0 ? receitaAnual / at : 0,
        margemBruta: dados.margem_bruta || 0,
        margemOperacional: dados.margem_operacional || 0,
        margemLiquida: receitaAnual > 0 ? (lucroAnual / receitaAnual * 100) : 0,
      };
    }
  };
  
  const indicesCalculados = calcularIndicesPeriodo();
  
  // Usar índices calculados ou do backend como fallback
  const liquidezCorrente = indicesCalculados.liquidezCorrente || dados.liquidez_corrente || 0;
  const liquidezSeca = indicesCalculados.liquidezSeca || dados.liquidez_seca || 0;
  const liquidezImediata = indicesCalculados.liquidezImediata || dados.liquidez_imediata || 0;
  const liquidezGeral = indicesCalculados.liquidezGeral || dados.liquidez_geral || 0;
  const liquidezCaixa = indicesCalculados.liquidezCaixa || dados.liquidez_caixa || 0;
  const liquidezOperacional = indicesCalculados.liquidezOperacional || dados.liquidez_operacional || 0;
  const liquidezAjustada = indicesCalculados.liquidezAjustada || dados.liquidez_ajustada || 0;
  const ncg = indicesCalculados.ncg || dados.ncg || 0;
  const saldoTesouraria = indicesCalculados.saldoTesouraria || dados.saldo_tesouraria || 0;
  const capitalGiro = indicesCalculados.capitalGiro || dados.capital_giro || 0;
  
  // Dados para exibição
  const ativoCirculante = indicesCalculados.ativoCirculante;
  const passivoCirculante = indicesCalculados.passivoCirculante;
  const estoques = indicesCalculados.estoques;
  const disponibilidades = indicesCalculados.disponibilidades;
  const contasReceber = indicesCalculados.contasReceber;
  const fornecedores = indicesCalculados.fornecedores;
  
  // Texto do período atual
  const getPeriodoTexto = () => {
    if (periodoCalculo === 'mensal') {
      return mesAtual ? `${String(mesAtual.mes).padStart(2, '0')}/${mesAtual.ano}` : 'Último mês';
    } else {
      const ano = ultimoMes?.ano || new Date().getFullYear();
      return `Ano ${ano}`;
    }
  };
  
  // Função para obter cor do status
  const getStatusColor = (valor, limites) => {
    if (valor >= limites.otimo) return 'text-green-600 bg-green-50 border-green-200';
    if (valor >= limites.bom) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (valor >= limites.regular) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };
  
  const getStatusText = (valor, limites) => {
    if (valor >= limites.otimo) return 'Ótimo';
    if (valor >= limites.bom) return 'Bom';
    if (valor >= limites.regular) return 'Regular';
    return 'Crítico';
  };

  // Card de índice individual
  const IndiceCard = ({ titulo, valor, formula, interpretacao, problemas, limites, unidade = '' }) => {
    const status = getStatusColor(valor, limites);
    const statusText = getStatusText(valor, limites);
    
    return (
      <Card className={`p-5 border-2 ${status}`}>
        <div className="flex justify-between items-start mb-3">
          <h4 className="font-bold text-slate-800">{titulo}</h4>
          <span className={`px-2 py-1 rounded text-xs font-semibold ${status}`}>
            {statusText}
          </span>
        </div>
        
        <div className="text-center my-4">
          <span className="text-4xl font-bold">
            {typeof valor === 'number' ? valor.toFixed(2) : '-'}
          </span>
          <span className="text-lg text-slate-500 ml-1">{unidade}</span>
        </div>
        
        <div className="bg-slate-100 rounded-lg p-3 mb-3">
          <p className="text-xs text-slate-500 mb-1 font-semibold">FÓRMULA:</p>
          <code className="text-xs text-slate-700 block whitespace-pre-wrap">{formula}</code>
        </div>
        
        <div className="mb-3">
          <p className="text-xs text-slate-500 mb-1 font-semibold">📌 INTERPRETAÇÃO:</p>
          <p className="text-sm text-slate-700">{interpretacao}</p>
        </div>
        
        {problemas && (
          <div className="border-t pt-3">
            <p className="text-xs text-amber-600 mb-1 font-semibold">⚠️ ATENÇÃO:</p>
            <p className="text-xs text-slate-600">{problemas}</p>
          </div>
        )}
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header com Toggle e Período */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-lg shadow-sm">
        <div>
          <h3 className="text-lg font-bold text-slate-800">Índices Financeiros</h3>
          <p className="text-sm text-slate-500">
            Período: <span className="font-semibold text-blue-600">{getPeriodoTexto()}</span>
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Seletor de mês (apenas no modo mensal) */}
          {periodoCalculo === 'mensal' && mesesDisponiveis.length > 0 && (
            <select
              value={mesAtual ? `${mesAtual.ano}-${mesAtual.mes}` : ''}
              onChange={(e) => {
                const [ano, mes] = e.target.value.split('-').map(Number);
                const selected = mesesDisponiveis.find(m => m.ano === ano && m.mes === mes);
                setMesSelecionado(selected || null);
              }}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {mesesDisponiveis.map(m => (
                <option key={`${m.ano}-${m.mes}`} value={`${m.ano}-${m.mes}`}>
                  {m.label}
                </option>
              ))}
            </select>
          )}
          
          {/* Toggle Mensal/Anual */}
          <div className="flex items-center gap-2 bg-slate-100 rounded-lg p-1">
            <button
              onClick={() => setPeriodoCalculo('mensal')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                periodoCalculo === 'mensal' 
                  ? 'bg-blue-600 text-white shadow' 
                  : 'text-slate-600 hover:bg-slate-200'
              }`}
            >
              Mensal
            </button>
            <button
              onClick={() => setPeriodoCalculo('anual')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                periodoCalculo === 'anual' 
                  ? 'bg-blue-600 text-white shadow' 
                  : 'text-slate-600 hover:bg-slate-200'
              }`}
            >
              Anual
            </button>
          </div>
        </div>
      </div>

      {/* Sub-abas */}
      <div className="flex gap-2 border-b border-slate-200 pb-2">
        {[
          { id: 'liquidez', label: 'Índices de Liquidez', icon: '💧' },
          { id: 'rentabilidade', label: 'Rentabilidade', icon: '📈' },
          { id: 'estrutura', label: 'Estrutura', icon: '🏗️' },
        ].map(aba => (
          <button
            key={aba.id}
            onClick={() => setAbaIndices(aba.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors text-sm ${
              abaIndices === aba.id 
                ? 'bg-blue-600 text-white' 
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <span>{aba.icon}</span>
            {aba.label}
          </button>
        ))}
      </div>

      {/* ÍNDICES DE LIQUIDEZ */}
      {abaIndices === 'liquidez' && (
        <div className="space-y-6">
          {/* Resumo Rápido */}
          <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-700">{liquidezCorrente.toFixed(2)}</p>
                <p className="text-xs text-slate-600">Liq. Corrente</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-purple-700">{liquidezSeca.toFixed(2)}</p>
                <p className="text-xs text-slate-600">Liq. Seca</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-indigo-700">{liquidezImediata.toFixed(2)}</p>
                <p className="text-xs text-slate-600">Liq. Imediata</p>
              </div>
              <div className="text-center">
                <p className={`text-3xl font-bold ${ncg >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {formatMoney(ncg)}
                </p>
                <p className="text-xs text-slate-600">NCG</p>
              </div>
            </div>
          </Card>

          {/* Grid de Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* 1. Liquidez Corrente */}
            <IndiceCard
              titulo="1. Liquidez Corrente"
              valor={liquidezCorrente}
              formula="Ativo Circulante / Passivo Circulante"
              interpretacao={
                liquidezCorrente >= 1.5 
                  ? "Excelente capacidade de pagar obrigações de curto prazo."
                  : liquidezCorrente >= 1 
                    ? "Consegue pagar obrigações, mas com pouca folga."
                    : "Risco de insolvência no curto prazo!"
              }
              problemas="Pode estar inflado por estoques encalhados ou contas a receber irrecuperáveis."
              limites={{ otimo: 1.5, bom: 1.2, regular: 1.0 }}
            />
            
            {/* 2. Liquidez Seca */}
            <IndiceCard
              titulo="2. Liquidez Seca"
              valor={liquidezSeca}
              formula="(Ativo Circulante − Estoques) / Passivo Circulante"
              interpretacao={
                liquidezSeca >= 1.0 
                  ? "Consegue pagar dívidas sem depender da venda de estoques."
                  : liquidezSeca >= 0.7 
                    ? "Capacidade razoável, mas depende parcialmente de estoques."
                    : "Alta dependência de estoques para honrar compromissos."
              }
              problemas="Ainda pode enganar se houver duplicatas vencidas ou clientes inadimplentes."
              limites={{ otimo: 1.0, bom: 0.8, regular: 0.6 }}
            />
            
            {/* 3. Liquidez Imediata */}
            <IndiceCard
              titulo="3. Liquidez Imediata"
              valor={liquidezImediata}
              formula="Disponibilidades / Passivo Circulante"
              interpretacao={
                liquidezImediata >= 0.3 
                  ? "Boa disponibilidade de caixa para emergências."
                  : liquidezImediata >= 0.1 
                    ? "Disponibilidade adequada para operação normal."
                    : "Baixa disponibilidade - comum em empresas saudáveis."
              }
              problemas="A maioria das empresas saudáveis tem esse índice baixo, e isso não é necessariamente ruim. Dinheiro parado não rende."
              limites={{ otimo: 0.3, bom: 0.15, regular: 0.05 }}
            />
            
            {/* 4. Liquidez Geral */}
            <IndiceCard
              titulo="4. Liquidez Geral"
              valor={liquidezGeral}
              formula="(AC + ANC Realizável LP) / (PC + PNC)"
              interpretacao={
                liquidezGeral >= 1.2 
                  ? "Boa capacidade de pagamento no longo prazo."
                  : liquidezGeral >= 1.0 
                    ? "Capacidade equilibrada de pagamento."
                    : "Atenção: passivos superam ativos realizáveis."
              }
              problemas="Mistura horizontes de tempo. Pode parecer boa, mas esconder problemas sérios de caixa no curto prazo."
              limites={{ otimo: 1.2, bom: 1.0, regular: 0.8 }}
            />
            
            {/* 5. Liquidez Operacional */}
            <IndiceCard
              titulo="5. Liquidez Operacional"
              valor={liquidezOperacional}
              formula="AC Operacional / PC Operacional"
              interpretacao={
                liquidezOperacional >= 1.5 
                  ? "Operação gera recursos suficientes para suas obrigações."
                  : liquidezOperacional >= 1.0 
                    ? "Equilíbrio entre ativos e passivos operacionais."
                    : "Operação não cobre suas obrigações - precisa de financiamento."
              }
              problemas="Exclui aplicações financeiras e empréstimos. Pouco usada, mas muito mais honesta sobre a saúde operacional."
              limites={{ otimo: 1.5, bom: 1.2, regular: 1.0 }}
            />
            
            {/* 6. Liquidez de Caixa (Cash Ratio) */}
            <IndiceCard
              titulo="6. Liquidez de Caixa (Cash Ratio)"
              valor={liquidezCaixa}
              formula="(Caixa + Equivalentes) / Passivo Circulante"
              interpretacao={
                liquidezCaixa >= 0.25 
                  ? "Alta disponibilidade de caixa - conservador."
                  : liquidezCaixa >= 0.1 
                    ? "Caixa suficiente para operação normal."
                    : "Caixa baixo - dependente de recebimentos."
              }
              problemas="Versão ultra conservadora. Muito caixa pode indicar dinheiro mal aproveitado."
              limites={{ otimo: 0.25, bom: 0.15, regular: 0.05 }}
            />
            
            {/* 7. NCG - Necessidade de Capital de Giro */}
            <Card className={`p-5 border-2 ${ncg >= 0 ? 'border-blue-200 bg-blue-50' : 'border-red-200 bg-red-50'}`}>
              <div className="flex justify-between items-start mb-3">
                <h4 className="font-bold text-slate-800">7. NCG - Necessidade de Capital de Giro</h4>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${ncg >= 0 ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'}`}>
                  {ncg >= 0 ? 'Operação Demanda Capital' : 'Operação Gera Capital'}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-4 my-4">
                <div className="text-center p-3 bg-white rounded-lg">
                  <p className="text-2xl font-bold text-slate-800">{formatMoney(ncg)}</p>
                  <p className="text-xs text-slate-500">NCG</p>
                </div>
                <div className="text-center p-3 bg-white rounded-lg">
                  <p className={`text-2xl font-bold ${saldoTesouraria >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    {formatMoney(saldoTesouraria)}
                  </p>
                  <p className="text-xs text-slate-500">Saldo Tesouraria</p>
                </div>
              </div>
              
              <div className="bg-white rounded-lg p-3 mb-3">
                <p className="text-xs text-slate-500 mb-1 font-semibold">FÓRMULAS:</p>
                <code className="text-xs text-slate-700 block">NCG = AC Operacional − PC Operacional</code>
                <code className="text-xs text-slate-700 block mt-1">Saldo Tesouraria = Disponibilidades − NCG</code>
              </div>
              
              <div className="mb-3">
                <p className="text-xs text-slate-500 mb-1 font-semibold">📌 INTERPRETAÇÃO:</p>
                <p className="text-sm text-slate-700">
                  {ncg > 0 
                    ? `A empresa precisa de ${formatMoney(ncg)} de capital de giro para operar.`
                    : `A operação gera ${formatMoney(Math.abs(ncg))} - fornecedores financiam o giro.`
                  }
                  {saldoTesouraria < 0 && " Saldo de tesouraria negativo indica dependência de financiamento!"}
                </p>
              </div>
              
              <div className="border-t pt-3">
                <p className="text-xs text-red-600 font-semibold">⚠️ CRÍTICO:</p>
                <p className="text-xs text-slate-600">Empresas quebram aqui, não na liquidez corrente! Este é o indicador mais realista de saúde financeira.</p>
              </div>
            </Card>
            
            {/* 8. Liquidez Ajustada */}
            <IndiceCard
              titulo="8. Liquidez Ajustada (Análise Avançada)"
              valor={liquidezAjustada}
              formula="(Caixa + 70%×CR + 30%×Estoques) / PC"
              interpretacao={
                liquidezAjustada >= 1.0 
                  ? "Mesmo com descontos conservadores, há boa liquidez."
                  : liquidezAjustada >= 0.7 
                    ? "Liquidez adequada considerando riscos de realização."
                    : "Liquidez preocupante quando ajustada ao risco real."
              }
              problemas="Não é fórmula padrão, mas é a mais inteligente para análise real. Desconta 30% das contas a receber (inadimplência) e 70% dos estoques (obsolescência)."
              limites={{ otimo: 1.0, bom: 0.8, regular: 0.6 }}
            />
          </div>
          
          {/* Legenda */}
          <Card className="p-4 bg-slate-50">
            <h4 className="font-semibold text-slate-700 mb-3">Legenda de Status</h4>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                <span className="text-sm text-slate-600">Ótimo</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                <span className="text-sm text-slate-600">Bom</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                <span className="text-sm text-slate-600">Regular</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500"></span>
                <span className="text-sm text-slate-600">Crítico</span>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-3">
              * Valores calculados para o período: <strong>{getPeriodoTexto()}</strong> ({periodoCalculo === 'mensal' ? 'dados do mês' : 'dados anualizados'})<br/>
              Ativo Circulante: {formatMoney(ativoCirculante)} | 
              Passivo Circulante: {formatMoney(passivoCirculante)} | 
              Estoques: {formatMoney(estoques)} | 
              Disponibilidades: {formatMoney(disponibilidades)}
            </p>
          </Card>
        </div>
      )}

      {/* RENTABILIDADE */}
      {abaIndices === 'rentabilidade' && (
        <div className="space-y-6">
          {/* Header com período */}
          <Card className="p-4 bg-gradient-to-r from-green-50 to-emerald-50">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-bold text-slate-800">Indicadores de Rentabilidade</h4>
                <p className="text-sm text-slate-600">Período: <span className="font-semibold text-green-700">{getPeriodoTexto()}</span></p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-green-700">{formatPct(indicesCalculados.margemLiquida || dados.margem_liquida)}</p>
                <p className="text-xs text-slate-500">Margem Líquida</p>
              </div>
            </div>
          </Card>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Margem Bruta */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">Margem Bruta</h4>
              <div className="text-center my-4">
                <span className="text-4xl font-bold text-green-600">
                  {formatPct(indicesCalculados.margemBruta || dados.margem_bruta)}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-3 mb-3">
                <div className="bg-green-500 h-3 rounded-full transition-all" 
                     style={{width: `${Math.min(indicesCalculados.margemBruta || dados.margem_bruta || 0, 100)}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Lucro Bruto / Receita Líquida × 100
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Quanto sobra da receita após pagar os custos diretos (CMV/CPV).
              </p>
            </Card>
            
            {/* Margem Operacional */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">Margem Operacional (EBIT)</h4>
              <div className="text-center my-4">
                <span className={`text-4xl font-bold ${(indicesCalculados.margemOperacional || dados.margem_operacional || 0) >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                  {formatPct(indicesCalculados.margemOperacional || dados.margem_operacional)}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-3 mb-3">
                <div className="bg-blue-500 h-3 rounded-full transition-all" 
                     style={{width: `${Math.min(Math.max(indicesCalculados.margemOperacional || dados.margem_operacional || 0, 0), 100)}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Lucro Operacional / Receita Líquida × 100
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Eficiência da operação antes de impostos e despesas financeiras.
              </p>
            </Card>
            
            {/* Margem Líquida */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">Margem Líquida</h4>
              <div className="text-center my-4">
                <span className={`text-4xl font-bold ${(indicesCalculados.margemLiquida || dados.margem_liquida || 0) >= 0 ? 'text-purple-600' : 'text-red-600'}`}>
                  {formatPct(indicesCalculados.margemLiquida || dados.margem_liquida)}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-3 mb-3">
                <div className={`h-3 rounded-full transition-all ${(indicesCalculados.margemLiquida || dados.margem_liquida || 0) >= 0 ? 'bg-purple-500' : 'bg-red-500'}`} 
                     style={{width: `${Math.min(Math.max(indicesCalculados.margemLiquida || dados.margem_liquida || 0, 0), 100)}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Lucro Líquido / Receita Líquida × 100
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Quanto efetivamente sobra para os sócios de cada R$ 100 de vendas.
              </p>
            </Card>
            
            {/* ROE */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">ROE - Retorno sobre PL</h4>
              <div className="text-center my-4">
                <span className={`text-4xl font-bold ${(indicesCalculados.roe || dados.roe || 0) >= 15 ? 'text-green-600' : 'text-orange-600'}`}>
                  {(indicesCalculados.roe || dados.roe || 0) > 1000 ? '>1000%' : formatPct(indicesCalculados.roe || dados.roe)}
                </span>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Lucro Líquido / Patrimônio Líquido × 100
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Rentabilidade do capital próprio investido. Benchmark: &gt; 15% {periodoCalculo === 'anual' ? 'a.a.' : 'mensal (1.25% a.m.)'}
              </p>
            </Card>
            
            {/* ROA */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">ROA - Retorno sobre Ativos</h4>
              <div className="text-center my-4">
                <span className={`text-4xl font-bold ${(indicesCalculados.roa || dados.roa || 0) >= 8 ? 'text-green-600' : 'text-orange-600'}`}>
                  {formatPct(indicesCalculados.roa || dados.roa)}
                </span>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Lucro Líquido / Ativo Total × 100
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Eficiência no uso de todos os ativos. Benchmark: &gt; 8% {periodoCalculo === 'anual' ? 'a.a.' : 'mensal (0.67% a.m.)'}
              </p>
            </Card>
            
            {/* Giro do Ativo */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">Giro do Ativo</h4>
              <div className="text-center my-4">
                <span className={`text-4xl font-bold ${(indicesCalculados.giroAtivo || dados.giro_ativo || 0) >= 1 ? 'text-green-600' : 'text-orange-600'}`}>
                  {(indicesCalculados.giroAtivo || dados.giro_ativo || 0).toFixed(2)}x
                </span>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Receita {periodoCalculo === 'anual' ? 'Anual' : 'Mensal'} / Ativo Total
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Quantas vezes o ativo "gira" em vendas {periodoCalculo === 'anual' ? 'por ano' : 'no mês'}. Mais = melhor uso.
              </p>
            </Card>
          </div>
        </div>
      )}

      {/* ESTRUTURA */}
      {abaIndices === 'estrutura' && (
        <div className="space-y-6">
          {/* Header com período */}
          <Card className="p-4 bg-gradient-to-r from-orange-50 to-amber-50">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-bold text-slate-800">Estrutura de Custos e Despesas</h4>
                <p className="text-sm text-slate-600">Período: <span className="font-semibold text-orange-700">{getPeriodoTexto()}</span></p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-orange-700">{formatMoney(capitalGiro)}</p>
                <p className="text-xs text-slate-500">Capital de Giro</p>
              </div>
            </div>
          </Card>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Estrutura de Custos */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-4">Estrutura de Custos</h4>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Custos (CMV/CPV)</span>
                    <span className="font-semibold">{formatPct(dados.peso_custos)}</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className="bg-orange-500 h-2 rounded-full" style={{width: `${Math.min(dados.peso_custos || 0, 100)}%`}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Despesas com Pessoal</span>
                    <span className={`font-semibold ${(dados.peso_folha || 0) > 35 ? 'text-red-600' : ''}`}>
                      {formatPct(dados.peso_folha)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className={`h-2 rounded-full ${(dados.peso_folha || 0) > 35 ? 'bg-red-500' : 'bg-blue-500'}`} 
                         style={{width: `${Math.min(dados.peso_folha || 0, 100)}%`}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Impostos</span>
                    <span className="font-semibold">{formatPct(dados.peso_impostos)}</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className="bg-red-500 h-2 rounded-full" style={{width: `${Math.min(dados.peso_impostos || 0, 100)}%`}}></div>
                  </div>
                </div>
              </div>
            </Card>
            
            {/* Indicadores Adicionais */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-4">Indicadores de Eficiência</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm text-slate-600">Produtividade da Folha</span>
                  <span className="font-bold text-lg">{(dados.produtividade_folha || 0).toFixed(1)}x</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm text-slate-600">Capital de Giro (dias)</span>
                  <span className="font-bold text-lg">{(dados.capital_giro_dias || 0).toFixed(0)} dias</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm text-slate-600">Variação de Receita</span>
                  <span className={`font-bold text-lg ${(dados.variacao_receita || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {(dados.variacao_receita || 0) >= 0 ? '+' : ''}{formatPct(dados.variacao_receita)}
                  </span>
                </div>
              </div>
            </Card>
            
            {/* Endividamento */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-4">Endividamento</h4>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Endividamento Geral</span>
                    <span className={`font-semibold ${(dados.endividamento_geral || 0) > 70 ? 'text-red-600' : (dados.endividamento_geral || 0) > 50 ? 'text-yellow-600' : 'text-green-600'}`}>
                      {formatPct(dados.endividamento_geral)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className={`h-2 rounded-full ${(dados.endividamento_geral || 0) > 70 ? 'bg-red-500' : (dados.endividamento_geral || 0) > 50 ? 'bg-yellow-500' : 'bg-green-500'}`} 
                         style={{width: `${Math.min(dados.endividamento_geral || 0, 100)}%`}}></div>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Passivo Total / Ativo Total (ideal: &lt; 50%)</p>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Composição Endividamento</span>
                    <span className="font-semibold">{formatPct(dados.composicao_endividamento)}</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className="bg-purple-500 h-2 rounded-full" style={{width: `${Math.min(dados.composicao_endividamento || 0, 100)}%`}}></div>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">PC / Passivo Total (% das dívidas no curto prazo)</p>
                </div>
                {(dados.endividamento_pl || 0) > 0 && (
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Endividamento s/ PL</span>
                      <span className={`font-semibold ${(dados.endividamento_pl || 0) > 150 ? 'text-red-600' : 'text-slate-700'}`}>
                        {formatPct(dados.endividamento_pl)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Passivo Total / Patrimônio Líquido</p>
                  </div>
                )}
              </div>
            </Card>
            
            {/* Saúde Geral */}
            <Card className="p-5 md:col-span-2">
              <h4 className="font-bold text-slate-800 mb-4">Diagnóstico Geral - {getPeriodoTexto()}</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className={`text-center py-6 rounded-lg ${
                  dados.saude_financeira === 'otima' ? 'bg-green-100 text-green-800' :
                  dados.saude_financeira === 'boa' ? 'bg-blue-100 text-blue-800' :
                  dados.saude_financeira === 'regular' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  <span className="text-3xl font-bold capitalize">{dados.saude_financeira || 'N/A'}</span>
                  <p className="text-sm mt-2 opacity-75">
                    {dados.saude_financeira === 'otima' ? 'Empresa em excelente situação financeira' :
                     dados.saude_financeira === 'boa' ? 'Boa saúde financeira com pontos de melhoria' :
                     dados.saude_financeira === 'regular' ? 'Situação estável, mas requer atenção' :
                     'Situação crítica - ação imediata necessária'}
                  </p>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600 mb-2">Score de Saúde</p>
                  <div className="flex items-center gap-3">
                    <div className="text-4xl font-bold text-slate-800">{dados.score_saude || 0}</div>
                    <div className="flex-1">
                      <div className="w-full bg-slate-200 rounded-full h-3">
                        <div className={`h-3 rounded-full ${
                          (dados.score_saude || 0) >= 80 ? 'bg-green-500' :
                          (dados.score_saude || 0) >= 60 ? 'bg-blue-500' :
                          (dados.score_saude || 0) >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                        }`} style={{width: `${dados.score_saude || 0}%`}}></div>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">de 100 pontos</p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

function AnaliseFinanceiraPage({ empresaId, empresaNome, onBack }) {
  const { api } = useAuth();
  const toast = useToast();
  
  const [loading, setLoading] = useState(true);
  const [analise, setAnalise] = useState(null);
  const [erro, setErro] = useState(null);
  const [abaAtiva, setAbaAtiva] = useState('resumo');
  const [setores, setSetores] = useState([
    { codigo: 'geral', nome: 'Geral' }
  ]);
  const [setorSelecionado, setSetorSelecionado] = useState('geral');
  const [setoresCarregados, setSetoresCarregados] = useState(false);
  
  useEffect(() => {
    loadSetores();
  }, []);
  
  useEffect(() => {
    if (empresaId) {
      loadAnalise();
    }
  }, [empresaId, setorSelecionado]);
  
  const loadAnalise = async () => {
    setLoading(true);
    setErro(null);
    try {
      const res = await api(`/empresas/${empresaId}/analise-financeira?setor=${setorSelecionado}`);
      const data = await res.json();
      
      if (data.dados_suficientes === false) {
        setErro(data.erro || "Dados insuficientes para análise");
        setAnalise(null);
      } else {
        setAnalise(data.analise || null);
      }
    } catch (err) {
      setErro("Erro ao carregar análise financeira");
      console.error(err);
    }
    setLoading(false);
  };
  
  const loadSetores = async () => {
    try {
      const res = await api('/setores');
      const data = await res.json();
      const setoresData = data.setores || [];
      if (setoresData.length > 0) {
        setSetores(setoresData);
      }
      setSetoresCarregados(true);
    } catch (err) {
      console.error('Erro ao carregar setores:', err);
      setSetoresCarregados(true);
    }
  };
  
  const formatMoney = (value) => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };
  
  const formatPct = (value) => {
    if (value === null || value === undefined) return '-';
    return `${value.toFixed(1)}%`;
  };
  
  const getSaudeColor = (saude) => {
    const colors = {
      'otima': 'text-green-600 bg-green-100',
      'boa': 'text-blue-600 bg-blue-100',
      'regular': 'text-yellow-600 bg-yellow-100',
      'ruim': 'text-orange-600 bg-orange-100',
      'critica': 'text-red-600 bg-red-100'
    };
    return colors[saude] || 'text-gray-600 bg-gray-100';
  };
  
  const getPosicaoColor = (posicao) => {
    const colors = {
      'acima_media': 'text-green-600',
      'na_media': 'text-blue-600',
      'abaixo_media': 'text-red-600'
    };
    return colors[posicao] || 'text-gray-600';
  };
  
  if (loading) return <LoadingScreen />;
  
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {onBack && (
            <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-lg">
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Análise Financeira</h1>
            <p className="text-slate-600">{empresaNome}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Select
            value={setorSelecionado}
            onChange={(e) => setSetorSelecionado(e.target.value)}
            className="w-48"
          >
            {(setores || []).map(s => (
              <option key={s.codigo} value={s.codigo}>{s.nome}</option>
            ))}
          </Select>
          <Button onClick={loadAnalise} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Atualizar
          </Button>
        </div>
      </div>
      
      {erro ? (
        <Card className="p-8 text-center">
          <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-800 mb-2">Dados Insuficientes</h3>
          <p className="text-slate-600">{erro}</p>
          <p className="text-sm text-slate-500 mt-2">
            Importe pelo menos 3 meses de dados financeiros para gerar a análise completa.
          </p>
        </Card>
      ) : analise && (
        <>
          {/* PAINEL DE ALERTAS CRÍTICOS */}
          {(() => {
            const indices = analise.indices || {};
            const alertasCriticos = [];
            
            // Verificar indicadores críticos
            if (indices.liquidez_corrente > 0 && indices.liquidez_corrente < 1) {
              alertasCriticos.push({
                tipo: 'INSOLVÊNCIA',
                msg: `Liquidez corrente de ${indices.liquidez_corrente?.toFixed(2) || 0} - empresa não consegue pagar dívidas de curto prazo`,
                icon: '🚨'
              });
            }
            if (indices.patrimonio_liquido < 0) {
              alertasCriticos.push({
                tipo: 'PASSIVO A DESCOBERTO',
                msg: `Patrimônio Líquido negativo de ${formatMoney(indices.patrimonio_liquido)} - prejuízos superaram o capital`,
                icon: '🚨'
              });
            }
            if (indices.endividamento_geral > 80) {
              alertasCriticos.push({
                tipo: 'ENDIVIDAMENTO CRÍTICO',
                msg: `Endividamento de ${indices.endividamento_geral?.toFixed(1)}% - muito acima do limite seguro`,
                icon: '⚠️'
              });
            }
            if (indices.margem_liquida < -10) {
              alertasCriticos.push({
                tipo: 'PREJUÍZO GRAVE',
                msg: `Margem líquida de ${indices.margem_liquida?.toFixed(1)}% - operação dando prejuízo significativo`,
                icon: '🚨'
              });
            }
            if (indices.capital_giro < 0) {
              alertasCriticos.push({
                tipo: 'CAPITAL GIRO NEGATIVO',
                msg: `Capital de giro de ${formatMoney(indices.capital_giro)} - financiando LP com dívidas CP`,
                icon: '🚨'
              });
            }
            if (indices.disponibilidades <= 1000 && indices.passivo_circulante > 10000) {
              alertasCriticos.push({
                tipo: 'CAIXA ZERADO',
                msg: `Disponibilidades de apenas ${formatMoney(indices.disponibilidades)} - sem recursos para operar`,
                icon: '🚨'
              });
            }
            
            if (alertasCriticos.length === 0) return null;
            
            return (
              <Card className="p-4 bg-red-50 border-2 border-red-300 mb-4">
                <div className="flex items-start gap-3">
                  <div className="text-3xl">🚨</div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-red-800 mb-2">
                      EMPRESA EM SITUAÇÃO CRÍTICA - {alertasCriticos.length} ALERTA{alertasCriticos.length > 1 ? 'S' : ''}
                    </h3>
                    <div className="space-y-2">
                      {alertasCriticos.map((alerta, idx) => (
                        <div key={idx} className="flex items-start gap-2 bg-white p-3 rounded-lg border border-red-200">
                          <span className="text-xl">{alerta.icon}</span>
                          <div>
                            <p className="font-bold text-red-700">{alerta.tipo}</p>
                            <p className="text-sm text-red-600">{alerta.msg}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-red-600 mt-3 font-medium">
                      ⚠️ Estes indicadores apontam risco iminente de falência. Ação imediata é necessária!
                    </p>
                  </div>
                </div>
              </Card>
            );
          })()}
          
          {/* Abas */}
          <div className="flex gap-2 border-b border-slate-200 pb-2">
            {[
              { id: 'resumo', label: 'Resumo Executivo', icon: FileText },
              { id: 'dre', label: 'DRE', icon: BarChart3 },
              { id: 'indices', label: 'Índices', icon: TrendingUp },
              { id: 'breakeven', label: 'Break-Even', icon: Target },
              { id: 'projecoes', label: 'Projeções', icon: TrendingUp },
              { id: 'benchmarks', label: 'Benchmarks', icon: Building2 }
            ].map(aba => (
              <button
                key={aba.id}
                onClick={() => setAbaAtiva(aba.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors ${
                  abaAtiva === aba.id 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                <aba.icon className="w-4 h-4" />
                {aba.label}
              </button>
            ))}
          </div>
          
          {/* Conteúdo das Abas */}
          {abaAtiva === 'resumo' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Saúde Financeira */}
              <Card className="p-6">
                <h3 className="font-semibold text-slate-800 mb-4">Saúde Financeira</h3>
                <div className={`text-center py-4 px-6 rounded-lg ${getSaudeColor(analise.indices?.saude_financeira)}`}>
                  <span className="text-2xl font-bold capitalize">
                    {analise.indices?.saude_financeira || 'N/A'}
                  </span>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Margem Líquida</span>
                    <span className="font-medium">{formatPct(analise.indices?.margem_liquida)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Liquidez</span>
                    <span className="font-medium">{analise.indices?.liquidez_corrente?.toFixed(2) || '-'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Capital de Giro</span>
                    <span className="font-medium">{analise.indices?.capital_giro_dias?.toFixed(0)} dias</span>
                  </div>
                </div>
              </Card>
              
              {/* Pontos Fortes */}
              <Card className="p-6">
                <h3 className="font-semibold text-green-700 mb-4 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  Pontos Fortes
                </h3>
                {analise.pontos_fortes?.length > 0 ? (
                  <ul className="space-y-2">
                    {analise.pontos_fortes.map((ponto, idx) => (
                      <li key={idx} className="text-sm text-slate-700 flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        {ponto}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">Nenhum ponto forte identificado</p>
                )}
              </Card>
              
              {/* Pontos de Atenção */}
              <Card className="p-6">
                <h3 className="font-semibold text-red-700 mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  Pontos de Atenção
                </h3>
                {analise.pontos_fracos?.length > 0 ? (
                  <ul className="space-y-2">
                    {analise.pontos_fracos.map((ponto, idx) => (
                      <li key={idx} className="text-sm text-slate-700 flex items-start gap-2">
                        <span className="text-red-500 mt-1">!</span>
                        {ponto}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">Nenhum ponto de atenção</p>
                )}
              </Card>
              
              {/* Recomendações */}
              <Card className="p-6 lg:col-span-3">
                <h3 className="font-semibold text-blue-700 mb-4 flex items-center gap-2">
                  <Lightbulb className="w-5 h-5" />
                  Recomendações
                </h3>
                {analise.recomendacoes?.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {analise.recomendacoes.map((rec, idx) => (
                      <div key={idx} className="bg-blue-50 p-3 rounded-lg text-sm text-blue-800">
                        {rec}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">Sem recomendações no momento</p>
                )}
              </Card>
            </div>
          )}
          
          {abaAtiva === 'dre' && analise.dre && (
            <Card className="p-6">
              <h3 className="font-semibold text-slate-800 mb-4">
                Demonstrativo de Resultado - {analise.dre.periodo}
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <tbody className="divide-y divide-slate-100">
                    <tr className="bg-slate-50">
                      <td className="py-3 px-4 font-semibold">Receita Bruta</td>
                      <td className="py-3 px-4 text-right font-semibold">{formatMoney(analise.dre.receita_bruta)}</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Deduções</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.deducoes_receita || 0))}</td>
                    </tr>
                    <tr className="bg-slate-50">
                      <td className="py-3 px-4 font-semibold">= Receita Líquida</td>
                      <td className="py-3 px-4 text-right font-semibold">{formatMoney(analise.dre.receita_liquida)}</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Custo das Mercadorias</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.custo_produtos_vendidos || 0))}</td>
                    </tr>
                    <tr className="bg-green-50">
                      <td className="py-3 px-4 font-semibold text-green-800">= Lucro Bruto</td>
                      <td className="py-3 px-4 text-right font-semibold text-green-800">
                        {formatMoney(analise.dre.lucro_bruto)}
                        <span className="text-sm ml-2">({formatPct(analise.dre.margem_bruta_pct)})</span>
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Despesas com Pessoal</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.despesas_pessoal || 0))}</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Despesas Administrativas</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.despesas_administrativas || 0))}</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Despesas Comerciais/Outras</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs((analise.dre.despesas_comerciais || 0) + (analise.dre.outras_despesas || 0)))}</td>
                    </tr>
                    {(analise.dre.despesas_financeiras || 0) > 0 && (
                      <tr>
                        <td className="py-3 px-4 text-slate-600 pl-8">(-) Despesas Financeiras</td>
                        <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.despesas_financeiras || 0))}</td>
                      </tr>
                    )}
                    <tr className="bg-blue-50">
                      <td className="py-3 px-4 font-semibold text-blue-800">= Resultado Operacional (EBIT)</td>
                      <td className="py-3 px-4 text-right font-semibold text-blue-800">
                        {formatMoney(analise.dre.lucro_operacional)}
                        <span className="text-sm ml-2">({formatPct(analise.dre.margem_operacional_pct)})</span>
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Impostos</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.impostos || 0))}</td>
                    </tr>
                    <tr className={`${analise.dre.lucro_liquido >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                      <td className="py-4 px-4 font-bold text-lg">= LUCRO LÍQUIDO</td>
                      <td className={`py-4 px-4 text-right font-bold text-lg ${analise.dre.lucro_liquido >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                        {formatMoney(analise.dre.lucro_liquido)}
                        <span className="text-sm ml-2">({formatPct(analise.dre.margem_liquida_pct)})</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              {/* Nota sobre valores acumulados */}
              <p className="text-xs text-slate-400 mt-4 text-center">
                * Valores consolidados do período. Deduções e impostos estimados quando não disponíveis no balancete.
              </p>
            </Card>
          )}
          
          {abaAtiva === 'indices' && analise.indices && (
            <IndicesLiquidezTab analise={analise} formatMoney={formatMoney} formatPct={formatPct} />
          )}
          
          {abaAtiva === 'breakeven' && analise.break_even && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="font-semibold text-slate-800 mb-4">Ponto de Equilíbrio</h3>
                <div className="space-y-4">
                  <div className="text-center p-6 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-600 mb-2">Receita necessária para break-even</p>
                    <div className="text-3xl font-bold text-slate-800">
                      {formatMoney(analise.break_even.ponto_equilibrio_valor)}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">por mês</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg text-center">
                      <p className="text-sm text-blue-600 mb-1">Custo Fixo Mensal</p>
                      <p className="text-lg font-bold text-blue-800">{formatMoney(analise.break_even.custo_fixo_mensal)}</p>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg text-center">
                      <p className="text-sm text-purple-600 mb-1">Custo Variável</p>
                      <p className="text-lg font-bold text-purple-800">{formatPct(analise.break_even.custo_variavel_pct)}</p>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-green-50 rounded-lg text-center">
                    <p className="text-sm text-green-600 mb-1">Margem de Contribuição</p>
                    <p className="text-2xl font-bold text-green-800">{formatPct(analise.break_even.margem_contribuicao_pct)}</p>
                  </div>
                </div>
              </Card>
              
              <Card className="p-6">
                <h3 className="font-semibold text-slate-800 mb-4">Situação Atual</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-4 bg-slate-50 rounded-lg">
                    <span className="text-slate-600">Receita Atual (média)</span>
                    <span className="text-xl font-bold">{formatMoney(analise.break_even.receita_media_mensal)}</span>
                  </div>
                  
                  <div className={`p-4 rounded-lg text-center ${(analise.break_even.folga_pct || 0) >= 20 ? 'bg-green-50' : (analise.break_even.folga_pct || 0) >= 0 ? 'bg-yellow-50' : 'bg-red-50'}`}>
                    <p className="text-sm mb-1">Margem de Segurança</p>
                    <p className={`text-3xl font-bold ${(analise.break_even.folga_pct || 0) >= 20 ? 'text-green-700' : (analise.break_even.folga_pct || 0) >= 0 ? 'text-yellow-700' : 'text-red-700'}`}>
                      {(analise.break_even.folga_pct || 0) >= 0 ? '+' : ''}{formatPct(analise.break_even.folga_pct || 0)}
                    </p>
                    <p className="text-sm mt-1">
                      {(analise.break_even.folga_operacional || 0) >= 0 ? 'Folga de ' : 'Déficit de '}
                      {formatMoney(Math.abs(analise.break_even.folga_operacional || 0))}/mês
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <h4 className="font-medium text-slate-700">Metas de Receita</h4>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Para lucro de 10%</span>
                      <span className="font-medium">{formatMoney(analise.break_even.receita_para_lucro_10pct)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Para lucro de 20%</span>
                      <span className="font-medium">{formatMoney(analise.break_even.receita_para_lucro_20pct)}</span>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          )}
          
          {abaAtiva === 'projecoes' && analise.projecoes?.length > 0 && (
            <Card className="p-6">
              <h3 className="font-semibold text-slate-800 mb-4">Projeções para os Próximos 12 Meses</h3>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {['pessimista', 'realista', 'otimista'].map(cenario => {
                  const proj = analise.projecoes.find(p => p.cenario === cenario);
                  const ultimo = proj?.dados_mensais?.[proj?.dados_mensais?.length - 1];
                  const cores = {
                    pessimista: 'border-red-200 bg-red-50',
                    realista: 'border-blue-200 bg-blue-50',
                    otimista: 'border-green-200 bg-green-50'
                  };
                  const textos = {
                    pessimista: 'text-red-800',
                    realista: 'text-blue-800',
                    otimista: 'text-green-800'
                  };
                  
                  return (
                    <div key={cenario} className={`p-4 rounded-lg border-2 ${cores[cenario]}`}>
                      <h4 className={`font-semibold mb-3 capitalize ${textos[cenario]}`}>
                        Cenário {cenario}
                      </h4>
                      {proj && (
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span>Receita Total</span>
                            <span className="font-medium">{formatMoney(proj.receita_total)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Lucro Total</span>
                            <span className={`font-medium ${proj.lucro_total < 0 ? 'text-red-600' : ''}`}>
                              {formatMoney(proj.lucro_total)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Caixa Final</span>
                            <span className={`font-medium ${proj.caixa_final < 0 ? 'text-red-600' : ''}`}>
                              {formatMoney(proj.caixa_final)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Margem Média</span>
                            <span className="font-medium">{formatPct(proj.margem_media)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Taxa Crescimento</span>
                            <span className="font-medium">{proj.taxa_crescimento_receita?.toFixed(1)}%/mês</span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              
              <div className="mt-6 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-100">
                      <th className="py-2 px-3 text-left">Mês</th>
                      <th className="py-2 px-3 text-right" colSpan={2}>Pessimista</th>
                      <th className="py-2 px-3 text-right" colSpan={2}>Realista</th>
                      <th className="py-2 px-3 text-right" colSpan={2}>Otimista</th>
                    </tr>
                    <tr className="bg-slate-50 text-xs text-slate-600">
                      <th></th>
                      <th className="py-1 px-3 text-right">Receita</th>
                      <th className="py-1 px-3 text-right">Lucro</th>
                      <th className="py-1 px-3 text-right">Receita</th>
                      <th className="py-1 px-3 text-right">Lucro</th>
                      <th className="py-1 px-3 text-right">Receita</th>
                      <th className="py-1 px-3 text-right">Lucro</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map(idx => {
                      const projPess = analise.projecoes.find(p => p.cenario === 'pessimista');
                      const projReal = analise.projecoes.find(p => p.cenario === 'realista');
                      const projOtim = analise.projecoes.find(p => p.cenario === 'otimista');
                      
                      const pess = projPess?.dados_mensais?.[idx];
                      const real = projReal?.dados_mensais?.[idx];
                      const otim = projOtim?.dados_mensais?.[idx];
                      
                      if (!pess) return null;
                      
                      return (
                        <tr key={idx} className="border-b">
                          <td className="py-2 px-3">{String(pess.mes).padStart(2, '0')}/{pess.ano}</td>
                          <td className="py-2 px-3 text-right text-red-700">{formatMoney(pess.receita)}</td>
                          <td className={`py-2 px-3 text-right ${pess.lucro < 0 ? 'text-red-600' : ''}`}>{formatMoney(pess.lucro)}</td>
                          <td className="py-2 px-3 text-right text-blue-700">{formatMoney(real?.receita)}</td>
                          <td className={`py-2 px-3 text-right ${(real?.lucro || 0) < 0 ? 'text-red-600' : ''}`}>{formatMoney(real?.lucro)}</td>
                          <td className="py-2 px-3 text-right text-green-700">{formatMoney(otim?.receita)}</td>
                          <td className={`py-2 px-3 text-right ${(otim?.lucro || 0) < 0 ? 'text-red-600' : ''}`}>{formatMoney(otim?.lucro)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
          
          {abaAtiva === 'benchmarks' && analise.benchmarks?.length > 0 && (
            <Card className="p-6">
              <h3 className="font-semibold text-slate-800 mb-4">Comparação com o Setor</h3>
              <div className="space-y-6">
                {analise.benchmarks.map((bench, idx) => (
                  <div key={idx} className="border-b pb-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">{bench.indicador}</span>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        bench.posicao === 'acima' ? 'bg-green-100 text-green-700' :
                        bench.posicao === 'abaixo' ? 'bg-red-100 text-red-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {bench.posicao === 'acima' ? 'Acima da Média' :
                         bench.posicao === 'abaixo' ? 'Abaixo da Média' : 'Na Média'}
                      </span>
                    </div>
                    
                    <div className="relative h-8 bg-slate-100 rounded-full overflow-hidden">
                      {/* Faixa do setor */}
                      <div 
                        className="absolute h-full bg-slate-300 opacity-50"
                        style={{
                          left: `${Math.max(0, (bench.valor_setor_min / Math.max(bench.valor_setor_max, bench.valor_empresa, 1)) * 100)}%`,
                          width: `${((bench.valor_setor_media - bench.valor_setor_min) / Math.max(bench.valor_setor_max, bench.valor_empresa, 1)) * 100}%`
                        }}
                      ></div>
                      
                      {/* Marcador da média do setor */}
                      <div 
                        className="absolute top-0 bottom-0 w-0.5 bg-slate-500"
                        style={{left: `${(bench.valor_setor_media / Math.max(bench.valor_setor_max, bench.valor_empresa, 1) * 100)}%`}}
                      ></div>
                      
                      {/* Valor da empresa */}
                      <div 
                        className={`absolute top-1 bottom-1 w-3 rounded-full ${
                          bench.posicao === 'acima' ? 'bg-green-500' :
                          bench.posicao === 'abaixo' ? 'bg-red-500' : 'bg-blue-500'
                        }`}
                        style={{left: `${Math.min(Math.max((bench.valor_empresa / Math.max(bench.valor_setor_max, bench.valor_empresa, 1) * 100), 2), 98)}%`}}
                      ></div>
                    </div>
                    
                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                      <span>Min: {bench.valor_setor_min?.toFixed(1)}</span>
                      <span>Sua empresa: <strong className={bench.posicao === 'acima' ? 'text-green-600' : bench.posicao === 'abaixo' ? 'text-red-600' : 'text-blue-600'}>{bench.valor_empresa?.toFixed(1)}</strong></span>
                      <span>Média: {bench.valor_setor_media?.toFixed(1)}</span>
                      <span>Max: {bench.valor_setor_max?.toFixed(1)}</span>
                    </div>
                    
                    <p className="text-sm text-slate-600 mt-2">
                      {(bench.diferenca_vs_media || 0) >= 0 ? '+' : ''}{(bench.diferenca_vs_media || 0).toFixed(1)} em relação à média do setor
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}



export { 
  AuthProvider, useAuth, AuthPages, DashboardPage, Sidebar, Header, 
  Card, Button, Input, Select, Badge, StatusBadge, ScoreCircle, 
  Modal, EmptyState, LoadingScreen, ToastProvider, useToast, LoadingOverlay,
  OrganizationProvider, useOrganization, OrganizationSelector, TeamMembersPage, AuditLogPage,
  PlanosPage, FaturasPage, UsoPage,
  ImportacaoAvancadaPage, ImportUploadModal,
  RelatoriosPage,
  AlertasPage,
  AnaliseFinanceiraPage,
  ThemeProvider, useTheme
};
