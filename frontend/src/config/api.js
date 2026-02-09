function getApiUrl() {
  // Build-time env (definido no Railway como VITE_API_URL)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // Dev local
  const host = window.location.hostname;
  if (host === 'localhost' || host === '127.0.0.1') {
    return 'http://localhost:8000';
  }

  // Fallback
  return '';
}

export const API_URL = getApiUrl();
