import React, { useState, useEffect } from 'react';
import { AlertTriangle, BarChart3, Building2, CheckCircle, ChevronRight, Filter, Home, Minus, Plus, RefreshCw, TrendingDown, TrendingUp, X, XCircle } from 'lucide-react';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Button, Card, EmptyState, LoadingScreen, ScoreCircle, StatusBadge } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { formatarMoeda, formatarMoedaCurta, CORES_GRAFICO } from '../../utils/formatters';

function DashboardPage({ onNavigate }) {
  const { api } = useAuth();
  const [stats, setStats] = useState(null);
  const [empresas, setEmpresas] = useState([]);
  const [graficos, setGraficos] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('visao-geral');
  const [empresaFiltro, setEmpresaFiltro] = useState('todas');

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (empresas.length > 0) {
      loadGraficos();
    }
  }, [empresaFiltro]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [dashRes, empRes, grafRes] = await Promise.all([
        api('/dashboard'),
        api('/empresas'),
        api('/dashboard/graficos?meses=12')
      ]);
      
      if (dashRes.ok) {
        const data = await dashRes.json();
        setStats(data.estatisticas);
      }
      if (empRes.ok) {
        const data = await empRes.json();
        setEmpresas(data.empresas || []);
      }
      if (grafRes.ok) {
        const data = await grafRes.json();
        setGraficos(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadGraficos = async () => {
    try {
      const url = empresaFiltro === 'todas' 
        ? '/dashboard/graficos?meses=12' 
        : `/dashboard/graficos?meses=12&empresa_id=${empresaFiltro}`;
      const res = await api(url);
      if (res.ok) {
        const data = await res.json();
        setGraficos(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <LoadingScreen />;

  const tabs = [
    { id: 'visao-geral', label: 'Visão Geral', icon: Home },
    { id: 'graficos', label: 'Gráficos', icon: BarChart3 },
    { id: 'empresas', label: 'Empresas', icon: Building2 },
  ];

  const empresaSelecionadaNome = empresaFiltro === 'todas' 
    ? 'Todas as empresas' 
    : empresas.find(e => e.id === parseInt(empresaFiltro))?.razao_social || 'Empresa';

  return (
    <div>
      <Header 
        title="Dashboard" 
        subtitle="Visão geral do seu portfólio"
        actions={
          <Button onClick={loadData} variant="secondary" size="sm">
            <RefreshCw className="w-4 h-4" /> Atualizar
          </Button>
        }
      />
      
      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-100 p-1 rounded-lg w-fit">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id 
                ? 'bg-white text-slate-900 shadow-sm' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab: Visão Geral */}
      {activeTab === 'visao-geral' && (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total de Empresas</p>
                  <p className="text-2xl font-bold text-slate-900">{stats?.total_empresas || 0}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Saudáveis</p>
                  <p className="text-2xl font-bold text-green-600">{stats?.empresas_saudaveis || 0}</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Em Atenção</p>
                  <p className="text-2xl font-bold text-amber-600">{stats?.empresas_atencao || 0}</p>
                </div>
                <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-amber-600" />
                </div>
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Críticas</p>
                  <p className="text-2xl font-bold text-red-600">{stats?.empresas_criticas || 0}</p>
                </div>
                <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                  <XCircle className="w-6 h-6 text-red-600" />
                </div>
              </div>
            </Card>
          </div>

          {/* Comparativo Mensal */}
          {graficos?.comparativo_mensal?.periodo_atual && (
            <Card className="p-6 mb-6">
              <h3 className="font-semibold text-slate-900 mb-4">
                Comparativo: {graficos.comparativo_mensal.periodo_atual} vs {graficos.comparativo_mensal.periodo_anterior}
              </h3>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {['receita', 'custos', 'despesas', 'lucro'].map(campo => {
                  const dados = graficos.comparativo_mensal[campo];
                  const isPositive = campo === 'lucro' || campo === 'receita' 
                    ? dados?.variacao > 0 
                    : dados?.variacao < 0;
                  return (
                    <div key={campo} className="bg-slate-50 p-4 rounded-lg">
                      <p className="text-sm text-slate-500 capitalize mb-1">{campo}</p>
                      <p className="text-xl font-bold text-slate-900">
                        {formatarMoeda(dados?.atual)}
                      </p>
                      <div className={`flex items-center gap-1 text-sm mt-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                        {dados?.variacao > 0 ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : dados?.variacao < 0 ? (
                          <TrendingDown className="w-4 h-4" />
                        ) : (
                          <Minus className="w-4 h-4" />
                        )}
                        <span>{dados?.variacao > 0 ? '+' : ''}{dados?.variacao}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* Totais Consolidados */}
          {graficos?.totais && (
            <div className="grid md:grid-cols-3 gap-4 mb-6">
              <Card className="p-4 bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                <p className="text-blue-100 text-sm">Receita Total (12 meses)</p>
                <p className="text-2xl font-bold">{formatarMoeda(graficos.totais.receita_total)}</p>
              </Card>
              <Card className="p-4 bg-gradient-to-br from-green-500 to-green-600 text-white">
                <p className="text-green-100 text-sm">Lucro Total (12 meses)</p>
                <p className="text-2xl font-bold">{formatarMoeda(graficos.totais.lucro_total)}</p>
              </Card>
              <Card className="p-4 bg-gradient-to-br from-purple-500 to-purple-600 text-white">
                <p className="text-purple-100 text-sm">Margem Média</p>
                <p className="text-2xl font-bold">{graficos.totais.margem_media}%</p>
              </Card>
            </div>
          )}

          {/* Mini gráfico de faturamento */}
          {graficos?.faturamento_mensal?.length > 0 && (
            <Card className="p-6 mb-6">
              <h3 className="font-semibold text-slate-900 mb-4">Faturamento (12 meses)</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={graficos.faturamento_mensal}>
                    <defs>
                      <linearGradient id="colorReceita" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="mes" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                    <YAxis tickFormatter={formatarMoedaCurta} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                    <Tooltip formatter={(val) => formatarMoeda(val)} />
                    <Area type="monotone" dataKey="receita" stroke="#3b82f6" strokeWidth={2} fill="url(#colorReceita)" name="Receita" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}
        </>
      )}

      {/* Tab: Gráficos */}
      {activeTab === 'graficos' && (
        <div className="space-y-6">
          {/* Filtro de Empresa */}
          <Card className="p-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Filter className="w-5 h-5 text-slate-500" />
                <span className="font-medium text-slate-700">Filtrar por empresa:</span>
              </div>
              <select
                value={empresaFiltro}
                onChange={(e) => setEmpresaFiltro(e.target.value)}
                className="px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white min-w-[200px]"
              >
                <option value="todas">📊 Todas as empresas (consolidado)</option>
                {empresas.map(emp => (
                  <option key={emp.id} value={emp.id}>🏢 {emp.razao_social}</option>
                ))}
              </select>
              {empresaFiltro !== 'todas' && (
                <button 
                  onClick={() => setEmpresaFiltro('todas')}
                  className="text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1"
                >
                  <X className="w-4 h-4" /> Limpar filtro
                </button>
              )}
            </div>
            {empresaFiltro !== 'todas' && (
              <p className="mt-2 text-sm text-emerald-600 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Exibindo dados de: <strong>{empresaSelecionadaNome}</strong>
              </p>
            )}
          </Card>

          {/* Faturamento vs Lucro */}
          {graficos?.faturamento_mensal?.length > 0 && (
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-900">Faturamento vs Lucro</h3>
                <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">{empresaSelecionadaNome}</span>
              </div>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={graficos.faturamento_mensal}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="mes" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                    <YAxis tickFormatter={formatarMoedaCurta} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                    <Tooltip formatter={(val) => formatarMoeda(val)} />
                    <Legend />
                    <Line type="monotone" dataKey="receita" stroke="#3b82f6" strokeWidth={2} name="Receita" dot={{ fill: '#3b82f6' }} />
                    <Line type="monotone" dataKey="lucro" stroke="#22c55e" strokeWidth={2} name="Lucro" dot={{ fill: '#22c55e' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Composição de Despesas */}
            {graficos?.composicao_despesas?.length > 0 && (
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-900">Composição de Despesas</h3>
                  <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">Último mês</span>
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={graficos.composicao_despesas}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={3}
                        dataKey="valor"
                        nameKey="nome"
                        label={false}
                      >
                        {graficos.composicao_despesas.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.cor || CORES_GRAFICO[index % CORES_GRAFICO.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(val) => formatarMoeda(val)} />
                      <Legend 
                        layout="vertical" 
                        align="right" 
                        verticalAlign="middle"
                        formatter={(value) => <span className="text-sm text-slate-600">{value}</span>}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex flex-wrap gap-3 justify-center mt-2">
                  {graficos.composicao_despesas.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.cor || CORES_GRAFICO[idx % CORES_GRAFICO.length] }} />
                      <span className="text-slate-600">{formatarMoeda(item.valor)}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Fluxo de Caixa */}
            {graficos?.fluxo_caixa?.length > 0 && (
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-900">Fluxo de Caixa</h3>
                  <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">{empresaSelecionadaNome}</span>
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={graficos.fluxo_caixa}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="mes" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                      <YAxis tickFormatter={formatarMoedaCurta} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                      <Tooltip formatter={(val) => formatarMoeda(val)} />
                      <Legend />
                      <Bar dataKey="entradas" fill="#22c55e" name="Entradas" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="saidas" fill="#ef4444" name="Saídas" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            )}
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Top Empresas por Faturamento */}
            {graficos?.top_empresas_faturamento?.length > 0 && empresaFiltro === 'todas' && (
              <Card className="p-6">
                <h3 className="font-semibold text-slate-900 mb-4">Top 5 Empresas por Faturamento</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={graficos.top_empresas_faturamento} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis type="number" tickFormatter={formatarMoedaCurta} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                      <YAxis dataKey="nome" type="category" tick={{ fontSize: 11 }} stroke="#94a3b8" width={100} />
                      <Tooltip formatter={(val) => formatarMoeda(val)} />
                      <Bar dataKey="faturamento_total" fill="#3b82f6" name="Faturamento" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            )}

            {/* Top Empresas por Score */}
            {graficos?.top_empresas_score?.length > 0 && empresaFiltro === 'todas' && (
              <Card className="p-6">
                <h3 className="font-semibold text-slate-900 mb-4">Top 5 Empresas por Score</h3>
                <div className="space-y-3">
                  {graficos.top_empresas_score.map((emp, idx) => (
                    <div key={emp.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                      <span className="text-lg font-bold text-slate-400 w-6">{idx + 1}</span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-900 truncate">{emp.nome}</p>
                        <StatusBadge status={emp.status} />
                      </div>
                      <ScoreCircle score={emp.score} size="md" />
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Se filtrou por empresa, mostra dados detalhados */}
            {empresaFiltro !== 'todas' && (
              <Card className="p-6 lg:col-span-2">
                <h3 className="font-semibold text-slate-900 mb-4">Resumo da Empresa</h3>
                {graficos?.totais ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <p className="text-sm text-blue-600 mb-1">Receita Total</p>
                      <p className="text-xl font-bold text-blue-700">{formatarMoeda(graficos.totais.receita_total)}</p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <p className="text-sm text-green-600 mb-1">Lucro Total</p>
                      <p className="text-xl font-bold text-green-700">{formatarMoeda(graficos.totais.lucro_total)}</p>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <p className="text-sm text-purple-600 mb-1">Margem Média</p>
                      <p className="text-xl font-bold text-purple-700">{graficos.totais.margem_media}%</p>
                    </div>
                    <div className="bg-amber-50 p-4 rounded-lg">
                      <p className="text-sm text-amber-600 mb-1">Meses com Dados</p>
                      <p className="text-xl font-bold text-amber-700">{graficos?.faturamento_mensal?.length || 0}</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-500">Nenhum dado encontrado para esta empresa</p>
                )}
              </Card>
            )}
          </div>

          {/* Sem dados */}
          {(!graficos?.faturamento_mensal?.length) && (
            <Card className="p-8">
              <EmptyState 
                icon={BarChart3}
                title="Sem dados para gráficos"
                description="Importe dados financeiros das suas empresas para visualizar os gráficos"
              />
            </Card>
          )}
        </div>
      )}

      {/* Tab: Empresas */}
      {activeTab === 'empresas' && (
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900">Suas Empresas</h3>
            <Button size="sm" onClick={() => onNavigate('nova-empresa')}>
              <Plus className="w-4 h-4" /> Nova Empresa
            </Button>
          </div>
          
          {empresas.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-slate-500 border-b">
                    <th className="pb-3 font-medium">Empresa</th>
                    <th className="pb-3 font-medium">Score</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Meses</th>
                    <th className="pb-3 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {empresas.map(emp => (
                    <tr 
                      key={emp.id} 
                      className="border-b last:border-0 hover:bg-slate-50 cursor-pointer"
                      onClick={() => onNavigate('empresa', emp.id)}
                    >
                      <td className="py-3">
                        <p className="font-medium text-slate-900">{emp.razao_social}</p>
                        {emp.cnpj && <p className="text-sm text-slate-500">{emp.cnpj}</p>}
                      </td>
                      <td className="py-3">
                        <ScoreCircle score={emp.ultimo_score} size="sm" />
                      </td>
                      <td className="py-3">
                        {emp.ultimo_status ? <StatusBadge status={emp.ultimo_status} /> : <span className="text-slate-400">—</span>}
                      </td>
                      <td className="py-3 text-sm text-slate-500">
                        {emp.meses_dados || 0} meses
                      </td>
                      <td className="py-3">
                        <ChevronRight className="w-5 h-5 text-slate-400" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState 
              icon={Building2}
              title="Nenhuma empresa cadastrada"
              description="Cadastre sua primeira empresa para começar"
              action={
                <Button onClick={() => onNavigate('nova-empresa')}>
                  <Plus className="w-4 h-4" /> Cadastrar Empresa
                </Button>
              }
            />
          )}
        </Card>
      )}
    </div>
  );
}

export default DashboardPage;
