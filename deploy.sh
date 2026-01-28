#!/bin/bash
# ==============================================================================
# Script de Gerenciamento de Ambientes - Sistema Contábil
# ==============================================================================
# Uso: ./deploy.sh [ambiente] [ação]
# Exemplos:
#   ./deploy.sh dev up        # Sobe ambiente de desenvolvimento
#   ./deploy.sh staging up    # Sobe ambiente de homologação
#   ./deploy.sh prod up       # Sobe ambiente de produção
#   ./deploy.sh dev down      # Derruba ambiente de desenvolvimento
#   ./deploy.sh dev logs      # Ver logs do ambiente de desenvolvimento

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ==============================================================================
# FUNÇÕES
# ==============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}=============================================="
    echo -e "  SISTEMA CONTÁBIL - DEPLOY"
    echo -e "==============================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

show_help() {
    echo "Uso: ./deploy.sh [AMBIENTE] [AÇÃO]"
    echo ""
    echo "Ambientes:"
    echo "  dev, development    Ambiente de desenvolvimento local"
    echo "  staging, homolog    Ambiente de homologação"
    echo "  prod, production    Ambiente de produção"
    echo ""
    echo "Ações:"
    echo "  up                  Iniciar ambiente"
    echo "  down                Parar ambiente"
    echo "  restart             Reiniciar ambiente"
    echo "  logs                Ver logs (Ctrl+C para sair)"
    echo "  status              Ver status dos containers"
    echo "  build               Rebuild das imagens"
    echo "  shell               Acessar shell do backend"
    echo "  db                  Acessar banco de dados"
    echo "  test                Executar testes"
    echo "  migrate             Executar migrations"
    echo ""
    echo "Exemplos:"
    echo "  ./deploy.sh dev up"
    echo "  ./deploy.sh staging logs"
    echo "  ./deploy.sh prod status"
}

get_compose_file() {
    case $1 in
        dev|development)
            echo "docker-compose.yml"
            ;;
        staging|homolog)
            echo "docker-compose.staging.yml"
            ;;
        prod|production)
            echo "docker-compose.prod.yml"
            ;;
        *)
            echo ""
            ;;
    esac
}

get_env_file() {
    case $1 in
        dev|development)
            echo ".env.development"
            ;;
        staging|homolog)
            echo ".env.staging"
            ;;
        prod|production)
            echo ".env.production"
            ;;
        *)
            echo ""
            ;;
    esac
}

check_env_file() {
    local env_file=$1
    if [ ! -f "$env_file" ]; then
        print_error "Arquivo de ambiente não encontrado: $env_file"
        print_info "Copie o arquivo de exemplo e configure:"
        echo "  cp .env.example $env_file"
        exit 1
    fi
}

confirm_production() {
    if [[ "$1" == "prod" || "$1" == "production" ]]; then
        print_warning "ATENÇÃO: Você está prestes a executar em PRODUÇÃO!"
        read -p "Digite 'CONFIRMAR' para continuar: " confirmation
        if [ "$confirmation" != "CONFIRMAR" ]; then
            print_error "Operação cancelada"
            exit 1
        fi
    fi
}

# ==============================================================================
# AÇÕES
# ==============================================================================

action_up() {
    local compose_file=$1
    local env_file=$2
    
    print_info "Iniciando ambiente..."
    
    # Copiar arquivo de ambiente
    cp "$env_file" .env
    
    docker-compose -f "$compose_file" up -d --build
    
    print_success "Ambiente iniciado!"
    echo ""
    print_info "Serviços:"
    docker-compose -f "$compose_file" ps
}

action_down() {
    local compose_file=$1
    
    print_info "Parando ambiente..."
    docker-compose -f "$compose_file" down
    print_success "Ambiente parado!"
}

action_restart() {
    local compose_file=$1
    local env_file=$2
    
    print_info "Reiniciando ambiente..."
    docker-compose -f "$compose_file" down
    cp "$env_file" .env
    docker-compose -f "$compose_file" up -d --build
    print_success "Ambiente reiniciado!"
}

action_logs() {
    local compose_file=$1
    
    print_info "Exibindo logs (Ctrl+C para sair)..."
    docker-compose -f "$compose_file" logs -f
}

action_status() {
    local compose_file=$1
    
    print_info "Status dos containers:"
    docker-compose -f "$compose_file" ps
}

action_build() {
    local compose_file=$1
    
    print_info "Rebuilding imagens..."
    docker-compose -f "$compose_file" build --no-cache
    print_success "Build concluído!"
}

action_shell() {
    local compose_file=$1
    
    print_info "Acessando shell do backend..."
    docker-compose -f "$compose_file" exec backend bash
}

action_db() {
    local compose_file=$1
    
    print_info "Acessando banco de dados..."
    docker-compose -f "$compose_file" exec db psql -U contabil -d contabil
}

action_test() {
    local compose_file=$1
    
    print_info "Executando testes..."
    docker-compose -f "$compose_file" exec backend pytest tests/ -v -p no:asyncio
}

action_migrate() {
    local compose_file=$1
    
    print_info "Executando migrations..."
    docker-compose -f "$compose_file" exec backend alembic upgrade head
    print_success "Migrations aplicadas!"
}

# ==============================================================================
# MAIN
# ==============================================================================

print_header

# Verificar argumentos
if [ $# -lt 2 ]; then
    show_help
    exit 1
fi

AMBIENTE=$1
ACAO=$2

# Obter arquivos de configuração
COMPOSE_FILE=$(get_compose_file "$AMBIENTE")
ENV_FILE=$(get_env_file "$AMBIENTE")

if [ -z "$COMPOSE_FILE" ]; then
    print_error "Ambiente inválido: $AMBIENTE"
    show_help
    exit 1
fi

# Verificar arquivo compose
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "Arquivo não encontrado: $COMPOSE_FILE"
    exit 1
fi

# Confirmar se for produção
if [[ "$ACAO" == "up" || "$ACAO" == "restart" || "$ACAO" == "migrate" ]]; then
    confirm_production "$AMBIENTE"
fi

# Executar ação
case $ACAO in
    up)
        check_env_file "$ENV_FILE"
        action_up "$COMPOSE_FILE" "$ENV_FILE"
        ;;
    down)
        action_down "$COMPOSE_FILE"
        ;;
    restart)
        check_env_file "$ENV_FILE"
        action_restart "$COMPOSE_FILE" "$ENV_FILE"
        ;;
    logs)
        action_logs "$COMPOSE_FILE"
        ;;
    status)
        action_status "$COMPOSE_FILE"
        ;;
    build)
        action_build "$COMPOSE_FILE"
        ;;
    shell)
        action_shell "$COMPOSE_FILE"
        ;;
    db)
        action_db "$COMPOSE_FILE"
        ;;
    test)
        action_test "$COMPOSE_FILE"
        ;;
    migrate)
        action_migrate "$COMPOSE_FILE"
        ;;
    *)
        print_error "Ação inválida: $ACAO"
        show_help
        exit 1
        ;;
esac

echo ""
print_info "Ambiente: $AMBIENTE | Compose: $COMPOSE_FILE"
