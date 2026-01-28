#!/bin/bash
# =============================================================================
# Script para criar contador e 4 empresas de teste
# Rodar no WSL após o docker-compose up
# =============================================================================

API_URL="http://localhost:8000"

echo "=============================================="
echo "  SETUP INICIAL - SISTEMA CONTÁBIL"
echo "=============================================="
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verifica se a API está rodando
echo "Verificando API..."
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}ERRO: API não está respondendo em $API_URL${NC}"
    echo "Execute primeiro: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ API online${NC}"
echo ""

# =============================================================================
# 1. REGISTRAR CONTADOR
# =============================================================================
echo "1. Registrando contador..."

# Senha forte que atende aos requisitos:
# - 8+ caracteres
# - 1 maiúscula, 1 minúscula, 1 número, 1 especial
SENHA="Contador@123"

REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/registrar" \
    -H "Content-Type: application/json" \
    -d "{
        \"nome\": \"João Contador\",
        \"email\": \"joao@contabil.com\",
        \"senha\": \"$SENHA\",
        \"telefone\": \"(11) 99999-9999\"
    }")

# Verifica se já existe
if echo "$REGISTER_RESPONSE" | grep -q "já cadastrado"; then
    echo "   Contador já existe, fazendo login..."
    LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"joao@contabil.com\", \"senha\": \"$SENHA\"}")
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
else
    TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
fi

if [ -z "$TOKEN" ]; then
    echo -e "${RED}ERRO: Não foi possível obter token${NC}"
    echo "Resposta: $REGISTER_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Autenticado com sucesso${NC}"
echo ""

# =============================================================================
# 2. CRIAR EMPRESAS
# =============================================================================
echo "2. Criando empresas..."
echo ""

# Função para criar empresa
criar_empresa() {
    local nome="$1"
    local cnpj="$2"
    local regime="$3"
    local setor="$4"
    
    RESPONSE=$(curl -s -X POST "$API_URL/empresas" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{
            \"razao_social\": \"$nome\",
            \"cnpj\": \"$cnpj\",
            \"regime_tributario\": \"$regime\",
            \"setor\": \"$setor\"
        }")
    
    ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    
    if [ -n "$ID" ]; then
        echo -e "   ${GREEN}✓ $nome (ID: $ID)${NC}"
        echo "$ID"
    else
        # Pode já existir, tenta listar
        echo -e "   ${YELLOW}! $nome - pode já existir${NC}"
        echo "0"
    fi
}

echo "   Criando Tech Solutions Ltda..."
ID1=$(criar_empresa "Tech Solutions Ltda" "12.345.678/0001-90" "Lucro Presumido" "Tecnologia")

echo "   Criando Comércio Central Ltda..."
ID2=$(criar_empresa "Comércio Central Ltda" "23.456.789/0001-01" "Simples Nacional" "Comércio")

echo "   Criando Restaurante Sabor & Arte..."
ID3=$(criar_empresa "Restaurante Sabor & Arte" "34.567.890/0001-12" "Simples Nacional" "Alimentação")

echo "   Criando Distribuidora Flex SA..."
ID4=$(criar_empresa "Distribuidora Flex SA" "45.678.901/0001-23" "Lucro Real" "Distribuição")

echo ""

# =============================================================================
# 3. LISTAR EMPRESAS CRIADAS
# =============================================================================
echo "3. Empresas cadastradas:"
echo ""

EMPRESAS=$(curl -s -X GET "$API_URL/empresas" \
    -H "Authorization: Bearer $TOKEN")

echo "$EMPRESAS" | grep -o '"razao_social":"[^"]*"' | while read line; do
    nome=$(echo "$line" | cut -d'"' -f4)
    echo "   • $nome"
done

echo ""
echo "=============================================="
echo -e "${GREEN}  SETUP CONCLUÍDO!${NC}"
echo "=============================================="
echo ""
echo "Credenciais de acesso:"
echo "  Email: joao@contabil.com"
echo "  Senha: Contador@123"
echo ""
echo "Próximos passos:"
echo "  1. Acesse http://localhost no navegador"
echo "  2. Faça login com as credenciais acima"
echo "  3. Clique em cada empresa"
echo "  4. Importe o CSV correspondente:"
echo ""
echo "     Tech Solutions      → empresa1_tech_solutions.csv"
echo "     Comércio Central    → empresa2_comercio_central.csv"
echo "     Restaurante Sabor   → empresa3_restaurante_sabor.csv"
echo "     Distribuidora Flex  → empresa4_distribuidora_flex.csv"
echo ""
echo "=============================================="
