import React, { useState } from 'react';
import { 
  AlertTriangle, ArrowDown, ArrowUp, Calendar, CheckCircle, ChevronDown, ChevronUp, 
  Clock, DollarSign, Edit, FileText, Minus, Percent, PiggyBank, Scale, 
  ShieldAlert, TrendingUp, Trash2, Upload, Wallet
} from 'lucide-react';
import { Area, AreaChart, ResponsiveContainer, Tooltip } from 'recharts';
import { Button, Card } from '../../../components/ui';
import { formatarMoeda, formatarMoedaCurta } from '../../../utils/formatters';

// ─── Helpers ──────────────────────────────────────────────
const MESES = ['', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

function safe(val) { return (val != null && !isNaN(val)) ? val : 0; }

function pct(atual, anterior) {
  if (!anterior || anterior === 0 || atual == null) return null;
  return ((atual - anterior) / Math.abs(anterior)) * 100;
}

function getAnoMes(r) {
  if (r.ano && r.mes) return { ano: r.ano, mes: r.mes };
  if (r.competencia) {
    const parts = r.competencia.split('-');
    return { ano: parseInt(parts[0]), mes: parseInt(parts[1]) };
  }
  return { ano: 0, mes: 0 };
}

function periodoLabel(r) {
  if (!r) return '—';
  const { ano, mes } = getAnoMes(r);
  if (!ano || !mes) return '—';
  return `${MESES[mes]}/${ano}`;
}

function diasDesde(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return null;
  const now = new Date();
  return Math.floor((now - d) / (1000 * 60 * 60 * 24));
}

function getRec(r) { return safe(r.receita_bruta) || safe(r.receita) || 0; }
function getCustos(r) { return safe(r.custos) || safe(r.custos_total) || 0; }
function getDesp(r) { return safe(r.despesas_operacionais) || safe(r.despesas) || 0; }
function getImp(r) { return safe(r.impostos) || 0; }
function getCaixa(r) { return safe(r.saldo_caixa) || safe(r.caixa) || 0; }
function getLucro(r) { 
  if (r.lucro_liquido != null && r.lucro_liquido !== 0) return r.lucro_liquido;
  return getRec(r) - getCustos(r) - getDesp(r) - getImp(r); 
}
function getMargem(r) {
  if (r.margem_liquida != null) return r.margem_liquida;
  const rec = getRec(r);
  if (rec === 0) return 0;
  return (getLucro(r) / rec) * 100;
}

function calcLiquidez(r) {
  const ac = safe(r.ativo_circulante);
  const pc = safe(r.passivo_circulante);
  if (!ac || !pc || pc === 0) return null;
  return ac / pc;
}

function calcEndividamento(r) {
  const at = safe(r.ativo_total);
  const pt = safe(r.passivo_total);
  if (!at || at === 0) return null;
  if (!pt) {
    const pc = safe(r.passivo_circulante);
    const pnc = safe(r.passivo_nao_circulante);
    if (!pc && !pnc) return null;
    return ((pc + pnc) / at) * 100;
  }
  return (pt / at) * 100;
}

// ─── StatusBar ────────────────────────────────────────────

function StatusBar({ registros, ultimaAnalise }) {
  const ultimo = registros[0];
  const temScore = ultimaAnalise && ultimaAnalise.score != null && ultimaAnalise.score > 0;
  const score = temScore ? ultimaAnalise.score : null;
  const status = ultimaAnalise?.status;
  
  let bgClass = 'bg-slate-50 border-slate-200';
  let dotClass = 'bg-slate-400';
  if (temScore) {
    if (score >= 70) { bgClass = 'bg-emerald-50 border-emerald-200'; dotClass = 'bg-emerald-500'; }
    else if (score >= 40) { bgClass = 'bg-amber-50 border-amber-200'; dotClass = 'bg-amber-500'; }
    else { bgClass = 'bg-red-50 border-red-200'; dotClass = 'bg-red-500'; }
  }

  const ultimoPeriodo = ultimo ? periodoLabel(ultimo) : null;
  const diasAtualizado = ultimo?.updated_at ? diasDesde(ultimo.updated_at) : null;

  return (
    <div className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border ${bgClass} flex-wrap`}>
      <span className={`w-2.5 h-2.5 rounded-full ${dotClass} flex-shrink-0`} />
      {temScore && (
        <>
          <span className="font-bold text-slate-900">{score}</span>
          <span className="text-sm text-slate-600">{status}</span>
          <span className="text-slate-300">|</span>
        </>
      )}
      {ultimoPeriodo ? (
        <>
          <span className="text-sm text-slate-600">Dados até <strong>{ultimoPeriodo}</strong></span>
          {registros.length > 0 && (
            <>
              <span className="text-slate-300">|</span>
              <span className="text-sm text-slate-500">{registros.length} {registros.length === 1 ? 'mês' : 'meses'}</span>
            </>
          )}
          {diasAtualizado != null && (
            <>
              <span className="text-slate-300 hidden sm:inline">|</span>
              <span className="text-xs text-slate-400 hidden sm:inline">
                Atualizado {diasAtualizado === 0 ? 'hoje' : `há ${diasAtualizado}d`}
              </span>
            </>
          )}
        </>
      ) : (
        <span className="text-sm text-slate-500">Nenhum dado importado</span>
      )}
      {!temScore && registros.length >= 1 && registros.length < 3 && (
        <>
          <span className="text-slate-300">|</span>
          <span className="text-xs text-slate-400">Análise disponível a partir de 3 meses</span>
        </>
      )}
    </div>
  );
}

// ─── KPI Card + Grid ──────────────────────────────────────

function KpiCard({ label, valorFormatado, variacao, icon: Icon, invertido = false }) {
  const temVariacao = variacao != null && isFinite(variacao);
  const positivo = temVariacao ? (invertido ? variacao < 0 : variacao > 0) : null;
  const negativo = temVariacao ? (invertido ? variacao > 0 : variacao < 0) : null;

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3.5 hover:shadow-sm transition-shadow">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</span>
        <Icon className="w-4 h-4 text-slate-400" />
      </div>
      <div className="text-lg font-bold text-slate-900 leading-tight">{valorFormatado}</div>
      {temVariacao ? (
        <div className={`flex items-center gap-1 mt-1 text-xs font-medium ${
          positivo ? 'text-emerald-600' : negativo ? 'text-red-500' : 'text-slate-400'
        }`}>
          {variacao > 0.05 ? <ArrowUp className="w-3 h-3" /> : variacao < -0.05 ? <ArrowDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
          <span>{variacao > 0 ? '+' : ''}{variacao.toFixed(1)}%</span>
          <span className="text-slate-400 font-normal">vs mês ant.</span>
        </div>
      ) : (
        <div className="text-xs text-slate-300 mt-1">—</div>
      )}
    </div>
  );
}

function KpiGrid({ registros }) {
  const atual = registros[0];
  const anterior = registros.length >= 2 ? registros[1] : null;
  if (!atual) return null;

  const recAtual = getRec(atual);
  const lucroAtual = getLucro(atual);
  const margemAtual = getMargem(atual);
  const caixaAtual = getCaixa(atual);
  const liqAtual = calcLiquidez(atual);
  const endivAtual = calcEndividamento(atual);

  const recAnt = anterior ? getRec(anterior) : null;
  const lucroAnt = anterior ? getLucro(anterior) : null;
  const margemAnt = anterior ? getMargem(anterior) : null;
  const caixaAnt = anterior ? getCaixa(anterior) : null;
  const liqAnt = anterior ? calcLiquidez(anterior) : null;
  const endivAnt = anterior ? calcEndividamento(anterior) : null;

  const kpis = [
    { label: 'Receita', valorFormatado: formatarMoedaCurta(recAtual), variacao: recAnt ? pct(recAtual, recAnt) : null, icon: DollarSign },
    { label: 'Lucro Líquido', valorFormatado: formatarMoedaCurta(lucroAtual), variacao: lucroAnt != null ? pct(lucroAtual, lucroAnt) : null, icon: TrendingUp },
    { label: 'Margem Líquida', valorFormatado: `${margemAtual.toFixed(1)}%`, variacao: margemAnt != null ? (margemAtual - margemAnt) : null, icon: Percent },
    { label: 'Caixa', valorFormatado: formatarMoedaCurta(caixaAtual), variacao: caixaAnt ? pct(caixaAtual, caixaAnt) : null, icon: Wallet },
    { label: 'Liquidez Corrente', valorFormatado: liqAtual != null ? liqAtual.toFixed(2) : '—', variacao: (liqAtual != null && liqAnt != null) ? pct(liqAtual, liqAnt) : null, icon: Scale },
    { label: 'Endividamento', valorFormatado: endivAtual != null ? `${endivAtual.toFixed(1)}%` : '—', variacao: (endivAtual != null && endivAnt != null) ? (endivAtual - endivAnt) : null, icon: ShieldAlert, invertido: true },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {kpis.map(kpi => <KpiCard key={kpi.label} {...kpi} />)}
    </div>
  );
}

// ─── Sparkline ────────────────────────────────────────────

function SparklineReceita({ registros }) {
  if (registros.length < 2) return null;

  const dados = [...registros]
    .slice(0, 12)
    .reverse()
    .map(r => {
      const { ano, mes } = getAnoMes(r);
      return {
        mes: `${MESES[mes] || mes}/${String(ano).slice(2)}`,
        receita: getRec(r),
      };
    });

  const total = dados.reduce((s, d) => s + d.receita, 0);

  return (
    <Card className="p-4 h-full">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-slate-700">Receita Mensal</h3>
        <span className="text-xs text-slate-400">{dados.length} meses</span>
      </div>
      <div className="h-28">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={dados} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
            <defs>
              <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <Tooltip 
              formatter={(val) => formatarMoeda(val)}
              labelStyle={{ fontSize: 12, color: '#64748b' }}
              contentStyle={{ fontSize: 13, borderRadius: 8, border: '1px solid #e2e8f0' }}
            />
            <Area 
              type="monotone" 
              dataKey="receita" 
              stroke="#3b82f6" 
              strokeWidth={2}
              fill="url(#sparkGrad)" 
              name="Receita"
              dot={false}
              activeDot={{ r: 4, fill: '#3b82f6', stroke: '#fff', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="text-xs text-slate-500 mt-1">
        Acumulado no período: <span className="font-semibold text-slate-700">{formatarMoeda(total)}</span>
      </div>
    </Card>
  );
}

// ─── Alertas Ativos ───────────────────────────────────────

function AlertasAtivos({ alertas }) {
  if (!alertas || alertas.length === 0) {
    return (
      <Card className="p-4 h-full flex items-center justify-center">
        <div className="flex items-center gap-2.5">
          <CheckCircle className="w-5 h-5 text-emerald-400" />
          <span className="text-sm text-emerald-700 font-medium">Nenhum alerta ativo</span>
        </div>
      </Card>
    );
  }

  const sevIcons = {
    critico: <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />,
    atencao: <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />,
    info: <Clock className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />,
  };
  const sevBg = {
    critico: 'bg-red-50 border-red-100',
    atencao: 'bg-amber-50 border-amber-100',
    info: 'bg-blue-50 border-blue-100',
  };

  const top3 = alertas.slice(0, 3);

  return (
    <Card className="p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          Alertas Ativos
          <span className="text-xs bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded-full">{alertas.length}</span>
        </h3>
      </div>
      <div className="space-y-2">
        {top3.map((a, i) => (
          <div key={a.id || i} className={`flex items-start gap-2.5 p-2.5 rounded-lg border ${sevBg[a.severidade] || sevBg.info}`}>
            {sevIcons[a.severidade] || sevIcons.info}
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-800 leading-tight">{a.titulo}</p>
              {a.mensagem && (
                <p className="text-xs text-slate-600 mt-0.5 line-clamp-1">{a.mensagem}</p>
              )}
            </div>
          </div>
        ))}
        {alertas.length > 3 && (
          <p className="text-xs text-slate-400 text-center pt-1">+{alertas.length - 3} alerta{alertas.length - 3 > 1 ? 's' : ''}</p>
        )}
      </div>
    </Card>
  );
}

// ─── Status dos Dados ─────────────────────────────────────

function StatusDados({ registros, onNavigate }) {
  const ultimo = registros[0];
  
  if (!ultimo) {
    return (
      <Card className="p-4 flex flex-col items-center justify-center text-center h-full">
        <Upload className="w-8 h-8 text-slate-300 mb-2" />
        <p className="text-sm font-medium text-slate-700 mb-1">Sem dados importados</p>
        <p className="text-xs text-slate-400 mb-3">Importe o primeiro mês para começar</p>
        <Button size="sm" onClick={() => onNavigate('importacao')}>
          <Upload className="w-3.5 h-3.5" /> Ir para Importação
        </Button>
      </Card>
    );
  }

  const { ano, mes } = getAnoMes(ultimo);
  let proxMes = mes + 1;
  let proxAno = ano;
  if (proxMes > 12) { proxMes = 1; proxAno++; }
  const proxLabel = `${MESES[proxMes]}/${proxAno}`;

  const agora = new Date();
  const mesPosterior = proxMes + 1 > 12 ? 1 : proxMes + 1;
  const anoPosterior = proxMes + 1 > 12 ? proxAno + 1 : proxAno;
  const limiteAtraso = new Date(anoPosterior, mesPosterior - 1, 20);
  const atrasado = agora > limiteAtraso;

  return (
    <Card className="p-4">
      <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2 mb-3">
        <Calendar className="w-4 h-4 text-slate-400" />
        Status dos Dados
      </h3>
      <div className="space-y-2.5">
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-500">Último importado</span>
          <span className="text-sm font-semibold text-slate-800">{periodoLabel(ultimo)}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-500">Próximo esperado</span>
          <span className={`text-sm font-semibold ${atrasado ? 'text-red-600' : 'text-slate-600'}`}>
            {proxLabel} {atrasado && '⚠️'}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-500">Status</span>
          {atrasado ? (
            <span className="text-xs font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded-full">Pendente</span>
          ) : (
            <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">Em dia</span>
          )}
        </div>
      </div>
      <Button size="sm" variant="secondary" className="w-full mt-3" onClick={() => onNavigate('importacao')}>
        <Upload className="w-3.5 h-3.5" /> Ir para Importação
      </Button>
    </Card>
  );
}

// ─── Próxima Ação ─────────────────────────────────────────

function ProximaAcao({ registros, alertas, ultimaAnalise, onNavigate }) {
  let acao = null;
  let icone = null;
  let corFundo = 'bg-blue-50 border-blue-200';
  let corTexto = 'text-blue-800';
  let corIcone = 'text-blue-500';
  let onClick = null;

  if (registros.length === 0) {
    acao = { titulo: 'Importar dados', descricao: 'Importe o primeiro mês de dados financeiros para começar a análise.' };
    icone = <Upload className="w-5 h-5" />;
    onClick = () => onNavigate('importacao');
  } else if (alertas?.some(a => a.severidade === 'critico')) {
    const critico = alertas.find(a => a.severidade === 'critico');
    acao = { titulo: critico.titulo, descricao: critico.mensagem || 'Ação urgente necessária.' };
    icone = <AlertTriangle className="w-5 h-5" />;
    corFundo = 'bg-red-50 border-red-200'; corTexto = 'text-red-800'; corIcone = 'text-red-500';
  } else if (ultimaAnalise?.score && ultimaAnalise.score < 40) {
    acao = { titulo: 'Revisar situação financeira', descricao: 'Score abaixo de 40 — recomendado revisar custos e fluxo de caixa com o cliente.' };
    icone = <ShieldAlert className="w-5 h-5" />;
    corFundo = 'bg-amber-50 border-amber-200'; corTexto = 'text-amber-800'; corIcone = 'text-amber-500';
  } else if (registros.length >= 3) {
    const margens = registros.slice(0, 3).map(r => getMargem(r));
    if (margens[0] < margens[1] && margens[1] < margens[2]) {
      acao = { titulo: 'Margem em queda', descricao: `Margem líquida caiu de ${margens[2].toFixed(1)}% para ${margens[0].toFixed(1)}% nos últimos 3 meses.` };
      icone = <TrendingUp className="w-5 h-5 rotate-180" />;
      corFundo = 'bg-amber-50 border-amber-200'; corTexto = 'text-amber-800'; corIcone = 'text-amber-500';
    }
  }

  if (!acao) {
    return (
      <Card className="p-4 flex flex-col items-center justify-center text-center h-full bg-emerald-50 border-emerald-200">
        <CheckCircle className="w-8 h-8 text-emerald-400 mb-2" />
        <p className="text-sm font-semibold text-emerald-700">Empresa em dia</p>
        <p className="text-xs text-emerald-600 mt-0.5">Nenhuma ação necessária no momento</p>
      </Card>
    );
  }

  const Wrapper = onClick ? 'button' : 'div';

  return (
    <Card className={`p-4 ${corFundo} ${onClick ? 'cursor-pointer hover:shadow-sm transition-shadow' : ''}`} onClick={onClick}>
      <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2 mb-3">
        <FileText className="w-4 h-4 text-slate-400" />
        Próxima Ação
      </h3>
      <div className="flex items-start gap-3">
        <div className={`${corIcone} mt-0.5`}>{icone}</div>
        <div>
          <p className={`text-sm font-semibold ${corTexto}`}>{acao.titulo}</p>
          <p className={`text-xs mt-0.5 ${corTexto} opacity-80`}>{acao.descricao}</p>
        </div>
      </div>
    </Card>
  );
}

// ─── Info Cadastral (colapsável) ──────────────────────────

function InfoEmpresa({ empresa, onEdit, onDelete }) {
  const [aberto, setAberto] = useState(false);

  const campos = [
    ['Nome Fantasia', empresa.nome_fantasia],
    ['CNPJ', empresa.cnpj],
    ['Regime Tributário', empresa.regime_tributario],
    ['Setor', empresa.setor],
    ['Cidade/UF', [empresa.cidade, empresa.estado].filter(Boolean).join('/') || null],
    ['Email', empresa.email],
    ['Telefone', empresa.telefone],
    ['Contato', empresa.contato_nome],
  ].filter(([, v]) => v && String(v).trim());

  return (
    <Card className="p-4">
      <button onClick={() => setAberto(!aberto)} className="flex items-center justify-between w-full text-left">
        <h3 className="text-sm font-semibold text-slate-700">Informações Cadastrais</h3>
        {aberto ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>
      {aberto && (
        <div className="mt-3 pt-3 border-t border-slate-100">
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
            {campos.map(([k, v]) => (
              <div key={k} className="flex justify-between sm:flex-col">
                <dt className="text-xs text-slate-400">{k}</dt>
                <dd className="text-sm font-medium text-slate-700">{v || '—'}</dd>
              </div>
            ))}
          </dl>
          {empresa.observacoes && (
            <div className="mt-3 pt-2 border-t border-slate-100">
              <dt className="text-xs text-slate-400 mb-1">Observações</dt>
              <dd className="text-sm text-slate-600">{empresa.observacoes}</dd>
            </div>
          )}
          <div className="flex items-center gap-2 mt-4 pt-3 border-t border-slate-100">
            <Button variant="ghost" size="sm" onClick={onEdit}>
              <Edit className="w-3.5 h-3.5" /> Editar
            </Button>
            <Button variant="ghost" size="sm" onClick={onDelete} className="text-red-600 hover:text-red-700 hover:bg-red-50">
              <Trash2 className="w-3.5 h-3.5" /> Excluir
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}

// ─── Main Component ───────────────────────────────────────

function VisaoGeralTab({ empresa, registros, ultimaAnalise, alertas, onEdit, onDelete, onNavigate }) {
  if (!registros || registros.length === 0) {
    return (
      <div className="space-y-4">
        <StatusBar registros={[]} ultimaAnalise={null} />
        <Card className="p-10 text-center">
          <PiggyBank className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-slate-700 mb-1">Nenhum dado financeiro</h3>
          <p className="text-sm text-slate-500 mb-4">Importe o primeiro mês para ver indicadores, gráficos e alertas aqui.</p>
          <Button onClick={() => onNavigate('importacao')}>
            <Upload className="w-4 h-4" /> Ir para Importação
          </Button>
        </Card>
        <InfoEmpresa empresa={empresa} onEdit={onEdit} onDelete={onDelete} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <StatusBar registros={registros} ultimaAnalise={ultimaAnalise} />
      <KpiGrid registros={registros} />

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          {registros.length >= 2 ? (
            <SparklineReceita registros={registros} />
          ) : (
            <Card className="p-4 h-full flex items-center justify-center">
              <p className="text-sm text-slate-400">Gráfico disponível a partir de 2 meses</p>
            </Card>
          )}
        </div>
        <div className="lg:col-span-2">
          <AlertasAtivos alertas={alertas} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <StatusDados registros={registros} onNavigate={onNavigate} />
        <ProximaAcao registros={registros} alertas={alertas} ultimaAnalise={ultimaAnalise} onNavigate={onNavigate} />
      </div>

      <InfoEmpresa empresa={empresa} onEdit={onEdit} onDelete={onDelete} />
    </div>
  );
}

export default VisaoGeralTab;
