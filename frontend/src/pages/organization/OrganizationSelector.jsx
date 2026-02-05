import React, { useState } from 'react';
import { Building2, CheckCircle, ChevronDown, Loader2, Plus } from 'lucide-react';
import { useOrganization } from '../../contexts/OrganizationContext';

function OrganizationSelector() {
  const { organizations, currentOrg, switchOrganization, createOrganization } = useOrganization();
  const [open, setOpen] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [creating, setCreating] = useState(false);

  if (!organizations || organizations.length === 0) {
    return null;
  }

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    
    setCreating(true);
    try {
      await createOrganization({ nome: newOrgName });
      setNewOrgName('');
      setShowCreate(false);
    } catch (err) {
      alert('Erro ao criar organização');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors"
      >
        <Building2 className="w-4 h-4 text-slate-600" />
        <span className="text-sm font-medium text-slate-700 max-w-[150px] truncate">
          {currentOrg?.nome || 'Selecionar'}
        </span>
        <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg shadow-lg border border-slate-200 z-50">
          <div className="p-2 border-b border-slate-100">
            <p className="text-xs text-slate-500 font-medium px-2">ORGANIZAÇÕES</p>
          </div>
          
          <div className="max-h-60 overflow-y-auto">
            {organizations.map(org => (
              <button
                key={org.id}
                onClick={() => {
                  switchOrganization(org);
                  setOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-3 py-2 hover:bg-slate-50 transition-colors ${
                  currentOrg?.id === org.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  currentOrg?.id === org.id ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'
                }`}>
                  {org.nome.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-slate-800">{org.nome}</p>
                  <p className="text-xs text-slate-500">{org.papel || 'Membro'}</p>
                </div>
                {currentOrg?.id === org.id && (
                  <CheckCircle className="w-4 h-4 text-blue-600" />
                )}
              </button>
            ))}
          </div>

          <div className="p-2 border-t border-slate-100">
            {!showCreate ? (
              <button
                onClick={() => setShowCreate(true)}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                Nova Organização
              </button>
            ) : (
              <form onSubmit={handleCreate} className="flex gap-2">
                <input
                  type="text"
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                  placeholder="Nome da organização"
                  className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={creating}
                  className="px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Criar'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default OrganizationSelector;
