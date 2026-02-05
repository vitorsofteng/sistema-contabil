import React, { useState, useEffect, useRef } from 'react';
import { AlertCircle, Check, Clock, Eye, Info, Loader2, Upload } from 'lucide-react';
import { Badge, Button, Card } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

function ImportacaoAvancadaPage({ empresaId, onSuccess }) {
  const { api } = useAuth();
  const toast = useToast();
  const fileInputRef = useRef(null);
  
  const [step, setStep] = useState('upload'); // upload, preview, mapping, importing, done
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [mapeamento, setMapeamento] = useState({});
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [historico, setHistorico] = useState([]);
  const [showHistorico, setShowHistorico] = useState(false);
  const [config, setConfig] = useState({
    ignorar_duplicados: true,
    modo_agregacao: 'substituir'
  });

  useEffect(() => {
    if (empresaId) loadHistorico();
  }, [empresaId]);

  const loadHistorico = async () => {
    try {
      const res = await api(`/empresas/${empresaId}/importacoes?limite=10`);
      if (res.ok) {
        const data = await res.json();
        setHistorico(data.importacoes || []);
      }
    } catch (err) {
      console.error('Erro ao carregar histórico:', err);
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setStep('upload');
      setPreview(null);
      setResultado(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setStep('upload');
      setPreview(null);
      setResultado(null);
    }
  };

  const handlePreview = async () => {
    if (!file) return;
    
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await fetch(`/api/empresas/${empresaId}/importar/preview`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });
      
      if (res.ok) {
        const data = await res.json();
        setPreview(data);
        setMapeamento(data.mapeamento_sugerido || {});
        setStep('preview');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Erro ao analisar arquivo');
      }
    } catch (err) {
      toast.error('Erro ao processar arquivo');
    } finally {
      setLoading(false);
    }
  };

  const handleImportar = async () => {
    if (!file) return;
    
    setLoading(true);
    setStep('importing');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mapeamento', JSON.stringify(mapeamento));
    formData.append('ignorar_duplicados', config.ignorar_duplicados);
    formData.append('modo_agregacao', config.modo_agregacao);
    
    try {
      const res = await fetch(`/api/empresas/${empresaId}/importar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });
      
      const data = await res.json();
      
      if (res.ok && data.sucesso) {
        setResultado(data);
        setStep('done');
        toast.success(`Importação concluída: ${data.registros_importados} registros`);
        loadHistorico();
        if (onSuccess) onSuccess();
      } else {
        setResultado(data);
        setStep('done');
        toast.error(data.erro || 'Importação concluída com erros');
      }
    } catch (err) {
      toast.error('Erro ao importar dados');
      setStep('preview');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setMapeamento({});
    setResultado(null);
    setStep('upload');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const camposSistema = [
    { key: 'data', label: 'Data/Período', required: true },
    { key: 'receita', label: 'Receita' },
    { key: 'custos', label: 'Custos' },
    { key: 'despesas', label: 'Despesas' },
    { key: 'impostos', label: 'Impostos' },
    { key: 'folha', label: 'Folha de Pagamento' },
    { key: 'caixa', label: 'Saldo Caixa' }
  ];

  const getTipoIcon = (tipo) => {
    const icons = {
      'csv': '📊',
      'xlsx': '📗',
      'ofx': '🏦',
      'xml_nfe': '📄'
    };
    return icons[tipo] || '📁';
  };

  const getStatusColor = (status) => {
    const colors = {
      'sucesso': 'bg-green-100 text-green-700',
      'parcial': 'bg-yellow-100 text-yellow-700',
      'erro': 'bg-red-100 text-red-700',
      'processando': 'bg-blue-100 text-blue-700'
    };
    return colors[status] || 'bg-slate-100 text-slate-700';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Importação Avançada</h2>
          <p className="text-sm text-slate-500">Suporte a CSV, Excel, OFX e XML NFe</p>
        </div>
        <Button variant="secondary" onClick={() => setShowHistorico(!showHistorico)}>
          <Clock className="w-4 h-4 mr-2" />
          Histórico
        </Button>
      </div>

      {/* Histórico */}
      {showHistorico && (
        <Card className="p-4">
          <h3 className="font-semibold text-slate-800 mb-3">Importações Recentes</h3>
          {historico.length === 0 ? (
            <p className="text-slate-500 text-sm">Nenhuma importação realizada</p>
          ) : (
            <div className="space-y-2">
              {historico.map(imp => (
                <div key={imp.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{getTipoIcon(imp.tipo_arquivo)}</span>
                    <div>
                      <p className="font-medium text-slate-800 text-sm">{imp.nome_arquivo}</p>
                      <p className="text-xs text-slate-500">
                        {new Date(imp.created_at).toLocaleString('pt-BR')} • {imp.periodo}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(imp.status)}`}>
                      {imp.status_label}
                    </span>
                    <span className="text-sm text-slate-600">
                      {imp.registros_importados}/{imp.total_registros}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Upload Area */}
      {step === 'upload' && (
        <Card 
          className="p-8 border-2 border-dashed border-slate-300 hover:border-blue-400 transition-colors cursor-pointer"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.ofx,.qif,.xml"
            onChange={handleFileSelect}
            className="hidden"
          />
          
          <div className="text-center">
            <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-lg font-medium text-slate-700 mb-2">
              {file ? file.name : 'Arraste um arquivo ou clique para selecionar'}
            </p>
            <p className="text-sm text-slate-500">
              Formatos: CSV, OFX (extrato bancário), XML (NFe)
            </p>
            
            {file && (
              <div className="mt-4 flex justify-center gap-3">
                <Button onClick={(e) => { e.stopPropagation(); handlePreview(); }} disabled={loading}>
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
                  Analisar Arquivo
                </Button>
                <Button variant="secondary" onClick={(e) => { e.stopPropagation(); handleReset(); }}>
                  Cancelar
                </Button>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Preview */}
      {step === 'preview' && preview && (
        <div className="space-y-4">
          {/* Info do arquivo */}
          <Card className="p-4">
            <div className="flex items-center gap-4">
              <span className="text-3xl">{getTipoIcon(preview.tipo_arquivo)}</span>
              <div className="flex-1">
                <p className="font-semibold text-slate-800">{file?.name}</p>
                <p className="text-sm text-slate-500">
                  {preview.total_registros} registros • Período: {preview.periodo_inicio} a {preview.periodo_fim}
                </p>
              </div>
              <div className="flex gap-2">
                <Badge variant={preview.registros_validos > 0 ? 'success' : 'warning'}>
                  {preview.registros_validos} válidos
                </Badge>
                {preview.registros_duplicados > 0 && (
                  <Badge variant="warning">{preview.registros_duplicados} duplicados</Badge>
                )}
                {preview.registros_erro > 0 && (
                  <Badge variant="danger">{preview.registros_erro} erros</Badge>
                )}
              </div>
            </div>
          </Card>

          {/* Mapeamento de colunas */}
          <Card className="p-4">
            <h3 className="font-semibold text-slate-800 mb-4">Mapeamento de Colunas</h3>
            <p className="text-sm text-slate-500 mb-4">
              Relacione as colunas do arquivo com os campos do sistema
            </p>
            
            <div className="grid md:grid-cols-2 gap-4">
              {camposSistema.map(campo => (
                <div key={campo.key}>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    {campo.label} {campo.required && <span className="text-red-500">*</span>}
                  </label>
                  <select
                    value={mapeamento[campo.key] || ''}
                    onChange={(e) => setMapeamento({...mapeamento, [campo.key]: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">-- Não mapear --</option>
                    {preview.colunas_detectadas?.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </Card>

          {/* Preview de dados */}
          <Card className="p-4">
            <h3 className="font-semibold text-slate-800 mb-4">Preview dos Dados</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-slate-600">Linha</th>
                    <th className="px-3 py-2 text-left font-medium text-slate-600">Período</th>
                    <th className="px-3 py-2 text-right font-medium text-slate-600">Receita</th>
                    <th className="px-3 py-2 text-right font-medium text-slate-600">Custos</th>
                    <th className="px-3 py-2 text-right font-medium text-slate-600">Despesas</th>
                    <th className="px-3 py-2 text-center font-medium text-slate-600">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {preview.preview?.slice(0, 10).map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="px-3 py-2 text-slate-500">{row.linha}</td>
                      <td className="px-3 py-2">{row.ano}/{String(row.mes).padStart(2, '0')}</td>
                      <td className="px-3 py-2 text-right text-green-600">
                        {row.receita?.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                      </td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {row.custos?.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                      </td>
                      <td className="px-3 py-2 text-right text-orange-600">
                        {row.despesas?.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {row.erro ? (
                          <span className="text-red-500 text-xs">{row.erro}</span>
                        ) : row.is_duplicado ? (
                          <Badge variant="warning">Duplicado</Badge>
                        ) : (
                          <Badge variant="success">OK</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Configurações */}
          <Card className="p-4">
            <h3 className="font-semibold text-slate-800 mb-4">Configurações</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.ignorar_duplicados}
                  onChange={(e) => setConfig({...config, ignorar_duplicados: e.target.checked})}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <span className="text-sm text-slate-700">Ignorar registros duplicados</span>
              </label>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Modo de Agregação
                </label>
                <select
                  value={config.modo_agregacao}
                  onChange={(e) => setConfig({...config, modo_agregacao: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                >
                  <option value="substituir">Substituir dados existentes</option>
                  <option value="somar">Somar aos dados existentes</option>
                  <option value="ignorar">Ignorar se já existir</option>
                </select>
              </div>
            </div>
          </Card>

          {/* Erros */}
          {preview.erros?.length > 0 && (
            <Card className="p-4 border-red-200 bg-red-50">
              <h3 className="font-semibold text-red-800 mb-2 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Erros Encontrados ({preview.erros.length})
              </h3>
              <ul className="text-sm text-red-700 space-y-1">
                {preview.erros.slice(0, 5).map((err, idx) => (
                  <li key={idx}>Linha {err.linha}: {err.erro}</li>
                ))}
                {preview.erros.length > 5 && (
                  <li className="text-red-500">... e mais {preview.erros.length - 5} erros</li>
                )}
              </ul>
            </Card>
          )}

          {/* Ações */}
          <div className="flex gap-3">
            <Button onClick={handleImportar} disabled={loading || !mapeamento.data}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Check className="w-4 h-4 mr-2" />}
              Importar {preview.registros_validos} Registros
            </Button>
            <Button variant="secondary" onClick={handleReset}>
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {/* Importing */}
      {step === 'importing' && (
        <Card className="p-8 text-center">
          <Loader2 className="w-12 h-12 text-blue-500 mx-auto mb-4 animate-spin" />
          <p className="text-lg font-medium text-slate-700">Importando dados...</p>
          <p className="text-sm text-slate-500">Isso pode levar alguns segundos</p>
        </Card>
      )}

      {/* Done */}
      {step === 'done' && resultado && (
        <Card className="p-6">
          <div className="text-center mb-6">
            {resultado.sucesso ? (
              <>
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Check className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-800 mb-2">Importação Concluída!</h3>
              </>
            ) : (
              <>
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <AlertCircle className="w-8 h-8 text-red-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-800 mb-2">Importação com Problemas</h3>
              </>
            )}
          </div>

          <div className="grid md:grid-cols-4 gap-4 mb-6">
            <div className="bg-slate-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-slate-800">{resultado.total_registros || 0}</p>
              <p className="text-sm text-slate-500">Total</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-green-600">{resultado.registros_importados || 0}</p>
              <p className="text-sm text-slate-500">Importados</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-yellow-600">{resultado.registros_duplicados || 0}</p>
              <p className="text-sm text-slate-500">Duplicados</p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-red-600">{resultado.registros_erro || 0}</p>
              <p className="text-sm text-slate-500">Erros</p>
            </div>
          </div>

          {resultado.periodo_inicio && (
            <p className="text-sm text-slate-600 text-center mb-4">
              Período: {resultado.periodo_inicio} a {resultado.periodo_fim}
            </p>
          )}

          {resultado.erros?.length > 0 && (
            <div className="bg-red-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold text-red-800 mb-2">Erros:</h4>
              <ul className="text-sm text-red-700 space-y-1">
                {resultado.erros.slice(0, 5).map((err, idx) => (
                  <li key={idx}>{err.periodo || `Linha ${err.linha}`}: {err.erro}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex justify-center gap-3">
            <Button onClick={handleReset}>
              <Upload className="w-4 h-4 mr-2" />
              Nova Importação
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}

export default ImportacaoAvancadaPage;
