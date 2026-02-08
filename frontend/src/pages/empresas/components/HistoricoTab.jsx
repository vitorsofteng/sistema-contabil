import React from 'react';
import { Card, ScoreCircle, StatusBadge } from '../../../components/ui';

function HistoricoTab({ analises }) {
  const formatPeriodo = (analise) => {
    if (analise.periodo_inicio && analise.periodo_fim) {
      return `${analise.periodo_inicio} a ${analise.periodo_fim}`;
    }
    if (analise.periodo_analise) {
      return analise.periodo_analise;
    }
    return `${analise.meses_analisados || 0} meses analisados`;
  };

  return (
    <Card className="p-4">
      <h3 className="font-semibold text-slate-900 mb-4">Histórico de Análises</h3>
      {analises.length > 0 ? (
        <div className="space-y-3">
          {analises.map(a => (
            <div key={a.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div className="flex items-center gap-3">
                <ScoreCircle score={a.score} size="sm" />
                <div>
                  <p className="font-medium text-slate-900">{formatPeriodo(a)}</p>
                  <p className="text-sm text-slate-500">{new Date(a.data_analise).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
                </div>
              </div>
              <StatusBadge status={a.status} />
            </div>
          ))}
        </div>
      ) : <p className="text-slate-500 text-sm">Nenhuma análise no histórico</p>}
    </Card>
  );
}

// ============================================================================
// MODALS
// ============================================================================

export default HistoricoTab;
