import React, { useState, useEffect } from 'react';
import { Building2, Download, FileText } from 'lucide-react';
import { Card, LoadingScreen } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useOrganization } from '../../contexts/OrganizationContext';

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

export default FaturasPage;
