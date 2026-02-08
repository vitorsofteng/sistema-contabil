import React from 'react';
import { X, Download, Loader2, CheckCircle, AlertCircle, Clock, Trash2, FileText, FileSpreadsheet, Presentation } from 'lucide-react';
import { useExport } from '../../contexts/ExportContext';

const STATUS_CONFIG = {
  pendente: {
    icon: Clock,
    color: 'text-amber-500',
    bg: 'bg-amber-50',
    label: 'Na fila',
  },
  processando: {
    icon: Loader2,
    color: 'text-blue-500',
    bg: 'bg-blue-50',
    label: 'Gerando...',
    animate: true,
  },
  concluido: {
    icon: CheckCircle,
    color: 'text-emerald-500',
    bg: 'bg-emerald-50',
    label: 'Pronto para download',
  },
  erro: {
    icon: AlertCircle,
    color: 'text-red-500',
    bg: 'bg-red-50',
    label: 'Erro',
  },
};

const TIPO_CONFIG = {
  pdf: {
    label: 'Relatório Técnico',
    badge: 'PDF',
    badgeColor: 'bg-red-100 text-red-700',
  },
  pdf_parecer: {
    label: 'Parecer Consultivo',
    badge: 'PDF',
    badgeColor: 'bg-emerald-100 text-emerald-700',
  },
  excel: {
    label: 'Planilha Excel',
    badge: 'XLSX',
    badgeColor: 'bg-green-100 text-green-700',
  },
  pptx: {
    label: 'Apresentação',
    badge: 'PPTX',
    badgeColor: 'bg-orange-100 text-orange-700',
  },
};

function ExportItem({ exportacao }) {
  const { baixarExportacao, removerExportacao } = useExport();
  const status = STATUS_CONFIG[exportacao.status] || STATUS_CONFIG.pendente;
  const tipo = TIPO_CONFIG[exportacao.tipo] || TIPO_CONFIG.pdf;
  const StatusIcon = status.icon;

  const timeAgo = (dateStr) => {
    const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
    if (diff < 60) return 'agora';
    if (diff < 3600) return `${Math.floor(diff / 60)}min atrás`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h atrás`;
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  return (
    <div className="px-4 py-3 hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-0">
      <div className="flex items-start gap-3">
        {/* Status icon */}
        <div className={`mt-0.5 p-1.5 rounded-lg ${status.bg}`}>
          <StatusIcon className={`w-4 h-4 ${status.color} ${status.animate ? 'animate-spin' : ''}`} />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-slate-800 truncate">
              {exportacao.empresa_nome || 'Empresa'}
            </p>
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${tipo.badgeColor} shrink-0`}>
              {tipo.badge}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">{tipo.label}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-xs font-medium ${status.color}`}>{status.label}</span>
            <span className="text-xs text-slate-400">· {timeAgo(exportacao.created_at)}</span>
          </div>
          {exportacao.status === 'erro' && exportacao.erro && (
            <p className="text-xs text-red-500 mt-1">{exportacao.erro}</p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 shrink-0">
          {exportacao.status === 'concluido' && (
            <button
              onClick={() => baixarExportacao(exportacao)}
              className="p-1.5 bg-emerald-100 hover:bg-emerald-200 rounded-lg transition-colors"
              title="Baixar"
            >
              <Download className="w-4 h-4 text-emerald-600" />
            </button>
          )}
          {(exportacao.status === 'concluido' || exportacao.status === 'erro') && (
            <button
              onClick={() => removerExportacao(exportacao.id)}
              className="p-1.5 hover:bg-slate-200 rounded-lg transition-colors"
              title="Remover"
            >
              <X className="w-3.5 h-3.5 text-slate-400" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function ExportPanel() {
  const { exportacoes, panelOpen, setPanelOpen, limparConcluidas } = useExport();
  
  const concluidas = exportacoes.filter(e => e.status === 'concluido' || e.status === 'erro').length;

  if (!panelOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/20 z-40 transition-opacity"
        onClick={() => setPanelOpen(false)}
      />
      
      {/* Panel */}
      <div className="fixed top-0 right-0 h-full w-80 bg-white shadow-2xl z-50 flex flex-col animate-slide-in">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2">
            <Download className="w-5 h-5 text-slate-600" />
            <h2 className="font-semibold text-slate-800">Exportações</h2>
            {exportacoes.length > 0 && (
              <span className="text-xs bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded-full">
                {exportacoes.length}
              </span>
            )}
          </div>
          <button
            onClick={() => setPanelOpen(false)}
            className="p-1.5 hover:bg-slate-200 rounded-lg transition-colors"
          >
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {exportacoes.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-6">
              <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mb-3">
                <Download className="w-6 h-6 text-slate-400" />
              </div>
              <p className="text-sm text-slate-500">Nenhuma exportação</p>
              <p className="text-xs text-slate-400 mt-1">
                Exporte relatórios nas páginas de empresas ou relatórios
              </p>
            </div>
          ) : (
            exportacoes.map(exp => (
              <ExportItem key={exp.id} exportacao={exp} />
            ))
          )}
        </div>

        {/* Footer */}
        {concluidas > 0 && (
          <div className="px-4 py-3 border-t border-slate-200 bg-slate-50">
            <button
              onClick={limparConcluidas}
              className="w-full text-center text-xs text-slate-500 hover:text-slate-700 py-1 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5 inline mr-1" />
              Limpar finalizadas
            </button>
          </div>
        )}
      </div>

      {/* Animation */}
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        .animate-slide-in {
          animation: slideIn 0.2s ease-out;
        }
      `}</style>
    </>
  );
}

export default ExportPanel;
