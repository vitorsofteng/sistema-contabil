import React, { useState, useEffect } from 'react';
import { Building2, Loader2, Plus } from 'lucide-react';
import { Badge, Button, Card, Input, LoadingScreen, Modal, Select } from '../../components/ui';
import { Header } from '../../components/layout';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import { useOrganization } from '../../contexts/OrganizationContext';

function TeamMembersPage() {
  const { api } = useAuth();
  const { currentOrg } = useOrganization();
  const toast = useToast();
  const [members, setMembers] = useState([]);
  const [papeis, setPapeis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [invitePapel, setInvitePapel] = useState('');
  const [inviting, setInviting] = useState(false);

  useEffect(() => {
    if (currentOrg) {
      loadMembers();
      loadPapeis();
    }
  }, [currentOrg]);

  const loadMembers = async () => {
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/membros`);
      if (res.ok) {
        const data = await res.json();
        setMembers(data.membros || []);
      }
    } catch (err) {
      toast.error('Erro ao carregar membros');
    } finally {
      setLoading(false);
    }
  };

  const loadPapeis = async () => {
    try {
      const res = await api('/papeis');
      if (res.ok) {
        const data = await res.json();
        setPapeis(data.papeis || []);
      }
    } catch (err) {
      console.error('Erro ao carregar papéis:', err);
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail || !invitePapel) return;

    setInviting(true);
    try {
      const res = await api(`/organizacoes/${currentOrg.id}/convites`, {
        method: 'POST',
        body: JSON.stringify({ email: inviteEmail, papel_id: parseInt(invitePapel) })
      });
      if (res.ok) {
        toast.success('Convite enviado!');
        setShowInvite(false);
        setInviteEmail('');
        setInvitePapel('');
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Erro ao enviar convite');
      }
    } catch (err) {
      toast.error('Erro ao enviar convite');
    } finally {
      setInviting(false);
    }
  };

  if (!currentOrg) {
    return (
      <div className="p-6">
        <Card className="p-8 text-center">
          <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Selecione uma organização</p>
        </Card>
      </div>
    );
  }

  if (loading) return <LoadingScreen />;

  return (
    <div>
      <Header 
        title="Equipe" 
        subtitle={`${members.length} membro(s) em ${currentOrg.nome}`}
        actions={
          <Button onClick={() => setShowInvite(true)}>
            <Plus className="w-4 h-4" /> Convidar
          </Button>
        }
      />

      <div className="grid gap-4">
        {members.map(m => (
          <Card key={m.id} className="p-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                {m.nome?.charAt(0).toUpperCase() || '?'}
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-slate-800">{m.nome}</h3>
                <p className="text-sm text-slate-500">{m.email}</p>
              </div>
              <Badge variant={m.papel_nivel >= 30 ? 'success' : m.papel_nivel >= 20 ? 'warning' : 'default'}>
                {m.papel_nome}
              </Badge>
            </div>
          </Card>
        ))}
      </div>

      <Modal isOpen={showInvite} onClose={() => setShowInvite(false)} title="Convidar Membro">
        <form onSubmit={handleInvite} className="space-y-4">
          <Input
            label="Email"
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="email@exemplo.com"
            required
          />
          <Select
            label="Papel"
            value={invitePapel}
            onChange={(e) => setInvitePapel(e.target.value)}
            required
          >
            <option value="">Selecione um papel</option>
            {papeis.filter(p => p.nivel < 99).map(p => (
              <option key={p.id} value={p.id}>{p.nome} - {p.descricao}</option>
            ))}
          </Select>
          <div className="flex gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={() => setShowInvite(false)} className="flex-1">
              Cancelar
            </Button>
            <Button type="submit" disabled={inviting} className="flex-1">
              {inviting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Enviar Convite'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default TeamMembersPage;
