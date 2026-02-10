import VisaoGeralTab from './components/VisaoGeralTab';
import DadosTab from './components/DadosTab';
import AnaliseDetail from './components/AnaliseDetail';
import HistoricoTab from './components/HistoricoTab';
import UploadModal from './components/UploadModal';
import RegistroModal from './components/RegistroModal';
import EditEmpresaModal from './components/EditEmpresaModal';
import React, { useState, useEffect } from 'react';
import { AlertTriangle, ArrowLeft, ChevronDown, Download, FileText, PieChart as PieChartIcon, Trash2, Upload, BarChart3 } from 'lucide-react';
import { BarChart } from 'recharts';
import { Button, Card, EmptyState, LoadingOverlay, LoadingScreen, Modal, ScoreCircle, StatusBadge } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import { useExport } from '../../contexts/ExportContext';

function EmpresaDetailPage({ empresaId, onNavigate }) {
  const { api } = useAuth();
  const toast = useToast();
  const { agendarExportacao } = useExport();
  const [empresa, setEmpresa] = useState(null);
  const [registros, setRegistros] = useState([]);
  const [showPdfMenu, setShowPdfMenu] = useState(false);
  const [analises, setAnalises] = useState([]);
  const [ultimaAnalise, setUltimaAnalise] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [showRegistro, setShowRegistro] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [tab, setTab] = useState('visao-geral');

  // Recarregar dados sempre que a página for acessada (não apenas quando empresaId muda)
  useEffect(() => { 
    loadData(); 
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
  
  // Callback quando importação é bem sucedida
  const handleImportSuccess = () => {
    loadData();
  };



  const exportarPDF = (comParecer = false) => {
    if (!ultimaAnalise) return;
    setShowPdfMenu(false);
    const tipo = comParecer ? 'pdf_parecer' : 'pdf';
    agendarExportacao(empresaId, tipo, empresa?.razao_social || 'Empresa');
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
      <Header 
        title={empresa.razao_social}
        subtitle={empresa.cnpj}
        actions={
          <div className="flex items-center gap-2 flex-wrap">
            <Button variant="ghost" size="sm" onClick={() => onNavigate('empresas')}><ArrowLeft className="w-4 h-4" /> <span className="hidden sm:inline">Voltar</span></Button>
            <Button variant="secondary" size="sm" onClick={() => setShowUpload(true)}><Upload className="w-4 h-4" /> <span className="hidden sm:inline">Importar</span><span className="sm:hidden">Importar</span></Button>
            <Button 
              variant="secondary" 
              size="sm"
              onClick={() => onNavigate('analise-financeira', { empresaId: empresaId, empresaNome: empresa.razao_social })}
              disabled={registros.length < 1}
            >
              <PieChartIcon className="w-4 h-4" /> <span className="hidden sm:inline">DRE & Índices</span><span className="sm:hidden">DRE</span>
            </Button>
          </div>
        }
      />
      
      {ultimaAnalise && (
        <Card className="p-4 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <ScoreCircle score={ultimaAnalise.score} size="lg" />
              <div>
                <StatusBadge status={ultimaAnalise.status} />
                <p className="text-sm text-slate-500 mt-1">Última análise: {new Date(ultimaAnalise.data_analise).toLocaleDateString('pt-BR')}</p>
              </div>
            </div>
            <div className="relative">
              <Button 
                variant="secondary" 
                size="sm" 
                onClick={() => setShowPdfMenu(!showPdfMenu)}
                className="flex items-center gap-1.5 w-full sm:w-auto justify-center"
              >
                <><Download className="w-4 h-4" /> Exportar PDF <ChevronDown className="w-3.5 h-3.5" /></>
              </Button>
              {showPdfMenu && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowPdfMenu(false)} />
                  <div className="absolute right-0 top-full mt-1 z-20 bg-white rounded-lg shadow-lg border border-slate-200 py-1 w-56">
                    <button
                      onClick={() => exportarPDF(false)}
                      className="w-full text-left px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 transition-colors"
                    >
                      <FileText className="w-4 h-4 text-slate-500" />
                      <div>
                        <p className="text-sm font-medium text-slate-700">Relatório Técnico</p>
                        <p className="text-xs text-slate-400">Indicadores e demonstrativos</p>
                      </div>
                    </button>
                    {registros.length >= 6 && (
                    <>
                    <div className="border-t border-slate-100 mx-2" />
                    <button
                      onClick={() => exportarPDF(true)}
                      className="w-full text-left px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 transition-colors"
                    >
                      <FileText className="w-4 h-4 text-emerald-500" />
                      <div>
                        <p className="text-sm font-medium text-slate-700">Parecer Consultivo</p>
                        <p className="text-xs text-slate-400">Análise detalhada com recomendações</p>
                      </div>
                    </button>
                    </>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </Card>
      )}
      
      <div className="border-b border-slate-200 mb-6 -mx-4 px-4 md:mx-0 md:px-0">
        <nav className="flex gap-4 overflow-x-auto scrollbar-hide">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${tab === t.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
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
          <EmptyState icon={BarChart3} title="Nenhuma análise disponível"
            description={registros.length < 3 ? "Importe pelo menos 3 meses de dados — a análise será gerada automaticamente" : "A análise será gerada automaticamente após a importação de dados"}
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
