#!/bin/bash
# ==============================================================================
# Script de Execução de Testes - Sistema Contábil
# Sprint 4 - CI/CD
# ==============================================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Variáveis de ambiente
export ENVIRONMENT=testing
export RATE_LIMIT_ENABLED=false

# ==============================================================================
# FUNÇÕES
# ==============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}=============================================="
    echo -e "  $1"
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

show_help() {
    echo "Uso: ./run_tests.sh [OPÇÃO]"
    echo ""
    echo "Opções:"
    echo "  --unit          Executa apenas testes unitários"
    echo "  --integration   Executa apenas testes de integração"
    echo "  --e2e           Executa apenas testes E2E"
    echo "  --load          Executa apenas testes de carga"
    echo "  --coverage      Executa testes com cobertura de código"
    echo "  --all           Executa todos os testes"
    echo "  --fast          Executa testes rápidos (unit + integration)"
    echo "  --ci            Modo CI (todos os testes + cobertura)"
    echo "  --help          Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  ./run_tests.sh --unit"
    echo "  ./run_tests.sh --coverage"
    echo "  ./run_tests.sh --all"
}

run_unit_tests() {
    print_header "TESTES UNITÁRIOS"
    pytest tests/test_security.py tests/test_security_advanced.py tests/test_analise.py \
        -v -p no:asyncio --tb=short
}

run_integration_tests() {
    print_header "TESTES DE INTEGRAÇÃO"
    pytest tests/test_integration_api.py \
        -v -p no:asyncio --tb=short
}

run_e2e_tests() {
    print_header "TESTES E2E"
    pytest tests/test_e2e_flows.py \
        -v -p no:asyncio --tb=short
}

run_load_tests() {
    print_header "TESTES DE CARGA"
    pytest tests/test_load.py \
        -v -p no:asyncio --tb=short -s
}

run_with_coverage() {
    print_header "TESTES COM COBERTURA"
    pytest tests/ \
        -v -p no:asyncio --tb=short \
        --cov=. \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-report=xml \
        --cov-fail-under=50
    
    echo ""
    print_info "Relatório HTML gerado em: htmlcov/index.html"
}

run_all_tests() {
    print_header "TODOS OS TESTES"
    pytest tests/ -v -p no:asyncio --tb=short
}

run_fast_tests() {
    print_header "TESTES RÁPIDOS"
    pytest tests/test_security.py tests/test_security_advanced.py tests/test_analise.py tests/test_integration_api.py \
        -v -p no:asyncio --tb=short
}

run_ci_mode() {
    print_header "MODO CI - PIPELINE COMPLETO"
    
    echo ""
    print_info "Executando testes unitários..."
    run_unit_tests
    
    echo ""
    print_info "Executando testes de integração..."
    run_integration_tests
    
    echo ""
    print_info "Executando testes E2E..."
    run_e2e_tests
    
    echo ""
    print_info "Executando testes de carga..."
    run_load_tests
    
    echo ""
    print_info "Gerando relatório de cobertura..."
    run_with_coverage
}

# ==============================================================================
# MAIN
# ==============================================================================

print_header "SISTEMA CONTÁBIL - TESTES"

# Verificar argumento
case "${1:-}" in
    --unit)
        run_unit_tests
        ;;
    --integration)
        run_integration_tests
        ;;
    --e2e)
        run_e2e_tests
        ;;
    --load)
        run_load_tests
        ;;
    --coverage)
        run_with_coverage
        ;;
    --all)
        run_all_tests
        ;;
    --fast)
        run_fast_tests
        ;;
    --ci)
        run_ci_mode
        ;;
    --help|-h)
        show_help
        exit 0
        ;;
    "")
        # Padrão: testes unitários
        run_unit_tests
        ;;
    *)
        print_error "Opção inválida: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

# Resultado final
if [ $? -eq 0 ]; then
    echo ""
    print_success "TESTES CONCLUÍDOS COM SUCESSO!"
else
    echo ""
    print_error "ALGUNS TESTES FALHARAM"
    exit 1
fi
