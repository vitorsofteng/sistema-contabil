#!/bin/bash
# =============================================================================
# SCRIPT DE DESENVOLVIMENTO LOCAL - SEM DOCKER
# =============================================================================
# Roda backend (Python) e frontend (Node) diretamente na máquina
# Requer: Python 3.10+, Node 18+, PostgreSQL

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Sistema Contábil - Dev Local${NC}"
echo -e "${BLUE}========================================${NC}"

# Diretório base
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verifica dependências
check_deps() {
    echo -e "\n${YELLOW}Verificando dependências...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 não encontrado. Instale com: sudo apt install python3 python3-pip python3-venv${NC}"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js não encontrado. Instale com: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Python: $(python3 --version)${NC}"
    echo -e "${GREEN}✅ Node: $(node --version)${NC}"
    echo -e "${GREEN}✅ NPM: $(npm --version)${NC}"
}

# Configura variáveis de ambiente
setup_env() {
    echo -e "\n${YELLOW}Configurando ambiente...${NC}"
    
    # Cria .env se não existir
    if [ ! -f "$BASE_DIR/.env" ]; then
        cat > "$BASE_DIR/.env" << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/contabil_db

# Se não tiver PostgreSQL local, use SQLite:
# DATABASE_URL=sqlite:///./contabil.db

# JWT Secret
JWT_SECRET=sua-chave-secreta-muito-segura-aqui-2024

# Ambiente
ENVIRONMENT=development

# Frontend
VITE_API_URL=http://localhost:8000
EOF
        echo -e "${GREEN}✅ Arquivo .env criado${NC}"
    fi
    
    # Exporta variáveis
    export $(grep -v '^#' "$BASE_DIR/.env" | xargs)
}

# Setup do Backend
setup_backend() {
    echo -e "\n${YELLOW}Configurando Backend...${NC}"
    cd "$BASE_DIR/backend"
    
    # Cria venv se não existir
    if [ ! -d "venv" ]; then
        echo "Criando ambiente virtual Python..."
        python3 -m venv venv
    fi
    
    # Ativa venv
    source venv/bin/activate
    
    # Instala dependências
    echo "Instalando dependências Python..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    
    echo -e "${GREEN}✅ Backend configurado${NC}"
}

# Setup do Frontend
setup_frontend() {
    echo -e "\n${YELLOW}Configurando Frontend...${NC}"
    cd "$BASE_DIR/frontend"
    
    # Instala dependências
    if [ ! -d "node_modules" ]; then
        echo "Instalando dependências Node..."
        npm install
    fi
    
    echo -e "${GREEN}✅ Frontend configurado${NC}"
}

# Inicia Backend
start_backend() {
    echo -e "\n${BLUE}Iniciando Backend na porta 8000...${NC}"
    cd "$BASE_DIR/backend"
    source venv/bin/activate
    
    # Exporta variáveis
    export $(grep -v '^#' "$BASE_DIR/.env" | xargs)
    
    # Roda o backend
    python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BASE_DIR/.backend.pid"
    echo -e "${GREEN}✅ Backend rodando (PID: $BACKEND_PID)${NC}"
}

# Inicia Frontend
start_frontend() {
    echo -e "\n${BLUE}Iniciando Frontend na porta 5173...${NC}"
    cd "$BASE_DIR/frontend"
    
    # Roda o frontend
    npm run dev -- --host 0.0.0.0 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$BASE_DIR/.frontend.pid"
    echo -e "${GREEN}✅ Frontend rodando (PID: $FRONTEND_PID)${NC}"
}

# Para os serviços
stop_services() {
    echo -e "\n${YELLOW}Parando serviços...${NC}"
    
    if [ -f "$BASE_DIR/.backend.pid" ]; then
        kill $(cat "$BASE_DIR/.backend.pid") 2>/dev/null || true
        rm "$BASE_DIR/.backend.pid"
    fi
    
    if [ -f "$BASE_DIR/.frontend.pid" ]; then
        kill $(cat "$BASE_DIR/.frontend.pid") 2>/dev/null || true
        rm "$BASE_DIR/.frontend.pid"
    fi
    
    # Mata processos restantes
    pkill -f "uvicorn api.main:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    echo -e "${GREEN}✅ Serviços parados${NC}"
}

# Mostra status
show_status() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}   Sistema iniciado com sucesso!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e ""
    echo -e "  ${BLUE}Frontend:${NC} http://localhost:5173"
    echo -e "  ${BLUE}Backend:${NC}  http://localhost:8000"
    echo -e "  ${BLUE}API Docs:${NC} http://localhost:8000/docs"
    echo -e ""
    echo -e "  ${YELLOW}Para parar: ./start-local.sh stop${NC}"
    echo -e ""
}

# Main
case "${1:-start}" in
    start)
        check_deps
        setup_env
        setup_backend
        setup_frontend
        start_backend
        sleep 2
        start_frontend
        sleep 2
        show_status
        
        # Aguarda Ctrl+C
        echo -e "${YELLOW}Pressione Ctrl+C para parar...${NC}"
        trap stop_services EXIT
        wait
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        $0 start
        ;;
    backend)
        setup_env
        setup_backend
        cd "$BASE_DIR/backend"
        source venv/bin/activate
        export $(grep -v '^#' "$BASE_DIR/.env" | xargs)
        python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    frontend)
        setup_env
        setup_frontend
        cd "$BASE_DIR/frontend"
        npm run dev -- --host 0.0.0.0
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|backend|frontend}"
        exit 1
        ;;
esac
