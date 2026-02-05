import RevisaoImportacao from './RevisaoImportacao';
import React, { useState, useEffect } from 'react';
import { AlertTriangle, ArrowLeft, BarChart3, Building2, Check, CheckCircle, Eye, FileSpreadsheet, FileText, Info, Loader2, Plus, Search, TrendingUp, Upload, X } from 'lucide-react';
import { Button, Card, Modal } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import { formatarMoeda } from '../../utils/formatters';

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

export default ImportacaoPage;
