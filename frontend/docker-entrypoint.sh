#!/bin/sh
set -e

echo "=== Kontabil Frontend Entrypoint ==="

# 1. Porta (Railway define $PORT automaticamente)
if [ -n "$PORT" ]; then
  sed -i "s/listen 80/listen $PORT/" /etc/nginx/conf.d/default.conf
  echo ">> Porta: $PORT"
else
  echo ">> Porta: 80 (padrao)"
fi

# 2. Backend proxy
RESOLVED="${BACKEND_URL:-}"

if [ -z "$RESOLVED" ] && [ -n "$RAILWAY_PRIVATE_DOMAIN" ]; then
  RESOLVED="http://${RAILWAY_PRIVATE_DOMAIN}:8080"
fi

if [ -z "$RESOLVED" ]; then
  RESOLVED="http://backend:8000"
fi

echo ">> Backend URL: $RESOLVED"

# Substituir placeholder no nginx.conf
sed -i "s|__BACKEND_URL__|${RESOLVED}|g" /etc/nginx/conf.d/default.conf

# Verificar se substituiu
if grep -q "__BACKEND_URL__" /etc/nginx/conf.d/default.conf; then
  echo ">> ERRO: __BACKEND_URL__ nao foi substituido!"
else
  echo ">> Proxy configurado OK"
fi

# 3. runtime-config.js (vazio = usa proxy)
cat > /usr/share/nginx/html/runtime-config.js <<JSEOF
window.__RUNTIME_CONFIG__={API_URL:""};
JSEOF

# 4. Debug: mostra config final
echo ">> nginx.conf final:"
cat /etc/nginx/conf.d/default.conf
echo ""
echo "=== Iniciando nginx ==="

exec nginx -g "daemon off;"
