import React, { useState } from 'react';
import { Button, Input, Modal } from '../../../components/ui';
import { useAuth } from '../../../contexts/AuthContext';
import { useToast } from '../../../contexts/ToastContext';

function RegistroModal({ isOpen, onClose, empresaId, onSuccess }) {
  const { api } = useAuth();
  const toast = useToast();
  const [form, setForm] = useState({ competencia: '', receita_bruta: '', custos: '', despesas_operacionais: '', folha_pagamento: '', impostos: '', saldo_caixa: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = {
        competencia: form.competencia,
        receita_bruta: parseFloat(form.receita_bruta) || 0,
        custos: parseFloat(form.custos) || 0,
        despesas_operacionais: parseFloat(form.despesas_operacionais) || 0,
        folha_pagamento: parseFloat(form.folha_pagamento) || 0,
        impostos: parseFloat(form.impostos) || 0,
        saldo_caixa: parseFloat(form.saldo_caixa) || 0
      };
      const res = await api(`/empresas/${empresaId}/dados`, { method: 'POST', body: JSON.stringify(data) });
      if (!res.ok) throw new Error((await res.json()).detail || 'Erro ao salvar');
      toast.success('Registro adicionado com sucesso!');
      onSuccess();
      onClose();
      setForm({ competencia: '', receita_bruta: '', custos: '', despesas_operacionais: '', folha_pagamento: '', impostos: '', saldo_caixa: '' });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Adicionar Registro Mensal" size="md">
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Competência (AAAA-MM)" value={form.competencia} onChange={e => setForm({...form, competencia: e.target.value})} placeholder="2024-01" pattern="\d{4}-\d{2}" required />
        <div className="grid grid-cols-2 gap-4">
          <Input label="Receita Bruta" type="number" step="0.01" value={form.receita_bruta} onChange={e => setForm({...form, receita_bruta: e.target.value})} required />
          <Input label="Custos" type="number" step="0.01" value={form.custos} onChange={e => setForm({...form, custos: e.target.value})} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Despesas" type="number" step="0.01" value={form.despesas_operacionais} onChange={e => setForm({...form, despesas_operacionais: e.target.value})} />
          <Input label="Folha" type="number" step="0.01" value={form.folha_pagamento} onChange={e => setForm({...form, folha_pagamento: e.target.value})} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Impostos" type="number" step="0.01" value={form.impostos} onChange={e => setForm({...form, impostos: e.target.value})} />
          <Input label="Saldo Caixa" type="number" step="0.01" value={form.saldo_caixa} onChange={e => setForm({...form, saldo_caixa: e.target.value})} />
        </div>
        <div className="flex justify-end gap-2 pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button type="submit" loading={loading}>Salvar</Button>
        </div>
      </form>
    </Modal>
  );
}

export default RegistroModal;
