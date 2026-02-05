// Decodifica payload do JWT (sem verificar assinatura - só para ler expiração)
export function decodeJWT(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(window.atob(base64));
    return payload;
  } catch {
    return null;
  }
}

// Verifica se token está próximo de expirar (menos de 30 minutos)
export function isTokenExpiringSoon(token, minutesBefore = 30) {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) return true;
  const expiresAt = payload.exp * 1000; // converter para ms
  const now = Date.now();
  const threshold = minutesBefore * 60 * 1000;
  return (expiresAt - now) < threshold;
}
