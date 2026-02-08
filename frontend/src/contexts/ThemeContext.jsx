import React, { useState, useEffect, createContext, useContext } from 'react';
import { API_URL } from '../config/api';
import { useAuth } from './AuthContext';

const ThemeContext = createContext(null);

function ThemeProvider({ children }) {
  const { token } = useAuth() || {};
  const [theme, setTheme] = useState({
    cor_primaria: '#1e40af',
    cor_secundaria: '#3b82f6',
    cor_destaque: '#059669',
    nome_escritorio: ''
  });
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (token) {
      loadTheme();
    }
  }, [token]);

  useEffect(() => {
    // Aplicar cores como CSS variables
    const root = document.documentElement;
    root.style.setProperty('--cor-primaria', theme.cor_primaria);
    root.style.setProperty('--cor-secundaria', theme.cor_secundaria);
    root.style.setProperty('--cor-destaque', theme.cor_destaque);
    
    // Converter hex para RGB para usar com opacity
    const hexToRgb = (hex) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '30, 64, 175';
    };
    
    root.style.setProperty('--cor-primaria-rgb', hexToRgb(theme.cor_primaria));
    root.style.setProperty('--cor-secundaria-rgb', hexToRgb(theme.cor_secundaria));
  }, [theme]);

  const loadTheme = async () => {
    try {
      const res = await fetch(`${API_URL}/relatorios/configuracao`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTheme(prev => ({
          ...prev,
          cor_primaria: data.cor_primaria || '#1e40af',
          cor_secundaria: data.cor_secundaria || '#3b82f6',
          cor_destaque: data.cor_destaque || '#059669',
          nome_escritorio: data.nome_escritorio || ''
        }));
      }
    } catch (err) {
      console.error('Erro ao carregar tema:', err);
    }
    setLoaded(true);
  };

  const updateTheme = (newTheme) => {
    setTheme(prev => ({ ...prev, ...newTheme }));
  };

  return (
    <ThemeContext.Provider value={{ theme, updateTheme, loadTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

const useTheme = () => useContext(ThemeContext);

export { ThemeProvider, useTheme };
