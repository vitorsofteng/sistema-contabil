import React, { useState, useEffect } from 'react';
import { 
  AuthProvider, useAuth, AuthPages, DashboardPage, Sidebar, Header, Card, Button, 
  Input, Select, Badge, StatusBadge, ScoreCircle, Modal, EmptyState, LoadingScreen,
  ToastProvider, useToast, LoadingOverlay, ImportacaoAvancadaPage, RelatoriosPage,
  AlertasPage, AnaliseFinanceiraPage, ThemeProvider
} from './components.jsx';
import { 
  Plus, Search, Upload, Download, Eye, Edit, Trash2, RefreshCw, ChevronRight,
  Building2, FileText, Calendar, TrendingUp, TrendingDown, Minus, AlertTriangle,
  CheckCircle, Bell, ArrowLeft, FileSpreadsheet, Loader2, BarChart3, X, PieChart
} from 'lucide-react';
import Papa from 'papaparse';

const API_URL = import.meta.env.VITE_API_URL || '/api';

// ============================================================================
// PAGES - Empresas
// ============================================================================

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

function NovaEmpresaPage({ onNavigate }) {
  const { api } = useAuth();
  const toast = useToast();
  const [form, setForm] = useState({
    razao_social: '', nome_fantasia: '', cnpj: '', regime_tributario: '',
    setor: '', email: '', telefone: '', cidade: '', estado: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const res = await api('/empresas', {
        method: 'POST',
        body: JSON.stringify(form)
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Erro ao cadastrar');
      }
      
      const empresa = await res.json();
      toast.success('Empresa cadastrada com sucesso!');
      onNavigate('empresa', empresa.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const regimes = [
    { value: '', label: 'Selecione...' },
    { value: 'Simples Nacional', label: 'Simples Nacional' },
    { value: 'Lucro Presumido', label: 'Lucro Presumido' },
    { value: 'Lucro Real', label: 'Lucro Real' },
    { value: 'MEI', label: 'MEI' },
  ];

  const estados = [
    { value: '', label: 'UF' },
    ...['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']
      .map(uf => ({ value: uf, label: uf }))
  ];

  return (
    <div>
      <Header 
        title="Nova Empresa" 
        subtitle="Cadastre uma nova empresa cliente"
        actions={
          <Button variant="ghost" onClick={() => onNavigate('empresas')}>
            <ArrowLeft className="w-4 h-4" /> Voltar
          </Button>
        }
      />
      
      <Card className="p-6 max-w-2xl">
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Razão Social *" value={form.razao_social} onChange={e => setForm({...form, razao_social: e.target.value})} required />
          
          <div className="grid grid-cols-2 gap-4">
            <Input label="Nome Fantasia" value={form.nome_fantasia} onChange={e => setForm({...form, nome_fantasia: e.target.value})} />
            <Input label="CNPJ" value={form.cnpj} onChange={e => setForm({...form, cnpj: e.target.value})} placeholder="00.000.000/0000-00" />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <Select label="Regime Tributário" options={regimes} value={form.regime_tributario} onChange={e => setForm({...form, regime_tributario: e.target.value})} />
            <Input label="Setor/Atividade" value={form.setor} onChange={e => setForm({...form, setor: e.target.value})} placeholder="Ex: Comércio, Serviços..." />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <Input label="Email" type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
            <Input label="Telefone" value={form.telefone} onChange={e => setForm({...form, telefone: e.target.value})} />
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            <Input label="Cidade" value={form.cidade} onChange={e => setForm({...form, cidade: e.target.value})} className="col-span-2" />
            <Select label="Estado" options={estados} value={form.estado} onChange={e => setForm({...form, estado: e.target.value})} />
          </div>
          
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => onNavigate('empresas')}>Cancelar</Button>
            <Button type="submit" loading={loading}>Cadastrar Empresa</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

function EmpresaDetailPage({ empresaId, onNavigate }) {
  const { api } = useAuth();
  const toast = useToast();
  const [empresa, setEmpresa] = useState(null);
  const [registros, setRegistros] = useState([]);
  const [analises, setAnalises] = useState([]);
  const [ultimaAnalise, setUltimaAnalise] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analisando, setAnalisando] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [showRegistro, setShowRegistro] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [tab, setTab] = useState('visao-geral');

  useEffect(() => { loadData(); }, [empresaId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [empRes, regRes, anaRes] = await Promise.all([
        api(`/empresas/${empresaId}`),
        api(`/empresas/${empresaId}/dados`),
        api(`/empresas/${empresaId}/analises`)
      ]);
      
      if (empRes.ok) {
        const empData = await empRes.json();
        setEmpresa(empData.empresa || empData);
      }
      if (regRes.ok) {
        const regData = await regRes.json();
        setRegistros(regData.dados || regData || []);
      }
      if (anaRes.ok) {
        const anaData = await anaRes.json();
        const analisesList = anaData.analises || anaData || [];
        setAnalises(analisesList);
        if (analisesList.length > 0) setUltimaAnalise(analisesList[0]);
      }
    } catch (err) {
      toast.error('Erro ao carregar dados da empresa');
    } finally {
      setLoading(false);
    }
  };

  const executarAnalise = async () => {
    if (registros.length < 3) {
      toast.warning('Necessário pelo menos 6 meses de dados para análise');
      return;
    }
    
    setAnalisando(true);
    try {
      const res = await api(`/empresas/${empresaId}/analises`, { method: 'POST' });
      if (res.ok) {
        const result = await res.json();
        toast.success('Análise concluída com sucesso!');
        await loadData();
        setTab('analise');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Erro ao executar análise');
      }
    } catch (err) {
      toast.error('Erro de conexão ao executar análise');
    } finally {
      setAnalisando(false);
    }
  };

  const downloadPDF = async () => {
    if (!ultimaAnalise) return;
    try {
      const res = await api(`/empresas/${empresaId}/analises/${ultimaAnalise.id}/pdf`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analise_${empresa?.razao_social || 'empresa'}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('PDF baixado com sucesso!');
    } catch (err) {
      toast.error('Erro ao baixar PDF');
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      const res = await api(`/empresas/${empresaId}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Empresa excluída com sucesso!');
        onNavigate('empresas');
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Erro ao excluir empresa');
      }
    } catch (err) {
      toast.error('Erro ao excluir empresa');
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  if (loading) return <LoadingScreen />;
  if (!empresa) return <div>Empresa não encontrada</div>;

  const tabs = [
    { id: 'visao-geral', label: 'Visão Geral' },
    { id: 'dados', label: `Dados Mensais (${registros.length})` },
    { id: 'analise', label: 'Última Análise' },
    { id: 'historico', label: `Histórico (${analises.length})` },
  ];

  return (
    <div>
      {analisando && <LoadingOverlay message="Executando análise financeira..." />}
      <Header 
        title={empresa.razao_social}
        subtitle={empresa.cnpj}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => onNavigate('empresas')}><ArrowLeft className="w-4 h-4" /> Voltar</Button>
            <Button variant="secondary" onClick={() => setShowUpload(true)}><Upload className="w-4 h-4" /> Importar Dados</Button>
            <Button 
              variant="secondary" 
              onClick={() => onNavigate('analise-financeira', { empresaId: empresaId, empresaNome: empresa.razao_social })}
              disabled={registros.length < 1}
            >
              <PieChart className="w-4 h-4" /> DRE & Índices
            </Button>
            <Button onClick={executarAnalise} loading={analisando} disabled={registros.length < 3}><BarChart3 className="w-4 h-4" /> Analisar</Button>
          </div>
        }
      />
      
      {ultimaAnalise && (
        <Card className="p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <ScoreCircle score={ultimaAnalise.score} size="lg" />
              <div>
                <StatusBadge status={ultimaAnalise.status} />
                <p className="text-sm text-slate-500 mt-1">Última análise: {new Date(ultimaAnalise.data_analise).toLocaleDateString('pt-BR')}</p>
              </div>
            </div>
            <Button variant="secondary" size="sm" onClick={downloadPDF}><Download className="w-4 h-4" /> Baixar PDF</Button>
          </div>
        </Card>
      )}
      
      <div className="border-b border-slate-200 mb-6">
        <nav className="flex gap-4">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${tab === t.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
              {t.label}
            </button>
          ))}
        </nav>
      </div>
      
      {tab === 'visao-geral' && <VisaoGeralTab empresa={empresa} registros={registros} onEdit={() => setShowEdit(true)} onDelete={() => setShowDeleteConfirm(true)} />}
      {tab === 'dados' && <DadosTab registros={registros} onAddManual={() => setShowRegistro(true)} onUpload={() => setShowUpload(true)} />}
      {tab === 'analise' && ultimaAnalise && <AnaliseDetail analise={ultimaAnalise} />}
      {tab === 'analise' && !ultimaAnalise && (
        <Card className="p-8">
          <EmptyState icon={BarChart3} title="Nenhuma análise realizada"
            description={registros.length < 3 ? "Cadastre pelo menos 3 meses de dados para análise" : "Execute uma análise para ver o diagnóstico"}
            action={<Button onClick={executarAnalise} disabled={registros.length < 3} loading={analisando}><BarChart3 className="w-4 h-4" /> Executar Análise</Button>}
          />
        </Card>
      )}
      {tab === 'historico' && <HistoricoTab analises={analises} />}
      
      <UploadModal isOpen={showUpload} onClose={() => setShowUpload(false)} empresaId={empresaId} onSuccess={loadData} />
      <RegistroModal isOpen={showRegistro} onClose={() => setShowRegistro(false)} empresaId={empresaId} onSuccess={loadData} />
      <EditEmpresaModal isOpen={showEdit} onClose={() => setShowEdit(false)} empresa={empresa} onSuccess={() => { setShowEdit(false); loadData(); }} />
      
      {/* Modal de confirmação de exclusão */}
      <Modal isOpen={showDeleteConfirm} onClose={() => setShowDeleteConfirm(false)} title="Excluir Empresa">
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-4 bg-red-50 rounded-lg">
            <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0" />
            <div>
              <p className="font-medium text-red-900">Tem certeza que deseja excluir esta empresa?</p>
              <p className="text-sm text-red-700 mt-1">Esta ação não pode ser desfeita. Todos os dados, análises e relatórios serão permanentemente excluídos.</p>
            </div>
          </div>
          
          <div className="p-3 bg-slate-50 rounded-lg">
            <p className="font-medium text-slate-900">{empresa?.razao_social}</p>
            <p className="text-sm text-slate-500">{empresa?.cnpj || 'CNPJ não informado'}</p>
          </div>
          
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setShowDeleteConfirm(false)}>Cancelar</Button>
            <Button variant="danger" onClick={handleDelete} loading={deleting}>
              <Trash2 className="w-4 h-4" /> Excluir Empresa
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

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

function AnaliseDetail({ analise }) {
  const resultado = analise.resultado_completo || analise.resultado || {};
  
  // Novo formato (analyzer profissional)
  const indicadores = resultado.indicadores || {};
  const insights = resultado.insights || analise.insights || [];
  const tendencias = resultado.tendencias || {};
  const projecoes = resultado.projecoes || {};
  const recomendacoes = resultado.recomendacoes || [];
  const alertasCriticos = resultado.alertas_criticos || [];
  const resumo = resultado.resumo || '';
  const score = resultado.score || analise.score || 50;
  const status = resultado.status || analise.status || 'Regular';
  
  // Formato antigo (compatibilidade)
  const tendencia = resultado.tendencia || {};
  const caixa = resultado.risco_caixa || {};
  const anomalias = resultado.anomalias || {};
  const prob = resultado.probabilidades || {};

  const formatarMoeda = (valor) => {
    if (!valor && valor !== 0) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  };

  // Verificar se é novo formato
  const isNovoFormato = Object.keys(indicadores).length > 0;
  
  if (isNovoFormato) {
    // NOVO LAYOUT - Analyzer Profissional
    return (
      <div className="space-y-6">
        {/* Resumo Executivo */}
        {resumo && (
          <Card className="p-4 bg-slate-50">
            <h3 className="font-semibold text-slate-900 mb-2">Resumo Executivo</h3>
            <p className="text-slate-700">{resumo}</p>
          </Card>
        )}

        {/* Score e Status */}
        <div className="grid grid-cols-2 gap-4">
          <Card className="p-6 text-center">
            <div className={`text-5xl font-bold mb-2 ${
              score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {score}
            </div>
            <p className="text-slate-600">Score de Saúde</p>
            <Badge className={`mt-2 ${
              status === 'Excelente' ? 'bg-green-100 text-green-800' :
              status === 'Bom' ? 'bg-blue-100 text-blue-800' :
              status === 'Regular' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>{status}</Badge>
          </Card>

          <Card className="p-4">
            <h4 className="font-semibold text-slate-900 mb-3">Tendências</h4>
            <div className="space-y-2">
              {Object.entries(tendencias).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm text-slate-600 capitalize">{key}</span>
                  <div className="flex items-center gap-2">
                    {val.direcao === 'alta' && <TrendingUp className="w-4 h-4 text-green-600" />}
                    {val.direcao === 'baixa' && <TrendingDown className="w-4 h-4 text-red-600" />}
                    {val.direcao === 'estavel' && <Minus className="w-4 h-4 text-gray-600" />}
                    <span className={`font-medium ${
                      val.direcao === 'alta' ? 'text-green-600' : 
                      val.direcao === 'baixa' ? 'text-red-600' : 'text-gray-600'
                    }`}>
                      {val.variacao > 0 ? '+' : ''}{val.variacao}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Indicadores Principais */}
        <Card className="p-4">
          <h3 className="font-semibold text-slate-900 mb-4">Indicadores Financeiros</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {indicadores.liquidez_corrente !== undefined && (
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <p className={`text-2xl font-bold ${
                  indicadores.liquidez_corrente >= 1.5 ? 'text-green-600' :
                  indicadores.liquidez_corrente >= 1 ? 'text-yellow-600' : 'text-red-600'
                }`}>{indicadores.liquidez_corrente}</p>
                <p className="text-xs text-slate-500">Liquidez Corrente</p>
              </div>
            )}
            {indicadores.margem_liquida !== undefined && (
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <p className={`text-2xl font-bold ${
                  indicadores.margem_liquida >= 15 ? 'text-green-600' :
                  indicadores.margem_liquida >= 5 ? 'text-yellow-600' : 'text-red-600'
                }`}>{indicadores.margem_liquida}%</p>
                <p className="text-xs text-slate-500">Margem Líquida</p>
              </div>
            )}
            {indicadores.margem_bruta !== undefined && (
              <div className="text-center p-3 bg-emerald-50 rounded-lg">
                <p className="text-2xl font-bold text-emerald-600">{indicadores.margem_bruta}%</p>
                <p className="text-xs text-slate-500">Margem Bruta</p>
              </div>
            )}
            {indicadores.roe !== undefined && (
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">
                  {indicadores.roe > 1000 ? '>1000' : indicadores.roe}%
                </p>
                <p className="text-xs text-slate-500">ROE</p>
              </div>
            )}
            {indicadores.roa !== undefined && (
              <div className="text-center p-3 bg-indigo-50 rounded-lg">
                <p className="text-2xl font-bold text-indigo-600">{indicadores.roa}%</p>
                <p className="text-xs text-slate-500">ROA</p>
              </div>
            )}
            {indicadores.carga_tributaria !== undefined && (
              <div className="text-center p-3 bg-orange-50 rounded-lg">
                <p className={`text-2xl font-bold ${
                  indicadores.carga_tributaria > 25 ? 'text-red-600' : 'text-orange-600'
                }`}>{indicadores.carga_tributaria}%</p>
                <p className="text-xs text-slate-500">Carga Tributária</p>
              </div>
            )}
            {indicadores.endividamento_geral !== undefined && (
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <p className={`text-2xl font-bold ${
                  indicadores.endividamento_geral > 70 ? 'text-red-600' : 'text-slate-600'
                }`}>{indicadores.endividamento_geral}%</p>
                <p className="text-xs text-slate-500">Endividamento</p>
              </div>
            )}
            {indicadores.giro_ativo !== undefined && (
              <div className="text-center p-3 bg-cyan-50 rounded-lg">
                <p className="text-2xl font-bold text-cyan-600">{indicadores.giro_ativo}x</p>
                <p className="text-xs text-slate-500">Giro do Ativo</p>
              </div>
            )}
            {indicadores.ebitda !== undefined && indicadores.ebitda > 0 && (
              <div className="text-center p-3 bg-teal-50 rounded-lg">
                <p className="text-2xl font-bold text-teal-600">{formatarMoeda(indicadores.ebitda)}</p>
                <p className="text-xs text-slate-500">EBITDA</p>
              </div>
            )}
            {indicadores.margem_ebitda !== undefined && (
              <div className="text-center p-3 bg-slate-100 rounded-lg">
                <p className="text-2xl font-bold text-slate-700">{indicadores.margem_ebitda}%</p>
                <p className="text-xs text-slate-500">Margem EBITDA</p>
              </div>
            )}
          </div>
        </Card>

        {/* Alertas Críticos */}
        {alertasCriticos.length > 0 && (
          <Card className="p-4 bg-red-50 border-red-200">
            <h3 className="font-semibold text-red-900 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Alertas Críticos ({alertasCriticos.length})
            </h3>
            <div className="space-y-2">
              {alertasCriticos.map((alerta, i) => (
                <div key={i} className="p-3 bg-white rounded-lg border border-red-200">
                  <p className="font-medium text-red-800">{alerta.titulo}</p>
                  <p className="text-sm text-red-700">{alerta.descricao}</p>
                  {alerta.recomendacao && (
                    <p className="text-sm text-red-600 mt-1 italic">→ {alerta.recomendacao}</p>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Insights */}
        {insights.length > 0 && (
          <Card className="p-4">
            <h3 className="font-semibold text-slate-900 mb-3">Insights ({insights.length})</h3>
            <div className="space-y-3">
              {insights.filter(i => i.severidade !== 'alta').slice(0, 5).map((insight, i) => (
                <div key={i} className={`p-3 rounded-lg border ${
                  insight.tipo === 'positivo' ? 'bg-green-50 border-green-200' :
                  insight.tipo === 'atencao' ? 'bg-yellow-50 border-yellow-200' :
                  'bg-blue-50 border-blue-200'
                }`}>
                  <div className="flex items-start gap-2">
                    {insight.tipo === 'positivo' && <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />}
                    {insight.tipo === 'atencao' && <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />}
                    {insight.tipo === 'alerta' && <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />}
                    <div>
                      <p className="font-medium text-slate-800">{insight.titulo}</p>
                      <p className="text-sm text-slate-600">{insight.descricao}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Projeções */}
        {Object.keys(projecoes).length > 0 && (
          <Card className="p-4">
            <h3 className="font-semibold text-slate-900 mb-3">Projeções</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {projecoes.receita_proximos_12m && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-slate-600">Receita (12 meses)</p>
                  <p className="text-xl font-bold text-blue-600">{formatarMoeda(projecoes.receita_proximos_12m)}</p>
                </div>
              )}
              {projecoes.lucro_proximos_12m && (
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-sm text-slate-600">Lucro (12 meses)</p>
                  <p className="text-xl font-bold text-green-600">{formatarMoeda(projecoes.lucro_proximos_12m)}</p>
                </div>
              )}
              {projecoes.impostos_proximos_12m && (
                <div className="p-3 bg-orange-50 rounded-lg">
                  <p className="text-sm text-slate-600">Impostos (12 meses)</p>
                  <p className="text-xl font-bold text-orange-600">{formatarMoeda(projecoes.impostos_proximos_12m)}</p>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Recomendações Priorizadas */}
        {recomendacoes.length > 0 && (
          <Card className="p-4 bg-blue-50 border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-3">Recomendações Prioritárias</h3>
            <div className="space-y-2">
              {recomendacoes.slice(0, 5).map((rec, i) => (
                <div key={i} className="flex items-start gap-3 p-2 bg-white rounded">
                  <span className={`px-2 py-1 text-xs font-bold rounded ${
                    rec.prioridade === 1 ? 'bg-red-100 text-red-800' :
                    rec.prioridade === 2 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>P{rec.prioridade}</span>
                  <div>
                    <p className="font-medium text-slate-800">{rec.titulo}</p>
                    <p className="text-sm text-slate-600">{rec.acao}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    );
  }
  
  // LAYOUT ANTIGO - Compatibilidade
  return (
    <div className="space-y-6">
      <Card className="p-4">
        <h3 className="font-semibold text-slate-900 mb-4">Composição do Score</h3>
        <div className="grid grid-cols-5 gap-4 text-center">
          {[{ label: 'Tendência', value: analise.score_tendencia, max: 25 },
            { label: 'Margem', value: analise.score_margem, max: 25 },
            { label: 'Caixa', value: analise.score_caixa, max: 25 },
            { label: 'Estabilidade', value: analise.score_estabilidade, max: 15 },
            { label: 'Anomalias', value: analise.score_anomalias, max: 10 }].map(item => (
            <div key={item.label}>
              <div className="text-2xl font-bold text-slate-900">{item.value?.toFixed(1) || 0}</div>
              <div className="text-xs text-slate-500">de {item.max}</div>
              <div className="text-sm font-medium text-slate-700 mt-1">{item.label}</div>
            </div>
          ))}
        </div>
      </Card>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            {tendencia.direcao === 'up' && <TrendingUp className="w-5 h-5 text-emerald-600" />}
            {tendencia.direcao === 'down' && <TrendingDown className="w-5 h-5 text-red-600" />}
            {tendencia.direcao === 'stable' && <Minus className="w-5 h-5 text-amber-600" />}
            <h4 className="font-semibold text-slate-900">Tendência</h4>
          </div>
          <p className="text-lg font-bold text-slate-900">{tendencia.tendencia || '—'}</p>
          <p className="text-sm text-slate-500">Taxa: {tendencia.taxa_mensal}%/mês</p>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className={`w-5 h-5 ${caixa.nivel === 'Crítico' ? 'text-red-600' : caixa.nivel === 'Alto' ? 'text-amber-600' : 'text-emerald-600'}`} />
            <h4 className="font-semibold text-slate-900">Risco de Caixa</h4>
          </div>
          <p className="text-lg font-bold text-slate-900">{caixa.nivel || '—'}</p>
          <p className="text-sm text-slate-500">Runway: {caixa.runway_p10}-{caixa.runway_p90} meses</p>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className={`w-5 h-5 ${anomalias.total > 0 ? 'text-amber-600' : 'text-emerald-600'}`} />
            <h4 className="font-semibold text-slate-900">Anomalias</h4>
          </div>
          <p className="text-lg font-bold text-slate-900">{anomalias.total || 0} detectadas</p>
          <p className="text-sm text-slate-500">Normalidade: {anomalias.score_normalidade_geral?.toFixed(0)}/100</p>
        </Card>
        
        <Card className="p-4">
          <h4 className="font-semibold text-slate-900 mb-3">Probabilidades</h4>
          <div className="space-y-2">
            {[['Prejuízo', prob.prob_prejuizo], ['Problemas Caixa', prob.prob_quebra], ['Imposto Inesperado', prob.prob_imposto_inesperado]].map(([label, value]) => (
              <div key={label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-600">{label}</span>
                  <span className="font-medium">{value?.toFixed(0) || 0}%</span>
                </div>
                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${value >= 50 ? 'bg-red-500' : value >= 25 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${Math.min(100, value || 0)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
      
      {analise.insights?.length > 0 && (
        <Card className="p-4">
          <h4 className="font-semibold text-slate-900 mb-3">Insights</h4>
          <ul className="space-y-2">{analise.insights.map((insight, i) => <li key={i} className="text-sm text-slate-700">{typeof insight === 'string' ? insight : insight.descricao}</li>)}</ul>
        </Card>
      )}
      
      <Card className="p-4 bg-blue-50 border-blue-200">
        <h4 className="font-semibold text-blue-900 mb-2">Recomendação Principal</h4>
        <p className="text-blue-800">{analise.recomendacao_principal}</p>
      </Card>
    </div>
  );
}

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

function UploadModal({ isOpen, onClose, empresaId, onSuccess }) {
  const { api } = useAuth();
  const toast = useToast();
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [csvContent, setCsvContent] = useState('');
  const [preview, setPreview] = useState(null);
  const [mapping, setMapping] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setError('');
    const text = await f.text();
    setCsvContent(text);
    
    Papa.parse(text, {
      header: true,
      preview: 5,
      complete: (results) => {
        setPreview({ columns: results.meta.fields || [], rows: results.data });
        const autoMap = {};
        (results.meta.fields || []).forEach(col => {
          const lower = col.toLowerCase();
          // Data/Período
          if (lower.includes('compet') || lower.includes('data') || lower.includes('period') || lower.includes('date') || lower.includes('mes') || lower.includes('mês')) autoMap.data = col;
          // Receita
          if (lower.includes('fatur') || lower.includes('receit') || lower.includes('venda') || lower.includes('revenue') || lower.includes('sales')) autoMap.receita = col;
          // Custos
          if (lower.includes('custo') || lower.includes('cmv') || lower.includes('cpv') || lower.includes('cogs') || lower.includes('cost')) autoMap.custos = col;
          // Despesas
          if (lower.includes('desp') || lower.includes('gasto') || lower.includes('expense') || lower.includes('admin')) autoMap.despesas = col;
          // Impostos
          if (lower.includes('impost') || lower.includes('tribut') || lower.includes('tax')) autoMap.impostos = col;
          // Folha
          if (lower.includes('folha') || lower.includes('salar') || lower.includes('pessoal') || lower.includes('payroll') || lower.includes('wage')) autoMap.folha = col;
          // Caixa
          if (lower.includes('caixa') || lower.includes('banco') || lower.includes('saldo') || lower.includes('cash') || lower.includes('dispon')) autoMap.caixa = col;
        });
        setMapping(autoMap);
        setStep(2);
      },
      error: () => setError('Erro ao processar arquivo')
    });
  };

  const handleConfirm = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api(`/empresas/${empresaId}/dados/upload/confirmar`, {
        method: 'POST',
        body: JSON.stringify({ csv_content: csvContent, mapping, substituir_existentes: false })
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Erro ao importar');
      const result = await res.json();
      toast.success(`${result.registros_criados} registros importados com sucesso!`);
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen) { setStep(1); setFile(null); setCsvContent(''); setPreview(null); setMapping({}); setError(''); }
  }, [isOpen]);

  const campos = [
    { key: 'data', label: 'Data/Competência', required: true },
    { key: 'receita', label: 'Receita', required: true },
    { key: 'custos', label: 'Custos' }, { key: 'despesas', label: 'Despesas' },
    { key: 'impostos', label: 'Impostos' }, { key: 'folha', label: 'Folha' }, { key: 'caixa', label: 'Caixa' },
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Importar Dados" size="lg">
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>}
      {step === 1 && (
        <div className="text-center py-8">
          <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileChange} className="hidden" id="file-upload" />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4"><Upload className="w-10 h-10 text-blue-600" /></div>
            <p className="text-lg font-medium text-slate-900 mb-1">Selecione um arquivo</p>
            <p className="text-sm text-slate-500">CSV ou Excel</p>
          </label>
        </div>
      )}
      {step === 2 && preview && (
        <div>
          <p className="text-sm text-slate-600 mb-4">Arquivo: <strong>{file?.name}</strong></p>
          <h4 className="font-medium text-slate-900 mb-3">Mapeie as colunas:</h4>
          <div className="grid grid-cols-2 gap-3 mb-4">
            {campos.map(campo => (
              <div key={campo.key}>
                <label className="block text-sm font-medium text-slate-700 mb-1">{campo.label} {campo.required && <span className="text-red-500">*</span>}</label>
                <select value={mapping[campo.key] || ''} onChange={e => setMapping({...mapping, [campo.key]: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm">
                  <option value="">Selecione...</option>
                  {preview.columns.map(col => <option key={col} value={col}>{col}</option>)}
                </select>
              </div>
            ))}
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="secondary" onClick={() => setStep(1)}>Voltar</Button>
            <Button onClick={handleConfirm} loading={loading} disabled={!mapping.data || !mapping.receita}>Importar</Button>
          </div>
        </div>
      )}
    </Modal>
  );
}

function RegistroModal({ isOpen, onClose, empresaId, onSuccess }) {
  const { api } = useAuth();
  const toast = useToast();
  const [form, setForm] = useState({ competencia: '', receita_bruta: '', custos: '', despesas_operacionais: '', folha_pagamento: '', impostos: '', saldo_caixa: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = {
        competencia: form.competencia,
        receita_bruta: parseFloat(form.receita_bruta) || 0,
        custos: parseFloat(form.custos) || 0,
        despesas_operacionais: parseFloat(form.despesas_operacionais) || 0,
        folha_pagamento: parseFloat(form.folha_pagamento) || 0,
        impostos: parseFloat(form.impostos) || 0,
        saldo_caixa: parseFloat(form.saldo_caixa) || 0
      };
      const res = await api(`/empresas/${empresaId}/dados`, { method: 'POST', body: JSON.stringify(data) });
      if (!res.ok) throw new Error((await res.json()).detail || 'Erro ao salvar');
      toast.success('Registro adicionado com sucesso!');
      onSuccess();
      onClose();
      setForm({ competencia: '', receita_bruta: '', custos: '', despesas_operacionais: '', folha_pagamento: '', impostos: '', saldo_caixa: '' });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Adicionar Registro Mensal" size="md">
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Competência (AAAA-MM)" value={form.competencia} onChange={e => setForm({...form, competencia: e.target.value})} placeholder="2024-01" pattern="\d{4}-\d{2}" required />
        <div className="grid grid-cols-2 gap-4">
          <Input label="Receita Bruta" type="number" step="0.01" value={form.receita_bruta} onChange={e => setForm({...form, receita_bruta: e.target.value})} required />
          <Input label="Custos" type="number" step="0.01" value={form.custos} onChange={e => setForm({...form, custos: e.target.value})} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Despesas" type="number" step="0.01" value={form.despesas_operacionais} onChange={e => setForm({...form, despesas_operacionais: e.target.value})} />
          <Input label="Folha" type="number" step="0.01" value={form.folha_pagamento} onChange={e => setForm({...form, folha_pagamento: e.target.value})} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Impostos" type="number" step="0.01" value={form.impostos} onChange={e => setForm({...form, impostos: e.target.value})} />
          <Input label="Saldo Caixa" type="number" step="0.01" value={form.saldo_caixa} onChange={e => setForm({...form, saldo_caixa: e.target.value})} />
        </div>
        <div className="flex justify-end gap-2 pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button type="submit" loading={loading}>Salvar</Button>
        </div>
      </form>
    </Modal>
  );
}

function EditEmpresaModal({ isOpen, onClose, empresa, onSuccess }) {
  const { api } = useAuth();
  const toast = useToast();
  const [form, setForm] = useState({
    razao_social: '',
    nome_fantasia: '',
    cnpj: '',
    regime_tributario: '',
    setor: '',
    email: '',
    telefone: '',
    cidade: '',
    estado: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Atualiza form quando empresa muda
  useEffect(() => {
    if (empresa) {
      setForm({
        razao_social: empresa.razao_social || '',
        nome_fantasia: empresa.nome_fantasia || '',
        cnpj: empresa.cnpj || '',
        regime_tributario: empresa.regime_tributario || '',
        setor: empresa.setor || '',
        email: empresa.email || '',
        telefone: empresa.telefone || '',
        cidade: empresa.cidade || '',
        estado: empresa.estado || ''
      });
    }
  }, [empresa]);

  const regimes = [
    { value: '', label: 'Selecione...' },
    { value: 'Simples Nacional', label: 'Simples Nacional' },
    { value: 'Lucro Presumido', label: 'Lucro Presumido' },
    { value: 'Lucro Real', label: 'Lucro Real' },
    { value: 'MEI', label: 'MEI' }
  ];

  const estados = [
    { value: '', label: 'UF' }, { value: 'AC', label: 'AC' }, { value: 'AL', label: 'AL' },
    { value: 'AP', label: 'AP' }, { value: 'AM', label: 'AM' }, { value: 'BA', label: 'BA' },
    { value: 'CE', label: 'CE' }, { value: 'DF', label: 'DF' }, { value: 'ES', label: 'ES' },
    { value: 'GO', label: 'GO' }, { value: 'MA', label: 'MA' }, { value: 'MT', label: 'MT' },
    { value: 'MS', label: 'MS' }, { value: 'MG', label: 'MG' }, { value: 'PA', label: 'PA' },
    { value: 'PB', label: 'PB' }, { value: 'PR', label: 'PR' }, { value: 'PE', label: 'PE' },
    { value: 'PI', label: 'PI' }, { value: 'RJ', label: 'RJ' }, { value: 'RN', label: 'RN' },
    { value: 'RS', label: 'RS' }, { value: 'RO', label: 'RO' }, { value: 'RR', label: 'RR' },
    { value: 'SC', label: 'SC' }, { value: 'SP', label: 'SP' }, { value: 'SE', label: 'SE' },
    { value: 'TO', label: 'TO' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.razao_social.trim()) {
      setError('Razão Social é obrigatória');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const res = await api(`/empresas/${empresa.id}`, {
        method: 'PUT',
        body: JSON.stringify(form)
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Erro ao atualizar empresa');
      }
      
      toast.success('Empresa atualizada com sucesso!');
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Editar Empresa" size="lg">
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input 
          label="Razão Social *" 
          value={form.razao_social} 
          onChange={e => setForm({...form, razao_social: e.target.value})} 
          required 
        />
        
        <div className="grid grid-cols-2 gap-4">
          <Input 
            label="Nome Fantasia" 
            value={form.nome_fantasia} 
            onChange={e => setForm({...form, nome_fantasia: e.target.value})} 
          />
          <Input 
            label="CNPJ" 
            value={form.cnpj} 
            onChange={e => setForm({...form, cnpj: e.target.value})} 
            placeholder="00.000.000/0000-00" 
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <Select 
            label="Regime Tributário" 
            options={regimes} 
            value={form.regime_tributario} 
            onChange={e => setForm({...form, regime_tributario: e.target.value})} 
          />
          <Input 
            label="Setor/Atividade" 
            value={form.setor} 
            onChange={e => setForm({...form, setor: e.target.value})} 
            placeholder="Ex: Comércio, Serviços..." 
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <Input 
            label="Email" 
            type="email" 
            value={form.email} 
            onChange={e => setForm({...form, email: e.target.value})} 
          />
          <Input 
            label="Telefone" 
            value={form.telefone} 
            onChange={e => setForm({...form, telefone: e.target.value})} 
          />
        </div>
        
        <div className="grid grid-cols-3 gap-4">
          <Input 
            label="Cidade" 
            value={form.cidade} 
            onChange={e => setForm({...form, cidade: e.target.value})} 
            className="col-span-2" 
          />
          <Select 
            label="Estado" 
            options={estados} 
            value={form.estado} 
            onChange={e => setForm({...form, estado: e.target.value})} 
          />
        </div>
        
        <div className="flex justify-end gap-2 pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button type="submit" loading={loading}>Salvar Alterações</Button>
        </div>
      </form>
    </Modal>
  );
}

// ============================================================================
// PAGES - Importação Avançada
// ============================================================================

function ImportacaoPage({ onNavigate }) {
  const { api } = useAuth();
  const toast = useToast();
  
  // Estados do fluxo
  const [etapa, setEtapa] = useState('upload'); // upload, processando, preview, sucesso
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState('');
  
  // Arquivos
  const [arquivos, setArquivos] = useState([]);
  const [arquivosProcessados, setArquivosProcessados] = useState([]);
  const [progresso, setProgresso] = useState(0);
  
  // Dados consolidados
  const [dadosConsolidados, setDadosConsolidados] = useState(null);
  const [empresaExistente, setEmpresaExistente] = useState(null);
  
  // Drag and drop
  const [dragAtivo, setDragAtivo] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragAtivo(true);
  };

  const handleDragLeave = () => {
    setDragAtivo(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragAtivo(false);
    const files = Array.from(e.dataTransfer.files);
    adicionarArquivos(files);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    adicionarArquivos(files);
  };

  const adicionarArquivos = (files) => {
    const validFiles = files.filter(f => {
      const ext = f.name.split('.').pop().toLowerCase();
      return ['pdf', 'xls', 'xlsx'].includes(ext);
    });
    
    if (validFiles.length < files.length) {
      toast.warning('Alguns arquivos foram ignorados (formato inválido)');
    }
    
    setArquivos(prev => [...prev, ...validFiles]);
  };

  const removerArquivo = (index) => {
    setArquivos(prev => prev.filter((_, i) => i !== index));
  };

  const processarArquivos = async () => {
    if (arquivos.length === 0) {
      setErro('Selecione pelo menos um arquivo');
      return;
    }

    setEtapa('processando');
    setLoading(true);
    setErro('');
    setArquivosProcessados([]);
    setProgresso(0);

    const resultados = [];
    let empresaInfo = null;
    let cnpjEncontrado = null;

    for (let i = 0; i < arquivos.length; i++) {
      const file = arquivos[i];
      setProgresso(Math.round((i / arquivos.length) * 100));

      try {
        const formData = new FormData();
        formData.append('file', file);

        const res = await api('/importar/balancete', {
          method: 'POST',
          body: formData
        });

        const dados = await res.json();

        if (dados.sucesso) {
          const balancete = dados.balancete || dados;
          const empresa = balancete?.empresa || dados.empresa;
          
          // Capturar info da empresa
          if (!empresaInfo && empresa) {
            empresaInfo = empresa;
            cnpjEncontrado = empresa.cnpj;
          }

          resultados.push({
            nome: file.name,
            sucesso: true,
            competencia: balancete?.periodo?.fim?.substring(0, 7) || 'N/A',
            dados: balancete
          });
        } else {
          resultados.push({
            nome: file.name,
            sucesso: false,
            erro: dados.mensagem || 'Erro ao processar'
          });
        }
      } catch (err) {
        resultados.push({
          nome: file.name,
          sucesso: false,
          erro: err.message
        });
      }
    }

    setArquivosProcessados(resultados);
    setProgresso(100);

    // Verificar se empresa existe
    if (cnpjEncontrado) {
      try {
        const resEmp = await api(`/empresas/cnpj/${cnpjEncontrado}`);
        if (resEmp.ok) {
          setEmpresaExistente(await resEmp.json());
        }
      } catch {}
    }

    // Consolidar dados
    const sucessos = resultados.filter(r => r.sucesso);
    if (sucessos.length > 0) {
      setDadosConsolidados({
        empresa: empresaInfo,
        arquivos: sucessos,
        totalReceita: sucessos.reduce((sum, r) => sum + (r.dados?.totais?.receita_bruta || 0), 0),
        totalLucro: sucessos.reduce((sum, r) => sum + (r.dados?.totais?.lucro_liquido || 0), 0),
        competencias: sucessos.map(r => r.competencia).sort()
      });
    }

    setLoading(false);
    setEtapa('preview');
  };

  const confirmarImportacao = async () => {
    setLoading(true);
    setErro('');

    try {
      let empresaId = empresaExistente?.id;

      // Criar empresa se não existe
      if (!empresaId && dadosConsolidados?.empresa) {
        const emp = dadosConsolidados.empresa;
        const res = await api('/empresas', {
          method: 'POST',
          body: JSON.stringify({
            razao_social: emp.nome,
            cnpj: emp.cnpj,
            regime_tributario: 'Lucro Presumido'
          })
        });

        if (!res.ok) throw new Error('Erro ao criar empresa');
        
        const data = await res.json();
        empresaId = data.id;
        toast.success(`Empresa "${emp.nome}" criada!`);
      }

      // Salvar cada período com TODOS os campos do balancete
      for (const arq of arquivosProcessados.filter(a => a.sucesso)) {
        const totais = arq.dados?.totais || {};
        const periodo = arq.dados?.periodo || {};

        // Enviar todos os campos expandidos
        const dadosMensais = {
          competencia: periodo.fim?.substring(0, 7) || arq.competencia,
          // Campos básicos (compatibilidade)
          receita_bruta: totais.receita_bruta || totais.receita_servicos || 0,
          receita: totais.receita_bruta || totais.receita_servicos || 0,
          custos: totais.custos_total || 0,
          despesas: totais.despesas_operacionais || totais.despesas_financeiras || 0,
          impostos: totais.impostos_total || totais.deducoes_receita || 0,
          caixa: totais.disponivel || totais.caixa || 0,
          lucro_liquido: totais.lucro_liquido || totais.lucro_exercicio || 0,
          // Balanço Patrimonial
          ativo_total: totais.ativo_total || 0,
          ativo_circulante: totais.ativo_circulante || 0,
          disponivel: totais.disponivel || 0,
          bancos: totais.bancos || 0,
          clientes: totais.clientes || totais.duplicatas_receber || 0,
          estoques: totais.estoques || 0,
          passivo_total: totais.passivo_total || 0,
          passivo_circulante: totais.passivo_circulante || 0,
          passivo_nao_circulante: totais.passivo_nao_circulante || 0,
          patrimonio_liquido: totais.patrimonio_liquido || totais.capital_social || 0,
          capital_social: totais.capital_social || 0,
          // DRE
          receita_servicos: totais.receita_servicos || 0,
          deducoes_receita: totais.deducoes_receita || totais.impostos_sobre_vendas || 0,
          custos_total: totais.custos_total || 0,
          despesas_operacionais: totais.despesas_operacionais || 0,
          despesas_financeiras: totais.despesas_financeiras || 0,
          receitas_financeiras: totais.receitas_financeiras || 0,
          // Impostos detalhados
          iss: totais.iss_deducao || totais.iss_recolher || 0,
          pis: totais.pis_deducao || totais.pis_recolher || 0,
          cofins: totais.cofins_deducao || totais.cofins_recolher || 0,
          irpj: totais.irpj_deducao || totais.irpj_recolher || 0,
          csll: totais.csll_deducao || totais.csll_recolher || 0,
          impostos_total: totais.impostos_total || totais.deducoes_receita || 0,
          // Meta
          arquivo_origem: arq.nome
        };

        await api(`/empresas/${empresaId}/dados`, {
          method: 'POST',
          body: JSON.stringify(dadosMensais)
        });
      }

      setEtapa('sucesso');
      toast.success('Importação concluída com sucesso!');

    } catch (err) {
      setErro(err.message);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const resetar = () => {
    setEtapa('upload');
    setArquivos([]);
    setArquivosProcessados([]);
    setDadosConsolidados(null);
    setEmpresaExistente(null);
    setErro('');
    setProgresso(0);
  };

  const formatarMoeda = (valor) => {
    if (!valor && valor !== 0) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  };

  // ============ ETAPA 1: UPLOAD MÚLTIPLO ============
  if (etapa === 'upload') {
    return (
      <div>
        <Header 
          title="Importação de Balancetes" 
          subtitle="Importe múltiplos arquivos - cada um representa um mês"
        />

        <Card className="p-6 mb-4">
          {erro && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              {erro}
            </div>
          )}

          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
              dragAtivo 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'
            }`}
          >
            <Upload className="w-12 h-12 text-slate-400 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-slate-700 mb-1">
              Arraste seus arquivos aqui
            </h3>
            <p className="text-slate-500 mb-4 text-sm">
              Você pode selecionar múltiplos arquivos de uma vez
            </p>
            <input
              type="file"
              accept=".pdf,.xls,.xlsx"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload-import"
              multiple
            />
            <label 
              htmlFor="file-upload-import"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition-colors"
            >
              <FileSpreadsheet className="w-4 h-4" />
              Selecionar Arquivos
            </label>
            <p className="text-xs text-slate-400 mt-3">
              PDF, XLS, XLSX • Cada arquivo = 1 mês de dados
            </p>
          </div>
        </Card>

        {/* Lista de arquivos selecionados */}
        {arquivos.length > 0 && (
          <Card className="p-4 mb-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-semibold text-slate-800">
                {arquivos.length} arquivo(s) selecionado(s)
              </h3>
              <Button variant="ghost" size="sm" onClick={() => setArquivos([])}>
                Limpar todos
              </Button>
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {arquivos.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-500" />
                    <span className="text-sm text-slate-700">{file.name}</span>
                    <span className="text-xs text-slate-400">
                      ({(file.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                  <button
                    onClick={() => removerArquivo(index)}
                    className="p-1 hover:bg-slate-200 rounded"
                  >
                    <X className="w-4 h-4 text-slate-400" />
                  </button>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t">
              <Button onClick={processarArquivos} className="w-full">
                <Upload className="w-4 h-4" />
                Processar {arquivos.length} arquivo(s)
              </Button>
            </div>
          </Card>
        )}

        <Card className="p-4 bg-blue-50 border-blue-200">
          <h4 className="font-medium text-blue-800 mb-2 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Como funciona
          </h4>
          <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
            <li>Cada arquivo de balancete representa os dados de um mês</li>
            <li>O sistema extrai automaticamente a empresa pelo CNPJ</li>
            <li>Se a empresa já existe, os dados são adicionados ao histórico</li>
            <li>Se é nova, ela é cadastrada automaticamente</li>
          </ul>
        </Card>
      </div>
    );
  }

  // ============ ETAPA 2: PROCESSANDO ============
  if (etapa === 'processando') {
    return (
      <div>
        <Header title="Processando Arquivos" />
        <Card className="p-8 text-center">
          <Loader2 className="w-16 h-16 text-blue-500 animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-800 mb-2">
            Processando {arquivos.length} arquivo(s)...
          </h2>
          <div className="w-full max-w-md mx-auto bg-slate-200 rounded-full h-3 mt-4">
            <div 
              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${progresso}%` }}
            />
          </div>
          <p className="text-slate-500 mt-2">{progresso}% concluído</p>
        </Card>
      </div>
    );
  }

  // ============ ETAPA 3: PREVIEW ============
  if (etapa === 'preview') {
    const sucessos = arquivosProcessados.filter(a => a.sucesso);
    const erros = arquivosProcessados.filter(a => !a.sucesso);
    const empresa = dadosConsolidados?.empresa || {};
    
    // Pegar último período para indicadores
    const ultimoPeriodo = sucessos.length > 0 ? sucessos[sucessos.length - 1].dados : null;
    const indicadores = ultimoPeriodo?.indicadores || {};
    const totaisUltimo = ultimoPeriodo?.totais || {};

    return (
      <div>
        <Header 
          title="Confirmar Importação" 
          subtitle={`${sucessos.length} de ${arquivosProcessados.length} arquivos processados com sucesso`}
          actions={
            <Button variant="ghost" onClick={resetar}>
              <ArrowLeft className="w-4 h-4" /> Voltar
            </Button>
          }
        />

        {erro && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {erro}
          </div>
        )}

        {/* Status da Empresa */}
        <Card className={`p-4 mb-4 ${empresaExistente ? 'bg-blue-50 border-blue-200' : 'bg-green-50 border-green-200'}`}>
          <div className="flex items-center gap-3">
            {empresaExistente ? (
              <>
                <CheckCircle className="w-6 h-6 text-blue-600" />
                <div>
                  <p className="font-medium text-blue-800">Empresa já cadastrada</p>
                  <p className="text-sm text-blue-600">
                    {sucessos.length} meses serão adicionados ao histórico de "{empresaExistente.razao_social}"
                  </p>
                </div>
              </>
            ) : (
              <>
                <Plus className="w-6 h-6 text-green-600" />
                <div>
                  <p className="font-medium text-green-800">Nova empresa será criada</p>
                  <p className="text-sm text-green-600">
                    "{empresa.nome}" com {sucessos.length} meses de dados
                  </p>
                </div>
              </>
            )}
          </div>
        </Card>

        <div className="grid lg:grid-cols-3 gap-4 mb-4">
          {/* Info Empresa */}
          <Card className="p-4">
            <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-600" />
              Empresa
            </h3>
            <div className="space-y-2 text-sm">
              <p className="font-medium">{empresa.nome || '-'}</p>
              <p className="text-slate-500">{empresa.cnpj_formatado || empresa.cnpj || '-'}</p>
              {empresa.contador?.nome && (
                <p className="text-slate-500 text-xs">Contador: {empresa.contador.nome}</p>
              )}
            </div>
          </Card>

          {/* Resumo Financeiro */}
          <Card className="p-4">
            <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              Total Acumulado
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-slate-500">Receita:</span>
                <span className="font-semibold text-green-600">
                  {formatarMoeda(dadosConsolidados?.totalReceita)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-500">Lucro:</span>
                <span className="font-semibold text-blue-600">
                  {formatarMoeda(dadosConsolidados?.totalLucro)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-500">Margem Média:</span>
                <span className="font-semibold">
                  {dadosConsolidados?.totalReceita > 0 
                    ? ((dadosConsolidados.totalLucro / dadosConsolidados.totalReceita) * 100).toFixed(1) 
                    : 0}%
                </span>
              </div>
            </div>
          </Card>

          {/* Indicadores do Último Período */}
          <Card className="p-4">
            <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-purple-600" />
              Último Período
            </h3>
            <div className="grid grid-cols-2 gap-2 text-center">
              <div className="p-2 bg-slate-50 rounded">
                <p className="text-lg font-bold text-blue-600">{indicadores.margem_liquida || 0}%</p>
                <p className="text-xs text-slate-500">Margem</p>
              </div>
              <div className="p-2 bg-slate-50 rounded">
                <p className="text-lg font-bold text-green-600">{indicadores.liquidez_corrente || 0}</p>
                <p className="text-xs text-slate-500">Liquidez</p>
              </div>
              <div className="p-2 bg-slate-50 rounded">
                <p className="text-lg font-bold text-purple-600">{indicadores.roe > 1000 ? '>1000' : indicadores.roe || 0}%</p>
                <p className="text-xs text-slate-500">ROE</p>
              </div>
              <div className="p-2 bg-slate-50 rounded">
                <p className="text-lg font-bold text-orange-600">{indicadores.carga_tributaria || 0}%</p>
                <p className="text-xs text-slate-500">Tributos</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Lista de arquivos processados */}
        <Card className="p-4 mb-4">
          <h3 className="font-semibold text-slate-800 mb-3">Arquivos Processados</h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {arquivosProcessados.map((arq, i) => (
              <div 
                key={i} 
                className={`flex items-center justify-between p-3 rounded-lg ${
                  arq.sucesso ? 'bg-green-50' : 'bg-red-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  {arq.sucesso ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                  )}
                  <div>
                    <p className="font-medium text-slate-800">{arq.nome}</p>
                    <p className={`text-xs ${arq.sucesso ? 'text-green-600' : 'text-red-600'}`}>
                      {arq.sucesso ? `Competência: ${arq.competencia}` : arq.erro}
                    </p>
                  </div>
                </div>
                {arq.sucesso && arq.dados?.totais?.receita_bruta && (
                  <span className="text-sm text-slate-600">
                    {formatarMoeda(arq.dados.totais.receita_bruta)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </Card>

        {/* Erros */}
        {erros.length > 0 && (
          <Card className="p-4 mb-4 bg-red-50 border-red-200">
            <h3 className="font-semibold text-red-800 mb-2">
              {erros.length} arquivo(s) com erro
            </h3>
            <ul className="text-sm text-red-700 space-y-1">
              {erros.map((e, i) => (
                <li key={i}>• {e.nome}: {e.erro}</li>
              ))}
            </ul>
          </Card>
        )}

        {/* Botões */}
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={resetar}>Cancelar</Button>
          {sucessos.length > 0 && (
            <Button onClick={confirmarImportacao} loading={loading}>
              <CheckCircle className="w-4 h-4" />
              {empresaExistente ? `Adicionar ${sucessos.length} meses` : `Criar Empresa e Importar`}
            </Button>
          )}
        </div>
      </div>
    );
  }

  // ============ ETAPA 4: SUCESSO ============
  if (etapa === 'sucesso') {
    const empresa = dadosConsolidados?.empresa || {};
    const sucessos = arquivosProcessados.filter(a => a.sucesso);
    
    return (
      <div>
        <Header title="Importação Concluída" />
        
        <Card className="p-8 text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-800 mb-2">
            Importação realizada com sucesso!
          </h2>
          <p className="text-slate-600 mb-2">
            {empresa.nome}
          </p>
          <p className="text-slate-500 mb-6">
            {sucessos.length} meses de dados importados
          </p>
          
          <div className="flex justify-center gap-3">
            <Button variant="secondary" onClick={resetar}>
              <Upload className="w-4 h-4" />
              Importar mais arquivos
            </Button>
            <Button onClick={() => onNavigate('empresas')}>
              <Building2 className="w-4 h-4" />
              Ver Empresas
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return null;
}

// ============================================================================
// MAIN APP
// ============================================================================

function AppContent() {
  const { user, loading } = useAuth();
  const [page, setPage] = useState('dashboard');
  const [pageParams, setPageParams] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  if (loading) return <LoadingScreen />;
  if (!user) return <AuthPages />;

  const navigate = (pageName, params = null) => { setPage(pageName); setPageParams(params); };

  const renderPage = () => {
    switch (page) {
      case 'dashboard': return <DashboardPage onNavigate={navigate} />;
      case 'empresas': return <EmpresasPage onNavigate={navigate} />;
      case 'nova-empresa': return <NovaEmpresaPage onNavigate={navigate} />;
      case 'empresa': return <EmpresaDetailPage empresaId={pageParams} onNavigate={navigate} />;
      case 'alertas': return <AlertasPage onNavigate={navigate} />;
      case 'importacao': return <ImportacaoPage onNavigate={navigate} />;
      case 'relatorios': return <RelatoriosPage onNavigate={navigate} />;
      case 'analise-financeira': 
        return <AnaliseFinanceiraPage 
          empresaId={pageParams?.empresaId} 
          empresaNome={pageParams?.empresaNome}
          onBack={() => navigate('empresa', pageParams?.empresaId)} 
        />;
      default: return <DashboardPage onNavigate={navigate} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar currentPage={page} onNavigate={navigate} collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
      <main className={`transition-all ${sidebarCollapsed ? 'ml-16' : 'ml-64'} p-6`}>{renderPage()}</main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <ToastProvider>
          <AppContent />
        </ToastProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}
