// Detecta ambiente automaticamente
function getApiUrl() {
  // 1. Runtime config (gerado pelo docker-entrypoint.sh)
  //    Normalmente vazio em produção pois nginx proxeia tudo.
  //    Preenchido apenas se VITE_API_URL for definido explicitamente.
  if (window.__RUNTIME_CONFIG__ && window.__RUNTIME_CONFIG__.API_URL) {
    return window.__RUNTIME_CONFIG__.API_URL;
  }

  // 2. Build-time env (Vite dev)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // 3. Desenvolvimento local sem Docker
  const host = window.location.hostname;
  if (host === 'localhost' || host === '127.0.0.1') {
    // Se porta 3000/5173 (Vite dev), aponta pro backend direto
    const port = window.location.port;
    if (port === '3000' || port === '5173') {
      return 'http://localhost:8000';
    }
  }

  // 4. Produção: nginx proxeia tudo, usa mesma origem (sem CORS)
  return '';
}

export const API_URL = getApiUrl();
