import React, { useState, useEffect } from 'react';
import { BarChart3, Building2, FileText, Users } from 'lucide-react';
import { BarChart } from 'recharts';
import { Card, LoadingScreen } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useOrganization } from '../../contexts/OrganizationContext';

function UsoPage() {
  const { api } = useAuth();
  const { currentOrg } = useOrganization();
  const [uso, setUso] = useState(null);
  const [assinatura, setAssinatura] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentOrg) {
      loadUso();
      loadAssinatura();
    }
  }, [currentOrg]);

  const loadUso = async () => {
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/uso`);
      if (res.ok) {
        const data = await res.json();
        setUso(data.uso);
      }
    } catch (err) {
      console.error('Erro ao carregar uso:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadAssinatura = async () => {
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/assinatura`);
      if (res.ok) {
        const data = await res.json();
        setAssinatura(data.assinatura);
      }
    } catch (err) {
      console.error('Erro ao carregar assinatura:', err);
    }
  };

  if (!currentOrg) {
    return (
      <div className="p-6">
        <Card className="p-8 text-center">
          <BarChart3 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Selecione uma organização</p>
        </Card>
      </div>
    );
  }

  if (loading) return <LoadingScreen />;

  const limites = assinatura?.plano?.limites || {};

  const calcPercent = (atual, max) => Math.min(100, (atual / max) * 100);

  const UsageBar = ({ label, atual, max, icon: Icon }) => {
    const percent = calcPercent(atual, max);
    const isNearLimit = percent >= 80;

    return (
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <div className="flex items-center gap-2">
            <Icon className="w-4 h-4 text-slate-500" />
            <span className="text-sm font-medium text-slate-700">{label}</span>
          </div>
          <span className={`text-sm ${isNearLimit ? 'text-orange-600 font-semibold' : 'text-slate-500'}`}>
            {atual} / {max}
          </span>
        </div>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full transition-all ${
              isNearLimit ? 'bg-orange-500' : 'bg-blue-500'
            }`}
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <div>
      <Header 
        title="Uso e Limites" 
        subtitle={`Consumo de ${currentOrg.nome} em ${uso?.periodo || 'mês atual'}`}
      />

      <div className="grid md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="font-semibold text-slate-800 mb-4">Recursos</h3>
          
          <UsageBar 
            label="Empresas" 
            atual={uso?.empresas_ativas || 0} 
            max={limites.empresas || 5}
            icon={Building2}
          />
          <UsageBar 
            label="Usuários" 
            atual={uso?.usuarios_ativos || 0} 
            max={limites.usuarios || 1}
            icon={Users}
          />
          <UsageBar 
            label="Análises" 
            atual={uso?.analises_realizadas || 0} 
            max={limites.analises_mes || 10}
            icon={BarChart3}
          />
          <UsageBar 
            label="Storage (MB)" 
            atual={uso?.storage_usado_mb?.toFixed(1) || 0} 
            max={limites.storage_mb || 100}
            icon={FileText}
          />
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold text-slate-800 mb-4">Atividade</h3>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center py-3 border-b border-slate-100">
              <span className="text-slate-600">Relatórios gerados</span>
              <span className="font-semibold text-slate-800">{uso?.relatorios_gerados || 0}</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-slate-100">
              <span className="text-slate-600">Chamadas API</span>
              <span className="font-semibold text-slate-800">{uso?.api_calls || 0}</span>
            </div>
            <div className="flex justify-between items-center py-3">
              <span className="text-slate-600">Período</span>
              <span className="font-semibold text-slate-800">{uso?.periodo || '-'}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default UsoPage;
