import React from 'react';
import { FileSpreadsheet, Plus, Upload } from 'lucide-react';
import { Button, Card, EmptyState } from '../../../components/ui';

function DadosTab({ registros, onAddManual, onUpload }) {
  const formatMoney = (v) => {
    if (v === null || v === undefined) return '—';
    return `R$ ${Number(v).toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0})}`;
  };

  const calcularLucro = (r) => {
    const receita = r.receita || r.receita_bruta || 0;
    const custos = r.custos || r.custos_total || 0;
    const despesas = r.despesas || r.despesas_operacionais || 0;
    const impostos = r.impostos || r.impostos_total || 0;
    return r.lucro_liquido ?? (receita - custos - despesas - impostos);
  };

  const calcularMargem = (r) => {
    const receita = r.receita || r.receita_bruta || 0;
    if (receita === 0) return 0;
    const lucro = calcularLucro(r);
    return (lucro / receita) * 100;
  };

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-900">Dados Mensais</h3>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={onAddManual}><Plus className="w-4 h-4" /> Adicionar Manual</Button>
          <Button variant="secondary" size="sm" onClick={onUpload}><Upload className="w-4 h-4" /> Importar CSV</Button>
        </div>
      </div>
      {registros.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b">
                {['Competência', 'Receita', 'Custos', 'Despesas', 'Lucro', 'Margem'].map(h => <th key={h} className="pb-3 font-medium">{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {registros.map(r => {
                const lucro = calcularLucro(r);
                const margem = calcularMargem(r);
                return (
                  <tr key={r.id} className="border-b last:border-0">
                    <td className="py-3 font-medium">{r.competencia || `${r.ano}-${String(r.mes).padStart(2, '0')}`}</td>
                    <td className="py-3">{formatMoney(r.receita || r.receita_bruta)}</td>
                    <td className="py-3 text-red-600">{formatMoney(r.custos || r.custos_total)}</td>
                    <td className="py-3 text-red-600">{formatMoney(r.despesas || r.despesas_operacionais)}</td>
                    <td className={`py-3 ${lucro >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatMoney(lucro)}</td>
                    <td className={`py-3 ${margem >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{margem.toFixed(1)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState icon={FileSpreadsheet} title="Nenhum dado cadastrado" description="Importe um CSV ou adicione manualmente"
          action={<Button onClick={onUpload}><Upload className="w-4 h-4" /> Importar Dados</Button>} />
      )}
    </Card>
  );
}

export default DadosTab;
