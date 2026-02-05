import React, { useState, useEffect } from 'react';
import { CheckCircle, Loader2 } from 'lucide-react';
import { Badge, Button, Card, LoadingScreen } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import { useOrganization } from '../../contexts/OrganizationContext';

function PlanosPage({ onSelectPlan }) {
  const { api } = useAuth();
  const { currentOrg, refreshOrganizations } = useOrganization();
  const toast = useToast();
  const [planos, setPlanos] = useState([]);
  const [assinatura, setAssinatura] = useState(null);
  const [loading, setLoading] = useState(true);
  const [ciclo, setCiclo] = useState('mensal');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    loadPlanos();
    if (currentOrg) loadAssinatura();
  }, [currentOrg]);

  const loadPlanos = async () => {
    try {
      const res = await api('/planos');
      if (res.ok) {
        const data = await res.json();
        setPlanos(data.planos || []);
      }
    } catch (err) {
      toast.error('Erro ao carregar planos');
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

  const handleSelectPlan = async (plano) => {
    if (!currentOrg) {
      toast.error('Selecione uma organização primeiro');
      return;
    }

    setProcessing(true);
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/assinatura`, {
        method: 'POST',
        body: JSON.stringify({ plano: plano.codigo, ciclo })
      });
      
      if (res.ok) {
        toast.success(`Plano ${plano.nome} ativado!`);
        loadAssinatura();
        refreshOrganizations();
        if (onSelectPlan) onSelectPlan(plano);
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Erro ao selecionar plano');
      }
    } catch (err) {
      toast.error('Erro ao processar solicitação');
    } finally {
      setProcessing(false);
    }
  };

  const handleStartTrial = async () => {
    if (!currentOrg) {
      toast.error('Selecione uma organização primeiro');
      return;
    }

    setProcessing(true);
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/assinatura/trial`, {
        method: 'POST'
      });
      
      if (res.ok) {
        toast.success('Período de teste iniciado!');
        loadAssinatura();
        refreshOrganizations();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Erro ao iniciar teste');
      }
    } catch (err) {
      toast.error('Erro ao iniciar período de teste');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) return <LoadingScreen />;

  const planoAtual = assinatura?.plano?.codigo || 'free';

  return (
    <div>
      <Header 
        title="Planos e Preços" 
        subtitle="Escolha o plano ideal para seu escritório"
      />

      {/* Status atual */}
      {assinatura && (
        <Card className="p-4 mb-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Plano atual</p>
              <p className="text-xl font-bold text-slate-800">{assinatura.plano?.nome || 'Gratuito'}</p>
              {assinatura.is_trialing && (
                <p className="text-sm text-orange-600">
                  ⏰ {assinatura.dias_restantes_trial} dias restantes de teste
                </p>
              )}
            </div>
            <Badge variant={assinatura.is_active ? 'success' : 'warning'}>
              {assinatura.status_label}
            </Badge>
          </div>
        </Card>
      )}

      {/* Toggle mensal/anual */}
      <div className="flex justify-center mb-8">
        <div className="bg-slate-100 p-1 rounded-xl inline-flex">
          <button
            onClick={() => setCiclo('mensal')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
              ciclo === 'mensal' 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            Mensal
          </button>
          <button
            onClick={() => setCiclo('anual')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
              ciclo === 'anual' 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            Anual <span className="text-green-600 text-xs ml-1">-17%</span>
          </button>
        </div>
      </div>

      {/* Cards de planos */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {planos.map(plano => {
          const preco = ciclo === 'mensal' ? plano.preco_mensal : plano.preco_anual / 12;
          const isAtual = plano.codigo === planoAtual;
          const isPopular = plano.codigo === 'pro';

          return (
            <Card 
              key={plano.id} 
              className={`p-6 relative ${isPopular ? 'border-2 border-blue-500 shadow-lg' : ''} ${isAtual ? 'ring-2 ring-green-500' : ''}`}
            >
              {isPopular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                    POPULAR
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-slate-800">{plano.nome}</h3>
                <p className="text-sm text-slate-500 mt-1">{plano.descricao}</p>
                
                <div className="mt-4">
                  <span className="text-4xl font-bold text-slate-800">
                    R$ {preco.toFixed(0)}
                  </span>
                  <span className="text-slate-500">/mês</span>
                </div>
                
                {ciclo === 'anual' && plano.economia_anual > 0 && (
                  <p className="text-sm text-green-600 mt-1">
                    Economia de R$ {plano.economia_anual.toFixed(0)}/ano
                  </p>
                )}
              </div>

              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>{plano.limites.usuarios} usuário(s)</span>
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>{plano.limites.empresas} empresa(s)</span>
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>{plano.limites.analises_mes} análises/mês</span>
                </li>
                {plano.features.api && (
                  <li className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Acesso API</span>
                  </li>
                )}
                {plano.features.whitelabel && (
                  <li className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>White-label</span>
                  </li>
                )}
                {plano.features.suporte_prioritario && (
                  <li className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Suporte prioritário</span>
                  </li>
                )}
              </ul>

              {isAtual ? (
                <Button disabled className="w-full" variant="secondary">
                  Plano Atual
                </Button>
              ) : plano.codigo === 'free' ? (
                <Button 
                  className="w-full" 
                  variant="secondary"
                  disabled={processing}
                >
                  Gratuito
                </Button>
              ) : (
                <Button 
                  onClick={() => handleSelectPlan(plano)}
                  className="w-full"
                  disabled={processing}
                >
                  {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Assinar'}
                </Button>
              )}
            </Card>
          );
        })}
      </div>

      {/* CTA Trial */}
      {planoAtual === 'free' && !assinatura?.is_trialing && (
        <Card className="p-6 mt-8 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-center">
          <h3 className="text-2xl font-bold mb-2">Teste grátis por 14 dias</h3>
          <p className="text-purple-100 mb-4">
            Experimente o plano Profissional sem compromisso
          </p>
          <Button 
            onClick={handleStartTrial}
            disabled={processing}
            className="bg-white text-purple-600 hover:bg-purple-50"
          >
            {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Começar teste grátis'}
          </Button>
        </Card>
      )}
    </div>
  );
}

export default PlanosPage;
