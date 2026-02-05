import React from 'react';
import { Edit, Trash2 } from 'lucide-react';
import { Button, Card } from '../../../components/ui';

function VisaoGeralTab({ empresa, registros, onEdit, onDelete }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Informações da Empresa</h3>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onEdit}>
              <Edit className="w-4 h-4" /> Editar
            </Button>
            <Button variant="ghost" size="sm" onClick={onDelete} className="text-red-600 hover:text-red-700 hover:bg-red-50">
              <Trash2 className="w-4 h-4" /> Excluir
            </Button>
          </div>
        </div>
        <dl className="space-y-2">
          {[['Nome Fantasia', empresa.nome_fantasia], ['Regime Tributário', empresa.regime_tributario], ['Setor', empresa.setor], 
            ['Cidade/UF', `${empresa.cidade || '—'}${empresa.estado ? `/${empresa.estado}` : ''}`],
            ['Email', empresa.email], ['Telefone', empresa.telefone]].map(([k, v]) => (
            <div key={k} className="flex justify-between"><dt className="text-slate-500">{k}</dt><dd className="font-medium">{v || '—'}</dd></div>
          ))}
        </dl>
      </Card>
      <Card className="p-4">
        <h3 className="font-semibold text-slate-900 mb-4">Resumo Financeiro</h3>
        {registros.length > 0 ? (
          <dl className="space-y-2">
            {[['Último Faturamento', `R$ ${registros[0]?.receita_bruta?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`],
              ['Última Margem', `${registros[0]?.margem_liquida?.toFixed(1)}%`],
              ['Saldo em Caixa', `R$ ${registros[0]?.saldo_caixa?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`]].map(([k, v]) => (
              <div key={k} className="flex justify-between"><dt className="text-slate-500">{k}</dt><dd className="font-medium">{v}</dd></div>
            ))}
          </dl>
        ) : <p className="text-slate-500 text-sm">Nenhum dado cadastrado</p>}
      </Card>
    </div>
  );
}

export default VisaoGeralTab;
