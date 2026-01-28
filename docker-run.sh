#!/bin/bash
# =============================================================================
# SISTEMA CONTÁBIL - DOCKER SEM RATE LIMIT
# =============================================================================
# Este script resolve o problema de rate limit do Docker Hub
# 
# Uso: ./docker-run.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       SISTEMA CONTÁBIL v2.9.0 - Docker Setup             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# =============================================================================
# VERIFICAÇÕES
# =============================================================================

# Verifica Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não encontrado!${NC}"
    echo "Instale com: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Verifica se Docker está rodando
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker não está rodando!${NC}"
    echo "Execute: sudo systemctl start docker"
    exit 1
fi

echo -e "${GREEN}✅ Docker está funcionando${NC}"

# =============================================================================
# LOGIN NO DOCKER HUB (RESOLVE RATE LIMIT)
# =============================================================================

echo -e "\n${BLUE}🔐 Verificando autenticação no Docker Hub...${NC}"

# Verifica se já está logado
if docker info 2>/dev/null | grep -q "Username:"; then
    USERNAME=$(docker info 2>/dev/null | grep "Username:" | awk '{print $2}')
    echo -e "${GREEN}✅ Já logado como: $USERNAME${NC}"
else
    echo -e "${YELLOW}⚠️  Você NÃO está logado no Docker Hub${NC}"
    echo ""
    echo "O Docker Hub limita pulls para usuários não autenticados."
    echo "Fazer login é GRATUITO e resolve o problema de rate limit."
    echo ""
    echo -e "${CYAN}Opções:${NC}"
    echo "  1) Fazer login agora (recomendado)"
    echo "  2) Criar conta em https://hub.docker.com/signup"
    echo "  3) Continuar sem login (pode falhar)"
    echo ""
    read -p "Escolha [1/2/3]: " choice
    
    case $choice in
        1)
            echo -e "\n${BLUE}Fazendo login no Docker Hub...${NC}"
            docker login
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Login realizado com sucesso!${NC}"
            else
                echo -e "${RED}❌ Falha no login. Continuando mesmo assim...${NC}"
            fi
            ;;
        2)
            echo -e "\n${CYAN}Abra https://hub.docker.com/signup no navegador${NC}"
            echo "Depois de criar a conta, execute este script novamente."
            exit 0
            ;;
        3)
            echo -e "${YELLOW}Continuando sem login...${NC}"
            ;;
    esac
fi

# =============================================================================
# PULL DAS IMAGENS COM RETRY
# =============================================================================

echo -e "\n${BLUE}📦 Baixando imagens necessárias...${NC}"

pull_with_retry() {
    local image=$1
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo -e "  Baixando ${CYAN}$image${NC} (tentativa $attempt/$max_attempts)..."
        
        if docker pull "$image" 2>&1; then
            echo -e "  ${GREEN}✅ $image${NC}"
            return 0
        else
            if [ $attempt -lt $max_attempts ]; then
                echo -e "  ${YELLOW}⚠️ Falhou, aguardando 30s antes de tentar novamente...${NC}"
                sleep 30
            fi
        fi
        ((attempt++))
    done
    
    echo -e "  ${RED}❌ Não foi possível baixar $image${NC}"
    return 1
}

# Imagens necessárias
IMAGES=(
    "postgres:16-alpine"
    "node:20-alpine"
    "python:3.11-slim"
)

FAILED=0
for img in "${IMAGES[@]}"; do
    if ! pull_with_retry "$img"; then
        FAILED=1
    fi
done

if [ $FAILED -eq 1 ]; then
    echo -e "\n${RED}❌ Algumas imagens falharam ao baixar.${NC}"
    echo -e "${YELLOW}Tente fazer login no Docker Hub: docker login${NC}"
    echo -e "Ou aguarde alguns minutos e tente novamente."
    read -p "Deseja continuar mesmo assim? (s/N): " cont
    if [[ ! $cont =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

# =============================================================================
# PARA CONTAINERS ANTIGOS
# =============================================================================

echo -e "\n${BLUE}🧹 Limpando containers antigos...${NC}"
docker-compose down 2>/dev/null || true
docker rm -f contabil-postgres contabil-backend contabil-frontend 2>/dev/null || true

# =============================================================================
# BUILD E START
# =============================================================================

echo -e "\n${BLUE}🔨 Construindo e iniciando containers...${NC}"

# Build sem cache para evitar problemas
docker-compose build --no-cache

# Inicia
docker-compose up -d

# =============================================================================
# AGUARDA SERVIÇOS
# =============================================================================

echo -e "\n${BLUE}⏳ Aguardando serviços iniciarem...${NC}"

# Aguarda PostgreSQL
echo -n "  PostgreSQL"
for i in {1..30}; do
    if docker exec contabil-postgres pg_isready -U contabil -d contabil_db &>/dev/null; then
        echo -e " ${GREEN}✅${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Aguarda Backend
echo -n "  Backend"
for i in {1..60}; do
    if curl -s http://localhost:8000/health &>/dev/null; then
        echo -e " ${GREEN}✅${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Aguarda Frontend
echo -n "  Frontend"
for i in {1..30}; do
    if curl -s http://localhost &>/dev/null; then
        echo -e " ${GREEN}✅${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# =============================================================================
# SUCESSO
# =============================================================================

echo -e "\n${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✅ SISTEMA INICIADO COM SUCESSO!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "   ${CYAN}🌐 Frontend:${NC}  http://localhost"
echo -e "   ${CYAN}🔧 Backend:${NC}   http://localhost:8000"
echo -e "   ${CYAN}📚 API Docs:${NC}  http://localhost:8000/docs"
echo -e "   ${CYAN}🗄️  Database:${NC} localhost:5432"
echo ""
echo -e "   ${YELLOW}Ver logs:${NC}     docker-compose logs -f"
echo -e "   ${YELLOW}Parar:${NC}        docker-compose down"
echo ""
