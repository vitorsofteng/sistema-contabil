import React, { useState, useEffect, createContext, useContext, useRef } from 'react';
import { API_URL } from '../config/api';
import { isTokenExpiringSoon } from '../utils/jwt';

const AuthContext = createContext(null);

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refresh_token'));
  const [loading, setLoading] = useState(true);
  
  // Mutex para evitar múltiplos refreshes simultâneos
  const refreshingRef = useRef(false);
  const refreshPromiseRef = useRef(null);

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  // Refresh proativo - verifica a cada 5 minutos se precisa renovar
  useEffect(() => {
    if (!token || !refreshToken) return;
    
    const checkAndRefresh = async () => {
      if (isTokenExpiringSoon(token, 30)) {
        console.log('🔄 Token expirando em breve, renovando proativamente...');
        await tryRefreshToken();
      }
    };
    
    // Verifica imediatamente
    checkAndRefresh();
    
    // Verifica a cada 5 minutos
    const interval = setInterval(checkAndRefresh, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [token, refreshToken]);

  const fetchUser = async () => {
    try {
      // Se token está expirando, renova primeiro
      let currentToken = token;
      if (isTokenExpiringSoon(token, 5)) {
        const refreshed = await tryRefreshToken();
        if (refreshed) {
          currentToken = localStorage.getItem('token');
        }
      }
      
      const res = await fetch(`${API_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${currentToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else if (res.status === 401 && refreshToken) {
        const refreshed = await tryRefreshToken();
        if (refreshed) {
          // Tenta novamente com novo token
          const newToken = localStorage.getItem('token');
          const retryRes = await fetch(`${API_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${newToken}` }
          });
          if (retryRes.ok) {
            const data = await retryRes.json();
            setUser(data);
          } else {
            logout();
          }
        } else {
          logout();
        }
      } else {
        logout();
      }
    } catch (err) {
      console.error('Erro ao buscar usuário:', err);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const tryRefreshToken = async () => {
    // Se já está refreshando, aguarda a promise existente
    if (refreshingRef.current && refreshPromiseRef.current) {
      console.log('⏳ Refresh já em andamento, aguardando...');
      return refreshPromiseRef.current;
    }
    
    refreshingRef.current = true;
    
    refreshPromiseRef.current = (async () => {
      try {
        const currentRefreshToken = localStorage.getItem('refresh_token');
        if (!currentRefreshToken) {
          return false;
        }
        
        const res = await fetch(`${API_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: currentRefreshToken })
        });
        
        if (res.ok) {
          const data = await res.json();
          localStorage.setItem('token', data.token);
          setToken(data.token);
          if (data.user) {
            setUser(data.user);
          }
          console.log('✅ Token renovado com sucesso');
          return true;
        }
        console.warn('❌ Falha ao renovar token:', res.status);
        return false;
      } catch (err) {
        console.error('❌ Erro ao renovar token:', err);
        return false;
      } finally {
        refreshingRef.current = false;
        refreshPromiseRef.current = null;
      }
    })();
    
    return refreshPromiseRef.current;
  };

  const login = async (email, senha) => {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, senha })
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.detail || 'Erro ao fazer login');
    }
    
    localStorage.setItem('token', data.token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setToken(data.token);
    setRefreshToken(data.refresh_token);
    setUser(data.user);
    return data;
  };

  const [pendingVerification, setPendingVerification] = useState(null);

  const register = async (dados) => {
    const res = await fetch(`${API_URL}/auth/registrar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados)
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.detail || 'Erro ao registrar');
    }
    
    // NÃO faz login automático - guarda token mas mostra tela de verificação
    localStorage.setItem('token', data.token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    // Sinaliza que precisa verificar email antes de entrar
    setPendingVerification({
      email: dados.email,
      nome: dados.nome
    });
    
    return data;
  };

  const completePendingVerification = () => {
    // Chamado quando o user clica "Continuar sem verificar"
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      setRefreshToken(localStorage.getItem('refresh_token'));
      // Buscar dados do usuário com o token já salvo
      fetch(`${API_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${storedToken}` }
      })
        .then(r => r.ok ? r.json() : null)
        .then(data => { if (data) setUser(data); })
        .catch(() => {});
    }
    setPendingVerification(null);
  };

  const logout = async () => {
    const currentToken = localStorage.getItem('token');
    if (currentToken) {
      try {
        await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${currentToken}` }
        });
      } catch {}
    }
    
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setRefreshToken(null);
    setUser(null);
  };

  const api = async (path, options = {}) => {
    let currentToken = localStorage.getItem('token');
    
    // Se token está expirando, renova antes de fazer a requisição
    if (currentToken && isTokenExpiringSoon(currentToken, 5)) {
      const refreshed = await tryRefreshToken();
      if (refreshed) {
        currentToken = localStorage.getItem('token');
      }
    }
    
    const headers = {
      'Authorization': `Bearer ${currentToken}`,
      ...options.headers
    };
    
    if (!(options.body instanceof FormData) && !options.headers?.hasOwnProperty('Content-Type')) {
      headers['Content-Type'] = 'application/json';
    }
    
    let res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers
    });
    
    // Se ainda assim deu 401, tenta refresh e retry
    if (res.status === 401) {
      const currentRefreshToken = localStorage.getItem('refresh_token');
      if (currentRefreshToken) {
        const refreshed = await tryRefreshToken();
        if (refreshed) {
          const newToken = localStorage.getItem('token');
          const retryHeaders = {
            'Authorization': `Bearer ${newToken}`,
            ...options.headers
          };
          if (!(options.body instanceof FormData) && !options.headers?.hasOwnProperty('Content-Type')) {
            retryHeaders['Content-Type'] = 'application/json';
          }
          res = await fetch(`${API_URL}${path}`, {
            ...options,
            headers: retryHeaders
          });
        } else {
          logout();
          throw new Error('Sessão expirada. Faça login novamente.');
        }
      } else {
        logout();
        throw new Error('Sessão expirada. Faça login novamente.');
      }
    }
    
    return res;
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, api, pendingVerification, completePendingVerification }}>
      {children}
    </AuthContext.Provider>
  );
}

const useAuth = () => useContext(AuthContext);

export { AuthProvider, useAuth };
