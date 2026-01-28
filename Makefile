# ============================================================================
# Makefile - Sistema Contábil
# ============================================================================

.PHONY: help install test test-unit test-cov lint clean docker-up docker-down

# Variáveis
PYTHON = python3
PIP = pip3
PYTEST = pytest
DOCKER_COMPOSE = docker-compose

# Ajuda
help:
	@echo "============================================"
	@echo "  Sistema Contábil - Comandos Disponíveis"
	@echo "============================================"
	@echo ""
	@echo "  make install      - Instala dependências"
	@echo "  make test         - Executa todos os testes"
	@echo "  make test-unit    - Executa testes unitários"
	@echo "  make test-cov     - Executa testes com cobertura"
	@echo "  make lint         - Verifica estilo de código"
	@echo "  make clean        - Remove arquivos temporários"
	@echo "  make docker-up    - Inicia containers Docker"
	@echo "  make docker-down  - Para containers Docker"
	@echo ""

# Instalação
install:
	cd backend && $(PIP) install -r requirements.txt --break-system-packages

install-dev: install
	cd backend && $(PIP) install pytest pytest-cov pytest-asyncio httpx black flake8 --break-system-packages

# Testes
test:
	cd backend && ENVIRONMENT=testing RATE_LIMIT_ENABLED=false $(PYTEST) tests/ -v

test-unit:
	cd backend && ENVIRONMENT=testing RATE_LIMIT_ENABLED=false $(PYTEST) tests/ -v -m "unit or not integration"

test-cov:
	cd backend && ENVIRONMENT=testing RATE_LIMIT_ENABLED=false $(PYTEST) tests/ \
		--cov=core \
		--cov=api \
		--cov=engine \
		--cov=data \
		--cov-report=term-missing \
		--cov-report=html \
		-v

test-security:
	cd backend && ENVIRONMENT=testing RATE_LIMIT_ENABLED=false $(PYTEST) tests/test_security*.py -v

test-auth:
	cd backend && ENVIRONMENT=testing RATE_LIMIT_ENABLED=false $(PYTEST) tests/test_auth.py -v

test-fast:
	cd backend && ENVIRONMENT=testing RATE_LIMIT_ENABLED=false $(PYTEST) tests/ -v --tb=short -q

# Linting
lint:
	cd backend && flake8 api core engine data --max-line-length=120

format:
	cd backend && black api core engine data tests --line-length=120

# Limpeza
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name "test_*.db" -delete
	rm -f backend/test_contabil.db

# Docker
docker-up:
	$(DOCKER_COMPOSE) up -d --build

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f

docker-restart:
	$(DOCKER_COMPOSE) restart

# Banco de dados
db-migrate:
	cd backend && alembic upgrade head

db-rollback:
	cd backend && alembic downgrade -1

# Desenvolvimento
dev:
	cd backend && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Produção
prod:
	cd backend && uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
