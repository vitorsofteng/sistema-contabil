#!/bin/bash

# ============================================
# SCRIPT DE SETUP INICIAL
# ============================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Setup do Sistema Contábil${NC}"
echo ""

# Verificar pré-requisitos
echo -e "${YELLOW}📋 Verificando pré-requisitos...${NC}"

# Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não encontrado. Instale em: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi
echo -e "  ✅ Docker instalado"

# Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose não encontrado${NC}"
    exit 1
fi
echo -e "  ✅ Docker Compose instalado"

# Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git não encontrado${NC}"
    exit 1
fi
echo -e "  ✅ Git instalado"

echo ""

# Configurar ambiente
echo -e "${YELLOW}⚙️ Configurando ambiente...${NC}"

# Criar .env se não existir
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "  ✅ Arquivo .env criado a partir do .env.example"
    else
        echo -e "${RED}❌ Arquivo .env.example não encontrado${NC}"
        exit 1
    fi
else
    echo -e "  ⏭️  Arquivo .env já existe"
fi

# Gerar JWT_SECRET se não estiver definido
if grep -q "JWT_SECRET=.*CHANGE\|JWT_SECRET=$" .env 2>/dev/null; then
    NEW_SECRET=$(openssl rand -hex 32)
    sed -i "s/JWT_SECRET=.*/JWT_SECRET=$NEW_SECRET/" .env
    echo -e "  ✅ JWT_SECRET gerado automaticamente"
fi

echo ""

# Build das imagens
echo -e "${YELLOW}🏗️ Construindo imagens Docker...${NC}"
docker-compose build

echo ""

# Subir containers
echo -e "${YELLOW}🐳 Iniciando containers...${NC}"
docker-compose up -d

# Aguardar banco ficar pronto
echo -e "${YELLOW}⏳ Aguardando banco de dados...${NC}"
sleep 5

# Verificar se banco está pronto
for i in {1..30}; do
    if docker-compose exec -T db pg_isready -U contabil > /dev/null 2>&1; then
        echo -e "  ✅ Banco de dados pronto"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Timeout aguardando banco de dados${NC}"
        exit 1
    fi
    sleep 1
done

echo ""

# Executar migrations
echo -e "${YELLOW}📦 Executando migrations...${NC}"
docker-compose exec -T backend alembic upgrade head || echo -e "  ⚠️ Algumas migrations podem ter falhado (verificar manualmente)"

echo ""

# Health check
echo -e "${YELLOW}🏥 Verificando saúde dos serviços...${NC}"
sleep 3

if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "  ✅ Backend: http://localhost:8000"
else
    echo -e "  ${YELLOW}⚠️ Backend ainda iniciando...${NC}"
fi

if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo -e "  ✅ Frontend: http://localhost:3000"
else
    echo -e "  ${YELLOW}⚠️ Frontend ainda iniciando...${NC}"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ Setup concluído com sucesso!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "📌 Próximos passos:"
echo -e "   1. Acesse http://localhost:3000"
echo -e "   2. Crie uma conta de contador"
echo -e "   3. Importe dados de teste"
echo ""
echo -e "📚 Comandos úteis:"
echo -e "   make dev          - Inicia o ambiente"
echo -e "   make logs         - Ver logs"
echo -e "   make test         - Executar testes"
echo -e "   make help         - Ver todos os comandos"
echo ""
