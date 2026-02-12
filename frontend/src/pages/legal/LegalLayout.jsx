import React from 'react';
import { BarChart3, ArrowLeft, FileText, Shield, Cookie } from 'lucide-react';

function LegalLayout({ children, title, onBack, onNavigate, currentPage }) {
  const tabs = [
    { id: 'termos', label: 'Termos de Uso', icon: FileText },
    { id: 'privacidade', label: 'Política de Privacidade', icon: Shield },
    { id: 'cookies', label: 'Política de Cookies', icon: Cookie },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={onBack}
                className="p-2 -ml-2 hover:bg-slate-100 rounded-lg transition-colors"
                title="Voltar"
              >
                <ArrowLeft className="w-5 h-5 text-slate-600" />
              </button>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-white" />
                </div>
                <span className="font-bold text-slate-900">Kontabil</span>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 mt-4 -mb-px overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => onNavigate(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg border-b-2 transition-colors whitespace-nowrap ${
                  currentPage === tab.id
                    ? 'border-emerald-500 text-emerald-700 bg-emerald-50/50'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-10">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">{title}</h1>
          <p className="text-sm text-slate-400 mb-8">
            Última atualização: {new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' })}
            {' · '}Versão 1.0
          </p>
          <div className="prose prose-slate max-w-none prose-headings:text-slate-800 prose-p:text-slate-600 prose-p:leading-relaxed prose-li:text-slate-600 prose-strong:text-slate-700">
            {children}
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 text-center text-sm text-slate-400 pb-8">
          <p>Kontabil — Análise Financeira Inteligente</p>
          <p className="mt-1">
            Dúvidas? Entre em contato:{' '}
            <a href="mailto:contato@kontabil.com.br" className="text-emerald-600 hover:underline">
              contato@kontabil.com.br
            </a>
          </p>
        </footer>
      </main>
    </div>
  );
}

export default LegalLayout;
