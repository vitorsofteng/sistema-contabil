/**
 * Componente de Revisão de Importação - v2.0
 * ==========================================
 * 
 * PRINCÍPIO: Mostrar apenas DADOS BRUTOS do arquivo.
 * Indicadores (ROE, Margem, etc) são calculados DEPOIS da confirmação.
 * 
 * O usuário deve conseguir:
 * 1. Ver todos os valores extraídos
 * 2. Comparar facilmente com o arquivo original
 * 3. Editar qualquer valor incorreto
 * 4. Entender de onde vieram os dados (Parser vs IA)
 */

import React, { useState, useEffect, useMemo } from 'react';

// ============================================================================
// CONFIGURAÇÃO DOS CAMPOS
// ============================================================================

const GRUPOS_CAMPOS = {
  dre: {
    titulo: 'Demonstração do Resultado (DRE)',
    descricao: 'Receitas, custos e despesas do período',
    icone: '📊',
    cor: 'blue',
    campos: [
      { nome: 'receita_bruta', label: 'Receita Bruta', obrigatorio: true, dica: 'Conta 3.1.1 - Receita Bruta de Vendas' },
      { nome: 'receita_servicos', label: 'Receita de Serviços', obrigatorio: false, dica: 'Se houver prestação de serviços' },
      { nome: 'deducoes_receita', label: '(-) Deduções da Receita', obrigatorio: false, dica: 'Impostos sobre vendas (ICMS, PIS, COFINS, ISS)' },
      { nome: 'receita_liquida', label: 'Receita Líquida', obrigatorio: false, dica: 'Receita Bruta - Deduções', calculado: true },
      { nome: 'custos', label: '(-) Custos (CMV/CPV)', obrigatorio: false, dica: 'Custo das Mercadorias/Produtos Vendidos' },
      { nome: 'lucro_bruto', label: 'Lucro Bruto', obrigatorio: false, dica: 'Receita Líquida - Custos', calculado: true },
      { nome: 'despesas_operacionais', label: '(-) Despesas Operacionais', obrigatorio: false, dica: 'Vendas + Administrativas + Gerais' },
      { nome: 'despesas_financeiras', label: '(-) Despesas Financeiras', obrigatorio: false, dica: 'Juros, multas, IOF' },
      { nome: 'lucro_liquido', label: 'Resultado do Exercício', obrigatorio: true, dica: 'RESUMO DO BALANCETE → Resultado do Exercício', destaque: true },
    ]
  },
  ativo: {
    titulo: 'Balanço - Ativo',
    descricao: 'Bens e direitos da empresa',
    icone: '🏦',
    cor: 'green',
    campos: [
      { nome: 'ativo_total', label: 'Ativo Total', obrigatorio: true, dica: 'Conta 1 - Total do Ativo', destaque: true },
      { nome: 'ativo_circulante', label: 'Ativo Circulante', obrigatorio: true, dica: 'Conta 1.1 - Realizável até 12 meses' },
      { nome: 'disponivel', label: 'Disponível', obrigatorio: false, dica: 'Caixa + Bancos + Aplicações' },
      { nome: 'caixa', label: 'Caixa', obrigatorio: false, dica: 'Dinheiro em espécie' },
      { nome: 'bancos', label: 'Bancos', obrigatorio: false, dica: 'Saldo em contas bancárias' },
      { nome: 'clientes', label: 'Clientes / Contas a Receber', obrigatorio: false, dica: 'Duplicatas a receber' },
      { nome: 'estoques', label: 'Estoques', obrigatorio: false, dica: 'Mercadorias, produtos, matéria-prima' },
      { nome: 'ativo_nao_circulante', label: 'Ativo Não Circulante', obrigatorio: false, dica: 'Realizável após 12 meses + Imobilizado' },
    ]
  },
  passivo: {
    titulo: 'Balanço - Passivo',
    descricao: 'Obrigações da empresa',
    icone: '📋',
    cor: 'red',
    campos: [
      { nome: 'passivo_circulante', label: 'Passivo Circulante', obrigatorio: true, dica: 'Conta 2.1 - Exigível até 12 meses', destaque: true },
      { nome: 'fornecedores', label: 'Fornecedores', obrigatorio: false, dica: 'Contas a pagar a fornecedores' },
      { nome: 'obrigacoes_tributarias', label: 'Obrigações Tributárias', obrigatorio: false, dica: 'Impostos a recolher' },
      { nome: 'obrigacoes_trabalhistas', label: 'Obrigações Trabalhistas', obrigatorio: false, dica: 'Salários, FGTS, INSS a pagar' },
      { nome: 'emprestimos_cp', label: 'Empréstimos (Curto Prazo)', obrigatorio: false, dica: 'Empréstimos vencendo em até 12 meses' },
      { nome: 'passivo_nao_circulante', label: 'Passivo Não Circulante', obrigatorio: false, dica: 'Conta 2.2 - Exigível após 12 meses' },
    ]
  },
  patrimonio: {
    titulo: 'Patrimônio Líquido',
    descricao: 'Capital dos sócios',
    icone: '💰',
    cor: 'purple',
    campos: [
      { nome: 'patrimonio_liquido', label: 'Patrimônio Líquido (Grupo 2.3)', obrigatorio: true, dica: 'Capital + Reservas (sem resultado)', destaque: true },
      { nome: 'capital_social', label: 'Capital Social', obrigatorio: true, dica: 'Capital integralizado pelos sócios' },
      { nome: 'reservas', label: 'Reservas de Capital/Lucros', obrigatorio: false, dica: 'Reservas diversas' },
      { nome: 'lucros_acumulados', label: 'Lucros Acumulados', obrigatorio: false, dica: 'Lucros de exercícios anteriores' },
    ]
  },
  impostos: {
    titulo: 'Detalhamento de Impostos',
    descricao: 'Tributos sobre faturamento',
    icone: '🧾',
    cor: 'orange',
    campos: [
      { nome: 'icms', label: 'ICMS', obrigatorio: false, dica: 'Imposto sobre circulação de mercadorias' },
      { nome: 'pis', label: 'PIS', obrigatorio: false, dica: 'Programa de Integração Social' },
      { nome: 'cofins', label: 'COFINS', obrigatorio: false, dica: 'Contribuição para Financiamento da Seguridade Social' },
      { nome: 'iss', label: 'ISS', obrigatorio: false, dica: 'Imposto sobre serviços (se aplicável)' },
      { nome: 'irpj', label: 'IRPJ', obrigatorio: false, dica: 'Imposto de Renda Pessoa Jurídica' },
      { nome: 'csll', label: 'CSLL', obrigatorio: false, dica: 'Contribuição Social sobre Lucro Líquido' },
    ]
  }
};

// ============================================================================
// UTILITÁRIOS
// ============================================================================

const formatarMoeda = (valor) => {
  if (valor === null || valor === undefined || valor === '') return '';
  const numero = typeof valor === 'string' ? parseFloat(valor) : valor;
  if (isNaN(numero)) return '';
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(numero);
};

const parseMoeda = (valor) => {
  if (!valor) return 0;
  if (typeof valor === 'number') return valor;
  // Remove R$, pontos de milhar e troca vírgula por ponto
  const limpo = valor.toString()
    .replace(/R\$\s?/g, '')
    .replace(/\./g, '')
    .replace(',', '.');
  return parseFloat(limpo) || 0;
};

// ============================================================================
// COMPONENTES DE UI
// ============================================================================

const AlertaFonte = ({ metodo }) => {
  const isIA = metodo?.toLowerCase().includes('ia') || metodo?.toLowerCase().includes('claude');
  
  if (isIA) {
    return (
      <div className="bg-amber-50 border-l-4 border-amber-400 p-4 mb-6">
        <div className="flex items-start gap-3">
          <span className="text-2xl">⚠️</span>
          <div>
            <h4 className="font-semibold text-amber-800">Dados extraídos por Inteligência Artificial</h4>
            <p className="text-amber-700 text-sm mt-1">
              A IA pode cometer erros. <strong>Revise cada valor comparando com seu arquivo original</strong> antes de confirmar.
            </p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
      <div className="flex items-start gap-3">
        <span className="text-2xl">✅</span>
        <div>
          <h4 className="font-semibold text-blue-800">Dados extraídos por Parser Local</h4>
          <p className="text-blue-700 text-sm mt-1">
            Extração automática do sistema Domínio. Recomendamos uma revisão rápida para garantir precisão.
          </p>
        </div>
      </div>
    </div>
  );
};

const CampoEditavel = ({ 
  campo, 
  valor, 
  onChange, 
  erro, 
  aviso,
  editando,
  onStartEdit,
  onEndEdit 
}) => {
  const [valorLocal, setValorLocal] = useState(formatarMoeda(valor));
  
  useEffect(() => {
    if (!editando) {
      setValorLocal(formatarMoeda(valor));
    }
  }, [valor, editando]);
  
  const handleFocus = () => {
    onStartEdit();
    // Mostra valor numérico para edição
    setValorLocal(valor ? valor.toString().replace('.', ',') : '');
  };
  
  const handleBlur = () => {
    const novoValor = parseMoeda(valorLocal);
    onChange(novoValor);
    setValorLocal(formatarMoeda(novoValor));
    onEndEdit();
  };
  
  const handleChange = (e) => {
    // Permite apenas números, vírgula e ponto
    const input = e.target.value.replace(/[^\d,.-]/g, '');
    setValorLocal(input);
  };
  
  const temValor = valor !== null && valor !== undefined && valor !== 0 && valor !== '';
  
  return (
    <div className={`
      relative group
      ${erro ? 'bg-red-50' : aviso ? 'bg-amber-50' : temValor ? 'bg-white' : 'bg-gray-50'}
      ${campo.destaque ? 'ring-2 ring-offset-1 ring-blue-200' : ''}
      rounded-lg border ${erro ? 'border-red-300' : aviso ? 'border-amber-300' : 'border-gray-200'}
      transition-all duration-200
      hover:border-blue-400 hover:shadow-sm
    `}>
      <div className="p-3">
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wide flex items-center gap-1">
            {campo.label}
            {campo.obrigatorio && <span className="text-red-500">*</span>}
            {campo.calculado && <span className="text-blue-500 text-xs normal-case">(calculado)</span>}
          </label>
          {campo.dica && (
            <span className="text-xs text-gray-400 hidden group-hover:inline" title={campo.dica}>
              ℹ️
            </span>
          )}
        </div>
        
        <input
          type="text"
          value={valorLocal}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          className={`
            w-full text-lg font-semibold bg-transparent border-none p-0
            focus:outline-none focus:ring-0
            ${temValor ? 'text-gray-900' : 'text-gray-400'}
            ${erro ? 'text-red-700' : ''}
            ${aviso ? 'text-amber-700' : ''}
          `}
          placeholder="R$ 0,00"
        />
        
        {erro && (
          <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
            <span>⚠️</span> {erro}
          </p>
        )}
        {aviso && !erro && (
          <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
            <span>💡</span> {aviso}
          </p>
        )}
      </div>
    </div>
  );
};

const GrupoCampos = ({ grupo, config, dados, erros, avisos, onChange, campoEditando, setCampoEditando }) => {
  const [expandido, setExpandido] = useState(true);
  
  const coresGrupo = {
    blue: 'border-blue-200 bg-blue-50/30',
    green: 'border-green-200 bg-green-50/30',
    red: 'border-red-200 bg-red-50/30',
    purple: 'border-purple-200 bg-purple-50/30',
    orange: 'border-orange-200 bg-orange-50/30',
  };
  
  const coresTitulo = {
    blue: 'text-blue-800 bg-blue-100',
    green: 'text-green-800 bg-green-100',
    red: 'text-red-800 bg-red-100',
    purple: 'text-purple-800 bg-purple-100',
    orange: 'text-orange-800 bg-orange-100',
  };
  
  // Conta campos preenchidos
  const camposPreenchidos = config.campos.filter(c => {
    const valor = dados[c.nome];
    return valor !== null && valor !== undefined && valor !== 0 && valor !== '';
  }).length;
  
  return (
    <div className={`rounded-xl border-2 ${coresGrupo[config.cor]} overflow-hidden`}>
      {/* Header do grupo */}
      <button
        onClick={() => setExpandido(!expandido)}
        className={`w-full flex items-center justify-between p-4 ${coresTitulo[config.cor]} hover:opacity-90 transition-opacity`}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{config.icone}</span>
          <div className="text-left">
            <h3 className="font-bold">{config.titulo}</h3>
            <p className="text-sm opacity-75">{config.descricao}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium">
            {camposPreenchidos}/{config.campos.length} campos
          </span>
          <span className="text-xl">{expandido ? '▼' : '▶'}</span>
        </div>
      </button>
      
      {/* Campos do grupo */}
      {expandido && (
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {config.campos.map(campo => (
            <CampoEditavel
              key={campo.nome}
              campo={campo}
              valor={dados[campo.nome]}
              onChange={(novoValor) => onChange(campo.nome, novoValor)}
              erro={erros[campo.nome]}
              aviso={avisos[campo.nome]}
              editando={campoEditando === campo.nome}
              onStartEdit={() => setCampoEditando(campo.nome)}
              onEndEdit={() => setCampoEditando(null)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const ValidacaoBalanco = ({ dados }) => {
  const ativo = parseMoeda(dados.ativo_total) || 0;
  const passivo = parseMoeda(dados.passivo_circulante) + parseMoeda(dados.passivo_nao_circulante) || 0;
  const pl = parseMoeda(dados.patrimonio_liquido) || 0;
  const resultado = parseMoeda(dados.lucro_liquido) || 0;
  
  // PL Total = PL do grupo 2.3 + Resultado do Exercício
  const plTotal = pl + resultado;
  const ladoDireito = passivo + plTotal;
  
  const diferenca = Math.abs(ativo - ladoDireito);
  const percentualDif = ativo > 0 ? (diferenca / ativo * 100) : 0;
  
  const balanceFecha = percentualDif <= 5;
  
  if (ativo === 0) return null;
  
  return (
    <div className={`rounded-xl p-4 mb-6 ${balanceFecha ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
      <h4 className={`font-bold mb-3 flex items-center gap-2 ${balanceFecha ? 'text-green-800' : 'text-red-800'}`}>
        {balanceFecha ? '✅' : '❌'} Verificação do Balanço
      </h4>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="bg-white rounded-lg p-3">
          <div className="text-gray-500 text-xs uppercase">Ativo Total</div>
          <div className="font-bold text-lg">{formatarMoeda(ativo)}</div>
        </div>
        
        <div className="bg-white rounded-lg p-3">
          <div className="text-gray-500 text-xs uppercase">=</div>
          <div className="font-bold text-lg text-gray-400">deve ser igual a</div>
        </div>
        
        <div className="bg-white rounded-lg p-3">
          <div className="text-gray-500 text-xs uppercase">Passivo + PL Total</div>
          <div className="font-bold text-lg">{formatarMoeda(ladoDireito)}</div>
          <div className="text-xs text-gray-500 mt-1">
            Passivo: {formatarMoeda(passivo)} + PL: {formatarMoeda(pl)} + Resultado: {formatarMoeda(resultado)}
          </div>
        </div>
      </div>
      
      {!balanceFecha && (
        <p className="mt-3 text-sm text-red-700">
          ⚠️ Diferença de {formatarMoeda(diferenca)} ({percentualDif.toFixed(1)}%). 
          Verifique se todos os valores foram extraídos corretamente.
        </p>
      )}
    </div>
  );
};

const ResumoRapido = ({ dados }) => {
  const receita = parseMoeda(dados.receita_bruta) || 0;
  const lucro = parseMoeda(dados.lucro_liquido) || 0;
  const ativo = parseMoeda(dados.ativo_total) || 0;
  const pl = parseMoeda(dados.patrimonio_liquido) || 0;
  
  return (
    <div className="bg-gray-50 rounded-xl p-4 mb-6">
      <h4 className="font-bold text-gray-700 mb-3">📋 Resumo dos Valores Principais</h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="text-xs text-gray-500 uppercase">Receita Bruta</div>
          <div className="font-bold text-blue-600">{formatarMoeda(receita)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase">Resultado</div>
          <div className={`font-bold ${lucro >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatarMoeda(lucro)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase">Ativo Total</div>
          <div className="font-bold text-gray-700">{formatarMoeda(ativo)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase">Patrimônio Líquido</div>
          <div className="font-bold text-purple-600">{formatarMoeda(pl)}</div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================

const RevisaoImportacao = ({ 
  dadosValidacao, 
  empresa, 
  periodo, 
  onConfirmar, 
  onCancelar,
  carregando = false 
}) => {
  // Estado dos dados editáveis
  const [dados, setDados] = useState({});
  const [campoEditando, setCampoEditando] = useState(null);
  const [confirmouRevisao, setConfirmouRevisao] = useState(false);
  
  // Inicializa dados
  useEffect(() => {
    if (dadosValidacao?.dados_validados) {
      setDados(dadosValidacao.dados_validados);
    }
  }, [dadosValidacao]);
  
  // Handler de mudança
  const handleChange = (campo, valor) => {
    setDados(prev => ({
      ...prev,
      [campo]: valor
    }));
  };
  
  // Validações em tempo real
  const { erros, avisos } = useMemo(() => {
    const erros = {};
    const avisos = {};
    
    // Campos obrigatórios
    Object.values(GRUPOS_CAMPOS).forEach(grupo => {
      grupo.campos.forEach(campo => {
        if (campo.obrigatorio) {
          const valor = dados[campo.nome];
          if (!valor || valor === 0) {
            erros[campo.nome] = 'Campo obrigatório';
          }
        }
      });
    });
    
    // Lucro maior que receita
    const receita = parseMoeda(dados.receita_bruta) || 0;
    const lucro = parseMoeda(dados.lucro_liquido) || 0;
    if (lucro > receita && receita > 0) {
      erros.lucro_liquido = 'Lucro maior que receita - verifique os valores';
    }
    
    // AC maior que Ativo Total - apenas aviso (pode acontecer com ANC negativo)
    const ac = parseMoeda(dados.ativo_circulante) || 0;
    const at = parseMoeda(dados.ativo_total) || 0;
    if (ac > at && at > 0) {
      avisos.ativo_circulante = 'Ativo Circulante maior que Ativo Total (possível ANC negativo) - verificar classificação contábil';
    }
    
    // PL maior que Ativo
    const pl = parseMoeda(dados.patrimonio_liquido) || 0;
    if (pl > at && at > 0) {
      avisos.patrimonio_liquido = 'PL maior que Ativo Total - verificar';
    }
    
    // Margem muito alta
    if (receita > 0 && lucro > 0) {
      const margem = (lucro / receita) * 100;
      if (margem > 60) {
        avisos.lucro_liquido = `Margem de ${margem.toFixed(0)}% é incomum - confirme se está correto`;
      }
    }
    
    return { erros, avisos };
  }, [dados]);
  
  // Verifica se pode confirmar
  const temErrosCriticos = Object.keys(erros).some(campo => 
    GRUPOS_CAMPOS.dre.campos.some(c => c.nome === campo && c.obrigatorio) ||
    GRUPOS_CAMPOS.ativo.campos.some(c => c.nome === campo && c.obrigatorio) ||
    GRUPOS_CAMPOS.passivo.campos.some(c => c.nome === campo && c.obrigatorio) ||
    GRUPOS_CAMPOS.patrimonio.campos.some(c => c.nome === campo && c.obrigatorio)
  );
  
  const metodo = dadosValidacao?.metodo_extracao || 'desconhecido';
  const isIA = metodo?.toLowerCase().includes('ia') || metodo?.toLowerCase().includes('claude');
  
  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Revisão de Dados</h2>
            <p className="text-gray-500 mt-1">
              {empresa && <span className="font-medium text-gray-700">{empresa}</span>}
              {periodo && <span className="mx-2">•</span>}
              {periodo && <span>Período: {periodo}</span>}
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {isIA ? (
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-100 text-purple-800 border border-purple-300 font-medium">
                🤖 Extraído por IA
              </span>
            ) : (
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-100 text-blue-800 border border-blue-300 font-medium">
                📄 Parser Domínio
              </span>
            )}
          </div>
        </div>
      </div>
      
      {/* Alerta da fonte */}
      <AlertaFonte metodo={metodo} />
      
      {/* Resumo rápido */}
      <ResumoRapido dados={dados} />
      
      {/* Validação do balanço */}
      <ValidacaoBalanco dados={dados} />
      
      {/* Instruções */}
      <div className="bg-white rounded-xl shadow-sm border p-4 mb-6">
        <h4 className="font-semibold text-gray-800 mb-2">📝 Como revisar:</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Compare cada valor com seu arquivo original (PDF ou Excel)</li>
          <li>• Clique em qualquer campo para editar o valor</li>
          <li>• Campos marcados com <span className="text-red-500 font-bold">*</span> são obrigatórios</li>
          <li>• Campos em destaque são os mais importantes para os indicadores</li>
        </ul>
      </div>
      
      {/* Grupos de campos */}
      <div className="space-y-6">
        {Object.entries(GRUPOS_CAMPOS).map(([key, config]) => (
          <GrupoCampos
            key={key}
            grupo={key}
            config={config}
            dados={dados}
            erros={erros}
            avisos={avisos}
            onChange={handleChange}
            campoEditando={campoEditando}
            setCampoEditando={setCampoEditando}
          />
        ))}
      </div>
      
      {/* Checkbox de confirmação */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mt-6">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={confirmouRevisao}
            onChange={(e) => setConfirmouRevisao(e.target.checked)}
            className="mt-1 w-5 h-5 rounded border-amber-300 text-amber-600 focus:ring-amber-500"
          />
          <div>
            <span className="font-semibold text-amber-800">
              Confirmo que revisei os valores e estão corretos
            </span>
            <p className="text-sm text-amber-700 mt-1">
              Ao confirmar, os indicadores financeiros (ROE, Margem, Liquidez, etc.) serão calculados automaticamente com base nestes valores.
            </p>
          </div>
        </label>
      </div>
      
      {/* Botões de ação */}
      <div className="flex items-center justify-between mt-6 pt-6 border-t">
        <button
          onClick={onCancelar}
          disabled={carregando}
          className="px-6 py-3 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          Cancelar
        </button>
        
        <div className="flex items-center gap-3">
          {temErrosCriticos && (
            <span className="text-sm text-red-600">
              ⚠️ Corrija os erros antes de confirmar
            </span>
          )}
          
          <button
            onClick={() => onConfirmar(dados)}
            disabled={carregando || !confirmouRevisao || temErrosCriticos}
            className={`
              px-8 py-3 rounded-lg font-semibold transition-all
              ${confirmouRevisao && !temErrosCriticos
                ? 'bg-green-600 text-white hover:bg-green-700 shadow-lg hover:shadow-xl'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }
            `}
          >
            {carregando ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Salvando...
              </span>
            ) : (
              '✓ Confirmar e Calcular Indicadores'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RevisaoImportacao;
