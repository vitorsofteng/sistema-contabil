// Detecta ambiente automaticamente
function getApiUrl() {
  // 1. Runtime config (Railway deploy via docker-entrypoint.sh)
  if (window.__RUNTIME_CONFIG__ && window.__RUNTIME_CONFIG__.API_URL) {
    return window.__RUNTIME_CONFIG__.API_URL;
  }

  // 2. Build-time env (Vite)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // 3. Auto-detect: localhost = dev local, senão usa origem
  const host = window.location.hostname;
  if (host === 'localhost' || host === '127.0.0.1') {
    return 'http://localhost:8000';
  }

  // 4. Produção/staging: backend no mesmo domínio via proxy
  return '';
}

export const API_URL = getApiUrl();
