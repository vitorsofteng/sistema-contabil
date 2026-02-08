import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle, AlertTriangle, Menu } from 'lucide-react';

// Contexts
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { ToastProvider } from './contexts/ToastContext';
import { ExportProvider } from './contexts/ExportContext';

// Layout
import { Sidebar, ExportPanel } from './components/layout';
import { LoadingScreen } from './components/ui';

// Pages
import { AuthPages, EmailPendingVerification } from './pages/auth';
import { DashboardPage } from './pages/dashboard';
import { EmpresasPage, NovaEmpresaPage, EmpresaDetailPage } from './pages/empresas';
import { ImportacaoPage } from './pages/importacao';
import { RelatoriosPage } from './pages/relatorios';
import { AlertasPage } from './pages/alertas';
import { AnaliseFinanceiraPage } from './pages/analise';

// Config
import { API_URL } from './config/api';

function AppContent() {
  const { user, loading, pendingVerification, completePendingVerification } = useAuth();
  const themeCtx = useTheme();
  const theme = themeCtx?.theme || {};
  const [page, setPage] = useState('dashboard');
  const [pageParams, setPageParams] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const [emailVerifying, setEmailVerifying] = useState(false);
  const [emailVerifyResult, setEmailVerifyResult] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const verifyToken = params.get('verify_email');
    const resetTokenParam = params.get('reset_token');
    
    if (verifyToken) {
      setEmailVerifying(true);
      fetch(`${API_URL}/auth/verificar-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: verifyToken })
      })
        .then(r => r.json())
        .then(data => {
          if (data.ok) {
            setEmailVerifyResult({ success: true, message: data.message });
          } else {
            setEmailVerifyResult({ success: false, message: data.detail || 'Erro ao verificar email' });
          }
        })
        .catch(() => setEmailVerifyResult({ success: false, message: 'Erro de conexão' }))
        .finally(() => {
          setEmailVerifying(false);
          window.history.replaceState({}, '', window.location.pathname);
        });
    }
    
    if (resetTokenParam && localStorage.getItem('token')) {
      // AuthPages vai pegar o param
    }
  }, []);

  // Tela de verificação de email
  if (emailVerifying || emailVerifyResult) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-md text-center">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            {emailVerifying && (
              <div className="animate-pulse">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Verificando email...</h2>
                <p className="text-slate-500">Aguarde um momento</p>
              </div>
            )}
            {emailVerifyResult?.success && (
              <div>
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-emerald-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Email verificado!</h2>
                <p className="text-slate-500 mb-6">{emailVerifyResult.message}</p>
                <button
                  onClick={() => { setEmailVerifyResult(null); window.location.reload(); }}
                  className="px-6 py-3 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 transition-colors"
                >
                  Continuar
                </button>
              </div>
            )}
            {emailVerifyResult && !emailVerifyResult.success && (
              <div>
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <AlertTriangle className="w-8 h-8 text-red-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Erro na verificação</h2>
                <p className="text-red-600 mb-6">{emailVerifyResult.message}</p>
                <button
                  onClick={() => { setEmailVerifyResult(null); }}
                  className="px-6 py-3 bg-slate-600 text-white rounded-xl font-medium hover:bg-slate-700 transition-colors"
                >
                  Voltar
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (loading) return <LoadingScreen />;
  
  if (pendingVerification) {
    return <EmailPendingVerification 
      email={pendingVerification.email} 
      nome={pendingVerification.nome}
      onContinue={completePendingVerification}
    />;
  }
  
  if (!user) return <AuthPages />;

  const navigate = (pageName, params = null) => { setPage(pageName); setPageParams(params); setMobileMenuOpen(false); };

  const renderPage = () => {
    switch (page) {
      case 'dashboard': return <DashboardPage onNavigate={navigate} />;
      case 'empresas': return <EmpresasPage onNavigate={navigate} />;
      case 'nova-empresa': return <NovaEmpresaPage onNavigate={navigate} />;
      case 'empresa': return <EmpresaDetailPage empresaId={pageParams} onNavigate={navigate} />;
      case 'alertas': return <AlertasPage onNavigate={navigate} />;
      case 'importacao': return <ImportacaoPage onNavigate={navigate} />;
      case 'relatorios': return <RelatoriosPage onNavigate={navigate} />;
      case 'analise-financeira': 
        return <AnaliseFinanceiraPage 
          empresaId={pageParams?.empresaId} 
          empresaNome={pageParams?.empresaNome}
          onBack={() => navigate('empresa', pageParams?.empresaId)} 
        />;
      default: return <DashboardPage onNavigate={navigate} />;
    }
  };

  return (
    <ExportProvider>
      <div className="min-h-screen bg-slate-50">
        <Sidebar 
          currentPage={page} 
          onNavigate={navigate} 
          collapsed={sidebarCollapsed} 
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
          mobileOpen={mobileMenuOpen}
          onMobileClose={() => setMobileMenuOpen(false)}
        />
        {/* Mobile top bar */}
        <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-white border-b border-slate-200 flex items-center px-4 z-30">
          <button onClick={() => setMobileMenuOpen(true)} className="p-2 -ml-2 hover:bg-slate-100 rounded-lg">
            <Menu className="w-5 h-5 text-slate-700" />
          </button>
          <span className="ml-2 font-semibold text-slate-900 truncate">{theme?.nome_escritorio || 'Kontabil'}</span>
        </div>
        <main className={`transition-all pt-14 md:pt-0 ${sidebarCollapsed ? 'md:ml-16' : 'md:ml-64'} p-4 md:p-6`}>{renderPage()}</main>
        <ExportPanel />
      </div>
    </ExportProvider>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <ToastProvider>
          <AppContent />
        </ToastProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}
