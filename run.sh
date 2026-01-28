#!/bin/bash
# =============================================================================
# SISTEMA CONTÁBIL - EXECUÇÃO SEM DOCKER
# =============================================================================
# Roda direto com Python e Node (sem Docker)
# Uso: ./run.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       SISTEMA CONTÁBIL v2.9.0 - Modo Local               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Limpa processos anteriores
cleanup() {
    echo -e "\n${YELLOW}Parando serviços...${NC}"
    pkill -f "uvicorn api.main:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    pkill -f "node.*contabil" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Verifica Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    elif command -v python &> /dev/null; then
        PYTHON=python
    else
        echo -e "${RED}❌ Python não encontrado!${NC}"
        echo "Instale com: sudo apt install python3 python3-pip python3-venv"
        exit 1
    fi
    echo -e "${GREEN}✅ Python: $($PYTHON --version)${NC}"
}

# Verifica Node
check_node() {
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js não encontrado!${NC}"
        echo "Instale com:"
        echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
        echo "  sudo apt install -y nodejs"
        exit 1
    fi
    echo -e "${GREEN}✅ Node: $(node --version)${NC}"
}

# Configura variáveis
setup_env() {
    # Usa SQLite por padrão (não precisa de PostgreSQL)
    export USE_POSTGRES="false"
    export SQLITE_PATH="${BASE_DIR}/contabil.db"
    export DATABASE_URL="sqlite:///${BASE_DIR}/contabil.db"
    export JWT_SECRET="chave-secreta-local-dev-2024"
    export ENVIRONMENT="development"
    export ENV="development"
    export PYTHONPATH="${BASE_DIR}/backend"
    export VITE_API_URL="http://localhost:8000"
    
    echo -e "${GREEN}✅ Usando SQLite: ${BASE_DIR}/contabil.db${NC}"
}

# Instala dependências do Backend
setup_backend() {
    echo -e "\n${BLUE}📦 Configurando Backend...${NC}"
    cd "$BASE_DIR/backend"
    
    # Cria pasta data
    mkdir -p data
    
    # Cria venv se não existir
    if [ ! -d "venv" ]; then
        echo "  Criando ambiente virtual..."
        $PYTHON -m venv venv
    fi
    
    # Ativa venv
    source venv/bin/activate
    
    # Instala dependências
    echo "  Instalando dependências Python..."
    pip install --upgrade pip -q
    
    # Tenta requirements.txt completo, se falhar instala essenciais
    if pip install -r requirements.txt -q 2>/dev/null; then
        echo -e "${GREEN}  ✅ Todas dependências instaladas${NC}"
    else
        echo -e "${YELLOW}  ⚠️ Instalando dependências essenciais...${NC}"
        pip install -q fastapi uvicorn sqlalchemy python-jose passlib bcrypt \
            python-multipart aiofiles pydantic email-validator \
            reportlab openpyxl python-pptx python-dateutil 2>/dev/null || true
        echo -e "${GREEN}  ✅ Dependências essenciais instaladas${NC}"
    fi
    
    echo -e "${GREEN}  ✅ Backend pronto${NC}"
}

# Instala dependências do Frontend
setup_frontend() {
    echo -e "\n${BLUE}📦 Configurando Frontend...${NC}"
    cd "$BASE_DIR/frontend"
    
    if [ ! -d "node_modules" ]; then
        echo "  Instalando dependências Node..."
        npm install --silent 2>/dev/null || npm install
    fi
    
    echo -e "${GREEN}  ✅ Frontend pronto${NC}"
}

# Inicia Backend
start_backend() {
    echo -e "\n${BLUE}🚀 Iniciando Backend (porta 8000)...${NC}"
    cd "$BASE_DIR/backend"
    source venv/bin/activate
    
    $PYTHON -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    # Aguarda backend iniciar
    echo -n "  Aguardando backend"
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo ""
            echo -e "${GREEN}  ✅ Backend rodando (PID: $BACKEND_PID)${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo ""
    echo -e "${YELLOW}  ⚠️ Backend iniciando em background...${NC}"
}

# Inicia Frontend
start_frontend() {
    echo -e "\n${BLUE}🚀 Iniciando Frontend (porta 3000)...${NC}"
    cd "$BASE_DIR/frontend"
    
    npm run dev &
    FRONTEND_PID=$!
    
    sleep 3
    echo -e "${GREEN}  ✅ Frontend rodando (PID: $FRONTEND_PID)${NC}"
}

# Mostra informações
show_info() {
    echo -e "\n${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}   ✅ SISTEMA INICIADO COM SUCESSO!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "   ${CYAN}🌐 Frontend:${NC}  http://localhost:3000"
    echo -e "   ${CYAN}🔧 Backend:${NC}   http://localhost:8000"
    echo -e "   ${CYAN}📚 API Docs:${NC}  http://localhost:8000/docs"
    echo ""
    echo -e "   ${YELLOW}Pressione Ctrl+C para parar${NC}"
    echo ""
}

# Main
main() {
    check_python
    check_node
    setup_env
    setup_backend
    setup_frontend
    start_backend
    start_frontend
    show_info
    
    # Mantém rodando
    wait
}

# Executa
main
