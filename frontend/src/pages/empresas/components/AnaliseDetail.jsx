import React from 'react';
import { AlertTriangle, CheckCircle, Minus, TrendingDown, TrendingUp } from 'lucide-react';
import { Badge, Card } from '../../../components/ui';
import { formatarMoeda } from '../../../utils/formatters';

function AnaliseDetail({ analise }) {
  const resultado = analise.resultado_completo || analise.resultado || {};
  
  // Novo formato (analyzer profissional)
  const indicadores = resultado.indicadores || {};
  const insights = resultado.insights || analise.insights || [];
  const tendencias = resultado.tendencias || {};
  const projecoes = resultado.projecoes || {};
  const recomendacoes = resultado.recomendacoes || [];
  const alertasCriticos = resultado.alertas_criticos || [];
  const resumo = resultado.resumo || '';
  const score = resultado.score || analise.score || 50;
  const status = resultado.status || analise.status || 'Regular';
  
  // Formato antigo (compatibilidade)
  const tendencia = resultado.tendencia || {};
  const caixa = resultado.risco_caixa || {};
  const anomalias = resultado.anomalias || {};
  const prob = resultado.probabilidades || {};

  const formatarMoeda = (valor) => {
    if (!valor && valor !== 0) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  };

  // Verificar se é novo formato
  const isNovoFormato = Object.keys(indicadores).length > 0;
  
  if (isNovoFormato) {
    // NOVO LAYOUT - Analyzer Profissional
    return (
      <div className="space-y-6">
        {/* Resumo Executivo */}
        {resumo && (
          <Card className="p-4 bg-slate-50">
            <h3 className="font-semibold text-slate-900 mb-2">Resumo Executivo</h3>
            <p className="text-slate-700">{resumo}</p>
          </Card>
        )}

        {/* Score e Status */}
        <div className="grid grid-cols-2 gap-4">
          <Card className="p-6 text-center">
            <div className={`text-5xl font-bold mb-2 ${
              score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {score}
            </div>
            <p className="text-slate-600">Score de Saúde</p>
            <Badge className={`mt-2 ${
              status === 'Excelente' ? 'bg-green-100 text-green-800' :
              status === 'Bom' ? 'bg-blue-100 text-blue-800' :
              status === 'Regular' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>{status}</Badge>
          </Card>

          <Card className="p-4">
            <h4 className="font-semibold text-slate-900 mb-3">Tendências</h4>
            <div className="space-y-2">
              {Object.entries(tendencias).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm text-slate-600 capitalize">{key}</span>
                  <div className="flex items-center gap-2">
                    {val.direcao === 'alta' && <TrendingUp className="w-4 h-4 text-green-600" />}
                    {val.direcao === 'baixa' && <TrendingDown className="w-4 h-4 text-red-600" />}
                    {val.direcao === 'estavel' && <Minus className="w-4 h-4 text-gray-600" />}
                    <span className={`font-medium ${
                      val.direcao === 'alta' ? 'text-green-600' : 
                      val.direcao === 'baixa' ? 'text-red-600' : 'text-gray-600'
                    }`}>
                      {val.variacao > 0 ? '+' : ''}{val.variacao}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Indicadores Principais */}
        <Card className="p-4">
          <h3 className="font-semibold text-slate-900 mb-4">Indicadores Financeiros</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {indicadores.liquidez_corrente !== undefined && (
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <p className={`text-2xl font-bold ${
                  indicadores.liquidez_corrente >= 1.5 ? 'text-green-600' :
                  indicadores.liquidez_corrente >= 1 ? 'text-yellow-600' : 'text-red-600'
                }`}>{indicadores.liquidez_corrente}</p>
                <p className="text-xs text-slate-500">Liquidez Corrente</p>
              </div>
            )}
            {indicadores.margem_liquida !== undefined && (
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <p className={`text-2xl font-bold ${
                  indicadores.margem_liquida >= 15 ? 'text-green-600' :
                  indicadores.margem_liquida >= 5 ? 'text-yellow-600' : 'text-red-600'
                }`}>{indicadores.margem_liquida}%</p>
                <p className="text-xs text-slate-500">Margem Líquida</p>
              </div>
            )}
            {indicadores.margem_bruta !== undefined && (
              <div className="text-center p-3 bg-emerald-50 rounded-lg">
                <p className="text-2xl font-bold text-emerald-600">{indicadores.margem_bruta}%</p>
                <p className="text-xs text-slate-500">Margem Bruta</p>
              </div>
            )}
            {indicadores.roe !== undefined && (
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">
                  {indicadores.roe > 1000 ? '>1000' : indicadores.roe}%
                </p>
                <p className="text-xs text-slate-500">ROE</p>
              </div>
            )}
            {indicadores.roa !== undefined && (
              <div className="text-center p-3 bg-indigo-50 rounded-lg">
                <p className="text-2xl font-bold text-indigo-600">{indicadores.roa}%</p>
                <p className="text-xs text-slate-500">ROA</p>
              </div>
            )}
            {indicadores.carga_tributaria !== undefined && (
              <div className="text-center p-3 bg-orange-50 rounded-lg">
                <p className={`text-2xl font-bold ${
                  indicadores.carga_tributaria > 25 ? 'text-red-600' : 'text-orange-600'
                }`}>{indicadores.carga_tributaria}%</p>
                <p className="text-xs text-slate-500">Carga Tributária</p>
              </div>
            )}
            {indicadores.endividamento_geral !== undefined && (
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <p className={`text-2xl font-bold ${
                  indicadores.endividamento_geral > 70 ? 'text-red-600' : 'text-slate-600'
                }`}>{indicadores.endividamento_geral}%</p>
                <p className="text-xs text-slate-500">Endividamento</p>
              </div>
            )}
            {indicadores.giro_ativo !== undefined && (
              <div className="text-center p-3 bg-cyan-50 rounded-lg">
                <p className="text-2xl font-bold text-cyan-600">{indicadores.giro_ativo}x</p>
                <p className="text-xs text-slate-500">Giro do Ativo</p>
              </div>
            )}
            {indicadores.ebitda !== undefined && indicadores.ebitda > 0 && (
              <div className="text-center p-3 bg-teal-50 rounded-lg">
                <p className="text-2xl font-bold text-teal-600">{formatarMoeda(indicadores.ebitda)}</p>
                <p className="text-xs text-slate-500">EBITDA</p>
              </div>
            )}
            {indicadores.margem_ebitda !== undefined && (
              <div className="text-center p-3 bg-slate-100 rounded-lg">
                <p className="text-2xl font-bold text-slate-700">{indicadores.margem_ebitda}%</p>
                <p className="text-xs text-slate-500">Margem EBITDA</p>
              </div>
            )}
          </div>
        </Card>

        {/* Alertas Críticos */}
        {alertasCriticos.length > 0 && (
          <Card className="p-4 bg-red-50 border-red-200">
            <h3 className="font-semibold text-red-900 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Alertas Críticos ({alertasCriticos.length})
            </h3>
            <div className="space-y-2">
              {alertasCriticos.map((alerta, i) => (
                <div key={i} className="p-3 bg-white rounded-lg border border-red-200">
                  <p className="font-medium text-red-800">{alerta.titulo}</p>
                  <p className="text-sm text-red-700">{alerta.descricao}</p>
                  {alerta.recomendacao && (
                    <p className="text-sm text-red-600 mt-1 italic">→ {alerta.recomendacao}</p>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Insights */}
        {insights.length > 0 && (
          <Card className="p-4">
            <h3 className="font-semibold text-slate-900 mb-3">Insights ({insights.length})</h3>
            <div className="space-y-3">
              {insights.filter(i => i.severidade !== 'alta').slice(0, 5).map((insight, i) => (
                <div key={i} className={`p-3 rounded-lg border ${
                  insight.tipo === 'positivo' ? 'bg-green-50 border-green-200' :
                  insight.tipo === 'atencao' ? 'bg-yellow-50 border-yellow-200' :
                  'bg-blue-50 border-blue-200'
                }`}>
                  <div className="flex items-start gap-2">
                    {insight.tipo === 'positivo' && <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />}
                    {insight.tipo === 'atencao' && <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />}
                    {insight.tipo === 'alerta' && <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />}
                    <div>
                      <p className="font-medium text-slate-800">{insight.titulo}</p>
                      <p className="text-sm text-slate-600">{insight.descricao}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Projeções */}
        {Object.keys(projecoes).length > 0 && (
          <Card className="p-4">
            <h3 className="font-semibold text-slate-900 mb-3">Projeções</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {projecoes.receita_proximos_12m && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-slate-600">Receita (12 meses)</p>
                  <p className="text-xl font-bold text-blue-600">{formatarMoeda(projecoes.receita_proximos_12m)}</p>
                </div>
              )}
              {projecoes.lucro_proximos_12m && (
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-sm text-slate-600">Lucro (12 meses)</p>
                  <p className="text-xl font-bold text-green-600">{formatarMoeda(projecoes.lucro_proximos_12m)}</p>
                </div>
              )}
              {projecoes.impostos_proximos_12m && (
                <div className="p-3 bg-orange-50 rounded-lg">
                  <p className="text-sm text-slate-600">Impostos (12 meses)</p>
                  <p className="text-xl font-bold text-orange-600">{formatarMoeda(projecoes.impostos_proximos_12m)}</p>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Recomendações Priorizadas */}
        {recomendacoes.length > 0 && (
          <Card className="p-4 bg-blue-50 border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-3">Recomendações Prioritárias</h3>
            <div className="space-y-2">
              {recomendacoes.slice(0, 5).map((rec, i) => (
                <div key={i} className="flex items-start gap-3 p-2 bg-white rounded">
                  <span className={`px-2 py-1 text-xs font-bold rounded ${
                    rec.prioridade === 1 ? 'bg-red-100 text-red-800' :
                    rec.prioridade === 2 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>P{rec.prioridade}</span>
                  <div>
                    <p className="font-medium text-slate-800">{rec.titulo}</p>
                    <p className="text-sm text-slate-600">{rec.acao}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    );
  }
  
  // LAYOUT ANTIGO - Compatibilidade
  return (
    <div className="space-y-6">
      <Card className="p-4">
        <h3 className="font-semibold text-slate-900 mb-4">Composição do Score</h3>
        <div className="grid grid-cols-5 gap-4 text-center">
          {[{ label: 'Tendência', value: analise.score_tendencia, max: 25 },
            { label: 'Margem', value: analise.score_margem, max: 25 },
            { label: 'Caixa', value: analise.score_caixa, max: 25 },
            { label: 'Estabilidade', value: analise.score_estabilidade, max: 15 },
            { label: 'Anomalias', value: analise.score_anomalias, max: 10 }].map(item => (
            <div key={item.label}>
              <div className="text-2xl font-bold text-slate-900">{item.value?.toFixed(1) || 0}</div>
              <div className="text-xs text-slate-500">de {item.max}</div>
              <div className="text-sm font-medium text-slate-700 mt-1">{item.label}</div>
            </div>
          ))}
        </div>
      </Card>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            {tendencia.direcao === 'up' && <TrendingUp className="w-5 h-5 text-emerald-600" />}
            {tendencia.direcao === 'down' && <TrendingDown className="w-5 h-5 text-red-600" />}
            {tendencia.direcao === 'stable' && <Minus className="w-5 h-5 text-amber-600" />}
            <h4 className="font-semibold text-slate-900">Tendência</h4>
          </div>
          <p className="text-lg font-bold text-slate-900">{tendencia.tendencia || '—'}</p>
          <p className="text-sm text-slate-500">Taxa: {tendencia.taxa_mensal}%/mês</p>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className={`w-5 h-5 ${caixa.nivel === 'Crítico' ? 'text-red-600' : caixa.nivel === 'Alto' ? 'text-amber-600' : 'text-emerald-600'}`} />
            <h4 className="font-semibold text-slate-900">Risco de Caixa</h4>
          </div>
          <p className="text-lg font-bold text-slate-900">{caixa.nivel || '—'}</p>
          <p className="text-sm text-slate-500">Runway: {caixa.runway_p10}-{caixa.runway_p90} meses</p>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className={`w-5 h-5 ${anomalias.total > 0 ? 'text-amber-600' : 'text-emerald-600'}`} />
            <h4 className="font-semibold text-slate-900">Anomalias</h4>
          </div>
          <p className="text-lg font-bold text-slate-900">{anomalias.total || 0} detectadas</p>
          <p className="text-sm text-slate-500">Normalidade: {anomalias.score_normalidade_geral?.toFixed(0)}/100</p>
        </Card>
        
        <Card className="p-4">
          <h4 className="font-semibold text-slate-900 mb-3">Probabilidades</h4>
          <div className="space-y-2">
            {[['Prejuízo', prob.prob_prejuizo], ['Problemas Caixa', prob.prob_quebra], ['Imposto Inesperado', prob.prob_imposto_inesperado]].map(([label, value]) => (
              <div key={label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-600">{label}</span>
                  <span className="font-medium">{value?.toFixed(0) || 0}%</span>
                </div>
                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${value >= 50 ? 'bg-red-500' : value >= 25 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${Math.min(100, value || 0)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
      
      {analise.insights?.length > 0 && (
        <Card className="p-4">
          <h4 className="font-semibold text-slate-900 mb-3">Insights</h4>
          <ul className="space-y-2">{analise.insights.map((insight, i) => <li key={i} className="text-sm text-slate-700">{typeof insight === 'string' ? insight : insight.descricao}</li>)}</ul>
        </Card>
      )}
      
      <Card className="p-4 bg-blue-50 border-blue-200">
        <h4 className="font-semibold text-blue-900 mb-2">Recomendação Principal</h4>
        <p className="text-blue-800">{analise.recomendacao_principal}</p>
      </Card>
    </div>
  );
}

export default AnaliseDetail;
