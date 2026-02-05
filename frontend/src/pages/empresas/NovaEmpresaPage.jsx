import React, { useState, useEffect } from 'react';
import { ArrowLeft, Search } from 'lucide-react';
import { Button, Card, Input, Select } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

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

export default NovaEmpresaPage;
