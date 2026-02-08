import React, { useState, useEffect, createContext, useContext } from 'react';
import { useAuth } from './AuthContext';

const OrganizationContext = createContext(null);

function OrganizationProvider({ children }) {
  const { api, user } = useAuth();
  const [organizations, setOrganizations] = useState([]);
  const [currentOrg, setCurrentOrg] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadOrganizations();
    }
  }, [user]);

  const loadOrganizations = async () => {
    try {
      const res = await api('/organizacoes');
      if (res.ok) {
        const data = await res.json();
        const orgs = data.organizacoes || [];
        setOrganizations(orgs);
        
        // Define organização padrão ou primeira
        const defaultOrg = orgs.find(o => o.is_default) || orgs[0];
        if (defaultOrg && !currentOrg) {
          setCurrentOrg(defaultOrg);
        }
      }
    } catch (err) {
      console.error('Erro ao carregar organizações:', err);
    } finally {
      setLoading(false);
    }
  };

  const switchOrganization = (org) => {
    setCurrentOrg(org);
    localStorage.setItem('currentOrgId', org.id);
  };

  const createOrganization = async (data) => {
    const res = await api('/organizacoes', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    if (res.ok) {
      await loadOrganizations();
      return await res.json();
    }
    throw new Error('Erro ao criar organização');
  };

  return (
    <OrganizationContext.Provider value={{
      organizations,
      currentOrg,
      loading,
      switchOrganization,
      createOrganization,
      refreshOrganizations: loadOrganizations
    }}>
      {children}
    </OrganizationContext.Provider>
  );
}

function useOrganization() {
  const context = useContext(OrganizationContext);
  if (!context) {
    return { organizations: [], currentOrg: null, loading: false };
  }
  return context;
}

export { OrganizationProvider, useOrganization };
