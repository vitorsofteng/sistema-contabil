import React from 'react';
import { FileText } from 'lucide-react';
import { useExport } from '../../contexts/ExportContext';

function ExportButton() {
  const { setPanelOpen, pendingCount, readyCount } = useExport();

  const totalBadge = pendingCount + readyCount;
  const isPending = pendingCount > 0;

  return (
    <button
      onClick={() => setPanelOpen(true)}
      className="fixed top-4 right-4 z-30 flex items-center gap-2 bg-white hover:bg-slate-50 border border-slate-200 shadow-sm rounded-xl px-3 py-2 transition-all hover:shadow-md group"
      title="Exportações"
    >
      <div className="relative">
        <FileText className={`w-4.5 h-4.5 ${isPending ? 'text-blue-500' : 'text-slate-500'} group-hover:text-slate-700 transition-colors`} />
        {isPending && (
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
        )}
      </div>
      {totalBadge > 0 && (
        <span className={`text-xs font-medium px-1.5 py-0.5 rounded-full ${
          readyCount > 0 
            ? 'bg-emerald-100 text-emerald-700' 
            : 'bg-blue-100 text-blue-700'
        }`}>
          {readyCount > 0 ? `${readyCount} pronto${readyCount > 1 ? 's' : ''}` : `${pendingCount}...`}
        </span>
      )}
    </button>
  );
}

export default ExportButton;
