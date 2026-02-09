import React, { useState, useEffect, useRef } from 'react';
import { AlertTriangle, CheckCircle, FileText, Loader2, Upload, X, XCircle, Clock } from 'lucide-react';
import { Button, Modal } from '../../../components/ui';
import { useToast } from '../../../contexts/ToastContext';
import { API_URL } from '../../../config/api';

const STATUS_ICON = {
  pendente: { icon: Clock, color: 'text-slate-400', bg: 'bg-slate-50' },
  processando: { icon: Loader2, color: 'text-blue-500', bg: 'bg-blue-50', spin: true },
  concluido: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-50' },
  erro: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50' },
  conflito: { icon: AlertTriangle, color: 'text-amber-500', bg: 'bg-amber-50' },
};

function UploadModal({ isOpen, onClose, empresaId, onSuccess, registrosExistentes }) {
  const toast = useToast();
  const pollRef = useRef(null);
  
  // Steps: 'select' | 'single-processing' | 'single-preview' | 'single-conflict' | 'queue' | 'error'
  const [step, setStep] = useState('select');
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [substituir, setSubstituir] = useState(false);
  
  // Single file mode
  const [resultadoIA, setResultadoIA] = useState(null);
  const [singleFile, setSingleFile] = useState(null);
  
  // Queue mode
  const [loteId, setLoteId] = useState(null);
  const [loteStatus, setLoteStatus] = useState(null);

  // Reset on close
  useEffect(() => {
    if (!isOpen) {
      setStep('select');
      setFiles([]);
      setLoading(false);
      setError('');
      setResultadoIA(null);
      setSingleFile(null);
      setLoteId(null);
      setLoteStatus(null);
      setSubstituir(false);
      if (pollRef.current) clearInterval(pollRef.current);
    }
  }, [isOpen]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const getToken = () => localStorage.getItem('token');

  // Handle file selection
  const handleFileChange = async (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (!selectedFiles.length) return;
    
    setFiles(selectedFiles);
    
    if (selectedFiles.length === 1) {
      // Single file: use existing preview flow
      setSingleFile(selectedFiles[0]);
      await processarSingle(selectedFiles[0]);
    } else {
      // Multiple files: use queue
      await enviarParaFila(selectedFiles);
    }
  };

  // ============ SINGLE FILE FLOW ============
  const processarSingle = async (arquivo) => {
    setStep('single-processing');
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', arquivo);
      
      const res = await fetch(`${API_URL}/api/empresas/${empresaId}/importar/ia/preview`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` },
        body: formData
      });
      
      const result = await res.json();
      
      if (!res.ok) throw new Error(result.detail || 'Erro ao processar arquivo');
      
      if (result.sucesso) {
        setResultadoIA(result);
        setStep(result.periodo_existe ? 'single-conflict' : 'single-preview');
      } else {
        setError(result.erro || 'Não foi possível extrair dados do arquivo');
        setStep('error');
      }
    } catch (err) {
      setError(err.message || 'Erro ao processar arquivo com IA');
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const confirmarSingle = async (forcarSubstituir = false) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', singleFile);
      formData.append('substituir_existentes', forcarSubstituir ? 'true' : 'false');
      
      const res = await fetch(`${API_URL}/api/empresas/${empresaId}/importar/ia`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` },
        body: formData
      });
      
      const result = await res.json();
      
      if (result.sucesso) {
        toast.success(result.mensagem || 'Dados importados com sucesso!');
        onSuccess();
        onClose();
      } else if (result.requer_acao === 'confirmar_substituicao') {
        setResultadoIA(result);
        setStep('single-conflict');
      } else {
        throw new Error(result.erro || 'Erro na importação');
      }
    } catch (err) {
      setError(err.message);
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  // ============ QUEUE FLOW (MULTIPLE FILES) ============
  const enviarParaFila = async (arquivos) => {
    setStep('queue');
    setLoading(true);
    
    try {
      const formData = new FormData();
      arquivos.forEach(f => formData.append('files', f));
      formData.append('substituir_existentes', substituir ? 'true' : 'false');
      
      const res = await fetch(`${API_URL}/api/empresas/${empresaId}/importar/lote`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` },
        body: formData
      });
      
      const result = await res.json();
      
      if (!res.ok) throw new Error(result.detail || 'Erro ao agendar importação');
      
      setLoteId(result.lote_id);
      setLoteStatus({
        total: result.total_arquivos,
        concluidos: 0,
        erros: 0,
        processando: 0,
        pendentes: result.total_arquivos,
        finalizado: false,
        itens: result.itens.map(i => ({ ...i, status: 'pendente' }))
      });
      
      // Start polling
      startPolling(result.lote_id);
      
    } catch (err) {
      setError(err.message);
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const startPolling = (lid) => {
    if (pollRef.current) clearInterval(pollRef.current);
    
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/importacoes/lote/${lid}`, {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        
        if (res.ok) {
          const data = await res.json();
          setLoteStatus(data);
          
          if (data.finalizado) {
            clearInterval(pollRef.current);
            pollRef.current = null;
            
            if (data.concluidos > 0) {
              onSuccess(); // Reload data
            }
          }
        }
      } catch (err) {
        console.error('Poll error:', err);
      }
    }, 2000); // Poll every 2 seconds
  };

  // Formatters
  const formatarValor = (valor) => {
    if (!valor || valor === 0) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  };

  const progressPercent = loteStatus 
    ? Math.round(((loteStatus.concluidos + loteStatus.erros + loteStatus.conflitos) / loteStatus.total) * 100)
    : 0;

  return (
    <Modal isOpen={isOpen} onClose={step === 'queue' && !loteStatus?.finalizado ? undefined : onClose} title="Importar Dados" size="lg">
      
      {/* SELECT FILES */}
      {step === 'select' && (
        <div className="text-center py-8">
          <input type="file" accept=".pdf" multiple onChange={handleFileChange} className="hidden" id="file-upload" />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Upload className="w-10 h-10 text-blue-600" />
            </div>
            <p className="text-lg font-medium text-slate-900 mb-1">Selecione um ou mais arquivos</p>
            <p className="text-sm text-slate-500">PDF — selecione vários de uma vez para importação em lote</p>
          </label>
          
          <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg text-left border border-blue-100">
            <p className="text-sm font-medium text-blue-800 mb-2">🤖 Importação Inteligente</p>
            <p className="text-xs text-blue-600">
              Funciona com <strong>qualquer sistema contábil</strong>. 
              Múltiplos arquivos são processados <strong>sequencialmente</strong> com retry automático para evitar erros de limite.
            </p>
          </div>
          
          <label className="flex items-center gap-2 mt-4 justify-center text-sm text-slate-600 cursor-pointer">
            <input 
              type="checkbox" 
              checked={substituir} 
              onChange={e => setSubstituir(e.target.checked)}
              className="rounded border-slate-300"
            />
            Substituir dados existentes do mesmo período
          </label>
        </div>
      )}

      {/* SINGLE: PROCESSING */}
      {step === 'single-processing' && (
        <div className="text-center py-12">
          <div className="relative">
            <Loader2 className="w-16 h-16 text-blue-600 animate-spin mx-auto" />
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl">🤖</span>
            </div>
          </div>
          <p className="text-lg font-medium text-slate-900 mt-6">Analisando com IA...</p>
          <p className="text-sm text-slate-500 mt-2">Extraindo dados do documento</p>
        </div>
      )}

      {/* SINGLE: PREVIEW */}
      {step === 'single-preview' && resultadoIA && (
        <div>
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-6 h-6 text-green-600 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-green-800">Dados extraídos com sucesso!</h4>
                <p className="text-sm text-green-700 mt-1">
                  Confiança: <strong className="capitalize">{resultadoIA.confianca}</strong>
                  {resultadoIA.sistema_detectado && resultadoIA.sistema_detectado !== 'desconhecido' && (
                    <> • Sistema: <strong>{resultadoIA.sistema_detectado}</strong></>
                  )}
                  {resultadoIA.metodo_usado && (
                    <> • <strong className="capitalize">{resultadoIA.metodo_usado === 'parser_local' ? '📦 Parser Local' : '🤖 IA Claude'}</strong></>
                  )}
                </p>
              </div>
            </div>
          </div>
          
          <div className="mb-4 p-4 bg-slate-50 rounded-lg">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm mb-4">
              {resultadoIA.empresa_arquivo && (
                <div><span className="text-slate-500">Empresa:</span> <strong>{resultadoIA.empresa_arquivo}</strong></div>
              )}
              {resultadoIA.cnpj_arquivo && (
                <div><span className="text-slate-500">CNPJ:</span> <strong>{resultadoIA.cnpj_arquivo}</strong></div>
              )}
              {resultadoIA.periodo && (
                <div><span className="text-slate-500">Período:</span> <strong>{resultadoIA.periodo}</strong></div>
              )}
              <div><span className="text-slate-500">Campos:</span> <strong>{resultadoIA.campos_extraidos?.length || 0}</strong></div>
            </div>
            
            <h4 className="font-medium text-slate-900 mb-2">Valores encontrados:</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm max-h-48 overflow-y-auto">
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
          
          <div className="flex flex-col sm:flex-row justify-between gap-2">
            <Button variant="secondary" onClick={() => { setStep('select'); setSingleFile(null); setResultadoIA(null); }}>
              Cancelar
            </Button>
            <Button onClick={() => confirmarSingle(false)} loading={loading}>
              Confirmar e Importar
            </Button>
          </div>
        </div>
      )}

      {/* SINGLE: CONFLICT */}
      {step === 'single-conflict' && resultadoIA && (
        <div>
          <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-amber-800">Período já existe</h4>
                <p className="text-sm text-amber-700 mt-1">
                  Já existem dados para <strong>{resultadoIA.periodo || `${resultadoIA.mes}/${resultadoIA.ano}`}</strong>
                </p>
              </div>
            </div>
          </div>
          
          <p className="text-sm text-slate-700 mb-4">Deseja substituir os dados existentes?</p>
          
          <div className="flex flex-col sm:flex-row justify-between gap-2">
            <Button variant="secondary" onClick={onClose}>Cancelar</Button>
            <Button onClick={() => confirmarSingle(true)} loading={loading}>
              Substituir dados
            </Button>
          </div>
        </div>
      )}

      {/* QUEUE: PROGRESS */}
      {step === 'queue' && (
        <div>
          {/* Progress bar */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-slate-700">
                {loteStatus?.finalizado 
                  ? '✅ Importação concluída' 
                  : `Processando ${loteStatus?.processando > 0 ? (loteStatus.concluidos + loteStatus.erros + 1) : '...'} de ${loteStatus?.total || files.length}...`
                }
              </span>
              <span className="text-sm text-slate-500">{progressPercent}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2.5">
              <div 
                className={`h-2.5 rounded-full transition-all duration-500 ${loteStatus?.finalizado ? 'bg-green-500' : 'bg-blue-500'}`}
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            
            {loteStatus && (
              <div className="flex gap-4 mt-2 text-xs text-slate-500">
                {loteStatus.concluidos > 0 && <span className="text-green-600">✓ {loteStatus.concluidos} importado(s)</span>}
                {loteStatus.erros > 0 && <span className="text-red-600">✗ {loteStatus.erros} erro(s)</span>}
                {loteStatus.conflitos > 0 && <span className="text-amber-600">⚠ {loteStatus.conflitos} conflito(s)</span>}
                {loteStatus.pendentes > 0 && <span>⏳ {loteStatus.pendentes} na fila</span>}
              </div>
            )}
          </div>

          {/* File list */}
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {(loteStatus?.itens || files.map((f, i) => ({ nome_arquivo: f.name, status: 'pendente', posicao: i }))).map((item, idx) => {
              const cfg = STATUS_ICON[item.status] || STATUS_ICON.pendente;
              const Icon = cfg.icon;
              
              return (
                <div key={idx} className={`flex items-center gap-3 p-3 rounded-lg ${cfg.bg}`}>
                  <Icon className={`w-5 h-5 flex-shrink-0 ${cfg.color} ${cfg.spin ? 'animate-spin' : ''}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-700 truncate">{item.nome_arquivo}</p>
                    {item.status === 'concluido' && item.periodo && (
                      <p className="text-xs text-green-600">Período: {item.periodo}</p>
                    )}
                    {item.status === 'erro' && item.erro && (
                      <p className="text-xs text-red-600 truncate">{item.erro}</p>
                    )}
                    {item.status === 'processando' && item.tentativas > 0 && (
                      <p className="text-xs text-blue-600">Tentativa {item.tentativas + 1}...</p>
                    )}
                  </div>
                  {item.status === 'concluido' && <span className="text-xs text-green-500 flex-shrink-0">✓</span>}
                  {item.status === 'erro' && <span className="text-xs text-red-400 flex-shrink-0">✗</span>}
                </div>
              );
            })}
          </div>

          {/* Actions */}
          <div className="mt-4 pt-4 border-t flex justify-end gap-2">
            {loteStatus?.finalizado ? (
              <Button onClick={onClose}>
                Fechar
              </Button>
            ) : (
              <p className="text-xs text-slate-400 py-2">
                Processando sequencialmente com retry automático...
              </p>
            )}
          </div>
        </div>
      )}

      {/* ERROR */}
      {step === 'error' && (
        <div>
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-red-600 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-red-800">Erro na importação</h4>
                <p className="text-sm text-red-700 mt-2">{error}</p>
              </div>
            </div>
          </div>
          
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-6">
            <h4 className="font-medium text-blue-800 mb-2">O que fazer:</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Verifique se o arquivo não está corrompido</li>
              <li>• Tente com menos arquivos simultâneos</li>
              <li>• Certifique-se que são documentos contábeis válidos</li>
            </ul>
          </div>
          
          <div className="flex flex-col sm:flex-row justify-end gap-2">
            <Button variant="secondary" onClick={() => { setStep('select'); setFiles([]); setError(''); }}>
              Tentar novamente
            </Button>
            <Button onClick={onClose}>Fechar</Button>
          </div>
        </div>
      )}
    </Modal>
  );
}

export default UploadModal;
