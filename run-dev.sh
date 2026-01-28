#!/bin/bash

# =============================================================================
# Script para rodar o sistema localmente (sem Docker)
# =============================================================================

echo "=============================================="
echo "Diagnóstico Financeiro - Desenvolvimento Local"
echo "=============================================="

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python 3 não encontrado"
    exit 1
fi

# Verifica se Node está instalado
if ! command -v npm &> /dev/null; then
    echo "ERRO: Node.js/npm não encontrado"
    exit 1
fi

# Diretório base
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Função para limpar processos ao sair
cleanup() {
    echo ""
    echo "Encerrando..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# Inicia Backend
echo ""
echo ">>> Iniciando Backend (porta 8000)..."
cd "$DIR/backend"

# Instala dependências Python se necessário
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual Python..."
    python3 -m venv venv
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
pip install -q -r requirements.txt

uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Aguarda backend iniciar
sleep 3

# Verifica se backend está rodando
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "ERRO: Backend não iniciou corretamente"
    exit 1
fi
echo "Backend OK: http://localhost:8000"

# Inicia Frontend
echo ""
echo ">>> Iniciando Frontend (porta 3000)..."
cd "$DIR/frontend"

# Instala dependências Node se necessário
if [ ! -d "node_modules" ]; then
    echo "Instalando dependências Node..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!

# Aguarda
sleep 3

echo ""
echo "=============================================="
echo "Sistema rodando!"
echo "  Frontend: http://localhost:3000"
echo "  API:      http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Pressione Ctrl+C para encerrar"
echo "=============================================="

# Mantém script rodando
wait
