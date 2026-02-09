#!/bin/sh
set -e
# Ajusta porta para Railway
if [ -n "$PORT" ]; then
  sed -i "s/listen 80/listen $PORT/" /etc/nginx/conf.d/default.conf
  echo "Porta: $PORT"
fi
exec nginx -g "daemon off;"
