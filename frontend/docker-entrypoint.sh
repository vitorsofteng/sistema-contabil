#!/bin/sh
# Ajusta porta do nginx para $PORT do Railway
if [ -n "$PORT" ]; then
  sed -i "s/listen 80/listen $PORT/" /etc/nginx/conf.d/default.conf
fi

# Gera runtime-config.js com a URL real da API
if [ -n "$VITE_API_URL" ]; then
  cat > /usr/share/nginx/html/runtime-config.js <<JSEOF
window.__RUNTIME_CONFIG__={API_URL:"${VITE_API_URL}"};
JSEOF
  echo ">> runtime-config.js gerado com API_URL=${VITE_API_URL}"
else
  echo ">> AVISO: VITE_API_URL nao definido"
fi
