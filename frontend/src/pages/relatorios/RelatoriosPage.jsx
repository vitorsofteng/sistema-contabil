import React, { useState, useEffect } from 'react';
import { Check, Download, FileSpreadsheet, FileText, Plus, X, PieChart as PieChartIcon } from 'lucide-react';
import { Button, Card, EmptyState, LoadingScreen, Modal } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useToast } from '../../contexts/ToastContext';
import { useExport } from '../../contexts/ExportContext';

function RelatoriosPage({ onNavigate }) {
  const { api } = useAuth();
  const toast = useToast();
  const { agendarExportacao } = useExport();
  const themeCtx = useTheme();
  
  const [activeTab, setActiveTab] = useState('gerar');
  const [empresas, setEmpresas] = useState([]);
  const [empresaSelecionada, setEmpresaSelecionada] = useState(null);
  const [config, setConfig] = useState({
    nome_escritorio: '',
    cor_primaria: '#1e40af',
    cor_secundaria: '#3b82f6',
    cor_destaque: '#059669',
    mostrar_logo: true,
    mostrar_graficos: true,
    mostrar_recomendacoes: true,
    template_padrao: 'executivo',
    telefone: '',
    email_contato: '',
    website: '',
    texto_rodape: ''
  });
  const [historico, setHistorico] = useState([]);
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [incluirParecer, setIncluirParecer] = useState(false);
  
  // Modal para criar link
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [linkConfig, setLinkConfig] = useState({
    tipo_relatorio: 'pdf',
    template: 'executivo',
    permite_download: true,
    requer_senha: false,
    senha: '',
    expira_em_dias: 7,
    max_acessos: null
  });
  const [linkCriado, setLinkCriado] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [empRes, configRes, histRes, linksRes] = await Promise.all([
        api('/empresas'),
        api('/relatorios/configuracao'),
        api('/relatorios/historico?limite=10'),
        api('/relatorios/links')
      ]);
      
      if (empRes.ok) {
        const data = await empRes.json();
        setEmpresas(data.empresas || []);
      }
      
      if (configRes.ok) {
        const data = await configRes.json();
        setConfig(prev => ({ ...prev, ...data }));
      }
      
      if (histRes.ok) {
        const data = await histRes.json();
        setHistorico(data.historico || []);
      }
      
      if (linksRes.ok) {
        const data = await linksRes.json();
        setLinks(data.links || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const salvarConfiguracao = async () => {
    try {
      const res = await api('/relatorios/configuracao', {
        method: 'PUT',
        body: JSON.stringify(config)
      });
      
      if (res.ok) {
        toast.success('Configuração salva com sucesso!');
        
        // Atualizar tema global imediatamente
        if (themeCtx?.updateTheme) {
          themeCtx.updateTheme({
            cor_primaria: config.cor_primaria,
            cor_secundaria: config.cor_secundaria,
            cor_destaque: config.cor_destaque,
            nome_escritorio: config.nome_escritorio
          });
        }
      } else {
        toast.error('Erro ao salvar configuração');
      }
    } catch (err) {
      toast.error('Erro ao salvar');
    }
  };

  const gerarRelatorio = async (tipo) => {
    if (!empresaSelecionada) {
      toast.warning('Selecione uma empresa');
      return;
    }
    
    const empresa = empresas.find(e => e.id === empresaSelecionada);
    const empresaNome = empresa?.razao_social || 'Empresa';
    
    const tipoExport = tipo === 'pdf' && incluirParecer ? 'pdf_parecer' : tipo;
    agendarExportacao(empresaSelecionada, tipoExport, empresaNome);
  };

  const criarLink = async () => {
    if (!empresaSelecionada) {
      toast.warning('Selecione uma empresa');
      return;
    }
    
    try {
      const res = await api(`/empresas/${empresaSelecionada}/relatorios/link`, {
        method: 'POST',
        body: JSON.stringify(linkConfig)
      });
      
      if (res.ok) {
        const data = await res.json();
        setLinkCriado(data);
        toast.success('Link criado com sucesso!');
        loadData();
      } else {
        toast.error('Erro ao criar link');
      }
    } catch (err) {
      toast.error('Erro ao criar link');
    }
  };

  const desativarLink = async (token) => {
    try {
      const res = await api(`/relatorios/links/${token}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Link desativado');
        loadData();
      }
    } catch (err) {
      toast.error('Erro ao desativar link');
    }
  };

  const copiarLink = (url) => {
    navigator.clipboard.writeText(url);
    toast.success('Link copiado!');
  };

  if (loading) return <LoadingScreen />;

  return (
    <div>
      <Header 
        title="Relatórios" 
        subtitle="Gere relatórios profissionais em PDF, Excel e PowerPoint"
      />

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-100 p-1 rounded-lg overflow-x-auto scrollbar-hide">
        {[
          { id: 'gerar', label: 'Gerar Relatório' },
          { id: 'config', label: 'Configuração' },
          { id: 'historico', label: 'Histórico' },
          { id: 'links', label: 'Links' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id 
                ? 'bg-white text-slate-900 shadow-sm' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab: Gerar Relatório */}
      {activeTab === 'gerar' && (
        <div className="space-y-6">
          {/* Seleção de empresa */}
          <Card className="p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Selecione a Empresa</h3>
            <select
              value={empresaSelecionada || ''}
              onChange={(e) => setEmpresaSelecionada(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Selecione...</option>
              {empresas.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.razao_social}</option>
              ))}
            </select>
          </Card>

          {/* Tipos de relatório */}
          {empresaSelecionada && (
            <div className="grid md:grid-cols-3 gap-4">
              {/* PDF */}
              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="text-center">
                  <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <FileText className="w-8 h-8 text-red-600" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">Relatório PDF</h3>
                  <p className="text-sm text-slate-500 mb-4">Relatório financeiro completo com análises</p>
                  <label className="flex items-center gap-2 text-sm text-slate-600 mb-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={incluirParecer}
                      onChange={(e) => setIncluirParecer(e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    <span>Incluir Parecer Consultivo</span>
                  </label>
                  <Button 
                    onClick={() => gerarRelatorio('pdf')}
                    className="w-full"
                  >
                    <Download className="w-4 h-4" />
                    {incluirParecer ? 'Exportar Parecer Consultivo' : 'Exportar Relatório Técnico'}
                  </Button>
                </div>
              </Card>

              {/* Excel */}
              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <FileSpreadsheet className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">Planilha Excel</h3>
                  <p className="text-sm text-slate-500 mb-4">Dados e indicadores em formato editável</p>
                  <Button 
                    onClick={() => gerarRelatorio('excel')}
                    variant="secondary"
                    className="w-full"
                  >
                    <Download className="w-4 h-4" />
                    Exportar Excel
                  </Button>
                </div>
              </Card>

              {/* PowerPoint */}
              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="text-center">
                  <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <PieChartIcon className="w-8 h-8 text-orange-600" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">Apresentação</h3>
                  <p className="text-sm text-slate-500 mb-4">Slides prontos para apresentar ao cliente</p>
                  <Button 
                    onClick={() => gerarRelatorio('pptx')}
                    variant="secondary"
                    className="w-full"
                  >
                    <Download className="w-4 h-4" />
                    Exportar Apresentação
                  </Button>
                </div>
              </Card>
            </div>
          )}

          {/* Link compartilhável */}
          {empresaSelecionada && (
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-900">Link Compartilhável</h3>
                <Button size="sm" variant="secondary" onClick={() => setShowLinkModal(true)}>
                  <Plus className="w-4 h-4" /> Criar Link
                </Button>
              </div>
              <p className="text-sm text-slate-500">
                Crie um link temporário para compartilhar o relatório com seu cliente, sem necessidade de login.
              </p>
            </Card>
          )}
        </div>
      )}

      {/* Tab: Configuração */}
      {activeTab === 'config' && (
        <Card className="p-6">
          <h3 className="font-semibold text-slate-900 mb-6">Personalização (White-Label)</h3>
          
          <div className="grid md:grid-cols-2 gap-6">
            {/* Nome do escritório */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Nome do Escritório</label>
              <input
                type="text"
                value={config.nome_escritorio}
                onChange={(e) => setConfig({ ...config, nome_escritorio: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                placeholder="Seu Escritório Contábil"
              />
            </div>

            {/* Telefone */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Telefone</label>
              <input
                type="text"
                value={config.telefone}
                onChange={(e) => setConfig({ ...config, telefone: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                placeholder="(11) 99999-9999"
              />
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email de Contato</label>
              <input
                type="email"
                value={config.email_contato}
                onChange={(e) => setConfig({ ...config, email_contato: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                placeholder="contato@escritorio.com"
              />
            </div>

            {/* Website */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Website</label>
              <input
                type="text"
                value={config.website}
                onChange={(e) => setConfig({ ...config, website: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                placeholder="www.seuescritorio.com.br"
              />
            </div>

            {/* Cores */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Cor Primária</label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={config.cor_primaria}
                  onChange={(e) => setConfig({ ...config, cor_primaria: e.target.value })}
                  className="w-12 h-10 border border-slate-200 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={config.cor_primaria}
                  onChange={(e) => setConfig({ ...config, cor_primaria: e.target.value })}
                  className="flex-1 px-3 py-2 border border-slate-200 rounded-lg"
                />
              </div>
            </div>

            {/* Cor secundária */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Cor Secundária</label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={config.cor_secundaria}
                  onChange={(e) => setConfig({ ...config, cor_secundaria: e.target.value })}
                  className="w-12 h-10 border border-slate-200 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={config.cor_secundaria}
                  onChange={(e) => setConfig({ ...config, cor_secundaria: e.target.value })}
                  className="flex-1 px-3 py-2 border border-slate-200 rounded-lg"
                />
              </div>
            </div>

            {/* Texto do rodapé */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">Texto do Rodapé</label>
              <textarea
                value={config.texto_rodape}
                onChange={(e) => setConfig({ ...config, texto_rodape: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                rows={2}
                placeholder="Texto personalizado para aparecer no rodapé dos relatórios"
              />
            </div>

            {/* Opções */}
            <div className="md:col-span-2 space-y-3">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.mostrar_graficos}
                  onChange={(e) => setConfig({ ...config, mostrar_graficos: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm text-slate-700">Incluir gráficos nos relatórios</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.mostrar_recomendacoes}
                  onChange={(e) => setConfig({ ...config, mostrar_recomendacoes: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm text-slate-700">Incluir recomendações e plano de ação</span>
              </label>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t flex justify-end">
            <Button onClick={salvarConfiguracao}>
              <Check className="w-4 h-4" /> Salvar Configuração
            </Button>
          </div>
        </Card>
      )}

      {/* Tab: Histórico */}
      {activeTab === 'historico' && (
        <Card className="p-6">
          <h3 className="font-semibold text-slate-900 mb-4">Histórico de Relatórios</h3>
          
          {historico.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-slate-500 border-b">
                    <th className="pb-3 font-medium">Empresa</th>
                    <th className="pb-3 font-medium">Tipo</th>
                    <th className="pb-3 font-medium">Data</th>
                    <th className="pb-3 font-medium">Tamanho</th>
                  </tr>
                </thead>
                <tbody>
                  {historico.map(item => (
                    <tr key={item.id} className="border-b last:border-0">
                      <td className="py-3 font-medium">{item.empresa_nome}</td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          item.tipo === 'pdf' ? 'bg-red-100 text-red-700' :
                          item.tipo === 'excel' ? 'bg-green-100 text-green-700' :
                          'bg-orange-100 text-orange-700'
                        }`}>
                          {item.tipo?.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 text-sm text-slate-500">
                        {new Date(item.created_at).toLocaleDateString('pt-BR')}
                      </td>
                      <td className="py-3 text-sm text-slate-500">
                        {item.arquivo_tamanho ? `${(item.arquivo_tamanho / 1024).toFixed(0)} KB` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState 
              icon={FileText}
              title="Nenhum relatório gerado"
              description="Gere seu primeiro relatório na aba 'Gerar Relatório'"
            />
          )}
        </Card>
      )}

      {/* Tab: Links */}
      {activeTab === 'links' && (
        <Card className="p-6">
          <h3 className="font-semibold text-slate-900 mb-4">Links Compartilháveis Ativos</h3>
          
          {links.length > 0 ? (
            <div className="space-y-4">
              {links.map(link => (
                <div key={link.id} className="p-4 border border-slate-200 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">{link.empresa_nome}</p>
                      <p className="text-sm text-slate-500 mt-1">
                        Tipo: {link.tipo_relatorio?.toUpperCase()} | 
                        Acessos: {link.acessos}{link.max_acessos ? `/${link.max_acessos}` : ''}
                      </p>
                      {link.expira_em && (
                        <p className="text-xs text-slate-400 mt-1">
                          Expira em: {new Date(link.expira_em).toLocaleDateString('pt-BR')}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="secondary" onClick={() => copiarLink(link.url)}>
                        Copiar Link
                      </Button>
                      <Button size="sm" variant="danger" onClick={() => desativarLink(link.token)}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="mt-2 p-2 bg-slate-50 rounded text-sm text-slate-600 break-all">
                    {link.url}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState 
              icon={FileText}
              title="Nenhum link ativo"
              description="Crie links compartilháveis para enviar relatórios aos seus clientes"
            />
          )}
        </Card>
      )}

      {/* Modal criar link */}
      {showLinkModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg">Criar Link Compartilhável</h3>
              <button onClick={() => { setShowLinkModal(false); setLinkCriado(null); }}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            {linkCriado ? (
              <div className="space-y-4">
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-green-800 font-medium mb-2">Link criado com sucesso!</p>
                  <p className="text-sm text-green-700 break-all">{linkCriado.url}</p>
                </div>
                <Button className="w-full" onClick={() => copiarLink(linkCriado.url)}>
                  Copiar Link
                </Button>
                <Button className="w-full" variant="secondary" onClick={() => { setShowLinkModal(false); setLinkCriado(null); }}>
                  Fechar
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Tipo de Relatório</label>
                  <select
                    value={linkConfig.tipo_relatorio}
                    onChange={(e) => setLinkConfig({ ...linkConfig, tipo_relatorio: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                  >
                    <option value="pdf">PDF</option>
                    <option value="excel">Excel</option>
                    <option value="pptx">PowerPoint</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Expira em (dias)</label>
                  <input
                    type="number"
                    value={linkConfig.expira_em_dias || ''}
                    onChange={(e) => setLinkConfig({ ...linkConfig, expira_em_dias: e.target.value ? parseInt(e.target.value) : null })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                    placeholder="Ex: 7 (deixe vazio para não expirar)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Máximo de acessos</label>
                  <input
                    type="number"
                    value={linkConfig.max_acessos || ''}
                    onChange={(e) => setLinkConfig({ ...linkConfig, max_acessos: e.target.value ? parseInt(e.target.value) : null })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                    placeholder="Ex: 10 (deixe vazio para ilimitado)"
                  />
                </div>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={linkConfig.requer_senha}
                    onChange={(e) => setLinkConfig({ ...linkConfig, requer_senha: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm text-slate-700">Proteger com senha</span>
                </label>

                {linkConfig.requer_senha && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Senha</label>
                    <input
                      type="password"
                      value={linkConfig.senha}
                      onChange={(e) => setLinkConfig({ ...linkConfig, senha: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                    />
                  </div>
                )}

                <div className="flex gap-2 pt-2">
                  <Button className="flex-1" onClick={criarLink}>
                    Criar Link
                  </Button>
                  <Button variant="secondary" onClick={() => setShowLinkModal(false)}>
                    Cancelar
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

export default RelatoriosPage;
