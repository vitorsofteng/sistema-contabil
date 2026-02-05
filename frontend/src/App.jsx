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
  CheckCircle, Bell, ArrowLeft, FileSpreadsheet, Loader2, BarChart3, X, PieChart, Check, Info
} from 'lucide-react';
import Papa from 'papaparse';
import RevisaoImportacao from './RevisaoImportacao.jsx';

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
    setor: '', email: '', telefone: '', cidade: '', estado: '', sistema_contabil: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sistemasContabeis, setSistemasContabeis] = useState([]);
  const [buscaSistema, setBuscaSistema] = useState('');
  const [showSistemaDropdown, setShowSistemaDropdown] = useState(false);
  const [loadingSistemas, setLoadingSistemas] = useState(true);

  // Carregar lista de sistemas contábeis
  useEffect(() => {
    loadSistemasContabeis();
  }, []);

  const loadSistemasContabeis = async (busca = '') => {
    try {
      const url = busca 
        ? `/api/sistemas-contabeis?busca=${encodeURIComponent(busca)}`
        : '/api/sistemas-contabeis';
      const res = await api(url);
      if (res.ok) {
        const data = await res.json();
        setSistemasContabeis(data.sistemas || []);
      }
    } catch (err) {
      console.error('Erro ao carregar sistemas:', err);
      // Fallback local
      setSistemasContabeis([
        { id: 0, nome: 'Outro / Não sei', fabricante: 'Genérico', tem_parser: false, label: 'Outro / Não sei' },
        { id: 1, nome: 'Domínio Sistemas', fabricante: 'Thomson Reuters', tem_parser: true, label: 'Domínio Sistemas (Thomson Reuters)' },
      ]);
    } finally {
      setLoadingSistemas(false);
    }
  };

  // Filtrar sistemas localmente enquanto digita
  const sistemasFiltrados = buscaSistema
    ? sistemasContabeis.filter(s => 
        s.nome.toLowerCase().includes(buscaSistema.toLowerCase()) ||
        s.fabricante.toLowerCase().includes(buscaSistema.toLowerCase())
      )
    : sistemasContabeis;

  // Sistema selecionado
  const sistemaSelecionado = sistemasContabeis.find(s => s.id === form.sistema_contabil);

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
          
          {/* Sistema Contábil - Dropdown com busca */}
          <div className="relative">
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Sistema Contábil para Balancetes
            </label>
            <div className="relative">
              <input
                type="text"
                value={showSistemaDropdown ? buscaSistema : (sistemaSelecionado?.label || 'Selecione o sistema...')}
                onChange={e => {
                  setBuscaSistema(e.target.value);
                  setShowSistemaDropdown(true);
                }}
                onFocus={() => setShowSistemaDropdown(true)}
                placeholder="Digite para buscar..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            </div>
            
            {showSistemaDropdown && (
              <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-60 overflow-auto">
                {loadingSistemas ? (
                  <div className="p-3 text-center text-slate-500">Carregando...</div>
                ) : sistemasFiltrados.length > 0 ? (
                  sistemasFiltrados.map(sistema => (
                    <div
                      key={sistema.id}
                      onClick={() => {
                        setForm({...form, sistema_contabil: sistema.id});
                        setBuscaSistema('');
                        setShowSistemaDropdown(false);
                      }}
                      className={`px-3 py-2 cursor-pointer hover:bg-blue-50 flex items-center justify-between ${
                        form.sistema_contabil === sistema.id ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div>
                        <div className="font-medium text-slate-900">{sistema.nome}</div>
                        <div className="text-xs text-slate-500">{sistema.fabricante}</div>
                      </div>
                      {sistema.tem_parser && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                          Parser local
                        </span>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="p-3 text-center text-slate-500">Nenhum sistema encontrado</div>
                )}
              </div>
            )}
            
            {sistemaSelecionado && (
              <p className="mt-1 text-xs text-slate-500">
                {sistemaSelecionado.tem_parser 
                  ? '✓ Importação automática disponível (grátis e instantânea)'
                  : '○ Importação via IA (pode ter custo)'}
              </p>
            )}
          </div>
          
          {/* Overlay para fechar dropdown ao clicar fora */}
          {showSistemaDropdown && (
            <div 
              className="fixed inset-0 z-40" 
              onClick={() => setShowSistemaDropdown(false)}
            />
          )}
          
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
  const [temNovosDados, setTemNovosDados] = useState(false); // Controla se há novos dados desde última análise
  const [dataUltimoLoad, setDataUltimoLoad] = useState(null); // Controla quando foi o último load

  // Recarregar dados sempre que a página for acessada (não apenas quando empresaId muda)
  useEffect(() => { 
    loadData(); 
    // Marcar timestamp do load para debug
    setDataUltimoLoad(new Date().toISOString());
  }, [empresaId]);
  
  // Também recarregar quando o usuário volta para esta página (foco na janela)
  useEffect(() => {
    const handleFocus = () => {
      console.log('[EMPRESA] Janela ganhou foco, recarregando dados...');
      loadData();
    };
    
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [empresaId]);

  const loadData = async () => {
    setLoading(true);
    console.log('[EMPRESA] Carregando dados da empresa', empresaId);
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
        const dadosList = regData.dados || regData || [];
        setRegistros(dadosList);
        
        console.log('[EMPRESA] Dados carregados:', dadosList.length, 'registros');
        
        // Verificar se há dados mais recentes que a última análise
        if (anaRes.ok) {
          const anaData = await anaRes.json();
          const analisesList = anaData.analises || anaData || [];
          setAnalises(analisesList);
          
          if (analisesList.length > 0) {
            setUltimaAnalise(analisesList[0]);
            const dataUltimaAnalise = new Date(analisesList[0].data_analise);
            
            console.log('[EMPRESA] Última análise em:', analisesList[0].data_analise);
            
            // Verificar se algum dado foi criado/atualizado após a última análise
            const temDadosNovos = dadosList.some(d => {
              // Usar updated_at se disponível, senão created_at
              const dataStr = d.updated_at || d.created_at;
              if (!dataStr) {
                console.log(`[EMPRESA] Dado ${d.competencia} sem data de criação/atualização`);
                return false;
              }
              const dataAtualizacao = new Date(dataStr);
              const isNovo = dataAtualizacao > dataUltimaAnalise;
              if (isNovo) {
                console.log(`[EMPRESA] ✓ Dado ${d.competencia} é mais recente:`, dataStr);
              }
              return isNovo;
            });
            
            // Também verificar se há mais registros do que na última análise
            // (caso os timestamps não estejam disponíveis)
            const qtdMesesAnalise = analisesList[0].meses_analisados || 0;
            const temMaisRegistros = dadosList.length > qtdMesesAnalise;
            
            const deveHabilitar = temDadosNovos || temMaisRegistros;
            console.log(`[EMPRESA] Tem dados novos: ${temDadosNovos}, tem mais registros: ${temMaisRegistros} (${dadosList.length} vs ${qtdMesesAnalise})`);
            
            setTemNovosDados(deveHabilitar);
          } else {
            // Nunca fez análise, pode analisar se tem dados
            console.log('[EMPRESA] Nenhuma análise anterior, habilitando botão');
            setTemNovosDados(dadosList.length > 0);
          }
        }
      } else if (anaRes.ok) {
        const anaData = await anaRes.json();
        const analisesList = anaData.analises || anaData || [];
        setAnalises(analisesList);
        if (analisesList.length > 0) setUltimaAnalise(analisesList[0]);
        setTemNovosDados(analisesList.length === 0);
      }
    } catch (err) {
      toast.error('Erro ao carregar dados da empresa');
    } finally {
      setLoading(false);
    }
  };
  
  // Callback quando importação é bem sucedida
  const handleImportSuccess = () => {
    setTemNovosDados(true);
    loadData();
  };

  const executarAnalise = async () => {
    if (registros.length < 3) {
      toast.warning('Necessário pelo menos 3 meses de dados para análise');
      return;
    }
    
    setAnalisando(true);
    try {
      const res = await api(`/empresas/${empresaId}/analises`, { method: 'POST' });
      if (res.ok) {
        const result = await res.json();
        toast.success('Análise concluída com sucesso!');
        setTemNovosDados(false); // Análise feita, desabilita botão
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
            <div className="relative group">
              <Button 
                onClick={executarAnalise} 
                loading={analisando} 
                disabled={registros.length < 3 || (!temNovosDados && ultimaAnalise)}
              >
                <BarChart3 className="w-4 h-4" /> Analisar
              </Button>
              {!temNovosDados && ultimaAnalise && registros.length >= 3 && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  Importe novos dados para analisar novamente
                  <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800"></div>
                </div>
              )}
            </div>
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
      
      <UploadModal isOpen={showUpload} onClose={() => setShowUpload(false)} empresaId={empresaId} onSuccess={handleImportSuccess} registrosExistentes={registros} />
      <RegistroModal isOpen={showRegistro} onClose={() => setShowRegistro(false)} empresaId={empresaId} onSuccess={handleImportSuccess} />
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
  const toast = useToast();
  const [step, setStep] = useState(1); // 1=upload, 2=processando, 3=preview, 4=conflito, 5=erro
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resultadoIA, setResultadoIA] = useState(null);

  // Handler de seleção de arquivo - SEMPRE usa IA
  const handleFileChange = async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setError('');
    await processarComIA(f);
  };

  // Processar com IA
  const processarComIA = async (arquivo) => {
    setStep(2);
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', arquivo);
      
      const res = await fetch(`/api/empresas/${empresaId}/importar/ia/preview`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: formData
      });
      
      const result = await res.json();
      
      if (!res.ok) {
        throw new Error(result.detail || 'Erro ao processar arquivo');
      }
      
      if (result.sucesso) {
        setResultadoIA(result);
        setStep(result.periodo_existe ? 4 : 3);
      } else {
        setError(result.erro || 'Não foi possível extrair dados do arquivo');
        setStep(5);
      }
    } catch (err) {
      setError(err.message || 'Erro ao processar arquivo com IA');
      setStep(5);
    } finally {
      setLoading(false);
    }
  };

  // Confirmar importação
  const confirmarImportacao = async (substituir = false) => {
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('substituir_existentes', substituir ? 'true' : 'false');
      
      const res = await fetch(`/api/empresas/${empresaId}/importar/ia`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: formData
      });
      
      const result = await res.json();
      
      if (result.sucesso) {
        toast.success(result.mensagem || 'Dados importados com sucesso!');
        onSuccess();
        onClose();
      } else if (result.requer_acao === 'confirmar_substituicao') {
        setResultadoIA(result);
        setStep(4);
      } else {
        throw new Error(result.erro || 'Erro na importação');
      }
    } catch (err) {
      setError(err.message);
      setStep(5);
    } finally {
      setLoading(false);
    }
  };

  // Formatar valor monetário
  const formatarValor = (valor) => {
    if (!valor || valor === 0) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  };

  // Reset ao fechar
  useEffect(() => {
    if (!isOpen) { 
      setStep(1); 
      setFile(null); 
      setError(''); 
      setResultadoIA(null);
    }
  }, [isOpen]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Importar Dados" size="lg">
      
      {/* Step 1: Upload */}
      {step === 1 && (
        <div className="text-center py-8">
          <input type="file" accept=".pdf" onChange={handleFileChange} className="hidden" id="file-upload" />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Upload className="w-10 h-10 text-blue-600" />
            </div>
            <p className="text-lg font-medium text-slate-900 mb-1">Selecione um arquivo</p>
            <p className="text-sm text-slate-500">PDF, Excel, CSV ou Imagem</p>
          </label>
          <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg text-left border border-blue-100">
            <p className="text-sm font-medium text-blue-800 mb-2">🤖 Importação Inteligente com IA</p>
            <p className="text-xs text-blue-600">
              Funciona com <strong>qualquer sistema contábil</strong>: Domínio, Contmatic, Alterdata, Prosoft, Fortes, e outros.
              A IA analisa e extrai os dados automaticamente.
            </p>
          </div>
        </div>
      )}
      
      {/* Step 2: Processando com IA */}
      {step === 2 && (
        <div className="text-center py-12">
          <div className="relative">
            <Loader2 className="w-16 h-16 text-blue-600 animate-spin mx-auto" />
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl">🤖</span>
            </div>
          </div>
          <p className="text-lg font-medium text-slate-900 mt-6">Analisando com IA...</p>
          <p className="text-sm text-slate-500 mt-2">Extraindo dados do documento</p>
          <p className="text-xs text-slate-400 mt-4">Isso pode levar alguns segundos</p>
        </div>
      )}
      
      {/* Step 3: Preview dos dados */}
      {step === 3 && resultadoIA && (
        <div>
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-6 h-6 text-green-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-green-800">Dados extraídos com sucesso!</h4>
                <p className="text-sm text-green-700 mt-1">
                  Confiança: <strong className="capitalize">{resultadoIA.confianca}</strong>
                  {resultadoIA.sistema_detectado && resultadoIA.sistema_detectado !== 'desconhecido' && (
                    <> • Sistema: <strong>{resultadoIA.sistema_detectado}</strong></>
                  )}
                  {resultadoIA.metodo_usado && (
                    <> • Método: <strong className="capitalize">{resultadoIA.metodo_usado === 'parser_local' ? '📦 Parser Local (grátis)' : '🤖 IA Claude'}</strong></>
                  )}
                </p>
              </div>
            </div>
          </div>
          
          <div className="mb-4 p-4 bg-slate-50 rounded-lg">
            <div className="grid grid-cols-2 gap-4 text-sm mb-4">
              {resultadoIA.empresa_arquivo && (
                <div><span className="text-slate-500">Empresa:</span> <strong>{resultadoIA.empresa_arquivo}</strong></div>
              )}
              {resultadoIA.cnpj_arquivo && (
                <div><span className="text-slate-500">CNPJ:</span> <strong>{resultadoIA.cnpj_arquivo}</strong></div>
              )}
              {resultadoIA.periodo && (
                <div><span className="text-slate-500">Período:</span> <strong>{resultadoIA.periodo}</strong></div>
              )}
              <div><span className="text-slate-500">Campos extraídos:</span> <strong>{resultadoIA.campos_extraidos?.length || 0}</strong></div>
            </div>
            
            <h4 className="font-medium text-slate-900 mb-2">Valores encontrados:</h4>
            <div className="grid grid-cols-2 gap-2 text-sm max-h-48 overflow-y-auto">
              {Object.entries(resultadoIA.dados || {})
                .filter(([k, v]) => v && v > 0 && !['ano', 'mes'].includes(k))
                .map(([campo, valor]) => (
                  <div key={campo} className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-600 capitalize">{campo.replace(/_/g, ' ')}:</span>
                    <span className="font-medium">{formatarValor(valor)}</span>
                  </div>
                ))}
            </div>
          </div>
          
          {resultadoIA.observacoes?.length > 0 && (
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm font-medium text-amber-800 mb-1">Observações:</p>
              <ul className="text-xs text-amber-700">
                {resultadoIA.observacoes.map((obs, i) => <li key={i}>• {obs}</li>)}
              </ul>
            </div>
          )}
          
          <div className="text-xs text-slate-400 mb-4 flex justify-between">
            <span>Custo: ~R$ {resultadoIA.custo_estimado?.toFixed(4) || '0.00'}</span>
            <span>Tokens: {resultadoIA.tokens_usados || 0}</span>
          </div>
          
          <div className="flex justify-between">
            <Button variant="secondary" onClick={() => { setStep(1); setFile(null); setResultadoIA(null); }}>
              Cancelar
            </Button>
            <Button onClick={() => confirmarImportacao(false)} loading={loading}>
              Confirmar e Importar
            </Button>
          </div>
        </div>
      )}
      
      {/* Step 4: Conflito de período */}
      {step === 4 && resultadoIA && (
        <div>
          <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-amber-800">Período já existe</h4>
                <p className="text-sm text-amber-700 mt-1">
                  Já existem dados para <strong>{resultadoIA.periodo || `${resultadoIA.mes}/${resultadoIA.ano}`}</strong>
                </p>
              </div>
            </div>
          </div>
          
          <div className="mb-4 p-4 bg-slate-50 rounded-lg">
            <h4 className="font-medium text-slate-900 mb-2">Dados do arquivo:</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {resultadoIA.empresa_arquivo && <p><span className="text-slate-500">Empresa:</span> {resultadoIA.empresa_arquivo}</p>}
              <p><span className="text-slate-500">Campos:</span> {resultadoIA.campos_extraidos?.length || 0}</p>
              <p><span className="text-slate-500">Confiança:</span> <span className="capitalize">{resultadoIA.confianca}</span></p>
            </div>
          </div>
          
          <p className="text-sm text-slate-700 mb-4">Deseja substituir os dados existentes pelos novos dados?</p>
          
          <div className="flex justify-between">
            <Button variant="secondary" onClick={onClose}>Cancelar</Button>
            <Button onClick={() => confirmarImportacao(true)} loading={loading}>
              Substituir dados
            </Button>
          </div>
        </div>
      )}
      
      {/* Step 5: Erro */}
      {step === 5 && (
        <div>
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-red-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-red-800 text-lg">Erro na importação</h4>
                <p className="text-sm text-red-700 mt-2">{error}</p>
              </div>
            </div>
          </div>
          
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-6">
            <h4 className="font-medium text-blue-800 mb-2">O que fazer:</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Verifique se o arquivo não está corrompido ou protegido</li>
              <li>• Tente um arquivo com melhor qualidade (menos escaneado)</li>
              <li>• Certifique-se que é um documento contábil válido</li>
            </ul>
          </div>
          
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => { setStep(1); setFile(null); setError(''); }}>
              Tentar outro arquivo
            </Button>
            <Button onClick={onClose}>Fechar</Button>
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
  const [etapa, setEtapa] = useState('upload'); // upload, detectando, processando, preview, revisao, sucesso
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState('');
  
  // Arquivos
  const [arquivos, setArquivos] = useState([]);
  const [arquivosProcessados, setArquivosProcessados] = useState([]);
  const [progresso, setProgresso] = useState(0);
  
  // Dados consolidados
  const [dadosConsolidados, setDadosConsolidados] = useState(null);
  const [empresaExistente, setEmpresaExistente] = useState(null);
  
  // === NOVO: Estados para revisão individual ===
  const [arquivoSelecionado, setArquivoSelecionado] = useState(null);
  const [dadosRevisao, setDadosRevisao] = useState(null);
  const [carregandoRevisao, setCarregandoRevisao] = useState(false);
  
  // Modal de CNPJ faltando
  const [showModalCnpj, setShowModalCnpj] = useState(false);
  const [cnpjManual, setCnpjManual] = useState('');
  const [erroCnpj, setErroCnpj] = useState('');
  
  // Drag and drop
  const [dragAtivo, setDragAtivo] = useState(false);

  // Sistema contábil - Detecção automática
  const [sistemasContabeis, setSistemasContabeis] = useState([]);
  const [sistemaContabilSelecionado, setSistemaContabilSelecionado] = useState(null);
  const [loadingSistemas, setLoadingSistemas] = useState(true);
  
  // Modal de detecção
  const [showModalDeteccao, setShowModalDeteccao] = useState(false);
  const [sistemaDetectado, setSistemaDetectado] = useState(null);
  const [confiancaDeteccao, setConfiancaDeteccao] = useState(0);
  const [lembrarEscolha, setLembrarEscolha] = useState(false);
  const [showListaSistemas, setShowListaSistemas] = useState(false);
  const [buscaSistema, setBuscaSistema] = useState('');
  const [detectando, setDetectando] = useState(false);

  // Chave para localStorage baseada no contador logado
  const getStorageKey = () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return `sistema_contabil_preferido_${payload.contador_id || 'default'}`;
      } catch { return 'sistema_contabil_preferido_default'; }
    }
    return 'sistema_contabil_preferido_default';
  };

  // Carregar sistemas contábeis
  useEffect(() => {
    loadSistemasContabeis();
  }, []);

  const loadSistemasContabeis = async () => {
    try {
      const res = await api('/api/sistemas-contabeis');
      if (res.ok) {
        const data = await res.json();
        setSistemasContabeis(data.sistemas || []);
      }
    } catch (err) {
      console.error('Erro ao carregar sistemas:', err);
      setSistemasContabeis([
        { id: 0, nome: 'Outro / Não sei', fabricante: '', tem_parser: false, label: 'Outro / Não sei' },
        { id: 1, nome: 'Domínio Sistemas', fabricante: 'Thomson Reuters', tem_parser: true, label: 'Domínio Sistemas (Thomson Reuters)' },
      ]);
    } finally {
      setLoadingSistemas(false);
    }
  };

  // Verificar se há preferência salva
  const getSistemaPreferido = () => {
    try {
      const saved = localStorage.getItem(getStorageKey());
      if (saved) {
        return JSON.parse(saved);
      }
    } catch {}
    return null;
  };

  // Salvar preferência
  const salvarPreferencia = (sistemaId) => {
    try {
      localStorage.setItem(getStorageKey(), JSON.stringify({
        sistemaId,
        timestamp: Date.now()
      }));
    } catch {}
  };

  // Limpar preferência
  const limparPreferencia = () => {
    try {
      localStorage.removeItem(getStorageKey());
    } catch {}
  };

  // Filtrar sistemas
  const sistemasFiltrados = buscaSistema
    ? sistemasContabeis.filter(s => 
        s.nome.toLowerCase().includes(buscaSistema.toLowerCase()) ||
        (s.fabricante && s.fabricante.toLowerCase().includes(buscaSistema.toLowerCase()))
      )
    : sistemasContabeis;

  // Sistema selecionado
  const sistemaSelecionado = sistemasContabeis.find(s => s.id === sistemaContabilSelecionado);

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

  const adicionarArquivos = async (files) => {
    const validFiles = files.filter(f => {
      const ext = f.name.split('.').pop().toLowerCase();
      return ['pdf'].includes(ext);
    });
    
    if (validFiles.length < files.length) {
      toast.warning('Alguns arquivos foram ignorados (formato inválido)');
    }

    if (validFiles.length === 0) return;
    
    setArquivos(prev => [...prev, ...validFiles]);
    
    // Verificar se já tem preferência salva
    const preferencia = getSistemaPreferido();
    if (preferencia && preferencia.sistemaId !== undefined) {
      // Usar sistema preferido automaticamente
      setSistemaContabilSelecionado(preferencia.sistemaId);
      const sistema = sistemasContabeis.find(s => s.id === preferencia.sistemaId);
      if (sistema) {
        toast.success(`Usando sistema: ${sistema.nome}. Clique em "Alterar" para trocar.`, { duration: 4000 });
      }
      return;
    }
    
    // Detectar sistema automaticamente (usa o primeiro arquivo)
    if (validFiles.length > 0 && !sistemaContabilSelecionado) {
      await detectarSistema(validFiles[0]);
    }
  };

  const detectarSistema = async (arquivo) => {
    setDetectando(true);
    
    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);
      
      const res = await fetch('/api/detectar-sistema', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });
      
      if (res.ok) {
        const data = await res.json();
        
        console.log('[DETECTOR] Resultado:', data);
        console.log('[DETECTOR] Confiança:', data.confianca, '%');
        console.log('[DETECTOR] Indicadores:', data.indicadores);
        
        // Aumentado de 40% para 60% - só aceita se tiver indicadores fortes
        if (data.detectado && data.confianca >= 60) {
          // Sistema detectado com confiança suficiente
          setSistemaDetectado(data.sistema);
          setConfiancaDeteccao(data.confianca);
          setShowModalDeteccao(true);
        } else {
          // Não conseguiu detectar com confiança, mostra lista para seleção manual
          console.log('[DETECTOR] Confiança insuficiente, mostrando lista de sistemas');
          setSistemaDetectado(null);
          setShowListaSistemas(true);
          setShowModalDeteccao(true);
        }
      } else {
        // Erro na detecção, permite seleção manual
        setShowListaSistemas(true);
        setShowModalDeteccao(true);
      }
    } catch (err) {
      console.error('Erro ao detectar sistema:', err);
      setShowListaSistemas(true);
      setShowModalDeteccao(true);
    } finally {
      setDetectando(false);
    }
  };

  const confirmarSistemaDetectado = () => {
    if (sistemaDetectado) {
      setSistemaContabilSelecionado(sistemaDetectado.codigo);
      if (lembrarEscolha) {
        salvarPreferencia(sistemaDetectado.codigo);
        toast.success('Preferência salva! Não perguntaremos novamente.');
      }
    }
    setShowModalDeteccao(false);
    setShowListaSistemas(false);
  };

  const selecionarOutroSistema = (sistema) => {
    console.log('[SISTEMA] Selecionando sistema:', sistema);
    console.log('[SISTEMA] ID:', sistema.id);
    setSistemaContabilSelecionado(sistema.id);
    if (lembrarEscolha) {
      salvarPreferencia(sistema.id);
      toast.success('Preferência salva! Não perguntaremos novamente.');
    }
    setShowModalDeteccao(false);
    setShowListaSistemas(false);
  };

  const removerArquivo = (index) => {
    setArquivos(prev => prev.filter((_, i) => i !== index));
  };

  const processarArquivos = async () => {
    if (arquivos.length === 0) {
      setErro('Selecione pelo menos um arquivo');
      return;
    }

    if (sistemaContabilSelecionado === null) {
      setErro('Selecione o sistema contábil primeiro');
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
    
    // Verificar se sistema tem parser local
    const usarParserLocal = sistemaSelecionado?.tem_parser;
    
    console.log('[IMPORT] ========== DEBUG ==========');
    console.log('[IMPORT] sistemaContabilSelecionado:', sistemaContabilSelecionado);
    console.log('[IMPORT] sistemaSelecionado:', sistemaSelecionado);
    console.log('[IMPORT] usarParserLocal:', usarParserLocal);
    console.log('[IMPORT] Condição Domínio:', usarParserLocal && sistemaContabilSelecionado === 1);
    console.log('[IMPORT] ==============================');

    for (let i = 0; i < arquivos.length; i++) {
      const file = arquivos[i];
      setProgresso(Math.round((i / arquivos.length) * 100));

      try {
        const formData = new FormData();
        formData.append('file', file);

        // Escolher endpoint baseado no sistema
        let endpoint = '/api/importacao/ia/preview-lote';
        
        // Só usa parser Domínio se:
        // 1. Sistema tem parser local (tem_parser = true)
        // 2. Sistema selecionado é EXATAMENTE o Domínio (id = 1)
        // 3. Sistema selecionado NÃO é "Outro / Não sei" (id = 0)
        const ehDominio = sistemaContabilSelecionado === 1;
        const ehOutro = sistemaContabilSelecionado === 0;
        
        console.log('[IMPORT] Verificando endpoint:');
        console.log('[IMPORT]   - sistemaContabilSelecionado:', sistemaContabilSelecionado);
        console.log('[IMPORT]   - ehDominio:', ehDominio);
        console.log('[IMPORT]   - ehOutro:', ehOutro);
        console.log('[IMPORT]   - usarParserLocal:', usarParserLocal);
        
        if (usarParserLocal && ehDominio && !ehOutro) {
          // Sistema Domínio confirmado
          endpoint = '/api/importacao/dominio/preview';
          console.log('[IMPORT] >>> Usando PARSER DOMÍNIO');
        } else {
          console.log('[IMPORT] >>> Usando IA');
        }
        
        console.log(`[IMPORT] Endpoint final: ${endpoint} para ${file.name}`);
        
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: formData
        });

        const dados = await res.json();

        if (dados.sucesso) {
          const balancete = dados.balancete || dados;
          const empresa = balancete?.empresa || dados.empresa;
          const dadosExtraidos = balancete?.dados || dados.dados || {};
          
          // Capturar info da empresa
          if (!empresaInfo && empresa) {
            empresaInfo = empresa;
            cnpjEncontrado = empresa.cnpj;
          }

          // Extrai competência do período
          let competencia = 'N/A';
          if (balancete?.periodo?.fim) {
            competencia = balancete.periodo.fim.substring(0, 7);
          } else if (dadosExtraidos.ano && dadosExtraidos.mes) {
            competencia = `${dadosExtraidos.ano}-${String(dadosExtraidos.mes).padStart(2, '0')}`;
          }

          console.log('[PREVIEW] Arquivo:', file.name);
          console.log('[PREVIEW] Dados extraídos:', dadosExtraidos);
          console.log('[PREVIEW] Competência:', competencia);

          resultados.push({
            nome: file.name,
            sucesso: true,
            competencia: competencia,
            dados: balancete  // Guarda o balancete completo incluindo dados
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
        // Limpar CNPJ (remover formatação) para evitar problemas na URL
        const cnpjLimpo = cnpjEncontrado.replace(/[^\d]/g, '');
        console.log('[IMPORT] Verificando empresa existente - CNPJ:', cnpjEncontrado, '-> limpo:', cnpjLimpo);
        
        // Usar endpoint alternativo que não conflita com /empresas/{id}
        const resEmp = await api(`/api/buscar-empresa/${cnpjLimpo}`);
        const resultado = await resEmp.json();
        
        console.log('[IMPORT] Resposta da busca:', resultado);
        
        if (resultado.encontrada && resultado.empresa) {
          console.log('[IMPORT] ✓ Empresa encontrada:', resultado.empresa.razao_social);
          setEmpresaExistente(resultado.empresa);
        } else {
          console.log('[IMPORT] ✗ Empresa não encontrada, será criada nova');
          setEmpresaExistente(null);
        }
      } catch (err) {
        console.log('[IMPORT] Erro ao buscar empresa:', err);
        setEmpresaExistente(null);
      }
    } else {
      console.log('[IMPORT] CNPJ não encontrado nos arquivos');
      setEmpresaExistente(null);
    }

    // Consolidar dados
    const sucessos = resultados.filter(r => r.sucesso);
    if (sucessos.length > 0) {
      // Dados vêm de r.dados.dados (estrutura do endpoint preview-lote)
      const getTotalReceita = (r) => {
        const d = r.dados?.dados || r.dados?.totais || {};
        return d.receita_bruta || d.receita_servicos || d.receita || 0;
      };
      const getTotalLucro = (r) => {
        const d = r.dados?.dados || r.dados?.totais || {};
        return d.lucro_liquido || 0;
      };

      // IMPORTANTE: Balancetes brasileiros têm DRE ACUMULADA no exercício
      // Não devemos SOMAR os meses - o último mês já contém o total!
      // 
      // Exemplo:
      // - Janeiro: Receita = 50.000 (só janeiro)
      // - Fevereiro: Receita = 120.000 (jan + fev)
      // - Março: Receita = 190.000 (jan + fev + mar)
      // 
      // ERRADO: 50.000 + 120.000 + 190.000 = 360.000
      // CERTO: usar 190.000 (valor do último mês = total acumulado)

      // Ordena por competência para pegar o último
      const ordenados = [...sucessos].sort((a, b) => {
        const compA = a.competencia || '0000-00';
        const compB = b.competencia || '0000-00';
        return compA.localeCompare(compB);
      });
      
      const ultimo = ordenados[ordenados.length - 1];
      const ultimaReceita = getTotalReceita(ultimo);
      const ultimoLucro = getTotalLucro(ultimo);
      
      console.log('[CONSOLIDAÇÃO] Usando valores do ÚLTIMO mês (acumulado)');
      console.log('[CONSOLIDAÇÃO] Último período:', ultimo.competencia);
      console.log('[CONSOLIDAÇÃO] Receita acumulada:', ultimaReceita);
      console.log('[CONSOLIDAÇÃO] Lucro acumulado:', ultimoLucro);
      
      // Se tiver só 1 mês, usa ele diretamente
      // Se tiver múltiplos meses, usa o último (que é o acumulado do exercício)
      setDadosConsolidados({
        empresa: empresaInfo,
        arquivos: sucessos,
        totalReceita: ultimaReceita,
        totalLucro: ultimoLucro,
        competencias: sucessos.map(r => r.competencia).sort(),
        valoresAcumulados: true,  // Flag para indicar que são valores acumulados
        ultimoPeriodo: ultimo.competencia
      });
    }

    setLoading(false);
    setEtapa('preview');
  };

  const confirmarImportacao = async (cnpjOverride = null) => {
    console.log('[IMPORT] Iniciando confirmarImportacao, cnpjOverride:', cnpjOverride);
    console.log('[IMPORT] empresaExistente:', empresaExistente);
    console.log('[IMPORT] dadosConsolidados?.empresa:', dadosConsolidados?.empresa);
    
    setLoading(true);
    setErro('');

    try {
      let empresaId = empresaExistente?.id;

      // Se já tem empresa existente, pular criação
      if (empresaId) {
        console.log('[IMPORT] Usando empresa existente ID:', empresaId);
      } else {
        // Precisa criar empresa nova
        const emp = dadosConsolidados?.empresa;
        
        if (!emp) {
          // Não tem dados da empresa - criar com dados mínimos
          console.log('[IMPORT] Sem dados de empresa, verificando CNPJ manual');
        }
        
        // Determinar CNPJ final
        const cnpjDoDocumento = emp?.cnpj || '';
        const cnpjFinal = cnpjOverride || cnpjDoDocumento;
        
        console.log('[IMPORT] CNPJ do documento:', cnpjDoDocumento);
        console.log('[IMPORT] CNPJ final:', cnpjFinal);
        
        // Se não tem CNPJ, abrir modal para usuário digitar
        if (!cnpjFinal || cnpjFinal.trim() === '') {
          console.log('[IMPORT] CNPJ não encontrado, abrindo modal');
          setLoading(false);
          setShowModalCnpj(true);
          return;
        }
        
        // Determinar nome da empresa
        const nomeEmpresa = emp?.razao_social || emp?.nome || `Empresa ${cnpjFinal}`;
        
        console.log('[IMPORT] Criando empresa:', nomeEmpresa, cnpjFinal);
        
        const res = await api('/empresas', {
          method: 'POST',
          body: JSON.stringify({
            razao_social: nomeEmpresa,
            cnpj: cnpjFinal,
            regime_tributario: 'Lucro Presumido',
            sistema_contabil: sistemaContabilSelecionado
          })
        });

        if (!res.ok) {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Erro ao criar empresa');
        }
        
        const data = await res.json();
        empresaId = data.id;
        toast.success(`Empresa "${nomeEmpresa}" criada!`);
      }

      // Salvar cada período com TODOS os campos do balancete
      for (const arq of arquivosProcessados.filter(a => a.sucesso)) {
        // Dados vêm de arq.dados.dados (estrutura do endpoint preview-lote)
        const dadosIA = arq.dados?.dados || arq.dados?.totais || arq.dados || {};
        const periodo = arq.dados?.periodo || {};

        console.log('[IMPORT] Salvando arquivo:', arq.nome);
        console.log('[IMPORT] Dados IA:', dadosIA);

        // Extrai ano e mês do período
        let competencia = periodo.fim?.substring(0, 7) || arq.competencia;
        if (!competencia || competencia === 'N/A') {
          // Tenta extrair do nome do arquivo ou dos dados
          const ano = dadosIA.ano || new Date().getFullYear();
          const mes = dadosIA.mes || 1;
          competencia = `${ano}-${String(mes).padStart(2, '0')}`;
        }

        // Enviar todos os campos expandidos
        const dadosMensais = {
          competencia: competencia,
          // Campos básicos (compatibilidade)
          receita_bruta: dadosIA.receita_bruta || dadosIA.receita_servicos || 0,
          receita: dadosIA.receita || dadosIA.receita_bruta || dadosIA.receita_servicos || 0,
          custos: dadosIA.custos || dadosIA.custos_total || 0,
          despesas: dadosIA.despesas || dadosIA.despesas_operacionais || 0,
          impostos: dadosIA.impostos || dadosIA.impostos_sobre_vendas || dadosIA.impostos_total || dadosIA.deducoes_receita || 0,
          folha: dadosIA.folha || 0,
          caixa: dadosIA.caixa || dadosIA.disponivel || 0,
          lucro_liquido: dadosIA.lucro_liquido || 0,
          // Balanço Patrimonial
          ativo_total: dadosIA.ativo_total || 0,
          ativo_circulante: dadosIA.ativo_circulante || 0,
          disponivel: dadosIA.disponivel || 0,
          bancos: dadosIA.bancos || 0,
          clientes: dadosIA.clientes || 0,
          estoques: dadosIA.estoques || 0,
          passivo_total: dadosIA.passivo_total || 0,
          passivo_circulante: dadosIA.passivo_circulante || 0,
          passivo_nao_circulante: dadosIA.passivo_nao_circulante || 0,
          patrimonio_liquido: dadosIA.patrimonio_liquido || 0,
          capital_social: dadosIA.capital_social || 0,
          fornecedores: dadosIA.fornecedores || 0,
          // DRE
          receita_servicos: dadosIA.receita_servicos || 0,
          deducoes_receita: dadosIA.deducoes_receita || 0,
          custos_total: dadosIA.custos_total || dadosIA.custos || 0,
          despesas_operacionais: dadosIA.despesas_operacionais || 0,
          despesas_financeiras: dadosIA.despesas_financeiras || 0,
          receitas_financeiras: dadosIA.receitas_financeiras || 0,
          // Impostos detalhados
          iss: dadosIA.iss || 0,
          pis: dadosIA.pis || dadosIA.pis_deducao || 0,
          cofins: dadosIA.cofins || dadosIA.cofins_deducao || 0,
          irpj: dadosIA.irpj || dadosIA.irpj_deducao || 0,
          csll: dadosIA.csll || dadosIA.csll_deducao || 0,
          icms: dadosIA.icms || dadosIA.icms_deducao || 0,  // ADICIONADO: ICMS é o maior imposto
          // CORRIGIDO: Usar mesma fonte que 'impostos' para consistência
          impostos_total: dadosIA.impostos || dadosIA.impostos_sobre_vendas || dadosIA.impostos_total || dadosIA.deducoes_receita || 0,
          // Meta
          arquivo_origem: arq.nome
        };

        console.log('[IMPORT] Enviando para API:', dadosMensais);

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
    // Reset do modal de CNPJ
    setShowModalCnpj(false);
    setCnpjManual('');
    setErroCnpj('');
    // Reset da revisão
    setArquivoSelecionado(null);
    setDadosRevisao(null);
  };

  const formatarMoeda = (valor) => {
    if (!valor && valor !== 0) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  };

  // === FUNÇÕES DE REVISÃO ===
  
  // Abre a tela de revisão para um arquivo específico
  const abrirRevisao = (arquivo, index) => {
    console.log('[REVISAO] Abrindo revisão para:', arquivo.nome);
    
    // Montar dados para o componente de revisão
    const dados = arquivo.dados?.dados || arquivo.dados || {};
    
    // Criar validação simulada (normalmente viria do backend)
    const validacao = {
      confianca: arquivo.dados?.confianca > 80 ? 'alta' : arquivo.dados?.confianca > 60 ? 'media' : 'baixa',
      confianca_percentual: arquivo.dados?.confianca || 75,
      metodo_extracao: arquivo.dados?.metodo_usado || 'parser_dominio',
      resumo: '✅ Dados extraídos com sucesso. Revise os valores antes de confirmar.',
      alertas: [],
      dados_validados: dados,
      campos_editaveis: [
        // DRE
        { nome: 'receita_bruta', label: 'Receita Bruta', grupo: 'DRE', obrigatorio: true, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'receita_servicos', label: 'Receita de Serviços', grupo: 'DRE', obrigatorio: false, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'deducoes_receita', label: 'Deduções da Receita', grupo: 'DRE', obrigatorio: false, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'custos', label: 'Custos', grupo: 'DRE', obrigatorio: false, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'despesas_operacionais', label: 'Despesas Operacionais', grupo: 'DRE', obrigatorio: false, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'lucro_liquido', label: 'Lucro Líquido', grupo: 'DRE', obrigatorio: true, tem_erro: false, tem_aviso: false, alertas: [] },
        // Ativo
        { nome: 'ativo_total', label: 'Ativo Total', grupo: 'Ativo', obrigatorio: true, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'ativo_circulante', label: 'Ativo Circulante', grupo: 'Ativo', obrigatorio: true, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'disponivel', label: 'Disponível', grupo: 'Ativo', obrigatorio: false, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'clientes', label: 'Clientes', grupo: 'Ativo', obrigatorio: false, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'estoques', label: 'Estoques', grupo: 'Ativo', obrigatorio: false, tem_erro: false, tem_aviso: false, alertas: [] },
        // Passivo
        { nome: 'passivo_circulante', label: 'Passivo Circulante', grupo: 'Passivo', obrigatorio: true, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'passivo_nao_circulante', label: 'Passivo Não Circulante', grupo: 'Passivo', obrigatorio: false, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'fornecedores', label: 'Fornecedores', grupo: 'Passivo', obrigatorio: false, tem_erro: false, tem_aviso: false, alertas: [] },
        // PL
        { nome: 'patrimonio_liquido', label: 'Patrimônio Líquido', grupo: 'PL', obrigatorio: true, tem_erro: false, tem_aviso: false, alertas: [] },
        { nome: 'capital_social', label: 'Capital Social', grupo: 'PL', obrigatorio: false, tem_erro: false, tem_aviso: false, alertas: [] },
        // Impostos
        { nome: 'impostos', label: 'Total Impostos', grupo: 'Impostos', obrigatorio: false, tem_erro: false, tem_aviso: false, alertas: [] },
      ]
    };
    
    // Adicionar alertas baseados nos valores
    const receita = parseFloat(dados.receita_bruta) || 0;
    const lucro = parseFloat(dados.lucro_liquido) || 0;
    const pl = parseFloat(dados.patrimonio_liquido) || 0;
    
    if (lucro > receita && receita > 0) {
      validacao.alertas.push({
        tipo: 'erro',
        campo: 'lucro_liquido',
        mensagem: 'Lucro maior que receita',
        detalhes: 'Verifique se os valores estão corretos'
      });
      validacao.campos_editaveis.find(c => c.nome === 'lucro_liquido').tem_erro = true;
    }
    
    if (pl > 0 && lucro > 0) {
      const roe = (lucro / pl) * 100;
      if (roe > 200) {
        validacao.alertas.push({
          tipo: 'aviso',
          campo: 'roe',
          mensagem: `ROE muito elevado (${roe.toFixed(1)}%)`,
          detalhes: 'Verifique se o Patrimônio Líquido está correto'
        });
      }
    }
    
    // Adicionar alerta de sucesso se tudo OK
    if (validacao.alertas.length === 0) {
      validacao.alertas.push({
        tipo: 'sucesso',
        campo: 'geral',
        mensagem: 'Todos os valores parecem consistentes'
      });
    }
    
    setArquivoSelecionado({ ...arquivo, index });
    setDadosRevisao(validacao);
    setEtapa('revisao');
  };
  
  // Confirma os dados revisados de um arquivo
  const confirmarRevisao = (dadosEditados) => {
    console.log('[REVISAO] Confirmando dados editados:', dadosEditados);
    
    // Atualizar o arquivo nos processados
    const novosProcessados = [...arquivosProcessados];
    const index = arquivoSelecionado.index;
    
    // Mesclar dados editados
    novosProcessados[index] = {
      ...novosProcessados[index],
      dados: {
        ...novosProcessados[index].dados,
        dados: dadosEditados
      },
      revisado: true // Marcar como revisado
    };
    
    setArquivosProcessados(novosProcessados);
    
    // Atualizar consolidado se necessário
    const ultimoPeriodo = novosProcessados.filter(a => a.sucesso).sort((a, b) => 
      (a.competencia || '').localeCompare(b.competencia || '')
    ).pop();
    
    if (ultimoPeriodo) {
      const dadosUltimo = ultimoPeriodo.dados?.dados || {};
      setDadosConsolidados(prev => ({
        ...prev,
        totalReceita: dadosUltimo.receita_bruta || dadosUltimo.receita || prev?.totalReceita || 0,
        totalLucro: dadosUltimo.lucro_liquido || prev?.totalLucro || 0
      }));
    }
    
    toast.success(`Dados de ${arquivoSelecionado.nome} atualizados!`);
    
    // Voltar para preview
    setArquivoSelecionado(null);
    setDadosRevisao(null);
    setEtapa('preview');
  };
  
  // Cancela a revisão e volta para preview
  const cancelarRevisao = () => {
    setArquivoSelecionado(null);
    setDadosRevisao(null);
    setEtapa('preview');
  };

  // ============ ETAPA 1: UPLOAD MÚLTIPLO ============
  if (etapa === 'upload') {
    return (
      <div>
        <Header 
          title="Importação de Balancetes" 
          subtitle="Importe os balancetes mensais da empresa para análise financeira"
        />

        <Card className="p-6 mb-4">
          {/* Aviso sobre balancetes */}
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-3">
              <FileSpreadsheet className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-blue-800 mb-1">Importe Balancetes Mensais</h4>
                <p className="text-sm text-blue-700">
                  Aceitamos balancetes em PDF ou Excel dos principais sistemas contábeis 
                  (Domínio, Questor, Prosoft, etc.). Cada arquivo deve corresponder a um mês.
                  Para melhores análises, importe pelo menos 3 meses de dados.
                </p>
              </div>
            </div>
          </div>

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
              Arraste seus balancetes aqui
            </h3>
            <p className="text-slate-500 mb-4 text-sm">
              Selecione múltiplos arquivos de uma vez (um por mês)
            </p>
            <input
              type="file"
              accept=".pdf"
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
              PDF • Cada arquivo = 1 mês de dados
            </p>
          </div>
        </Card>

        {/* Sistema Contábil Detectado/Selecionado */}
        <Card className="p-4 mb-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Sistema Contábil
              </label>
              {detectando ? (
                <div className="flex items-center gap-2 text-slate-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Detectando sistema...</span>
                </div>
              ) : sistemaSelecionado ? (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-slate-900">{sistemaSelecionado.nome}</span>
                  {sistemaSelecionado.fabricante && (
                    <span className="text-sm text-slate-500">({sistemaSelecionado.fabricante})</span>
                  )}
                  {sistemaSelecionado.tem_parser ? (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                      Importação rápida
                    </span>
                  ) : (
                    <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded">
                      Via IA
                    </span>
                  )}
                  {getSistemaPreferido() && (
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                      Preferência salva
                    </span>
                  )}
                </div>
              ) : (
                <span className="text-slate-500">Adicione um arquivo para detectar automaticamente</span>
              )}
            </div>
            {sistemaContabilSelecionado !== null && (
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => {
                    // Se tinha preferência, limpa primeiro
                    if (getSistemaPreferido()) {
                      limparPreferencia();
                    }
                    setSistemaContabilSelecionado(null);
                    setShowListaSistemas(true);
                    setShowModalDeteccao(true);
                  }}
                >
                  Trocar Sistema
                </Button>
              </div>
            )}
          </div>
          {sistemaSelecionado && (
            <p className="mt-2 text-sm">
              {sistemaSelecionado.tem_parser ? (
                <span className="text-green-600">
                  ✓ Importação automática disponível - grátis e instantânea!
                </span>
              ) : (
                <span className="text-amber-600">
                  ○ Será usada IA para extrair os dados (pode demorar um pouco)
                </span>
              )}
            </p>
          )}
          {getSistemaPreferido() && (
            <p className="mt-2 text-xs text-blue-600">
              Sistema salvo como preferência. Clique em "Trocar Sistema" para selecionar outro.
            </p>
          )}
        </Card>

        {/* Modal de Detecção de Sistema */}
        {showModalDeteccao && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
              {!showListaSistemas && sistemaDetectado ? (
                <>
                  <div className="text-center mb-6">
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <FileSpreadsheet className="w-8 h-8 text-blue-600" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-800 mb-2">
                      Sistema Detectado
                    </h3>
                    <p className="text-slate-600">
                      Identificamos que seu arquivo é do sistema:
                    </p>
                    <div className="mt-3 p-4 bg-blue-50 rounded-lg">
                      <span className="font-bold text-blue-800 text-lg">
                        {sistemaDetectado.nome}
                      </span>
                      {sistemaDetectado.fabricante && (
                        <p className="text-sm text-blue-600">{sistemaDetectado.fabricante}</p>
                      )}
                      <div className="flex items-center justify-center gap-2 mt-2">
                        {sistemaDetectado.tem_parser ? (
                          <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" />
                            Importação rápida disponível
                          </span>
                        ) : (
                          <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded">
                            Usaremos IA para processar
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-blue-500 mt-2">
                        Confiança: {confiancaDeteccao}%
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mb-6 p-3 bg-slate-50 rounded-lg">
                    <input
                      type="checkbox"
                      id="lembrar"
                      checked={lembrarEscolha}
                      onChange={(e) => setLembrarEscolha(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded border-slate-300"
                    />
                    <label htmlFor="lembrar" className="text-sm text-slate-700">
                      Lembrar minha escolha (não perguntar novamente)
                    </label>
                  </div>

                  <div className="flex gap-3">
                    <Button
                      className="flex-1"
                      onClick={confirmarSistemaDetectado}
                    >
                      <Check className="w-4 h-4 mr-2" />
                      Sim, está correto
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => setShowListaSistemas(true)}
                    >
                      Não, é outro
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <div className="mb-4">
                    <h3 className="text-xl font-bold text-slate-800 mb-2">
                      Selecione o Sistema Contábil
                    </h3>
                    <p className="text-slate-600 text-sm">
                      Qual sistema gerou os arquivos que você está importando?
                    </p>
                  </div>

                  <div className="mb-4">
                    <div className="relative">
                      <input
                        type="text"
                        value={buscaSistema}
                        onChange={(e) => setBuscaSistema(e.target.value)}
                        placeholder="Buscar sistema..."
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-10"
                      />
                      <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    </div>
                  </div>

                  <div className="max-h-60 overflow-y-auto border border-slate-200 rounded-lg mb-4">
                    {sistemasFiltrados.map(sistema => (
                      <div
                        key={sistema.id}
                        onClick={() => selecionarOutroSistema(sistema)}
                        className="px-3 py-3 cursor-pointer hover:bg-blue-50 border-b border-slate-100 last:border-0 flex items-center justify-between"
                      >
                        <div>
                          <div className="font-medium text-slate-900">{sistema.nome}</div>
                          {sistema.fabricante && (
                            <div className="text-xs text-slate-500">{sistema.fabricante}</div>
                          )}
                        </div>
                        {sistema.tem_parser ? (
                          <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" />
                            Rápido
                          </span>
                        ) : sistema.id !== 0 && (
                          <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded">
                            Via IA
                          </span>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center gap-2 mb-4 p-3 bg-slate-50 rounded-lg">
                    <input
                      type="checkbox"
                      id="lembrar2"
                      checked={lembrarEscolha}
                      onChange={(e) => setLembrarEscolha(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded border-slate-300"
                    />
                    <label htmlFor="lembrar2" className="text-sm text-slate-700">
                      Lembrar minha escolha
                    </label>
                  </div>

                  <div className="flex gap-2">
                    {sistemaDetectado && (
                      <Button
                        variant="outline"
                        onClick={() => setShowListaSistemas(false)}
                      >
                        <ArrowLeft className="w-4 h-4 mr-1" />
                        Voltar
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => {
                        setShowModalDeteccao(false);
                        setShowListaSistemas(false);
                      }}
                    >
                      Cancelar
                    </Button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

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

  // ============ ETAPA REVISÃO: Edição Individual de Arquivo ============
  if (etapa === 'revisao' && arquivoSelecionado && dadosRevisao) {
    return (
      <div>
        <Header 
          title="Revisar Dados do Arquivo" 
          subtitle={arquivoSelecionado.nome}
          actions={
            <Button variant="ghost" onClick={cancelarRevisao}>
              <ArrowLeft className="w-4 h-4" /> Voltar
            </Button>
          }
        />
        
        <div className="mt-4">
          <RevisaoImportacao
            dadosValidacao={dadosRevisao}
            empresa={dadosConsolidados?.empresa?.nome || dadosConsolidados?.empresa?.razao_social}
            periodo={arquivoSelecionado.competencia}
            onConfirmar={confirmarRevisao}
            onCancelar={cancelarRevisao}
            carregando={carregandoRevisao}
          />
        </div>
      </div>
    );
  }

  // ============ ETAPA 3: PREVIEW ============
  if (etapa === 'preview') {
    const sucessos = arquivosProcessados.filter(a => a.sucesso);
    const erros = arquivosProcessados.filter(a => !a.sucesso);
    const empresaRaw = dadosConsolidados?.empresa || {};
    // Normalizar: alguns endpoints retornam razao_social, outros nome
    const empresa = {
      ...empresaRaw,
      nome: empresaRaw.razao_social || empresaRaw.nome || '-'
    };
    
    // Pegar último período para indicadores
    const ultimoPeriodo = sucessos.length > 0 ? sucessos[sucessos.length - 1].dados : null;
    // Dados vêm de ultimoPeriodo.dados (estrutura do endpoint preview-lote)
    const dadosUltimo = ultimoPeriodo?.dados || ultimoPeriodo?.totais || {};
    
    // Calcular indicadores a partir dos dados
    const receita = dadosUltimo.receita_bruta || dadosUltimo.receita || 0;
    const lucro = dadosUltimo.lucro_liquido || 0;
    const ativoCirc = dadosUltimo.ativo_circulante || 0;
    const passivoCirc = dadosUltimo.passivo_circulante || 1;
    const patrimonio = dadosUltimo.patrimonio_liquido || 1;
    // Usar impostos em ordem de prioridade: impostos > impostos_sobre_vendas > deducoes_receita
    const impostos = dadosUltimo.impostos || dadosUltimo.impostos_sobre_vendas || dadosUltimo.deducoes_receita || 0;
    
    console.log('[INDICADORES] Dados para cálculo:', {
      receita, lucro, impostos,
      fonteImpostos: dadosUltimo.impostos ? 'impostos' : (dadosUltimo.impostos_sobre_vendas ? 'impostos_sobre_vendas' : 'deducoes_receita')
    });
    
    const indicadores = {
      margem_liquida: receita > 0 ? ((lucro / receita) * 100).toFixed(1) : 0,
      liquidez_corrente: passivoCirc > 0 ? (ativoCirc / passivoCirc).toFixed(2) : 0,
      roe: patrimonio > 0 ? ((lucro / patrimonio) * 100).toFixed(1) : 0,
      carga_tributaria: receita > 0 ? ((impostos / receita) * 100).toFixed(1) : 0
    };

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
                  {(!empresa.cnpj || empresa.cnpj === '-') && (
                    <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      CNPJ não encontrado no documento - será solicitado ao confirmar
                    </p>
                  )}
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
              {empresa.cnpj && empresa.cnpj !== '-' ? (
                <p className="text-slate-500">{empresa.cnpj_formatado || empresa.cnpj}</p>
              ) : (
                <p className="text-amber-600 text-xs flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  CNPJ não informado
                </p>
              )}
              {empresa.contador?.nome && (
                <p className="text-slate-500 text-xs">Contador: {empresa.contador.nome}</p>
              )}
            </div>
          </Card>

          {/* Resumo Financeiro */}
          <Card className="p-4">
            <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              Acumulado do Exercício
              {dadosConsolidados?.ultimoPeriodo && (
                <span className="text-xs text-slate-500 font-normal">
                  (até {dadosConsolidados.ultimoPeriodo})
                </span>
              )}
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
                <span className="text-sm text-slate-500">Margem:</span>
                <span className="font-semibold">
                  {dadosConsolidados?.totalReceita > 0 
                    ? ((dadosConsolidados.totalLucro / dadosConsolidados.totalReceita) * 100).toFixed(1) 
                    : 0}%
                </span>
              </div>
            </div>
            {dadosConsolidados?.valoresAcumulados && (
              <p className="text-xs text-blue-600 mt-2 flex items-center gap-1">
                <Info className="w-3 h-3" />
                Valores acumulados no exercício
              </p>
            )}
          </Card>

          {/* Info sobre indicadores */}
          <Card className="p-4 bg-slate-50 border-slate-200">
            <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-slate-500" />
              Indicadores Financeiros
            </h3>
            <div className="text-center py-4">
              <p className="text-sm text-slate-600 mb-2">
                Os indicadores serão calculados após a revisão
              </p>
              <div className="flex flex-wrap justify-center gap-2 text-xs text-slate-500">
                <span className="px-2 py-1 bg-white rounded border">ROE</span>
                <span className="px-2 py-1 bg-white rounded border">Margem</span>
                <span className="px-2 py-1 bg-white rounded border">Liquidez</span>
                <span className="px-2 py-1 bg-white rounded border">Carga Tributária</span>
              </div>
              <p className="text-xs text-slate-400 mt-3">
                Revise os dados de cada arquivo para garantir precisão
              </p>
            </div>
          </Card>
        </div>

        {/* Aviso sobre revisão */}
        {sucessos.some(arq => {
          const metodo = arq.dados?.metodo_usado || arq.dados?.metodo || '';
          return metodo.toLowerCase().includes('ia') || metodo.toLowerCase().includes('claude');
        }) ? (
          <div className="mb-4 p-4 bg-amber-50 border-l-4 border-amber-400 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-amber-800">Alguns arquivos foram processados por IA</h4>
                <p className="text-sm text-amber-700 mt-1">
                  A IA pode cometer erros na extração. <strong>É obrigatório revisar cada arquivo</strong> comparando com o documento original antes de confirmar.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="mb-4 p-4 bg-blue-50 border-l-4 border-blue-400 rounded-lg">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-blue-800">Dados extraídos por Parser Local</h4>
                <p className="text-sm text-blue-700 mt-1">
                  Os dados foram extraídos automaticamente do sistema Domínio. Recomendamos uma revisão rápida para garantir que os valores estão corretos.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Lista de arquivos processados */}
        <Card className="p-4 mb-4">
          <h3 className="font-semibold text-slate-800 mb-3 flex items-center justify-between">
            <span>Arquivos Processados</span>
            <span className="text-xs font-normal text-slate-500">
              Clique em "Revisar" para verificar/editar os valores
            </span>
          </h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {arquivosProcessados.map((arq, i) => {
              const metodo = arq.dados?.metodo_usado || arq.dados?.metodo || '';
              const isIA = metodo.toLowerCase().includes('ia') || metodo.toLowerCase().includes('claude');
              return (
              <div 
                key={i} 
                className={`flex items-center justify-between p-3 rounded-lg border-2 transition-all ${
                  arq.sucesso 
                    ? arq.revisado 
                      ? 'bg-blue-50 border-blue-200' 
                      : isIA 
                        ? 'bg-amber-50 border-amber-200 hover:border-amber-400'
                        : 'bg-green-50 border-green-200 hover:border-blue-400' 
                    : 'bg-red-50 border-red-200'
                }`}
              >
                <div className="flex items-center gap-3">
                  {arq.sucesso ? (
                    arq.revisado ? (
                      <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                        <CheckCircle className="w-3 h-3 text-white" />
                      </div>
                    ) : isIA ? (
                      <div className="w-5 h-5 bg-amber-500 rounded-full flex items-center justify-center">
                        <AlertTriangle className="w-3 h-3 text-white" />
                      </div>
                    ) : (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    )
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                  )}
                  <div>
                    <p className="font-medium text-slate-800 flex items-center gap-2">
                      {arq.nome}
                      {arq.revisado && (
                        <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full">
                          ✓ Revisado
                        </span>
                      )}
                      {isIA && !arq.revisado && (
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full border border-purple-300">
                          🤖 IA
                        </span>
                      )}
                    </p>
                    <p className={`text-xs ${arq.sucesso ? (isIA && !arq.revisado ? 'text-amber-600' : 'text-green-600') : 'text-red-600'}`}>
                      {arq.sucesso 
                        ? `Competência: ${arq.competencia}${isIA && !arq.revisado ? ' • Revisão obrigatória' : ''}` 
                        : arq.erro}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {arq.sucesso && (arq.dados?.dados?.receita_bruta || arq.dados?.dados?.receita) && (
                    <span className="text-sm font-medium text-green-700">
                      {formatarMoeda(arq.dados.dados.receita_bruta || arq.dados.dados.receita)}
                    </span>
                  )}
                  {arq.sucesso && (
                    <button
                      onClick={() => abrirRevisao(arq, i)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1 ${
                        isIA && !arq.revisado
                          ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                          : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                      }`}
                    >
                      <Eye className="w-3 h-3" />
                      {arq.revisado ? 'Editar' : isIA ? '⚠️ Revisar' : 'Revisar'}
                    </button>
                  )}
                </div>
              </div>
            )})}
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
            <Button onClick={() => confirmarImportacao(null)} loading={loading}>
              <CheckCircle className="w-4 h-4" />
              {empresaExistente ? `Adicionar ${sucessos.length} meses` : `Criar Empresa e Importar`}
            </Button>
          )}
        </div>

        {/* Modal de CNPJ não encontrado */}
        {showModalCnpj && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <AlertTriangle className="w-8 h-8 text-amber-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-800 mb-2">
                  CNPJ não encontrado
                </h3>
                <p className="text-slate-600">
                  Não foi possível identificar o CNPJ da empresa no documento. 
                  Por favor, informe o CNPJ manualmente para continuar.
                </p>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  CNPJ da Empresa
                </label>
                <input
                  type="text"
                  value={cnpjManual}
                  onChange={(e) => {
                    // Formatar CNPJ automaticamente
                    let valor = e.target.value.replace(/\D/g, '');
                    if (valor.length > 14) valor = valor.slice(0, 14);
                    if (valor.length > 12) {
                      valor = valor.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2}).*/, '$1.$2.$3/$4-$5');
                    } else if (valor.length > 8) {
                      valor = valor.replace(/^(\d{2})(\d{3})(\d{3})(\d*).*/, '$1.$2.$3/$4');
                    } else if (valor.length > 5) {
                      valor = valor.replace(/^(\d{2})(\d{3})(\d*).*/, '$1.$2.$3');
                    } else if (valor.length > 2) {
                      valor = valor.replace(/^(\d{2})(\d*).*/, '$1.$2');
                    }
                    setCnpjManual(valor);
                    setErroCnpj('');
                  }}
                  placeholder="00.000.000/0000-00"
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg text-center tracking-wider"
                />
                {erroCnpj && (
                  <p className="text-red-500 text-sm mt-2">{erroCnpj}</p>
                )}
              </div>

              <div className="flex gap-3">
                <Button
                  className="flex-1"
                  onClick={() => {
                    // Validar CNPJ
                    const cnpjLimpo = cnpjManual.replace(/\D/g, '');
                    if (cnpjLimpo.length !== 14) {
                      setErroCnpj('CNPJ deve ter 14 dígitos');
                      return;
                    }
                    // Fechar modal e continuar importação com CNPJ manual
                    setShowModalCnpj(false);
                    setCnpjManual('');
                    setErroCnpj('');
                    // Continuar a importação passando o CNPJ
                    confirmarImportacao(cnpjLimpo);
                  }}
                  disabled={cnpjManual.replace(/\D/g, '').length !== 14}
                >
                  <Check className="w-4 h-4 mr-2" />
                  Confirmar e Continuar
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowModalCnpj(false);
                    setCnpjManual('');
                    setErroCnpj('');
                  }}
                >
                  Cancelar
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ============ ETAPA 4: SUCESSO ============
  if (etapa === 'sucesso') {
    const empresaRaw = dadosConsolidados?.empresa || {};
    const empresa = {
      ...empresaRaw,
      nome: empresaRaw.razao_social || empresaRaw.nome || '-'
    };
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
