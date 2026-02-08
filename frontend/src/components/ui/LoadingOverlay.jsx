import React from 'react';
import { Loader2 } from 'lucide-react';

function LoadingOverlay({ message = 'Processando...' }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl p-8 flex flex-col items-center gap-4 shadow-xl">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
        <p className="text-slate-700 font-medium">{message}</p>
      </div>
    </div>
  );
}

export default LoadingOverlay;
