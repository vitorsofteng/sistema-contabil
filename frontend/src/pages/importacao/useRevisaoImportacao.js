/**
 * Hooks e funções para integração da Revisão de Importação
 * =========================================================
 */

import { useState, useCallback } from 'react';
import { API_URL } from '../../config/api';

/**
 * Hook para gerenciar o fluxo de revisão de importação
 */
export function useRevisaoImportacao(apiCall) {
  const [dadosRevisao, setDadosRevisao] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState(null);
  const [etapa, setEtapa] = useState('idle'); // idle, carregando, revisao, salvando, sucesso, erro
  
  /**
   * Processa arquivo e obtém dados validados para revisão
   */
  const processarParaRevisao = useCallback(async (file, empresaId, forcarIA = false) => {
    setCarregando(true);
    setErro(null);
    setEtapa('carregando');
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('forcar_ia', forcarIA.toString());
      
      const response = await fetch(`${API_URL}/api/empresas/${empresaId}/importar/preview-validado`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Erro ao processar arquivo');
      }
      
      if (!data.sucesso) {
        throw new Error(data.erro || 'Falha na extração dos dados');
      }
      
      setDadosRevisao({
        ...data,
        arquivo: file.name
      });
      setEtapa('revisao');
      
      return data;
      
    } catch (err) {
      setErro(err.message);
      setEtapa('erro');
      throw err;
    } finally {
      setCarregando(false);
    }
  }, []);
  
  /**
   * Confirma e salva os dados revisados
   */
  const confirmarDados = useCallback(async (empresaId, dadosEditados, ano, mes) => {
    setCarregando(true);
    setEtapa('salvando');
    
    try {
      const response = await fetch(`${API_URL}/api/empresas/${empresaId}/importar/confirmar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          dados: dadosEditados,
          ano: ano,
          mes: mes
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Erro ao salvar dados');
      }
      
      setEtapa('sucesso');
      return data;
      
    } catch (err) {
      setErro(err.message);
      setEtapa('erro');
      throw err;
    } finally {
      setCarregando(false);
    }
  }, []);
  
  /**
   * Reseta o estado para nova importação
   */
  const resetar = useCallback(() => {
    setDadosRevisao(null);
    setCarregando(false);
    setErro(null);
    setEtapa('idle');
  }, []);
  
  return {
    dadosRevisao,
    carregando,
    erro,
    etapa,
    processarParaRevisao,
    confirmarDados,
    resetar
  };
}

/**
 * Formata dados para exibição
 */
export function formatarValor(valor, tipo = 'moeda') {
  if (valor === null || valor === undefined) return '-';
  
  if (tipo === 'moeda') {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor);
  }
  
  if (tipo === 'percentual') {
    return `${Number(valor).toFixed(1)}%`;
  }
  
  if (tipo === 'numero') {
    return new Intl.NumberFormat('pt-BR').format(valor);
  }
  
  return valor;
}

/**
 * Calcula indicadores a partir dos dados
 */
export function calcularIndicadores(dados) {
  const receita = parseFloat(dados.receita_bruta) || 0;
  const lucro = parseFloat(dados.lucro_liquido) || 0;
  const pl = parseFloat(dados.patrimonio_liquido) || 0;
  const ac = parseFloat(dados.ativo_circulante) || 0;
  const pc = parseFloat(dados.passivo_circulante) || 0;
  const impostos = parseFloat(dados.impostos) || parseFloat(dados.deducoes_receita) || 0;
  
  return {
    margem_liquida: receita > 0 ? (lucro / receita) * 100 : 0,
    roe: pl > 0 ? (lucro / pl) * 100 : 0,
    liquidez_corrente: pc > 0 ? ac / pc : 0,
    carga_tributaria: receita > 0 ? (impostos / receita) * 100 : 0
  };
}

/**
 * Determina status do indicador (bom, atencao, ruim)
 */
export function statusIndicador(nome, valor) {
  const limites = {
    margem_liquida: { bom: [5, 70], atencao: [-10, 100] },
    roe: { bom: [10, 100], atencao: [-20, 200] },
    liquidez_corrente: { bom: [1, 3], atencao: [0.5, 5] },
    carga_tributaria: { bom: [5, 30], atencao: [3, 50] }
  };
  
  const limite = limites[nome];
  if (!limite) return 'neutro';
  
  if (valor >= limite.bom[0] && valor <= limite.bom[1]) {
    return 'bom';
  }
  if (valor >= limite.atencao[0] && valor <= limite.atencao[1]) {
    return 'atencao';
  }
  return 'ruim';
}

export default useRevisaoImportacao;
