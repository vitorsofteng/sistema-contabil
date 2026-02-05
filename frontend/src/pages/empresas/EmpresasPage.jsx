import React, { useState, useEffect } from 'react';
import { Building2, ChevronRight, Plus, Search } from 'lucide-react';
import { Badge, Button, Card, EmptyState, LoadingScreen, ScoreCircle, StatusBadge } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

function EmpresasPage({ onNavigate }) {
  const { api } = useAuth();
  const toast = useToast();
  const [empresas, setEmpresas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => { loadEmpresas(); }, []);

  const loadEmpresas = async () => {
    try {
      const res = await api(`/empresas?search=${encodeURIComponent(search)}`);
      if (res.ok) {
        const data = await res.json();
        setEmpresas(data.empresas || data || []);
      }
    } catch (err) {
      toast.error('Erro ao carregar empresas');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setLoading(true);
    loadEmpresas();
  };

  if (loading && empresas.length === 0) return <LoadingScreen />;

  return (
    <div>
      <Header 
        title="Empresas" 
        subtitle={`${empresas.length} empresa(s) cadastrada(s)`}
        actions={
          <Button onClick={() => onNavigate('nova-empresa')}>
            <Plus className="w-4 h-4" /> Nova Empresa
          </Button>
        }
      />
      
      <Card className="p-4 mb-6">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Buscar por nome, CNPJ..."
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <Button type="submit" variant="secondary">Buscar</Button>
        </form>
      </Card>
      
      {empresas.length > 0 ? (
        <div className="grid gap-4">
          {empresas.map(emp => (
            <Card 
              key={emp.id} 
              className="p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => onNavigate('empresa', emp.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <ScoreCircle score={emp.ultimo_score} size="md" />
                  <div>
                    <h3 className="font-semibold text-slate-900">{emp.razao_social}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      {emp.cnpj && <span className="text-sm text-slate-500">{emp.cnpj}</span>}
                      {emp.regime_tributario && (
                        <Badge variant="info" size="sm">{emp.regime_tributario}</Badge>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    {emp.ultimo_status && <StatusBadge status={emp.ultimo_status} />}
                    <p className="text-sm text-slate-500 mt-1">
                      {emp.meses_dados} meses de dados
                    </p>
                  </div>
                  {emp.alertas_pendentes > 0 && (
                    <Badge variant="danger">{emp.alertas_pendentes} alertas</Badge>
                  )}
                  <ChevronRight className="w-5 h-5 text-slate-400" />
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="p-8">
          <EmptyState 
            icon={Building2}
            title="Nenhuma empresa encontrada"
            description="Cadastre sua primeira empresa para começar"
            action={
              <Button onClick={() => onNavigate('nova-empresa')}>
                <Plus className="w-4 h-4" /> Cadastrar Empresa
              </Button>
            }
          />
        </Card>
      )}
    </div>
  );
}

export default EmpresasPage;
