import React from 'react';
import { BarChart3, Building2, FileText, TrendingUp } from 'lucide-react';
import { BarChart } from 'recharts';

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
        <div>
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
          <div className="flex items-center gap-3 mt-4 text-xs text-slate-500">
            <a href="#termos" className="hover:text-slate-300 transition-colors">Termos de Uso</a>
            <span>·</span>
            <a href="#privacidade" className="hover:text-slate-300 transition-colors">Privacidade</a>
            <span>·</span>
            <a href="#cookies" className="hover:text-slate-300 transition-colors">Cookies</a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuthBranding;
