#!/bin/sh
set -e

echo "=== Frontend Entrypoint ==="

# 1. Ajusta porta do nginx para $PORT (Railway define automaticamente)
if [ -n "$PORT" ]; then
  sed -i "s/listen 80/listen $PORT/" /etc/nginx/conf.d/default.conf
  echo ">> Porta ajustada para $PORT"
else
  echo ">> Usando porta padrão 80"
fi

# 2. Configura proxy para o backend
# Railway: BACKEND_URL = URL interna (ex: http://backend.railway.internal:8000)
# Docker-compose: BACKEND_URL = http://backend:8000
# Fallback: tenta variáveis comuns do Railway
RESOLVED_BACKEND_URL="${BACKEND_URL:-}"

# Tenta detectar automaticamente no Railway
if [ -z "$RESOLVED_BACKEND_URL" ] && [ -n "$RAILWAY_PRIVATE_DOMAIN" ]; then
  RESOLVED_BACKEND_URL="http://${RAILWAY_PRIVATE_DOMAIN}:8000"
  echo ">> Backend via Railway private domain: $RESOLVED_BACKEND_URL"
fi

if [ -z "$RESOLVED_BACKEND_URL" ]; then
  RESOLVED_BACKEND_URL="http://backend:8000"
  echo ">> Backend fallback (docker-compose): $RESOLVED_BACKEND_URL"
fi

# Substitui __BACKEND_URL__ no nginx.conf
sed -i "s|__BACKEND_URL__|${RESOLVED_BACKEND_URL}|g" /etc/nginx/conf.d/default.conf
echo ">> Proxy configurado para: $RESOLVED_BACKEND_URL"

# 3. Gera runtime-config.js (fallback caso o proxy falhe)
# Em operação normal, API_URL fica vazio pois o nginx proxeia tudo
API_URL_FOR_JS="${VITE_API_URL:-}"
cat > /usr/share/nginx/html/runtime-config.js <<JSEOF
window.__RUNTIME_CONFIG__={API_URL:"${API_URL_FOR_JS}"};
JSEOF
echo ">> runtime-config.js gerado (API_URL=${API_URL_FOR_JS:-'(empty, using proxy)'})"

# 4. Log da config final
echo ">> Nginx config final:"
grep -E "listen|proxy_pass|__BACKEND" /etc/nginx/conf.d/default.conf || true
echo "=== Iniciando nginx ==="

exec nginx -g "daemon off;"
