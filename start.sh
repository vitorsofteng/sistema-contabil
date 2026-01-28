#!/bin/bash
# =============================================================================
# SISTEMA CONTÁBIL - SCRIPT DE INICIALIZAÇÃO
# =============================================================================
# Uso:
#   ./start.sh           - Inicia em modo desenvolvimento
#   ./start.sh prod      - Inicia em modo produção
#   ./start.sh stop      - Para todos os containers
#   ./start.sh logs      - Mostra logs
#   ./start.sh rebuild   - Reconstrói tudo do zero

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       SISTEMA CONTÁBIL - Gestão Financeira v2.9.0        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Função para verificar Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker não encontrado!${NC}"
        echo "Instale com: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker daemon não está rodando!${NC}"
        echo "Execute: sudo systemctl start docker"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker OK${NC}"
}

# Função para fazer pull das imagens com retry
pull_images() {
    echo -e "\n${YELLOW}📦 Baixando imagens base...${NC}"
    
    IMAGES=("postgres:16-alpine" "node:20-alpine" "python:3.11-slim")
    
    for img in "${IMAGES[@]}"; do
        echo -e "  Baixando ${BLUE}$img${NC}..."
        
        for i in {1..3}; do
            if docker pull "$img" 2>/dev/null; then
                echo -e "  ${GREEN}✅ $img${NC}"
                break
            else
                if [ $i -lt 3 ]; then
                    echo -e "  ${YELLOW}⚠️ Tentativa $i falhou, tentando novamente em 10s...${NC}"
                    sleep 10
                else
                    echo -e "  ${YELLOW}⚠️ Não foi possível baixar $img (usando cache se disponível)${NC}"
                fi
            fi
        done
    done
}

# Função para iniciar em modo desenvolvimento
start_dev() {
    echo -e "\n${BLUE}🚀 Iniciando em modo DESENVOLVIMENTO...${NC}"
    
    # Verifica se as imagens existem localmente
    if ! docker images | grep -q "node.*20-alpine"; then
        pull_images
    fi
    
    # Inicia os containers
    docker-compose up -d --build
    
    echo -e "\n${GREEN}✅ Sistema iniciado!${NC}"
    echo -e ""
    echo -e "  ${CYAN}Frontend:${NC}  http://localhost"
    echo -e "  ${CYAN}Backend:${NC}   http://localhost:8000"
    echo -e "  ${CYAN}API Docs:${NC}  http://localhost:8000/docs"
    echo -e "  ${CYAN}Database:${NC}  localhost:5432"
    echo -e ""
    echo -e "  ${YELLOW}Logs:${NC} docker-compose logs -f"
    echo -e "  ${YELLOW}Parar:${NC} ./start.sh stop"
}

# Função para iniciar em modo produção
start_prod() {
    echo -e "\n${BLUE}🚀 Iniciando em modo PRODUÇÃO...${NC}"
    
    # Pull das imagens necessárias
    pull_images
    docker pull nginx:alpine 2>/dev/null || echo -e "${YELLOW}⚠️ Usando nginx do cache${NC}"
    
    # Inicia com docker-compose de produção
    docker-compose -f docker-compose.prod.yml up -d --build
    
    echo -e "\n${GREEN}✅ Sistema iniciado em PRODUÇÃO!${NC}"
    echo -e ""
    echo -e "  ${CYAN}URL:${NC} http://localhost"
    echo -e ""
}

# Função para parar
stop_all() {
    echo -e "\n${YELLOW}🛑 Parando containers...${NC}"
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    echo -e "${GREEN}✅ Containers parados${NC}"
}

# Função para mostrar logs
show_logs() {
    docker-compose logs -f
}

# Função para rebuild completo
rebuild() {
    echo -e "\n${YELLOW}🔄 Reconstruindo tudo...${NC}"
    
    # Para tudo
    stop_all
    
    # Remove imagens antigas do projeto
    docker rmi contabil_system-frontend contabil_system-backend 2>/dev/null || true
    docker rmi contabil-frontend contabil-backend 2>/dev/null || true
    
    # Limpa volumes não usados (cuidado em produção!)
    read -p "Deseja limpar volumes de dados? (s/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        docker volume rm contabil_system_postgres-data 2>/dev/null || true
        docker volume rm postgres-data 2>/dev/null || true
        echo -e "${GREEN}✅ Volumes limpos${NC}"
    fi
    
    # Pull das imagens
    pull_images
    
    # Rebuild
    docker-compose build --no-cache
    
    echo -e "${GREEN}✅ Rebuild completo${NC}"
}

# Função para mostrar status
show_status() {
    echo -e "\n${BLUE}📊 Status dos containers:${NC}"
    docker-compose ps
}

# Main
check_docker

case "${1:-dev}" in
    dev|start)
        start_dev
        ;;
    prod|production)
        start_prod
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 2
        start_dev
        ;;
    logs)
        show_logs
        ;;
    rebuild)
        rebuild
        ;;
    status)
        show_status
        ;;
    pull)
        pull_images
        ;;
    *)
        echo "Uso: $0 {dev|prod|stop|restart|logs|rebuild|status|pull}"
        echo ""
        echo "  dev      - Inicia em modo desenvolvimento (padrão)"
        echo "  prod     - Inicia em modo produção"
        echo "  stop     - Para todos os containers"
        echo "  restart  - Reinicia os containers"
        echo "  logs     - Mostra logs em tempo real"
        echo "  rebuild  - Reconstrói tudo do zero"
        echo "  status   - Mostra status dos containers"
        echo "  pull     - Baixa imagens base"
        exit 1
        ;;
esac
