import React, { useState, useEffect } from 'react';
import { Activity, Edit, Plus, Trash2, User } from 'lucide-react';
import { Card, LoadingScreen } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useOrganization } from '../../contexts/OrganizationContext';

function AuditLogPage() {
  const { api } = useAuth();
  const { currentOrg } = useOrganization();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentOrg) {
      loadLogs();
    }
  }, [currentOrg]);

  const loadLogs = async () => {
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/audit?limite=100`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
      }
    } catch (err) {
      console.error('Erro ao carregar logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (acao) => {
    switch (acao) {
      case 'create': return <Plus className="w-4 h-4 text-green-600" />;
      case 'update': return <Edit className="w-4 h-4 text-blue-600" />;
      case 'delete': return <Trash2 className="w-4 h-4 text-red-600" />;
      case 'login': return <User className="w-4 h-4 text-purple-600" />;
      default: return <Activity className="w-4 h-4 text-slate-600" />;
    }
  };

  if (!currentOrg) {
    return (
      <div className="p-6">
        <Card className="p-8 text-center">
          <Activity className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Selecione uma organização</p>
        </Card>
      </div>
    );
  }

  if (loading) return <LoadingScreen />;

  return (
    <div>
      <Header 
        title="Logs de Auditoria" 
        subtitle={`Atividades em ${currentOrg.nome}`}
      />

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Ação</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Recurso</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Usuário</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Data</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map(log => (
                <tr key={log.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {getActionIcon(log.acao)}
                      <span className="text-sm font-medium text-slate-700 capitalize">{log.acao}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600 capitalize">{log.recurso}</td>
                  <td className="px-4 py-3 text-sm text-slate-600">{log.usuario_nome}</td>
                  <td className="px-4 py-3 text-sm text-slate-500">
                    {new Date(log.created_at).toLocaleString('pt-BR')}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400 font-mono">{log.ip_address || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

export default AuditLogPage;
