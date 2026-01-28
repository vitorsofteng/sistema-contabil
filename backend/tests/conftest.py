"""
Configuração do pytest - Fixtures compartilhadas
Sprint 4 - Testes de Integração + CI/CD
"""

import pytest
import sys
import os
from typing import Generator, Dict, Any
from unittest.mock import MagicMock, patch

# Configura ambiente de testes
os.environ["ENVIRONMENT"] = "testing"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-12345"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-chars-ok!"


# ============================================================================
# FIXTURES PARA TESTES UNITÁRIOS (sem dependências externas)
# ============================================================================

@pytest.fixture
def sample_empresa_data() -> Dict[str, Any]:
    """Dados de exemplo de empresa."""
    return {
        "nome": "Empresa Teste LTDA",
        "cnpj": "12.345.678/0001-90",
        "segmento": "Comércio",
        "porte": "Pequena"
    }


@pytest.fixture
def sample_dados_mensais() -> Dict[str, Any]:
    """Dados mensais de exemplo."""
    return {
        "mes": 1,
        "ano": 2024,
        "receita_bruta": 100000.00,
        "custos": 60000.00,
        "despesas_operacionais": 20000.00,
        "despesas_financeiras": 5000.00,
        "impostos": 3000.00,
        "lucro_liquido": 12000.00,
        "ativo_total": 500000.00,
        "ativo_circulante": 200000.00,
        "passivo_total": 300000.00,
        "passivo_circulante": 150000.00,
        "patrimonio_liquido": 200000.00,
        "disponivel": 50000.00
    }


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Dados de exemplo de usuário."""
    return {
        "nome": "Contador Teste",
        "email": "teste@contabil.com",
        "senha": "Senha@123"
    }


@pytest.fixture
def multiple_empresas_data() -> list:
    """Lista de empresas para testes de múltiplos registros."""
    return [
        {"nome": "Empresa Alpha LTDA", "cnpj": "11.111.111/0001-11", "segmento": "Indústria", "porte": "Média"},
        {"nome": "Empresa Beta SA", "cnpj": "22.222.222/0001-22", "segmento": "Serviços", "porte": "Grande"},
        {"nome": "Empresa Gamma ME", "cnpj": "33.333.333/0001-33", "segmento": "Comércio", "porte": "Pequena"},
    ]


@pytest.fixture
def multiple_meses_data() -> list:
    """Dados de múltiplos meses para análise."""
    base = {
        "despesas_operacionais": 20000.00,
        "despesas_financeiras": 5000.00,
        "impostos": 3000.00,
        "ativo_total": 500000.00,
        "ativo_circulante": 200000.00,
        "passivo_total": 300000.00,
        "passivo_circulante": 150000.00,
        "patrimonio_liquido": 200000.00,
        "disponivel": 50000.00
    }
    
    return [
        {**base, "mes": 1, "ano": 2024, "receita_bruta": 100000, "custos": 60000, "lucro_liquido": 12000},
        {**base, "mes": 2, "ano": 2024, "receita_bruta": 110000, "custos": 62000, "lucro_liquido": 15000},
        {**base, "mes": 3, "ano": 2024, "receita_bruta": 105000, "custos": 61000, "lucro_liquido": 14000},
        {**base, "mes": 4, "ano": 2024, "receita_bruta": 120000, "custos": 65000, "lucro_liquido": 18000},
        {**base, "mes": 5, "ano": 2024, "receita_bruta": 115000, "custos": 63000, "lucro_liquido": 17000},
        {**base, "mes": 6, "ano": 2024, "receita_bruta": 130000, "custos": 68000, "lucro_liquido": 22000},
    ]


# ============================================================================
# FIXTURES PARA MOCKS
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock de sessão de banco de dados."""
    mock_session = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.rollback = MagicMock()
    mock_session.close = MagicMock()
    mock_session.query = MagicMock()
    mock_session.add = MagicMock()
    mock_session.delete = MagicMock()
    mock_session.execute = MagicMock()
    return mock_session


@pytest.fixture
def mock_email_service():
    """Mock de serviço de email."""
    mock = MagicMock()
    mock.send_email = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_redis():
    """Mock de cliente Redis."""
    mock = MagicMock()
    mock.get = MagicMock(return_value=None)
    mock.set = MagicMock(return_value=True)
    mock.delete = MagicMock(return_value=True)
    mock.exists = MagicMock(return_value=False)
    return mock


# ============================================================================
# CONFIGURAÇÃO DO PYTEST
# ============================================================================

def pytest_configure(config):
    """Configuração do pytest."""
    config.addinivalue_line("markers", "unit: Testes unitários puros")
    config.addinivalue_line("markers", "integration: Testes de integração")
    config.addinivalue_line("markers", "e2e: Testes end-to-end")
    config.addinivalue_line("markers", "slow: Testes lentos")
    config.addinivalue_line("markers", "load: Testes de carga")


def pytest_collection_modifyitems(config, items):
    """Modifica itens de teste para adicionar markers automaticamente."""
    for item in items:
        # Marca testes de integração
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Marca testes e2e
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        
        # Marca testes de carga
        if "load" in item.nodeid:
            item.add_marker(pytest.mark.load)
