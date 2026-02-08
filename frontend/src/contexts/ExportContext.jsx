import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { useToast } from './ToastContext';

const ExportContext = createContext(null);

export function useExport() {
  return useContext(ExportContext);
}

export function ExportProvider({ children }) {
  const { api } = useAuth();
  const toast = useToast();
  const [exportacoes, setExportacoes] = useState([]);
  const [panelOpen, setPanelOpen] = useState(false);
  const pollingRef = useRef(null);
  const hasPendingRef = useRef(false);

  // Buscar exportações do backend
  const carregarExportacoes = useCallback(async () => {
    try {
      const res = await api('/exportacoes');
      if (res.ok) {
        const data = await res.json();
        const lista = data.exportacoes || [];
        setExportacoes(lista);
        
        // Verificar se alguma ficou pronta
        const pendingBefore = hasPendingRef.current;
        const hasPending = lista.some(e => e.status === 'pendente' || e.status === 'processando');
        hasPendingRef.current = hasPending;
        
        // Notificar quando uma exportação completou
        if (pendingBefore && !hasPending) {
          const concluidas = lista.filter(e => e.status === 'concluido');
          if (concluidas.length > 0) {
            toast.success('Exportação concluída! Abra o painel para baixar.');
          }
        }
        
        return hasPending;
      }
    } catch (err) {
      // Silently fail
    }
    return false;
  }, [api, toast]);

  // Polling: verifica a cada 3s se tem exportações pendentes
  useEffect(() => {
    const poll = async () => {
      const hasPending = await carregarExportacoes();
      if (hasPending) {
        pollingRef.current = setTimeout(poll, 3000);
      } else {
        pollingRef.current = setTimeout(poll, 15000); // polling lento quando não tem nada
      }
    };
    poll();
    return () => { if (pollingRef.current) clearTimeout(pollingRef.current); };
  }, [carregarExportacoes]);

  // Agendar nova exportação
  const agendarExportacao = useCallback(async (empresaId, tipo, empresaNome) => {
    try {
      const res = await api('/exportacoes', {
        method: 'POST',
        body: JSON.stringify({ empresa_id: empresaId, tipo })
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`${empresaNome}: exportação agendada`);
        hasPendingRef.current = true;
        await carregarExportacoes();
        // Forçar polling rápido
        if (pollingRef.current) clearTimeout(pollingRef.current);
        pollingRef.current = setTimeout(() => carregarExportacoes(), 2000);
        return data;
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Erro ao agendar exportação');
      }
    } catch (err) {
      toast.error('Erro de conexão');
    }
    return null;
  }, [api, toast, carregarExportacoes]);

  // Baixar exportação concluída
  const baixarExportacao = useCallback(async (exportacao) => {
    try {
      const res = await api(`/exportacoes/${exportacao.id}/download`);
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const ext = exportacao.tipo.includes('excel') ? 'xlsx' : exportacao.tipo === 'pptx' ? 'pptx' : 'pdf';
        const prefix = exportacao.tipo === 'pdf_parecer' ? 'parecer' : 'relatorio';
        a.download = `${prefix}_${exportacao.empresa_nome || 'empresa'}.${ext}`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        toast.error('Erro ao baixar arquivo');
      }
    } catch (err) {
      toast.error('Erro de conexão');
    }
  }, [api, toast]);

  // Remover exportação da lista
  const removerExportacao = useCallback(async (id) => {
    try {
      await api(`/exportacoes/${id}`, { method: 'DELETE' });
      setExportacoes(prev => prev.filter(e => e.id !== id));
    } catch (err) {
      // Silently fail
    }
  }, [api]);

  // Limpar concluídas
  const limparConcluidas = useCallback(async () => {
    const concluidas = exportacoes.filter(e => e.status === 'concluido' || e.status === 'erro');
    for (const exp of concluidas) {
      await removerExportacao(exp.id);
    }
  }, [exportacoes, removerExportacao]);

  const pendingCount = exportacoes.filter(e => e.status === 'pendente' || e.status === 'processando').length;
  const readyCount = exportacoes.filter(e => e.status === 'concluido').length;

  return (
    <ExportContext.Provider value={{
      exportacoes,
      panelOpen,
      setPanelOpen,
      agendarExportacao,
      baixarExportacao,
      removerExportacao,
      limparConcluidas,
      pendingCount,
      readyCount,
    }}>
      {children}
    </ExportContext.Provider>
  );
}
