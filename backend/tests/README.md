# 🧪 Testes - Sistema Contábil

## Visão Geral

Este módulo contém os testes automatizados do Sistema Contábil, organizados em diferentes níveis:

| Tipo | Arquivo | Descrição | Quantidade |
|------|---------|-----------|------------|
| **Unitários** | `test_security.py` | Segurança básica | 36 testes |
| **Unitários** | `test_security_advanced.py` | Segurança avançada (2FA, criptografia) | 27 testes |
| **Unitários** | `test_analise.py` | Análise financeira e indicadores | 35 testes |
| **Integração** | `test_integration_api.py` | API REST e fluxos integrados | 25+ testes |
| **E2E** | `test_e2e_flows.py` | Fluxos completos de uso | 15+ testes |
| **Carga** | `test_load.py` | Performance e stress | 12+ testes |

**Total: 150+ testes**

## Executando os Testes

### Dentro do Container Docker

```bash
# Acessar o container
docker exec -it contabil-backend bash

# Executar testes
./run_tests.sh --all
```

### Opções Disponíveis

```bash
# Testes unitários (padrão)
./run_tests.sh --unit

# Testes de integração
./run_tests.sh --integration

# Testes E2E
./run_tests.sh --e2e

# Testes de carga
./run_tests.sh --load

# Todos os testes
./run_tests.sh --all

# Testes rápidos (unit + integration)
./run_tests.sh --fast

# Com cobertura de código
./run_tests.sh --coverage

# Modo CI (completo + cobertura)
./run_tests.sh --ci
```

### Executando Diretamente com Pytest

```bash
# Todos os testes
pytest tests/ -v -p no:asyncio

# Apenas um arquivo
pytest tests/test_security.py -v -p no:asyncio

# Com cobertura
pytest tests/ --cov=. --cov-report=html

# Testes específicos por marker
pytest tests/ -m unit -v
pytest tests/ -m integration -v
pytest tests/ -m e2e -v
```

## Estrutura dos Testes

### Testes Unitários

Testam componentes isolados sem dependências externas:

- **PasswordValidator** - Validação de senhas fortes
- **InputSanitizer** - Proteção contra SQL Injection e XSS
- **RateLimiter** - Controle de requisições
- **TOTP** - Autenticação de dois fatores
- **DataEncryption** - Criptografia de dados
- **IndicadoresFinanceiros** - Cálculos contábeis
- **ClassificadorSaude** - Score de saúde financeira

### Testes de Integração

Testam integração entre componentes:

- **AuthIntegration** - Fluxo de autenticação
- **EmpresasIntegration** - CRUD de empresas
- **AnaliseIntegration** - Análise financeira
- **ConcurrencyIntegration** - Múltiplos usuários

### Testes E2E

Simulam cenários reais de uso:

- **OnboardingFlow** - Novo contador usando o sistema
- **AnalysisFlow** - Análise mensal de empresa
- **AlertFlow** - Sistema de alertas
- **MultiCompanyFlow** - Gestão de múltiplas empresas
- **SessionFlow** - Gerenciamento de sessão

### Testes de Carga

Medem performance do sistema:

- **Throughput** - Operações por segundo
- **Latência** - Tempo de resposta
- **Concorrência** - Múltiplas threads
- **Stress** - Grande volume de dados
- **Memória** - Uso de recursos

## CI/CD Pipeline

O projeto inclui pipeline GitHub Actions (`.github/workflows/ci.yml`):

```
┌─────────────────┐
│  Push/PR        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Testes Unitários│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Testes Integração│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Testes E2E    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Testes de Carga │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Cobertura    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Lint + Sec    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Docker   │
└─────────────────┘
```

## Cobertura de Código

Meta mínima: **50%**

Relatórios são gerados em:
- **HTML**: `htmlcov/index.html`
- **XML**: `coverage.xml`
- **JSON**: `coverage.json`

## Markers do Pytest

```python
@pytest.mark.unit          # Testes unitários
@pytest.mark.integration   # Testes de integração
@pytest.mark.e2e           # Testes end-to-end
@pytest.mark.slow          # Testes lentos (>1s)
@pytest.mark.load          # Testes de carga
```

## Fixtures Disponíveis

| Fixture | Descrição |
|---------|-----------|
| `sample_empresa_data` | Dados de empresa de teste |
| `sample_dados_mensais` | Dados mensais de exemplo |
| `sample_user_data` | Dados de usuário de teste |
| `multiple_empresas_data` | Lista de empresas |
| `multiple_meses_data` | Dados de 6 meses |
| `mock_db_session` | Mock de sessão de banco |
| `mock_email_service` | Mock de serviço de email |
| `mock_redis` | Mock de cliente Redis |

## Adicionando Novos Testes

### Teste Unitário

```python
class TestMinhaFuncionalidade:
    def test_caso_sucesso(self):
        resultado = minha_funcao(entrada_valida)
        assert resultado == esperado
    
    def test_caso_erro(self):
        with pytest.raises(ValueError):
            minha_funcao(entrada_invalida)
```

### Teste de Integração

```python
class TestMinhaIntegracao:
    @pytest.fixture
    def setup(self):
        # Configuração
        return dados_necessarios
    
    def test_fluxo_integrado(self, setup):
        # Passo 1
        resultado1 = api.chamar_endpoint1()
        # Passo 2
        resultado2 = api.chamar_endpoint2(resultado1)
        # Verificação
        assert resultado2.status == 200
```

## Troubleshooting

### Erro: `asyncio_mode`

Se aparecer warning sobre `asyncio_mode`, certifique-se de usar `-p no:asyncio`:

```bash
pytest tests/ -v -p no:asyncio
```

### Erro: Módulo não encontrado

Os testes são standalone e não requerem as dependências do projeto (fastapi, sqlalchemy, etc.).

### Testes lentos

Use `--timeout=60` para testes que podem demorar mais:

```bash
pytest tests/test_load.py --timeout=60
```

## Métricas de Performance

Benchmarks esperados:

| Operação | Alvo | Medição |
|----------|------|---------|
| Registro usuário | >1000/s | `test_throughput_registro_usuarios` |
| Criação empresa | >1000/s | `test_throughput_criacao_empresas` |
| Cálculo indicadores | >50000/s | `test_throughput_calculo_indicadores` |
| Latência P95 | <5ms | `test_response_time_p95` |
| Latência P99 | <10ms | `test_response_time_p95` |
