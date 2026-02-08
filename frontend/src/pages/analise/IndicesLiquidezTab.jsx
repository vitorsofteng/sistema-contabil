import React, { useState } from 'react';
import { Card } from '../../components/ui';
import { Header } from '../../components/layout';

function IndicesLiquidezTab({ analise, formatMoney, formatPct }) {
  const [periodoCalculo, setPeriodoCalculo] = useState('mensal');
  const [abaIndices, setAbaIndices] = useState('liquidez');
  const [mesSelecionado, setMesSelecionado] = useState(null);
  
  // Dados do período - usar índices já calculados pelo backend
  const dados = analise?.indices || {};
  const dre = analise?.dre || {};
  const dadosMensais = analise?.dados_mensais || [];
  
  // Período atual dos dados
  const periodoInfo = dados.periodo || dre.periodo || '';
  
  // Extrair meses disponíveis para seleção
  const mesesDisponiveis = dadosMensais.length > 0 
    ? dadosMensais.map(d => ({ 
        label: `${String(d.mes || 1).padStart(2, '0')}/${d.ano}`, 
        ano: d.ano, 
        mes: d.mes,
        dados: d 
      })).sort((a, b) => (b.ano - a.ano) || (b.mes - a.mes))
    : [];
  
  // Último mês disponível
  const ultimoMes = mesesDisponiveis[0] || null;
  const mesAtual = mesSelecionado || ultimoMes;
  
  // Dados do mês selecionado (para modo mensal)
  const dadosMes = mesAtual?.dados || {};
  
  // Calcular valores baseado no período selecionado
  const calcularIndicesPeriodo = () => {
    if (periodoCalculo === 'mensal' && dadosMes) {
      // Usar dados do mês selecionado
      const ac = dadosMes.ativo_circulante || dados.ativo_circulante || 0;
      const pc = dadosMes.passivo_circulante || dados.passivo_circulante || 0;
      const est = dadosMes.estoques || dados.estoques || 0;
      const disp = dadosMes.disponibilidades || dadosMes.caixa || dados.disponibilidades || 0;
      const anc = dadosMes.ativo_nao_circulante || dados.ativo_nao_circulante || 0;
      const pnc = dadosMes.passivo_nao_circulante || dados.passivo_nao_circulante || 0;
      const cr = dadosMes.clientes || dadosMes.contas_receber || dados.contas_receber || 0;
      const forn = dadosMes.fornecedores || dados.fornecedores || 0;
      const pl = dadosMes.patrimonio_liquido || dados.patrimonio_liquido || 0;
      const at = dadosMes.ativo_total || dados.ativo_total || (ac + anc) || 0;
      const realizavelLp = dadosMes.realizavel_lp || 0;
      
      // Dados de DRE do mês
      const receita = dadosMes.receita || dadosMes.receita_bruta || 0;
      const lucro = dadosMes.lucro_liquido || 0;
      const custos = dadosMes.custos || dadosMes.custos_total || 0;
      
      // Margem bruta do mês
      const receitaLiq = receita - (dadosMes.deducoes_receita || receita * 0.10);
      const lucroBruto = receitaLiq - custos;
      const margemBruta = receita > 0 ? (lucroBruto / receita * 100) : (dados.margem_bruta || 0);
      
      // Margem operacional do mês
      const despesas = dadosMes.despesas || dadosMes.despesas_operacionais || 0;
      const folha = dadosMes.folha || dadosMes.despesas_pessoal || 0;
      const lucroOp = lucroBruto - despesas - folha;
      const margemOp = receita > 0 ? (lucroOp / receita * 100) : (dados.margem_operacional || 0);
      
      return {
        ativoCirculante: ac,
        passivoCirculante: pc,
        estoques: est,
        disponibilidades: disp,
        ativoNaoCirculante: anc,
        passivoNaoCirculante: pnc,
        contasReceber: cr,
        fornecedores: forn,
        patrimonioLiquido: pl,
        ativoTotal: at,
        receita,
        lucro,
        // Índices calculados
        liquidezCorrente: pc > 0 ? ac / pc : 0,
        liquidezSeca: pc > 0 ? (ac - est) / pc : 0,
        liquidezImediata: pc > 0 ? disp / pc : 0,
        // Liquidez Geral: usa Realizável LP se disponível, senão apenas AC (conservador)
        liquidezGeral: (pc + pnc) > 0 ? (ac + realizavelLp) / (pc + pnc) : 0,
        liquidezCaixa: pc > 0 ? disp / pc : 0,
        liquidezOperacional: forn > 0 ? (cr + est) / forn : 0,
        liquidezAjustada: pc > 0 ? (disp + cr * 0.7 + est * 0.3) / pc : 0,
        ncg: (cr + est) - forn,
        saldoTesouraria: disp - ((cr + est) - forn),
        capitalGiro: ac - pc,
        // Rentabilidade
        roe: pl > 0 ? (lucro / pl * 100) : 0,
        roa: at > 0 ? (lucro / at * 100) : 0,
        giroAtivo: at > 0 ? receita / at : 0,
        margemBruta: margemBruta,
        margemOperacional: margemOp,
        margemLiquida: receita > 0 ? (lucro / receita * 100) : 0,
      };
    } else {
      // Modo Anual - usar dados do backend (já calcula corretamente com desacumulação)
      // Balanço: usa última posição do ano
      const anoAtual = ultimoMes?.ano || new Date().getFullYear();
      const dadosAno = dadosMensais.filter(d => d.ano === anoAtual);
      
      if (dadosAno.length === 0) {
        // Fallback para dados do backend
        return {
          ativoCirculante: dados.ativo_circulante || 0,
          passivoCirculante: dados.passivo_circulante || 0,
          estoques: dados.estoques || 0,
          disponibilidades: dados.disponibilidades || 0,
          ativoNaoCirculante: dados.ativo_nao_circulante || 0,
          passivoNaoCirculante: dados.passivo_nao_circulante || 0,
          contasReceber: dados.contas_receber || 0,
          fornecedores: dados.fornecedores || 0,
          patrimonioLiquido: dados.patrimonio_liquido || 0,
          ativoTotal: dados.ativo_total || 0,
          receita: 0, lucro: 0,
          liquidezCorrente: dados.liquidez_corrente || 0,
          liquidezSeca: dados.liquidez_seca || 0,
          liquidezImediata: dados.liquidez_imediata || 0,
          liquidezGeral: dados.liquidez_geral || 0,
          liquidezCaixa: dados.liquidez_caixa || 0,
          liquidezOperacional: dados.liquidez_operacional || 0,
          liquidezAjustada: dados.liquidez_ajustada || 0,
          ncg: dados.ncg || 0,
          saldoTesouraria: dados.saldo_tesouraria || 0,
          capitalGiro: dados.capital_giro || 0,
          roe: dados.roe || 0,
          roa: dados.roa || 0,
          giroAtivo: dados.giro_ativo || 0,
          margemBruta: dados.margem_bruta || 0,
          margemOperacional: dados.margem_operacional || 0,
          margemLiquida: dados.margem_liquida || 0,
        };
      }
      
      // Ordenar e pegar último mês para dados de balanço
      const dadosAnoSorted = [...dadosAno].sort((a, b) => (a.mes || 0) - (b.mes || 0));
      const ultimoDadosAno = dadosAnoSorted[dadosAnoSorted.length - 1] || {};
      
      const ac = ultimoDadosAno.ativo_circulante || dados.ativo_circulante || 0;
      const pc = ultimoDadosAno.passivo_circulante || dados.passivo_circulante || 0;
      const est = ultimoDadosAno.estoques || dados.estoques || 0;
      const disp = ultimoDadosAno.disponibilidades || ultimoDadosAno.caixa || dados.disponibilidades || 0;
      const anc = ultimoDadosAno.ativo_nao_circulante || dados.ativo_nao_circulante || 0;
      const pnc = ultimoDadosAno.passivo_nao_circulante || dados.passivo_nao_circulante || 0;
      const cr = ultimoDadosAno.clientes || ultimoDadosAno.contas_receber || dados.contas_receber || 0;
      const forn = ultimoDadosAno.fornecedores || dados.fornecedores || 0;
      const pl = ultimoDadosAno.patrimonio_liquido || dados.patrimonio_liquido || 0;
      const at = ultimoDadosAno.ativo_total || dados.ativo_total || (ac + anc) || 0;
      const realizavelLp = ultimoDadosAno.realizavel_lp || 0;
      
      // ============================================================
      // TOTAIS ANUAIS - TRATAR VALORES ACUMULADOS
      // ============================================================
      // Detectar se dados são acumulados (receitas crescem monotonicamente)
      const receitas = dadosAnoSorted.map(d => d.receita || d.receita_bruta || 0);
      const receitasPositivas = receitas.filter(r => r > 0);
      let acumulados = dadosAnoSorted.some(d => d._valores_acumulados);
      
      if (!acumulados && receitasPositivas.length >= 2) {
        const crescente = receitasPositivas.every((r, i) => i === 0 || r >= receitasPositivas[i-1]);
        if (crescente && receitasPositivas[0] > 0) {
          const crescimento = (receitasPositivas[receitasPositivas.length - 1] - receitasPositivas[0]) / receitasPositivas[0];
          if (crescimento > 0.5) acumulados = true;
        }
      }
      
      let receitaAnual, lucroAnual;
      
      if (acumulados) {
        // Para acumulados: último mês já tem o total do ano
        receitaAnual = ultimoDadosAno.receita || ultimoDadosAno.receita_bruta || 0;
        lucroAnual = ultimoDadosAno.lucro_liquido || 0;
      } else {
        // Para mensais: somar
        receitaAnual = dadosAno.reduce((sum, d) => sum + (d.receita || d.receita_bruta || 0), 0);
        lucroAnual = dadosAno.reduce((sum, d) => sum + (d.lucro_liquido || 0), 0);
      }
      
      return {
        ativoCirculante: ac,
        passivoCirculante: pc,
        estoques: est,
        disponibilidades: disp,
        ativoNaoCirculante: anc,
        passivoNaoCirculante: pnc,
        contasReceber: cr,
        fornecedores: forn,
        patrimonioLiquido: pl,
        ativoTotal: at,
        receita: receitaAnual,
        lucro: lucroAnual,
        // Índices de liquidez (balanço - posição final do ano)
        liquidezCorrente: pc > 0 ? ac / pc : 0,
        liquidezSeca: pc > 0 ? (ac - est) / pc : 0,
        liquidezImediata: pc > 0 ? disp / pc : 0,
        // Liquidez Geral: usa Realizável LP se disponível, senão apenas AC (conservador)
        liquidezGeral: (pc + pnc) > 0 ? (ac + realizavelLp) / (pc + pnc) : 0,
        liquidezCaixa: pc > 0 ? disp / pc : 0,
        liquidezOperacional: forn > 0 ? (cr + est) / forn : 0,
        liquidezAjustada: pc > 0 ? (disp + cr * 0.7 + est * 0.3) / pc : 0,
        ncg: (cr + est) - forn,
        saldoTesouraria: disp - ((cr + est) - forn),
        capitalGiro: ac - pc,
        // Rentabilidade (anualizada, corrigida)
        roe: pl > 0 ? (lucroAnual / pl * 100) : 0,
        roa: at > 0 ? (lucroAnual / at * 100) : 0,
        giroAtivo: at > 0 ? receitaAnual / at : 0,
        margemBruta: dados.margem_bruta || 0,
        margemOperacional: dados.margem_operacional || 0,
        margemLiquida: receitaAnual > 0 ? (lucroAnual / receitaAnual * 100) : 0,
      };
    }
  };
  
  const indicesCalculados = calcularIndicesPeriodo();
  
  // Usar índices calculados ou do backend como fallback
  const liquidezCorrente = indicesCalculados.liquidezCorrente || dados.liquidez_corrente || 0;
  const liquidezSeca = indicesCalculados.liquidezSeca || dados.liquidez_seca || 0;
  const liquidezImediata = indicesCalculados.liquidezImediata || dados.liquidez_imediata || 0;
  const liquidezGeral = indicesCalculados.liquidezGeral || dados.liquidez_geral || 0;
  const liquidezCaixa = indicesCalculados.liquidezCaixa || dados.liquidez_caixa || 0;
  const liquidezOperacional = indicesCalculados.liquidezOperacional || dados.liquidez_operacional || 0;
  const liquidezAjustada = indicesCalculados.liquidezAjustada || dados.liquidez_ajustada || 0;
  const ncg = indicesCalculados.ncg || dados.ncg || 0;
  const saldoTesouraria = indicesCalculados.saldoTesouraria || dados.saldo_tesouraria || 0;
  const capitalGiro = indicesCalculados.capitalGiro || dados.capital_giro || 0;
  
  // Dados para exibição
  const ativoCirculante = indicesCalculados.ativoCirculante;
  const passivoCirculante = indicesCalculados.passivoCirculante;
  const estoques = indicesCalculados.estoques;
  const disponibilidades = indicesCalculados.disponibilidades;
  const contasReceber = indicesCalculados.contasReceber;
  const fornecedores = indicesCalculados.fornecedores;
  
  // Texto do período atual
  const getPeriodoTexto = () => {
    if (periodoCalculo === 'mensal') {
      return mesAtual ? `${String(mesAtual.mes).padStart(2, '0')}/${mesAtual.ano}` : 'Último mês';
    } else {
      const ano = ultimoMes?.ano || new Date().getFullYear();
      return `Ano ${ano}`;
    }
  };
  
  // Função para obter cor do status
  const getStatusColor = (valor, limites) => {
    if (valor >= limites.otimo) return 'text-green-600 bg-green-50 border-green-200';
    if (valor >= limites.bom) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (valor >= limites.regular) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };
  
  const getStatusText = (valor, limites) => {
    if (valor >= limites.otimo) return 'Ótimo';
    if (valor >= limites.bom) return 'Bom';
    if (valor >= limites.regular) return 'Regular';
    return 'Crítico';
  };

  // Card de índice individual
  const IndiceCard = ({ titulo, valor, formula, interpretacao, problemas, limites, unidade = '' }) => {
    const status = getStatusColor(valor, limites);
    const statusText = getStatusText(valor, limites);
    
    return (
      <Card className={`p-5 border-2 ${status}`}>
        <div className="flex justify-between items-start mb-3">
          <h4 className="font-bold text-slate-800">{titulo}</h4>
          <span className={`px-2 py-1 rounded text-xs font-semibold ${status}`}>
            {statusText}
          </span>
        </div>
        
        <div className="text-center my-4">
          <span className="text-4xl font-bold">
            {typeof valor === 'number' ? valor.toFixed(2) : '-'}
          </span>
          <span className="text-lg text-slate-500 ml-1">{unidade}</span>
        </div>
        
        <div className="bg-slate-100 rounded-lg p-3 mb-3">
          <p className="text-xs text-slate-500 mb-1 font-semibold">FÓRMULA:</p>
          <code className="text-xs text-slate-700 block whitespace-pre-wrap">{formula}</code>
        </div>
        
        <div className="mb-3">
          <p className="text-xs text-slate-500 mb-1 font-semibold">📌 INTERPRETAÇÃO:</p>
          <p className="text-sm text-slate-700">{interpretacao}</p>
        </div>
        
        {problemas && (
          <div className="border-t pt-3">
            <p className="text-xs text-amber-600 mb-1 font-semibold">⚠️ ATENÇÃO:</p>
            <p className="text-xs text-slate-600">{problemas}</p>
          </div>
        )}
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header com Toggle e Período */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-lg shadow-sm">
        <div>
          <h3 className="text-lg font-bold text-slate-800">Índices Financeiros</h3>
          <p className="text-sm text-slate-500">
            Período: <span className="font-semibold text-blue-600">{getPeriodoTexto()}</span>
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Seletor de mês (apenas no modo mensal) */}
          {periodoCalculo === 'mensal' && mesesDisponiveis.length > 0 && (
            <select
              value={mesAtual ? `${mesAtual.ano}-${mesAtual.mes}` : ''}
              onChange={(e) => {
                const [ano, mes] = e.target.value.split('-').map(Number);
                const selected = mesesDisponiveis.find(m => m.ano === ano && m.mes === mes);
                setMesSelecionado(selected || null);
              }}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {mesesDisponiveis.map(m => (
                <option key={`${m.ano}-${m.mes}`} value={`${m.ano}-${m.mes}`}>
                  {m.label}
                </option>
              ))}
            </select>
          )}
          
          {/* Toggle Mensal/Anual */}
          <div className="flex items-center gap-2 bg-slate-100 rounded-lg p-1">
            <button
              onClick={() => setPeriodoCalculo('mensal')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                periodoCalculo === 'mensal' 
                  ? 'bg-blue-600 text-white shadow' 
                  : 'text-slate-600 hover:bg-slate-200'
              }`}
            >
              Mensal
            </button>
            <button
              onClick={() => setPeriodoCalculo('anual')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                periodoCalculo === 'anual' 
                  ? 'bg-blue-600 text-white shadow' 
                  : 'text-slate-600 hover:bg-slate-200'
              }`}
            >
              Anual
            </button>
          </div>
        </div>
      </div>

      {/* Sub-abas */}
      <div className="flex gap-2 border-b border-slate-200 pb-2">
        {[
          { id: 'liquidez', label: 'Índices de Liquidez', icon: '💧' },
          { id: 'rentabilidade', label: 'Rentabilidade', icon: '📈' },
          { id: 'estrutura', label: 'Estrutura', icon: '🏗️' },
        ].map(aba => (
          <button
            key={aba.id}
            onClick={() => setAbaIndices(aba.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors text-sm ${
              abaIndices === aba.id 
                ? 'bg-blue-600 text-white' 
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <span>{aba.icon}</span>
            {aba.label}
          </button>
        ))}
      </div>

      {/* ÍNDICES DE LIQUIDEZ */}
      {abaIndices === 'liquidez' && (
        <div className="space-y-6">
          {/* Resumo Rápido */}
          <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-700">{liquidezCorrente.toFixed(2)}</p>
                <p className="text-xs text-slate-600">Liq. Corrente</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-purple-700">{liquidezSeca.toFixed(2)}</p>
                <p className="text-xs text-slate-600">Liq. Seca</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-indigo-700">{liquidezImediata.toFixed(2)}</p>
                <p className="text-xs text-slate-600">Liq. Imediata</p>
              </div>
              <div className="text-center">
                <p className={`text-3xl font-bold ${ncg >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {formatMoney(ncg)}
                </p>
                <p className="text-xs text-slate-600">NCG</p>
              </div>
            </div>
          </Card>

          {/* Grid de Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* 1. Liquidez Corrente */}
            <IndiceCard
              titulo="1. Liquidez Corrente"
              valor={liquidezCorrente}
              formula="Ativo Circulante / Passivo Circulante"
              interpretacao={
                liquidezCorrente >= 1.5 
                  ? "Excelente capacidade de pagar obrigações de curto prazo."
                  : liquidezCorrente >= 1 
                    ? "Consegue pagar obrigações, mas com pouca folga."
                    : "Risco de insolvência no curto prazo!"
              }
              problemas="Pode estar inflado por estoques encalhados ou contas a receber irrecuperáveis."
              limites={{ otimo: 1.5, bom: 1.2, regular: 1.0 }}
            />
            
            {/* 2. Liquidez Seca */}
            <IndiceCard
              titulo="2. Liquidez Seca"
              valor={liquidezSeca}
              formula="(Ativo Circulante − Estoques) / Passivo Circulante"
              interpretacao={
                liquidezSeca >= 1.0 
                  ? "Consegue pagar dívidas sem depender da venda de estoques."
                  : liquidezSeca >= 0.7 
                    ? "Capacidade razoável, mas depende parcialmente de estoques."
                    : "Alta dependência de estoques para honrar compromissos."
              }
              problemas="Ainda pode enganar se houver duplicatas vencidas ou clientes inadimplentes."
              limites={{ otimo: 1.0, bom: 0.8, regular: 0.6 }}
            />
            
            {/* 3. Liquidez Imediata */}
            <IndiceCard
              titulo="3. Liquidez Imediata"
              valor={liquidezImediata}
              formula="Disponibilidades / Passivo Circulante"
              interpretacao={
                liquidezImediata >= 0.3 
                  ? "Boa disponibilidade de caixa para emergências."
                  : liquidezImediata >= 0.1 
                    ? "Disponibilidade adequada para operação normal."
                    : "Baixa disponibilidade - comum em empresas saudáveis."
              }
              problemas="A maioria das empresas saudáveis tem esse índice baixo, e isso não é necessariamente ruim. Dinheiro parado não rende."
              limites={{ otimo: 0.3, bom: 0.15, regular: 0.05 }}
            />
            
            {/* 4. Liquidez Geral */}
            <IndiceCard
              titulo="4. Liquidez Geral"
              valor={liquidezGeral}
              formula="(AC + ANC Realizável LP) / (PC + PNC)"
              interpretacao={
                liquidezGeral >= 1.2 
                  ? "Boa capacidade de pagamento no longo prazo."
                  : liquidezGeral >= 1.0 
                    ? "Capacidade equilibrada de pagamento."
                    : "Atenção: passivos superam ativos realizáveis."
              }
              problemas="Mistura horizontes de tempo. Pode parecer boa, mas esconder problemas sérios de caixa no curto prazo."
              limites={{ otimo: 1.2, bom: 1.0, regular: 0.8 }}
            />
            
            {/* 5. Liquidez Operacional */}
            <IndiceCard
              titulo="5. Liquidez Operacional"
              valor={liquidezOperacional}
              formula="AC Operacional / PC Operacional"
              interpretacao={
                liquidezOperacional >= 1.5 
                  ? "Operação gera recursos suficientes para suas obrigações."
                  : liquidezOperacional >= 1.0 
                    ? "Equilíbrio entre ativos e passivos operacionais."
                    : "Operação não cobre suas obrigações - precisa de financiamento."
              }
              problemas="Exclui aplicações financeiras e empréstimos. Pouco usada, mas muito mais honesta sobre a saúde operacional."
              limites={{ otimo: 1.5, bom: 1.2, regular: 1.0 }}
            />
            
            {/* 6. Liquidez de Caixa (Cash Ratio) */}
            <IndiceCard
              titulo="6. Liquidez de Caixa (Cash Ratio)"
              valor={liquidezCaixa}
              formula="(Caixa + Equivalentes) / Passivo Circulante"
              interpretacao={
                liquidezCaixa >= 0.25 
                  ? "Alta disponibilidade de caixa - conservador."
                  : liquidezCaixa >= 0.1 
                    ? "Caixa suficiente para operação normal."
                    : "Caixa baixo - dependente de recebimentos."
              }
              problemas="Versão ultra conservadora. Muito caixa pode indicar dinheiro mal aproveitado."
              limites={{ otimo: 0.25, bom: 0.15, regular: 0.05 }}
            />
            
            {/* 7. NCG - Necessidade de Capital de Giro */}
            <Card className={`p-5 border-2 ${ncg >= 0 ? 'border-blue-200 bg-blue-50' : 'border-red-200 bg-red-50'}`}>
              <div className="flex justify-between items-start mb-3">
                <h4 className="font-bold text-slate-800">7. NCG - Necessidade de Capital de Giro</h4>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${ncg >= 0 ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'}`}>
                  {ncg >= 0 ? 'Operação Demanda Capital' : 'Operação Gera Capital'}
                </span>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 my-4">
                <div className="text-center p-3 bg-white rounded-lg">
                  <p className="text-2xl font-bold text-slate-800">{formatMoney(ncg)}</p>
                  <p className="text-xs text-slate-500">NCG</p>
                </div>
                <div className="text-center p-3 bg-white rounded-lg">
                  <p className={`text-2xl font-bold ${saldoTesouraria >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    {formatMoney(saldoTesouraria)}
                  </p>
                  <p className="text-xs text-slate-500">Saldo Tesouraria</p>
                </div>
              </div>
              
              <div className="bg-white rounded-lg p-3 mb-3">
                <p className="text-xs text-slate-500 mb-1 font-semibold">FÓRMULAS:</p>
                <code className="text-xs text-slate-700 block">NCG = AC Operacional − PC Operacional</code>
                <code className="text-xs text-slate-700 block mt-1">Saldo Tesouraria = Disponibilidades − NCG</code>
              </div>
              
              <div className="mb-3">
                <p className="text-xs text-slate-500 mb-1 font-semibold">📌 INTERPRETAÇÃO:</p>
                <p className="text-sm text-slate-700">
                  {ncg > 0 
                    ? `A empresa precisa de ${formatMoney(ncg)} de capital de giro para operar.`
                    : `A operação gera ${formatMoney(Math.abs(ncg))} - fornecedores financiam o giro.`
                  }
                  {saldoTesouraria < 0 && " Saldo de tesouraria negativo indica dependência de financiamento!"}
                </p>
              </div>
              
              <div className="border-t pt-3">
                <p className="text-xs text-red-600 font-semibold">⚠️ CRÍTICO:</p>
                <p className="text-xs text-slate-600">Empresas quebram aqui, não na liquidez corrente! Este é o indicador mais realista de saúde financeira.</p>
              </div>
            </Card>
            
            {/* 8. Liquidez Ajustada */}
            <IndiceCard
              titulo="8. Liquidez Ajustada (Análise Avançada)"
              valor={liquidezAjustada}
              formula="(Caixa + 70%×CR + 30%×Estoques) / PC"
              interpretacao={
                liquidezAjustada >= 1.0 
                  ? "Mesmo com descontos conservadores, há boa liquidez."
                  : liquidezAjustada >= 0.7 
                    ? "Liquidez adequada considerando riscos de realização."
                    : "Liquidez preocupante quando ajustada ao risco real."
              }
              problemas="Não é fórmula padrão, mas é a mais inteligente para análise real. Desconta 30% das contas a receber (inadimplência) e 70% dos estoques (obsolescência)."
              limites={{ otimo: 1.0, bom: 0.8, regular: 0.6 }}
            />
          </div>
          
          {/* Legenda */}
          <Card className="p-4 bg-slate-50">
            <h4 className="font-semibold text-slate-700 mb-3">Legenda de Status</h4>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                <span className="text-sm text-slate-600">Ótimo</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                <span className="text-sm text-slate-600">Bom</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                <span className="text-sm text-slate-600">Regular</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500"></span>
                <span className="text-sm text-slate-600">Crítico</span>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-3">
              * Valores calculados para o período: <strong>{getPeriodoTexto()}</strong> ({periodoCalculo === 'mensal' ? 'dados do mês' : 'dados anualizados'})<br/>
              Ativo Circulante: {formatMoney(ativoCirculante)} | 
              Passivo Circulante: {formatMoney(passivoCirculante)} | 
              Estoques: {formatMoney(estoques)} | 
              Disponibilidades: {formatMoney(disponibilidades)}
            </p>
          </Card>
        </div>
      )}

      {/* RENTABILIDADE */}
      {abaIndices === 'rentabilidade' && (
        <div className="space-y-6">
          {/* Header com período */}
          <Card className="p-4 bg-gradient-to-r from-green-50 to-emerald-50">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-bold text-slate-800">Indicadores de Rentabilidade</h4>
                <p className="text-sm text-slate-600">Período: <span className="font-semibold text-green-700">{getPeriodoTexto()}</span></p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-green-700">{formatPct(indicesCalculados.margemLiquida || dados.margem_liquida)}</p>
                <p className="text-xs text-slate-500">Margem Líquida</p>
              </div>
            </div>
          </Card>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Margem Bruta */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">Margem Bruta</h4>
              <div className="text-center my-4">
                <span className="text-4xl font-bold text-green-600">
                  {formatPct(indicesCalculados.margemBruta || dados.margem_bruta)}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-3 mb-3">
                <div className="bg-green-500 h-3 rounded-full transition-all" 
                     style={{width: `${Math.min(indicesCalculados.margemBruta || dados.margem_bruta || 0, 100)}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Lucro Bruto / Receita Líquida × 100
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Quanto sobra da receita após pagar os custos diretos (CMV/CPV).
              </p>
            </Card>
            
            {/* Margem Operacional */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">Margem Operacional (EBIT)</h4>
              <div className="text-center my-4">
                <span className={`text-4xl font-bold ${(indicesCalculados.margemOperacional || dados.margem_operacional || 0) >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                  {formatPct(indicesCalculados.margemOperacional || dados.margem_operacional)}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-3 mb-3">
                <div className="bg-blue-500 h-3 rounded-full transition-all" 
                     style={{width: `${Math.min(Math.max(indicesCalculados.margemOperacional || dados.margem_operacional || 0, 0), 100)}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Lucro Operacional / Receita Líquida × 100
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Eficiência da operação antes de impostos e despesas financeiras.
              </p>
            </Card>
            
            {/* Margem Líquida */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">Margem Líquida</h4>
              <div className="text-center my-4">
                <span className={`text-4xl font-bold ${(indicesCalculados.margemLiquida || dados.margem_liquida || 0) >= 0 ? 'text-purple-600' : 'text-red-600'}`}>
                  {formatPct(indicesCalculados.margemLiquida || dados.margem_liquida)}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-3 mb-3">
                <div className={`h-3 rounded-full transition-all ${(indicesCalculados.margemLiquida || dados.margem_liquida || 0) >= 0 ? 'bg-purple-500' : 'bg-red-500'}`} 
                     style={{width: `${Math.min(Math.max(indicesCalculados.margemLiquida || dados.margem_liquida || 0, 0), 100)}%`}}></div>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Lucro Líquido / Receita Líquida × 100
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Quanto efetivamente sobra para os sócios de cada R$ 100 de vendas.
              </p>
            </Card>
            
            {/* ROE */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">ROE - Retorno sobre PL</h4>
              <div className="text-center my-4">
                <span className={`text-4xl font-bold ${(indicesCalculados.roe || dados.roe || 0) >= 15 ? 'text-green-600' : 'text-orange-600'}`}>
                  {(indicesCalculados.roe || dados.roe || 0) > 1000 ? '>1000%' : formatPct(indicesCalculados.roe || dados.roe)}
                </span>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Lucro Líquido / Patrimônio Líquido × 100
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Rentabilidade do capital próprio investido. Benchmark: &gt; 15% {periodoCalculo === 'anual' ? 'a.a.' : 'mensal (1.25% a.m.)'}
              </p>
            </Card>
            
            {/* ROA */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">ROA - Retorno sobre Ativos</h4>
              <div className="text-center my-4">
                <span className={`text-4xl font-bold ${(indicesCalculados.roa || dados.roa || 0) >= 8 ? 'text-green-600' : 'text-orange-600'}`}>
                  {formatPct(indicesCalculados.roa || dados.roa)}
                </span>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Lucro Líquido / Ativo Total × 100
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Eficiência no uso de todos os ativos. Benchmark: &gt; 8% {periodoCalculo === 'anual' ? 'a.a.' : 'mensal (0.67% a.m.)'}
              </p>
            </Card>
            
            {/* Giro do Ativo */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-2">Giro do Ativo</h4>
              <div className="text-center my-4">
                <span className={`text-4xl font-bold ${(indicesCalculados.giroAtivo || dados.giro_ativo || 0) >= 1 ? 'text-green-600' : 'text-orange-600'}`}>
                  {(indicesCalculados.giroAtivo || dados.giro_ativo || 0).toFixed(2)}x
                </span>
              </div>
              <p className="text-xs text-slate-600">
                <strong>Fórmula:</strong> Receita {periodoCalculo === 'anual' ? 'Anual' : 'Mensal'} / Ativo Total
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Quantas vezes o ativo "gira" em vendas {periodoCalculo === 'anual' ? 'por ano' : 'no mês'}. Mais = melhor uso.
              </p>
            </Card>
          </div>
        </div>
      )}

      {/* ESTRUTURA */}
      {abaIndices === 'estrutura' && (
        <div className="space-y-6">
          {/* Header com período */}
          <Card className="p-4 bg-gradient-to-r from-orange-50 to-amber-50">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-bold text-slate-800">Estrutura de Custos e Despesas</h4>
                <p className="text-sm text-slate-600">Período: <span className="font-semibold text-orange-700">{getPeriodoTexto()}</span></p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-orange-700">{formatMoney(capitalGiro)}</p>
                <p className="text-xs text-slate-500">Capital de Giro</p>
              </div>
            </div>
          </Card>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Estrutura de Custos */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-4">Estrutura de Custos</h4>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Custos (CMV/CPV)</span>
                    <span className="font-semibold">{formatPct(dados.peso_custos)}</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className="bg-orange-500 h-2 rounded-full" style={{width: `${Math.min(dados.peso_custos || 0, 100)}%`}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Despesas com Pessoal</span>
                    <span className={`font-semibold ${(dados.peso_folha || 0) > 35 ? 'text-red-600' : ''}`}>
                      {formatPct(dados.peso_folha)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className={`h-2 rounded-full ${(dados.peso_folha || 0) > 35 ? 'bg-red-500' : 'bg-blue-500'}`} 
                         style={{width: `${Math.min(dados.peso_folha || 0, 100)}%`}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Impostos</span>
                    <span className="font-semibold">{formatPct(dados.peso_impostos)}</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className="bg-red-500 h-2 rounded-full" style={{width: `${Math.min(dados.peso_impostos || 0, 100)}%`}}></div>
                  </div>
                </div>
              </div>
            </Card>
            
            {/* Indicadores Adicionais */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-4">Indicadores de Eficiência</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm text-slate-600">Produtividade da Folha</span>
                  <span className="font-bold text-lg">{(dados.produtividade_folha || 0).toFixed(1)}x</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm text-slate-600">Capital de Giro (dias)</span>
                  <span className="font-bold text-lg">{(dados.capital_giro_dias || 0).toFixed(0)} dias</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm text-slate-600">Variação de Receita</span>
                  <span className={`font-bold text-lg ${(dados.variacao_receita || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {(dados.variacao_receita || 0) >= 0 ? '+' : ''}{formatPct(dados.variacao_receita)}
                  </span>
                </div>
              </div>
            </Card>
            
            {/* Endividamento */}
            <Card className="p-5">
              <h4 className="font-bold text-slate-800 mb-4">Endividamento</h4>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Endividamento Geral</span>
                    <span className={`font-semibold ${(dados.endividamento_geral || 0) > 70 ? 'text-red-600' : (dados.endividamento_geral || 0) > 50 ? 'text-yellow-600' : 'text-green-600'}`}>
                      {formatPct(dados.endividamento_geral)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className={`h-2 rounded-full ${(dados.endividamento_geral || 0) > 70 ? 'bg-red-500' : (dados.endividamento_geral || 0) > 50 ? 'bg-yellow-500' : 'bg-green-500'}`} 
                         style={{width: `${Math.min(dados.endividamento_geral || 0, 100)}%`}}></div>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Passivo Total / Ativo Total (ideal: &lt; 50%)</p>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Composição Endividamento</span>
                    <span className="font-semibold">{formatPct(dados.composicao_endividamento)}</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className="bg-purple-500 h-2 rounded-full" style={{width: `${Math.min(dados.composicao_endividamento || 0, 100)}%`}}></div>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">PC / Passivo Total (% das dívidas no curto prazo)</p>
                </div>
                {(dados.endividamento_pl || 0) > 0 && (
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Endividamento s/ PL</span>
                      <span className={`font-semibold ${(dados.endividamento_pl || 0) > 150 ? 'text-red-600' : 'text-slate-700'}`}>
                        {formatPct(dados.endividamento_pl)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Passivo Total / Patrimônio Líquido</p>
                  </div>
                )}
              </div>
            </Card>
            
            {/* Saúde Geral */}
            <Card className="p-5 md:col-span-2">
              <h4 className="font-bold text-slate-800 mb-4">Diagnóstico Geral - {getPeriodoTexto()}</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className={`text-center py-6 rounded-lg ${
                  dados.saude_financeira === 'otima' ? 'bg-green-100 text-green-800' :
                  dados.saude_financeira === 'boa' ? 'bg-blue-100 text-blue-800' :
                  dados.saude_financeira === 'regular' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  <span className="text-3xl font-bold capitalize">{dados.saude_financeira || 'N/A'}</span>
                  <p className="text-sm mt-2 opacity-75">
                    {dados.saude_financeira === 'otima' ? 'Empresa em excelente situação financeira' :
                     dados.saude_financeira === 'boa' ? 'Boa saúde financeira com pontos de melhoria' :
                     dados.saude_financeira === 'regular' ? 'Situação estável, mas requer atenção' :
                     'Situação crítica - ação imediata necessária'}
                  </p>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600 mb-2">Score de Saúde</p>
                  <div className="flex items-center gap-3">
                    <div className="text-4xl font-bold text-slate-800">{dados.score_saude || 0}</div>
                    <div className="flex-1">
                      <div className="w-full bg-slate-200 rounded-full h-3">
                        <div className={`h-3 rounded-full ${
                          (dados.score_saude || 0) >= 80 ? 'bg-green-500' :
                          (dados.score_saude || 0) >= 60 ? 'bg-blue-500' :
                          (dados.score_saude || 0) >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                        }`} style={{width: `${dados.score_saude || 0}%`}}></div>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">de 100 pontos</p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

export default IndicesLiquidezTab;
