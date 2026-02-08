import React, { useState, useEffect } from 'react';
import { Activity, AlertCircle, AlertTriangle, Bell, Check, CheckCircle, DollarSign, Eye, Info, Loader2, RefreshCw, Settings, Target, TrendingDown, TrendingUp, X } from 'lucide-react';
import { Card } from '../../components/ui';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

function AlertasPage({ onNavigate }) {
  const { api } = useAuth();
  const toast = useToast();
  
  const [tab, setTab] = useState('alertas');
  const [alertas, setAlertas] = useState([]);
  const [resumo, setResumo] = useState({
    total: 0,
    nao_lidos: 0,
    por_severidade: { critico: 0, atencao: 0, info: 0 },
    alertas_criticos: [],
    por_empresa: []
  });
  const [empresas, setEmpresas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [gerando, setGerando] = useState(false);
  
  // Filtros
  const [filtroEmpresa, setFiltroEmpresa] = useState('');
  const [filtroSeveridade, setFiltroSeveridade] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('');
  const [apenasNaoLidos, setApenasNaoLidos] = useState(false);
  
  // Configuração de empresa selecionada
  const [empresaSelecionada, setEmpresaSelecionada] = useState(null);
  const [configEmpresa, setConfigEmpresa] = useState(null);
  const [salvandoConfig, setSalvandoConfig] = useState(false);
  
  useEffect(() => {
    loadData();
  }, []);
  
  useEffect(() => {
    loadAlertas();
  }, [filtroEmpresa, filtroSeveridade, filtroTipo, apenasNaoLidos]);
  
  const loadData = async () => {
    setLoading(true);
    try {
      const [resResumo, resEmpresas] = await Promise.all([
        api('/alertas/resumo'),
        api('/empresas')
      ]);
      
      // Parse JSON das respostas
      const dataResumo = await resResumo.json();
      const dataEmpresas = await resEmpresas.json();
      
      // Garantir estrutura do resumo
      setResumo({
        total: dataResumo?.total || 0,
        nao_lidos: dataResumo?.nao_lidos || 0,
        por_severidade: {
          critico: dataResumo?.por_severidade?.critico || 0,
          atencao: dataResumo?.por_severidade?.atencao || 0,
          info: dataResumo?.por_severidade?.info || 0
        },
        alertas_criticos: dataResumo?.alertas_criticos || [],
        por_empresa: dataResumo?.por_empresa || []
      });
      // Garantir que empresas seja array
      const listaEmpresas = dataEmpresas?.empresas || dataEmpresas;
      setEmpresas(Array.isArray(listaEmpresas) ? listaEmpresas : []);
    } catch (err) {
      console.error(err);
    }
    await loadAlertas();
    setLoading(false);
  };
  
  const loadAlertas = async () => {
    try {
      let url = '/alertas?limite=100';
      if (filtroEmpresa) url += `&empresa_id=${filtroEmpresa}`;
      if (filtroSeveridade) url += `&severidade=${filtroSeveridade}`;
      if (filtroTipo) url += `&tipo=${filtroTipo}`;
      if (apenasNaoLidos) url += '&apenas_nao_lidos=true';
      
      const res = await api(url);
      const data = await res.json();
      // Garantir que alertas seja array
      const listaAlertas = data?.alertas || data;
      setAlertas(Array.isArray(listaAlertas) ? listaAlertas : []);
    } catch (err) {
      console.error(err);
      setAlertas([]);
    }
  };
  
  const loadConfigEmpresa = async (empresaId) => {
    try {
      const res = await api(`/empresas/${empresaId}/alertas/configuracao`);
      const data = await res.json();
      setConfigEmpresa(data);
    } catch (err) {
      console.error(err);
      setConfigEmpresa(null);
    }
  };
  
  const gerarAlertasTodos = async () => {
    setGerando(true);
    try {
      const res = await api('/alertas/gerar-todos', { method: 'POST' });
      const data = await res.json();
      toast.success(`${data.total_alertas_salvos || 0} novos alertas gerados!`);
      await loadData();
    } catch (err) {
      toast.error('Erro ao gerar alertas');
    }
    setGerando(false);
  };
  
  // Helper para garantir estrutura do resumo
  const parseResumo = (res) => ({
    total: res?.total || 0,
    nao_lidos: res?.nao_lidos || 0,
    por_severidade: {
      critico: res?.por_severidade?.critico || 0,
      atencao: res?.por_severidade?.atencao || 0,
      info: res?.por_severidade?.info || 0
    },
    alertas_criticos: res?.alertas_criticos || [],
    por_empresa: res?.por_empresa || []
  });
  
  const gerarAlertasEmpresa = async (empresaId) => {
    setGerando(true);
    try {
      const res = await api(`/empresas/${empresaId}/alertas/gerar`, { method: 'POST' });
      const data = await res.json();
      toast.success(`${data.alertas_salvos || 0} novos alertas gerados!`);
      await loadAlertas();
      const resResumo = await api('/alertas/resumo');
      const dataResumo = await resResumo.json();
      setResumo(parseResumo(dataResumo));
    } catch (err) {
      toast.error('Erro ao gerar alertas');
    }
    setGerando(false);
  };
  
  const marcarLido = async (alertaId) => {
    try {
      await api(`/alertas/${alertaId}/lido`, { method: 'POST' });
      await loadAlertas();
      const resResumo = await api('/alertas/resumo');
      const dataResumo = await resResumo.json();
      setResumo(parseResumo(dataResumo));
    } catch (err) {
      toast.error('Erro ao marcar como lido');
    }
  };
  
  const resolverAlerta = async (alertaId, nota = '') => {
    try {
      await api(`/alertas/${alertaId}/resolver`, { 
        method: 'POST',
        body: JSON.stringify({ nota })
      });
      toast.success('Alerta resolvido!');
      await loadAlertas();
      const resResumo = await api('/alertas/resumo');
      const dataResumo = await resResumo.json();
      setResumo(parseResumo(dataResumo));
    } catch (err) {
      toast.error('Erro ao resolver alerta');
    }
  };
  
  const marcarTodosLidos = async () => {
    try {
      await api('/alertas/marcar-todos-lidos', { method: 'POST' });
      toast.success('Todos os alertas marcados como lidos');
      await loadAlertas();
      const resResumo = await api('/alertas/resumo');
      const dataResumo = await resResumo.json();
      setResumo(parseResumo(dataResumo));
    } catch (err) {
      toast.error('Erro ao marcar alertas');
    }
  };
  
  const salvarConfigEmpresa = async () => {
    if (!empresaSelecionada || !configEmpresa) return;
    
    setSalvandoConfig(true);
    try {
      await api(`/empresas/${empresaSelecionada}/alertas/configuracao`, {
        method: 'PUT',
        body: JSON.stringify(configEmpresa)
      });
      toast.success('Configuração salva!');
    } catch (err) {
      toast.error('Erro ao salvar configuração');
    }
    setSalvandoConfig(false);
  };
  
  const getSeveridadeStyle = (sev) => {
    switch (sev) {
      case 'critico': return 'bg-red-100 text-red-800 border-red-200';
      case 'atencao': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getSeveridadeIcon = (sev) => {
    switch (sev) {
      case 'critico': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'atencao': return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'info': return <Info className="w-5 h-5 text-blue-500" />;
      default: return <Bell className="w-5 h-5 text-gray-500" />;
    }
  };
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }
  
  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alertas Inteligentes</h1>
          <p className="text-gray-500">Monitore a saúde financeira das suas empresas</p>
        </div>
        <button
          onClick={gerarAlertasTodos}
          disabled={gerando}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {gerando ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          Verificar Todas
        </button>
      </div>
      
      {/* Cards de Resumo */}
      {resumo && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total de Alertas</p>
                <p className="text-2xl font-bold">{resumo.total || 0}</p>
              </div>
              <Bell className="w-8 h-8 text-gray-400" />
            </div>
          </Card>
          
          <Card className={`p-4 ${(resumo.por_severidade?.critico || 0) > 0 ? 'border-red-300 bg-red-50' : ''}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Críticos</p>
                <p className="text-2xl font-bold text-red-600">{resumo.por_severidade?.critico || 0}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </div>
          </Card>
          
          <Card className={`p-4 ${(resumo.por_severidade?.atencao || 0) > 0 ? 'border-yellow-300 bg-yellow-50' : ''}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Atenção</p>
                <p className="text-2xl font-bold text-yellow-600">{resumo.por_severidade?.atencao || 0}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-yellow-400" />
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Não Lidos</p>
                <p className="text-2xl font-bold text-blue-600">{resumo.nao_lidos || 0}</p>
              </div>
              <Eye className="w-8 h-8 text-blue-400" />
            </div>
          </Card>
        </div>
      )}
      
      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-4">
          {[
            { id: 'alertas', label: 'Alertas', icon: Bell },
            { id: 'configuracao', label: 'Configuração', icon: Settings },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                tab === t.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <t.icon className="w-4 h-4" />
              {t.label}
            </button>
          ))}
        </nav>
      </div>
      
      {/* Tab: Alertas */}
      {tab === 'alertas' && (
        <div className="space-y-4">
          {/* Filtros */}
          <Card className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <select
                value={filtroEmpresa}
                onChange={(e) => setFiltroEmpresa(e.target.value)}
                className="px-3 py-2 border rounded-lg"
              >
                <option value="">Todas as empresas</option>
                {(empresas || []).map(e => (
                  <option key={e.id} value={e.id}>{e.razao_social}</option>
                ))}
              </select>
              
              <select
                value={filtroSeveridade}
                onChange={(e) => setFiltroSeveridade(e.target.value)}
                className="px-3 py-2 border rounded-lg"
              >
                <option value="">Todas as severidades</option>
                <option value="critico">🔴 Crítico</option>
                <option value="atencao">🟡 Atenção</option>
                <option value="info">🔵 Informativo</option>
              </select>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={apenasNaoLidos}
                  onChange={(e) => setApenasNaoLidos(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">Apenas não lidos</span>
              </label>
              
              <div className="flex-1" />
              
              <button
                onClick={marcarTodosLidos}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Marcar todos como lidos
              </button>
            </div>
          </Card>
          
          {/* Lista de Alertas */}
          <div className="space-y-3">
            {(!alertas || alertas.length === 0) ? (
              <Card className="p-8 text-center">
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900">Nenhum alerta encontrado</h3>
                <p className="text-gray-500 mt-1">Todas as empresas estão com a saúde financeira em dia!</p>
              </Card>
            ) : (
              (alertas || []).map(alerta => (
                <Card 
                  key={alerta.id} 
                  className={`p-4 border-l-4 ${
                    alerta.severidade === 'critico' ? 'border-l-red-500' :
                    alerta.severidade === 'atencao' ? 'border-l-yellow-500' :
                    'border-l-blue-500'
                  } ${!alerta.lido ? 'bg-blue-50/30' : ''}`}
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 mt-1">
                      {getSeveridadeIcon(alerta.severidade)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getSeveridadeStyle(alerta.severidade)}`}>
                          {alerta.severidade?.toUpperCase()}
                        </span>
                        <span className="text-sm text-gray-500">{alerta.empresa_nome}</span>
                        {!alerta.lido && (
                          <span className="w-2 h-2 bg-blue-500 rounded-full" title="Não lido" />
                        )}
                      </div>
                      
                      <h4 className="font-medium text-gray-900">{alerta.titulo}</h4>
                      <p className="text-sm text-gray-600 mt-1">{alerta.mensagem}</p>
                      
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>{formatDate(alerta.created_at)}</span>
                        {alerta.periodo_referencia && (
                          <span>Período: {alerta.periodo_referencia}</span>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {!alerta.lido && (
                        <button
                          onClick={() => marcarLido(alerta.id)}
                          className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50"
                          title="Marcar como lido"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => resolverAlerta(alerta.id)}
                        className="p-2 text-gray-400 hover:text-green-600 rounded-lg hover:bg-green-50"
                        title="Resolver alerta"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}
      
      {/* Tab: Configuração */}
      {tab === 'configuracao' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Lista de Empresas */}
          <Card className="p-4">
            <h3 className="font-medium mb-4">Selecione uma empresa</h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {(empresas || []).map(e => (
                <button
                  key={e.id}
                  onClick={() => {
                    setEmpresaSelecionada(e.id);
                    loadConfigEmpresa(e.id);
                  }}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    empresaSelecionada === e.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium">{e.razao_social}</div>
                  <div className="text-sm text-gray-500">{e.cnpj || 'Sem CNPJ'}</div>
                </button>
              ))}
            </div>
          </Card>
          
          {/* Configuração da Empresa */}
          <Card className="lg:col-span-2 p-6">
            {!empresaSelecionada ? (
              <div className="text-center py-8 text-gray-500">
                <Settings className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Selecione uma empresa para configurar os alertas</p>
              </div>
            ) : !configEmpresa ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="font-medium text-lg">Configuração de Alertas</h3>
                  <button
                    onClick={() => gerarAlertasEmpresa(empresaSelecionada)}
                    disabled={gerando}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
                  >
                    {gerando ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                    Verificar Agora
                  </button>
                </div>
                
                {/* Alertas de Caixa */}
                <div className="border rounded-lg p-4 bg-gradient-to-r from-amber-50 to-white">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                        <DollarSign className="w-5 h-5 text-amber-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">Alertas de Caixa</h4>
                        <p className="text-xs text-gray-500">Monitora a saúde financeira de curto prazo</p>
                      </div>
                    </div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={configEmpresa.alerta_caixa_ativo}
                        onChange={(e) => setConfigEmpresa({...configEmpresa, alerta_caixa_ativo: e.target.checked})}
                        className="rounded text-amber-600 focus:ring-amber-500"
                      />
                      <span className="text-sm font-medium">Ativo</span>
                    </label>
                  </div>
                  {configEmpresa.alerta_caixa_ativo && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4 pt-4 border-t">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="w-4 h-4 text-red-500" />
                          <label className="text-sm font-medium text-gray-700">Dias crítico</label>
                        </div>
                        <input
                          type="number"
                          value={configEmpresa.caixa_dias_critico}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, caixa_dias_critico: parseInt(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">⚠️ Alerta CRÍTICO se o caixa cobrir menos de X dias de operação</p>
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <AlertCircle className="w-4 h-4 text-yellow-500" />
                          <label className="text-sm font-medium text-gray-700">Dias atenção</label>
                        </div>
                        <input
                          type="number"
                          value={configEmpresa.caixa_dias_atencao}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, caixa_dias_atencao: parseInt(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">📢 Alerta de ATENÇÃO se caixa cobrir menos de X dias</p>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Alertas de Margem */}
                <div className="border rounded-lg p-4 bg-gradient-to-r from-green-50 to-white">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                        <TrendingUp className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">Alertas de Margem</h4>
                        <p className="text-xs text-gray-500">Acompanha a lucratividade da empresa</p>
                      </div>
                    </div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={configEmpresa.alerta_margem_ativo}
                        onChange={(e) => setConfigEmpresa({...configEmpresa, alerta_margem_ativo: e.target.checked})}
                        className="rounded text-green-600 focus:ring-green-500"
                      />
                      <span className="text-sm font-medium">Ativo</span>
                    </label>
                  </div>
                  {configEmpresa.alerta_margem_ativo && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4 pt-4 border-t">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <Target className="w-4 h-4 text-green-600" />
                          <label className="text-sm font-medium text-gray-700">Margem mínima (%)</label>
                        </div>
                        <input
                          type="number"
                          step="0.1"
                          value={configEmpresa.margem_minima}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, margem_minima: parseFloat(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">📉 Alerta se margem líquida ficar abaixo de X%</p>
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <TrendingDown className="w-4 h-4 text-red-500" />
                          <label className="text-sm font-medium text-gray-700">Queda máxima (%)</label>
                        </div>
                        <input
                          type="number"
                          step="0.1"
                          value={configEmpresa.margem_queda_pct}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, margem_queda_pct: parseFloat(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">📊 Alerta se margem cair mais de X% vs mês anterior</p>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Alertas de Score */}
                <div className="border rounded-lg p-4 bg-gradient-to-r from-blue-50 to-white">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Activity className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">Alertas de Score</h4>
                        <p className="text-xs text-gray-500">Monitora a pontuação geral de saúde financeira</p>
                      </div>
                    </div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={configEmpresa.alerta_score_ativo}
                        onChange={(e) => setConfigEmpresa({...configEmpresa, alerta_score_ativo: e.target.checked})}
                        className="rounded text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm font-medium">Ativo</span>
                    </label>
                  </div>
                  {configEmpresa.alerta_score_ativo && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4 pt-4 border-t">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="w-4 h-4 text-red-500" />
                          <label className="text-sm font-medium text-gray-700">Score crítico</label>
                        </div>
                        <input
                          type="number"
                          value={configEmpresa.score_critico}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, score_critico: parseInt(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">🔴 Alerta CRÍTICO se score ficar abaixo de X pontos (0-100)</p>
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <TrendingDown className="w-4 h-4 text-orange-500" />
                          <label className="text-sm font-medium text-gray-700">Queda máxima (pontos)</label>
                        </div>
                        <input
                          type="number"
                          value={configEmpresa.score_queda_pontos}
                          onChange={(e) => setConfigEmpresa({...configEmpresa, score_queda_pontos: parseInt(e.target.value)})}
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">📉 Alerta se score cair mais de X pontos vs análise anterior</p>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Botão Salvar */}
                <div className="flex justify-end pt-4 border-t">
                  <button
                    onClick={salvarConfigEmpresa}
                    disabled={salvandoConfig}
                    className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 font-medium shadow-lg shadow-emerald-200"
                  >
                    {salvandoConfig ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                    Salvar Configuração
                  </button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

export default AlertasPage;
