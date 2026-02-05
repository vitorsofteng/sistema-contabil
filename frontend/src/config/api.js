// Prioridade: runtime config (Railway) > build-time env > fallback
export const API_URL = 
  (window.__RUNTIME_CONFIG__ && window.__RUNTIME_CONFIG__.API_URL) || 
  import.meta.env.VITE_API_URL || 
  '/api';
