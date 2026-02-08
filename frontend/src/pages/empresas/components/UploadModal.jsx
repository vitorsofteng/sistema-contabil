import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Loader2, Upload } from 'lucide-react';
import { Button, Modal } from '../../../components/ui';
import { useToast } from '../../../contexts/ToastContext';
import { API_URL } from '../../../config/api';

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
      
      const res = await fetch(`${API_URL}/api/empresas/${empresaId}/importar/ia/preview`, {
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
      
      const res = await fetch(`${API_URL}/api/empresas/${empresaId}/importar/ia`, {
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
              <div><span className="text-slate-500">Campos extraídos:</span> <strong>{resultadoIA.campos_extraidos?.length || 0}</strong></div>
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
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
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

export default UploadModal;
