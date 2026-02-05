import VisaoGeralTab from './components/VisaoGeralTab';
import DadosTab from './components/DadosTab';
import AnaliseDetail from './components/AnaliseDetail';
import HistoricoTab from './components/HistoricoTab';
import UploadModal from './components/UploadModal';
import RegistroModal from './components/RegistroModal';
import EditEmpresaModal from './components/EditEmpresaModal';
import React, { useState, useEffect } from 'react';
import { AlertTriangle, ArrowLeft, BarChart3, Download, PieChart as PieChartIcon, Trash2, Upload } from 'lucide-react';
import { BarChart } from 'recharts';
import { Button, Card, EmptyState, LoadingOverlay, LoadingScreen, Modal, ScoreCircle, StatusBadge } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

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
              <PieChartIcon className="w-4 h-4" /> DRE & Índices
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

export default EmpresaDetailPage;
