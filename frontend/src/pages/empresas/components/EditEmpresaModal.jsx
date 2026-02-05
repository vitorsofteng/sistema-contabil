import React, { useState, useEffect } from 'react';
import { Button, Input, Modal, Select } from '../../../components/ui';
import { useAuth } from '../../../contexts/AuthContext';
import { useToast } from '../../../contexts/ToastContext';

function EditEmpresaModal({ isOpen, onClose, empresa, onSuccess }) {
  const { api } = useAuth();
  const toast = useToast();
  const [form, setForm] = useState({
    razao_social: '',
    nome_fantasia: '',
    cnpj: '',
    regime_tributario: '',
    setor: '',
    email: '',
    telefone: '',
    cidade: '',
    estado: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Atualiza form quando empresa muda
  useEffect(() => {
    if (empresa) {
      setForm({
        razao_social: empresa.razao_social || '',
        nome_fantasia: empresa.nome_fantasia || '',
        cnpj: empresa.cnpj || '',
        regime_tributario: empresa.regime_tributario || '',
        setor: empresa.setor || '',
        email: empresa.email || '',
        telefone: empresa.telefone || '',
        cidade: empresa.cidade || '',
        estado: empresa.estado || ''
      });
    }
  }, [empresa]);

  const regimes = [
    { value: '', label: 'Selecione...' },
    { value: 'Simples Nacional', label: 'Simples Nacional' },
    { value: 'Lucro Presumido', label: 'Lucro Presumido' },
    { value: 'Lucro Real', label: 'Lucro Real' },
    { value: 'MEI', label: 'MEI' }
  ];

  const estados = [
    { value: '', label: 'UF' }, { value: 'AC', label: 'AC' }, { value: 'AL', label: 'AL' },
    { value: 'AP', label: 'AP' }, { value: 'AM', label: 'AM' }, { value: 'BA', label: 'BA' },
    { value: 'CE', label: 'CE' }, { value: 'DF', label: 'DF' }, { value: 'ES', label: 'ES' },
    { value: 'GO', label: 'GO' }, { value: 'MA', label: 'MA' }, { value: 'MT', label: 'MT' },
    { value: 'MS', label: 'MS' }, { value: 'MG', label: 'MG' }, { value: 'PA', label: 'PA' },
    { value: 'PB', label: 'PB' }, { value: 'PR', label: 'PR' }, { value: 'PE', label: 'PE' },
    { value: 'PI', label: 'PI' }, { value: 'RJ', label: 'RJ' }, { value: 'RN', label: 'RN' },
    { value: 'RS', label: 'RS' }, { value: 'RO', label: 'RO' }, { value: 'RR', label: 'RR' },
    { value: 'SC', label: 'SC' }, { value: 'SP', label: 'SP' }, { value: 'SE', label: 'SE' },
    { value: 'TO', label: 'TO' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.razao_social.trim()) {
      setError('Razão Social é obrigatória');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const res = await api(`/empresas/${empresa.id}`, {
        method: 'PUT',
        body: JSON.stringify(form)
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Erro ao atualizar empresa');
      }
      
      toast.success('Empresa atualizada com sucesso!');
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Editar Empresa" size="lg">
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input 
          label="Razão Social *" 
          value={form.razao_social} 
          onChange={e => setForm({...form, razao_social: e.target.value})} 
          required 
        />
        
        <div className="grid grid-cols-2 gap-4">
          <Input 
            label="Nome Fantasia" 
            value={form.nome_fantasia} 
            onChange={e => setForm({...form, nome_fantasia: e.target.value})} 
          />
          <Input 
            label="CNPJ" 
            value={form.cnpj} 
            onChange={e => setForm({...form, cnpj: e.target.value})} 
            placeholder="00.000.000/0000-00" 
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <Select 
            label="Regime Tributário" 
            options={regimes} 
            value={form.regime_tributario} 
            onChange={e => setForm({...form, regime_tributario: e.target.value})} 
          />
          <Input 
            label="Setor/Atividade" 
            value={form.setor} 
            onChange={e => setForm({...form, setor: e.target.value})} 
            placeholder="Ex: Comércio, Serviços..." 
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <Input 
            label="Email" 
            type="email" 
            value={form.email} 
            onChange={e => setForm({...form, email: e.target.value})} 
          />
          <Input 
            label="Telefone" 
            value={form.telefone} 
            onChange={e => setForm({...form, telefone: e.target.value})} 
          />
        </div>
        
        <div className="grid grid-cols-3 gap-4">
          <Input 
            label="Cidade" 
            value={form.cidade} 
            onChange={e => setForm({...form, cidade: e.target.value})} 
            className="col-span-2" 
          />
          <Select 
            label="Estado" 
            options={estados} 
            value={form.estado} 
            onChange={e => setForm({...form, estado: e.target.value})} 
          />
        </div>
        
        <div className="flex justify-end gap-2 pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button type="submit" loading={loading}>Salvar Alterações</Button>
        </div>
      </form>
    </Modal>
  );
}

// ============================================================================
// PAGES - Importação Avançada
// ============================================================================

export default EditEmpresaModal;
