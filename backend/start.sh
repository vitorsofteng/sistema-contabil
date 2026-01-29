#!/bin/bash

# ==================================================
# Script de inicialização para Railway/Produção
# Executa migrations e inicia o servidor
# ==================================================

set -e

echo "🚀 Iniciando Sistema Contábil..."

# Aguardar banco estar disponível
echo "⏳ Aguardando banco de dados..."
sleep 5

# Executar migrations
echo "📦 Executando migrations..."
python -m alembic upgrade head || echo "⚠️ Algumas migrations podem ter falhado"

# Iniciar servidor
echo "✅ Iniciando servidor na porta ${PORT:-8000}..."
exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
