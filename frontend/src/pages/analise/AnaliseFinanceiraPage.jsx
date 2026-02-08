import IndicesLiquidezTab from './IndicesLiquidezTab';
import React, { useState, useEffect } from 'react';
import { AlertTriangle, ArrowLeft, BarChart3, Building2, CheckCircle, FileText, Lightbulb, RefreshCw, Target, TrendingUp } from 'lucide-react';
import { Button, Card, LoadingScreen, Select } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

function AnaliseFinanceiraPage({ empresaId, empresaNome, onBack }) {
  const { api } = useAuth();
  const toast = useToast();
  
  const [loading, setLoading] = useState(true);
  const [analise, setAnalise] = useState(null);
  const [erro, setErro] = useState(null);
  const [abaAtiva, setAbaAtiva] = useState('resumo');
  const [setores, setSetores] = useState([
    { codigo: 'geral', nome: 'Geral' }
  ]);
  const [setorSelecionado, setSetorSelecionado] = useState('geral');
  const [setoresCarregados, setSetoresCarregados] = useState(false);
  
  useEffect(() => {
    loadSetores();
  }, []);
  
  useEffect(() => {
    if (empresaId) {
      loadAnalise();
    }
  }, [empresaId, setorSelecionado]);
  
  const loadAnalise = async () => {
    setLoading(true);
    setErro(null);
    try {
      const res = await api(`/empresas/${empresaId}/analise-financeira?setor=${setorSelecionado}`);
      const data = await res.json();
      
      if (data.dados_suficientes === false) {
        setErro(data.erro || "Dados insuficientes para análise");
        setAnalise(null);
      } else {
        setAnalise(data.analise || null);
      }
    } catch (err) {
      setErro("Erro ao carregar análise financeira");
      console.error(err);
    }
    setLoading(false);
  };
  
  const loadSetores = async () => {
    try {
      const res = await api('/setores');
      const data = await res.json();
      const setoresData = data.setores || [];
      if (setoresData.length > 0) {
        setSetores(setoresData);
      }
      setSetoresCarregados(true);
    } catch (err) {
      console.error('Erro ao carregar setores:', err);
      setSetoresCarregados(true);
    }
  };
  
  const formatMoney = (value) => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };
  
  const formatPct = (value) => {
    if (value === null || value === undefined) return '-';
    return `${value.toFixed(1)}%`;
  };
  
  const getSaudeColor = (saude) => {
    const colors = {
      'otima': 'text-green-600 bg-green-100',
      'boa': 'text-blue-600 bg-blue-100',
      'regular': 'text-yellow-600 bg-yellow-100',
      'ruim': 'text-orange-600 bg-orange-100',
      'critica': 'text-red-600 bg-red-100'
    };
    return colors[saude] || 'text-gray-600 bg-gray-100';
  };
  
  const getPosicaoColor = (posicao) => {
    const colors = {
      'acima_media': 'text-green-600',
      'na_media': 'text-blue-600',
      'abaixo_media': 'text-red-600'
    };
    return colors[posicao] || 'text-gray-600';
  };
  
  if (loading) return <LoadingScreen />;
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-4">
          {onBack && (
            <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-lg">
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Análise Financeira</h1>
            <p className="text-slate-600">{empresaNome}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Select
            value={setorSelecionado}
            onChange={(e) => setSetorSelecionado(e.target.value)}
            className="w-48"
          >
            {(setores || []).map(s => (
              <option key={s.codigo} value={s.codigo}>{s.nome}</option>
            ))}
          </Select>
          <Button onClick={loadAnalise} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Atualizar
          </Button>
        </div>
      </div>
      
      {erro ? (
        <Card className="p-8 text-center">
          <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-800 mb-2">Dados Insuficientes</h3>
          <p className="text-slate-600">{erro}</p>
          <p className="text-sm text-slate-500 mt-2">
            Importe pelo menos 3 meses de dados financeiros para gerar a análise completa.
          </p>
        </Card>
      ) : analise && (
        <>
          {/* PAINEL DE ALERTAS CRÍTICOS */}
          {(() => {
            const indices = analise.indices || {};
            const alertasCriticos = [];
            
            // Verificar indicadores críticos
            if (indices.liquidez_corrente > 0 && indices.liquidez_corrente < 1) {
              alertasCriticos.push({
                tipo: 'INSOLVÊNCIA',
                msg: `Liquidez corrente de ${indices.liquidez_corrente?.toFixed(2) || 0} - empresa não consegue pagar dívidas de curto prazo`,
                icon: '🚨'
              });
            }
            if (indices.patrimonio_liquido < 0) {
              alertasCriticos.push({
                tipo: 'PASSIVO A DESCOBERTO',
                msg: `Patrimônio Líquido negativo de ${formatMoney(indices.patrimonio_liquido)} - prejuízos superaram o capital`,
                icon: '🚨'
              });
            }
            if (indices.endividamento_geral > 80) {
              alertasCriticos.push({
                tipo: 'ENDIVIDAMENTO CRÍTICO',
                msg: `Endividamento de ${indices.endividamento_geral?.toFixed(1)}% - muito acima do limite seguro`,
                icon: '⚠️'
              });
            }
            if (indices.margem_liquida < -10) {
              alertasCriticos.push({
                tipo: 'PREJUÍZO GRAVE',
                msg: `Margem líquida de ${indices.margem_liquida?.toFixed(1)}% - operação dando prejuízo significativo`,
                icon: '🚨'
              });
            }
            if (indices.capital_giro < 0) {
              alertasCriticos.push({
                tipo: 'CAPITAL GIRO NEGATIVO',
                msg: `Capital de giro de ${formatMoney(indices.capital_giro)} - financiando LP com dívidas CP`,
                icon: '🚨'
              });
            }
            if (indices.disponibilidades <= 1000 && indices.passivo_circulante > 10000) {
              alertasCriticos.push({
                tipo: 'CAIXA ZERADO',
                msg: `Disponibilidades de apenas ${formatMoney(indices.disponibilidades)} - sem recursos para operar`,
                icon: '🚨'
              });
            }
            
            if (alertasCriticos.length === 0) return null;
            
            return (
              <Card className="p-4 bg-red-50 border-2 border-red-300 mb-4">
                <div className="flex items-start gap-3">
                  <div className="text-3xl">🚨</div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-red-800 mb-2">
                      EMPRESA EM SITUAÇÃO CRÍTICA - {alertasCriticos.length} ALERTA{alertasCriticos.length > 1 ? 'S' : ''}
                    </h3>
                    <div className="space-y-2">
                      {alertasCriticos.map((alerta, idx) => (
                        <div key={idx} className="flex items-start gap-2 bg-white p-3 rounded-lg border border-red-200">
                          <span className="text-xl">{alerta.icon}</span>
                          <div>
                            <p className="font-bold text-red-700">{alerta.tipo}</p>
                            <p className="text-sm text-red-600">{alerta.msg}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-red-600 mt-3 font-medium">
                      ⚠️ Estes indicadores apontam risco iminente de falência. Ação imediata é necessária!
                    </p>
                  </div>
                </div>
              </Card>
            );
          })()}
          
          {/* Abas */}
          <div className="flex gap-2 border-b border-slate-200 pb-2">
            {[
              { id: 'resumo', label: 'Resumo Executivo', icon: FileText },
              { id: 'dre', label: 'DRE', icon: BarChart3 },
              { id: 'indices', label: 'Índices', icon: TrendingUp },
              { id: 'breakeven', label: 'Break-Even', icon: Target },
              { id: 'projecoes', label: 'Projeções', icon: TrendingUp },
              { id: 'benchmarks', label: 'Benchmarks', icon: Building2 }
            ].map(aba => (
              <button
                key={aba.id}
                onClick={() => setAbaAtiva(aba.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors ${
                  abaAtiva === aba.id 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                <aba.icon className="w-4 h-4" />
                {aba.label}
              </button>
            ))}
          </div>
          
          {/* Conteúdo das Abas */}
          {abaAtiva === 'resumo' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Saúde Financeira */}
              <Card className="p-6">
                <h3 className="font-semibold text-slate-800 mb-4">Saúde Financeira</h3>
                <div className={`text-center py-4 px-6 rounded-lg ${getSaudeColor(analise.indices?.saude_financeira)}`}>
                  <span className="text-2xl font-bold capitalize">
                    {analise.indices?.saude_financeira || 'N/A'}
                  </span>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Margem Líquida</span>
                    <span className="font-medium">{formatPct(analise.indices?.margem_liquida)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Liquidez</span>
                    <span className="font-medium">{analise.indices?.liquidez_corrente?.toFixed(2) || '-'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Capital de Giro</span>
                    <span className="font-medium">{analise.indices?.capital_giro_dias?.toFixed(0)} dias</span>
                  </div>
                </div>
              </Card>
              
              {/* Pontos Fortes */}
              <Card className="p-6">
                <h3 className="font-semibold text-green-700 mb-4 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  Pontos Fortes
                </h3>
                {analise.pontos_fortes?.length > 0 ? (
                  <ul className="space-y-2">
                    {analise.pontos_fortes.map((ponto, idx) => (
                      <li key={idx} className="text-sm text-slate-700 flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        {ponto}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">Nenhum ponto forte identificado</p>
                )}
              </Card>
              
              {/* Pontos de Atenção */}
              <Card className="p-6">
                <h3 className="font-semibold text-red-700 mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  Pontos de Atenção
                </h3>
                {analise.pontos_fracos?.length > 0 ? (
                  <ul className="space-y-2">
                    {analise.pontos_fracos.map((ponto, idx) => (
                      <li key={idx} className="text-sm text-slate-700 flex items-start gap-2">
                        <span className="text-red-500 mt-1">!</span>
                        {ponto}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">Nenhum ponto de atenção</p>
                )}
              </Card>
              
              {/* Recomendações */}
              <Card className="p-6 lg:col-span-3">
                <h3 className="font-semibold text-blue-700 mb-4 flex items-center gap-2">
                  <Lightbulb className="w-5 h-5" />
                  Recomendações
                </h3>
                {analise.recomendacoes?.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {analise.recomendacoes.map((rec, idx) => (
                      <div key={idx} className="bg-blue-50 p-3 rounded-lg text-sm text-blue-800">
                        {rec}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">Sem recomendações no momento</p>
                )}
              </Card>
            </div>
          )}
          
          {abaAtiva === 'dre' && analise.dre && (
            <Card className="p-6">
              <h3 className="font-semibold text-slate-800 mb-4">
                Demonstrativo de Resultado - {analise.dre.periodo}
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <tbody className="divide-y divide-slate-100">
                    <tr className="bg-slate-50">
                      <td className="py-3 px-4 font-semibold">Receita Bruta</td>
                      <td className="py-3 px-4 text-right font-semibold">{formatMoney(analise.dre.receita_bruta)}</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Deduções</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.deducoes_receita || 0))}</td>
                    </tr>
                    <tr className="bg-slate-50">
                      <td className="py-3 px-4 font-semibold">= Receita Líquida</td>
                      <td className="py-3 px-4 text-right font-semibold">{formatMoney(analise.dre.receita_liquida)}</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Custo das Mercadorias</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.custo_produtos_vendidos || 0))}</td>
                    </tr>
                    <tr className="bg-green-50">
                      <td className="py-3 px-4 font-semibold text-green-800">= Lucro Bruto</td>
                      <td className="py-3 px-4 text-right font-semibold text-green-800">
                        {formatMoney(analise.dre.lucro_bruto)}
                        <span className="text-sm ml-2">({formatPct(analise.dre.margem_bruta_pct)})</span>
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Despesas com Pessoal</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.despesas_pessoal || 0))}</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Despesas Administrativas</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.despesas_administrativas || 0))}</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Despesas Comerciais/Outras</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs((analise.dre.despesas_comerciais || 0) + (analise.dre.outras_despesas || 0)))}</td>
                    </tr>
                    {(analise.dre.despesas_financeiras || 0) > 0 && (
                      <tr>
                        <td className="py-3 px-4 text-slate-600 pl-8">(-) Despesas Financeiras</td>
                        <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.despesas_financeiras || 0))}</td>
                      </tr>
                    )}
                    <tr className="bg-blue-50">
                      <td className="py-3 px-4 font-semibold text-blue-800">= Resultado Operacional (EBIT)</td>
                      <td className="py-3 px-4 text-right font-semibold text-blue-800">
                        {formatMoney(analise.dre.lucro_operacional)}
                        <span className="text-sm ml-2">({formatPct(analise.dre.margem_operacional_pct)})</span>
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 text-slate-600 pl-8">(-) Impostos</td>
                      <td className="py-3 px-4 text-right text-red-600">{formatMoney(-Math.abs(analise.dre.impostos || 0))}</td>
                    </tr>
                    <tr className={`${analise.dre.lucro_liquido >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                      <td className="py-4 px-4 font-bold text-lg">= LUCRO LÍQUIDO</td>
                      <td className={`py-4 px-4 text-right font-bold text-lg ${analise.dre.lucro_liquido >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                        {formatMoney(analise.dre.lucro_liquido)}
                        <span className="text-sm ml-2">({formatPct(analise.dre.margem_liquida_pct)})</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              {/* Nota sobre valores acumulados */}
              <p className="text-xs text-slate-400 mt-4 text-center">
                * Valores consolidados do período. Deduções e impostos estimados quando não disponíveis no balancete.
              </p>
            </Card>
          )}
          
          {abaAtiva === 'indices' && analise.indices && (
            <IndicesLiquidezTab analise={analise} formatMoney={formatMoney} formatPct={formatPct} />
          )}
          
          {abaAtiva === 'breakeven' && analise.break_even && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="font-semibold text-slate-800 mb-4">Ponto de Equilíbrio</h3>
                <div className="space-y-4">
                  <div className="text-center p-6 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-600 mb-2">Receita necessária para break-even</p>
                    <div className="text-3xl font-bold text-slate-800">
                      {formatMoney(analise.break_even.ponto_equilibrio_valor)}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">por mês</p>
                  </div>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg text-center">
                      <p className="text-sm text-blue-600 mb-1">Custo Fixo Mensal</p>
                      <p className="text-lg font-bold text-blue-800">{formatMoney(analise.break_even.custo_fixo_mensal)}</p>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg text-center">
                      <p className="text-sm text-purple-600 mb-1">Custo Variável</p>
                      <p className="text-lg font-bold text-purple-800">{formatPct(analise.break_even.custo_variavel_pct)}</p>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-green-50 rounded-lg text-center">
                    <p className="text-sm text-green-600 mb-1">Margem de Contribuição</p>
                    <p className="text-2xl font-bold text-green-800">{formatPct(analise.break_even.margem_contribuicao_pct)}</p>
                  </div>
                </div>
              </Card>
              
              <Card className="p-6">
                <h3 className="font-semibold text-slate-800 mb-4">Situação Atual</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-4 bg-slate-50 rounded-lg">
                    <span className="text-slate-600">Receita Atual (média)</span>
                    <span className="text-xl font-bold">{formatMoney(analise.break_even.receita_media_mensal)}</span>
                  </div>
                  
                  <div className={`p-4 rounded-lg text-center ${(analise.break_even.folga_pct || 0) >= 20 ? 'bg-green-50' : (analise.break_even.folga_pct || 0) >= 0 ? 'bg-yellow-50' : 'bg-red-50'}`}>
                    <p className="text-sm mb-1">Margem de Segurança</p>
                    <p className={`text-3xl font-bold ${(analise.break_even.folga_pct || 0) >= 20 ? 'text-green-700' : (analise.break_even.folga_pct || 0) >= 0 ? 'text-yellow-700' : 'text-red-700'}`}>
                      {(analise.break_even.folga_pct || 0) >= 0 ? '+' : ''}{formatPct(analise.break_even.folga_pct || 0)}
                    </p>
                    <p className="text-sm mt-1">
                      {(analise.break_even.folga_operacional || 0) >= 0 ? 'Folga de ' : 'Déficit de '}
                      {formatMoney(Math.abs(analise.break_even.folga_operacional || 0))}/mês
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <h4 className="font-medium text-slate-700">Metas de Receita</h4>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Para lucro de 10%</span>
                      <span className="font-medium">{formatMoney(analise.break_even.receita_para_lucro_10pct)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Para lucro de 20%</span>
                      <span className="font-medium">{formatMoney(analise.break_even.receita_para_lucro_20pct)}</span>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          )}
          
          {abaAtiva === 'projecoes' && analise.projecoes?.length > 0 && (
            <Card className="p-6">
              <h3 className="font-semibold text-slate-800 mb-4">Projeções para os Próximos 12 Meses</h3>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {['pessimista', 'realista', 'otimista'].map(cenario => {
                  const proj = analise.projecoes.find(p => p.cenario === cenario);
                  const ultimo = proj?.dados_mensais?.[proj?.dados_mensais?.length - 1];
                  const cores = {
                    pessimista: 'border-red-200 bg-red-50',
                    realista: 'border-blue-200 bg-blue-50',
                    otimista: 'border-green-200 bg-green-50'
                  };
                  const textos = {
                    pessimista: 'text-red-800',
                    realista: 'text-blue-800',
                    otimista: 'text-green-800'
                  };
                  
                  return (
                    <div key={cenario} className={`p-4 rounded-lg border-2 ${cores[cenario]}`}>
                      <h4 className={`font-semibold mb-3 capitalize ${textos[cenario]}`}>
                        Cenário {cenario}
                      </h4>
                      {proj && (
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span>Receita Total</span>
                            <span className="font-medium">{formatMoney(proj.receita_total)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Lucro Total</span>
                            <span className={`font-medium ${proj.lucro_total < 0 ? 'text-red-600' : ''}`}>
                              {formatMoney(proj.lucro_total)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Caixa Final</span>
                            <span className={`font-medium ${proj.caixa_final < 0 ? 'text-red-600' : ''}`}>
                              {formatMoney(proj.caixa_final)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Margem Média</span>
                            <span className="font-medium">{formatPct(proj.margem_media)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Taxa Crescimento</span>
                            <span className="font-medium">{proj.taxa_crescimento_receita?.toFixed(1)}%/mês</span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              
              <div className="mt-6 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-100">
                      <th className="py-2 px-3 text-left">Mês</th>
                      <th className="py-2 px-3 text-right" colSpan={2}>Pessimista</th>
                      <th className="py-2 px-3 text-right" colSpan={2}>Realista</th>
                      <th className="py-2 px-3 text-right" colSpan={2}>Otimista</th>
                    </tr>
                    <tr className="bg-slate-50 text-xs text-slate-600">
                      <th></th>
                      <th className="py-1 px-3 text-right">Receita</th>
                      <th className="py-1 px-3 text-right">Lucro</th>
                      <th className="py-1 px-3 text-right">Receita</th>
                      <th className="py-1 px-3 text-right">Lucro</th>
                      <th className="py-1 px-3 text-right">Receita</th>
                      <th className="py-1 px-3 text-right">Lucro</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map(idx => {
                      const projPess = analise.projecoes.find(p => p.cenario === 'pessimista');
                      const projReal = analise.projecoes.find(p => p.cenario === 'realista');
                      const projOtim = analise.projecoes.find(p => p.cenario === 'otimista');
                      
                      const pess = projPess?.dados_mensais?.[idx];
                      const real = projReal?.dados_mensais?.[idx];
                      const otim = projOtim?.dados_mensais?.[idx];
                      
                      if (!pess) return null;
                      
                      return (
                        <tr key={idx} className="border-b">
                          <td className="py-2 px-3">{String(pess.mes).padStart(2, '0')}/{pess.ano}</td>
                          <td className="py-2 px-3 text-right text-red-700">{formatMoney(pess.receita)}</td>
                          <td className={`py-2 px-3 text-right ${pess.lucro < 0 ? 'text-red-600' : ''}`}>{formatMoney(pess.lucro)}</td>
                          <td className="py-2 px-3 text-right text-blue-700">{formatMoney(real?.receita)}</td>
                          <td className={`py-2 px-3 text-right ${(real?.lucro || 0) < 0 ? 'text-red-600' : ''}`}>{formatMoney(real?.lucro)}</td>
                          <td className="py-2 px-3 text-right text-green-700">{formatMoney(otim?.receita)}</td>
                          <td className={`py-2 px-3 text-right ${(otim?.lucro || 0) < 0 ? 'text-red-600' : ''}`}>{formatMoney(otim?.lucro)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
          
          {abaAtiva === 'benchmarks' && analise.benchmarks?.length > 0 && (
            <Card className="p-6">
              <h3 className="font-semibold text-slate-800 mb-4">Comparação com o Setor</h3>
              <div className="space-y-6">
                {analise.benchmarks.map((bench, idx) => (
                  <div key={idx} className="border-b pb-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">{bench.indicador}</span>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        bench.posicao === 'acima' ? 'bg-green-100 text-green-700' :
                        bench.posicao === 'abaixo' ? 'bg-red-100 text-red-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {bench.posicao === 'acima' ? 'Acima da Média' :
                         bench.posicao === 'abaixo' ? 'Abaixo da Média' : 'Na Média'}
                      </span>
                    </div>
                    
                    <div className="relative h-8 bg-slate-100 rounded-full overflow-hidden">
                      {/* Faixa do setor */}
                      <div 
                        className="absolute h-full bg-slate-300 opacity-50"
                        style={{
                          left: `${Math.max(0, (bench.valor_setor_min / Math.max(bench.valor_setor_max, bench.valor_empresa, 1)) * 100)}%`,
                          width: `${((bench.valor_setor_media - bench.valor_setor_min) / Math.max(bench.valor_setor_max, bench.valor_empresa, 1)) * 100}%`
                        }}
                      ></div>
                      
                      {/* Marcador da média do setor */}
                      <div 
                        className="absolute top-0 bottom-0 w-0.5 bg-slate-500"
                        style={{left: `${(bench.valor_setor_media / Math.max(bench.valor_setor_max, bench.valor_empresa, 1) * 100)}%`}}
                      ></div>
                      
                      {/* Valor da empresa */}
                      <div 
                        className={`absolute top-1 bottom-1 w-3 rounded-full ${
                          bench.posicao === 'acima' ? 'bg-green-500' :
                          bench.posicao === 'abaixo' ? 'bg-red-500' : 'bg-blue-500'
                        }`}
                        style={{left: `${Math.min(Math.max((bench.valor_empresa / Math.max(bench.valor_setor_max, bench.valor_empresa, 1) * 100), 2), 98)}%`}}
                      ></div>
                    </div>
                    
                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                      <span>Min: {bench.valor_setor_min?.toFixed(1)}</span>
                      <span>Sua empresa: <strong className={bench.posicao === 'acima' ? 'text-green-600' : bench.posicao === 'abaixo' ? 'text-red-600' : 'text-blue-600'}>{bench.valor_empresa?.toFixed(1)}</strong></span>
                      <span>Média: {bench.valor_setor_media?.toFixed(1)}</span>
                      <span>Max: {bench.valor_setor_max?.toFixed(1)}</span>
                    </div>
                    
                    <p className="text-sm text-slate-600 mt-2">
                      {(bench.diferenca_vs_media || 0) >= 0 ? '+' : ''}{(bench.diferenca_vs_media || 0).toFixed(1)} em relação à média do setor
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

export default AnaliseFinanceiraPage;
