# ============================================
# MAKEFILE - Sistema Contábil
# ============================================

.PHONY: help dev up down logs test lint build deploy-staging deploy-prod backup migrate clean

# Cores para output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m

# Variáveis
ENV ?= development
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_STAGING = docker-compose -f docker-compose.staging.yml
DOCKER_COMPOSE_PROD = docker-compose -f docker-compose.prod.yml

# ============================================
# HELP
# ============================================
help: ## Mostra esta ajuda
	@echo ""
	@echo "$(GREEN)Sistema Contábil - Comandos Disponíveis$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ============================================
# DESENVOLVIMENTO
# ============================================
dev: ## Inicia ambiente de desenvolvimento com hot-reload
	@echo "$(GREEN)🚀 Iniciando ambiente de desenvolvimento...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Ambiente pronto!$(NC)"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

up: ## Sobe os containers
	$(DOCKER_COMPOSE) up -d

down: ## Para os containers
	$(DOCKER_COMPOSE) down

restart: ## Reinicia os containers
	$(DOCKER_COMPOSE) restart

logs: ## Mostra logs em tempo real
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Mostra logs do backend
	$(DOCKER_COMPOSE) logs -f backend

logs-frontend: ## Mostra logs do frontend
	$(DOCKER_COMPOSE) logs -f frontend

shell-backend: ## Abre shell no container backend
	$(DOCKER_COMPOSE) exec backend bash

shell-db: ## Abre psql no container do banco
	$(DOCKER_COMPOSE) exec db psql -U contabil -d contabil

# ============================================
# TESTES
# ============================================
test: ## Executa todos os testes
	@echo "$(GREEN)🧪 Executando testes...$(NC)"
	$(DOCKER_COMPOSE) exec backend pytest tests/ -v

test-cov: ## Executa testes com cobertura
	@echo "$(GREEN)🧪 Executando testes com cobertura...$(NC)"
	$(DOCKER_COMPOSE) exec backend pytest tests/ -v --cov=. --cov-report=html
	@echo "$(GREEN)📊 Relatório em backend/htmlcov/index.html$(NC)"

# ============================================
# QUALIDADE DE CÓDIGO
# ============================================
lint: ## Verifica qualidade do código
	@echo "$(GREEN)🔍 Verificando código...$(NC)"
	$(DOCKER_COMPOSE) exec backend ruff check . || true
	$(DOCKER_COMPOSE) exec backend black --check . || true

format: ## Formata o código automaticamente
	@echo "$(GREEN)🎨 Formatando código...$(NC)"
	$(DOCKER_COMPOSE) exec backend black .
	$(DOCKER_COMPOSE) exec backend isort .

# ============================================
# BUILD
# ============================================
build: ## Build das imagens Docker
	@echo "$(GREEN)🏗️ Building images...$(NC)"
	$(DOCKER_COMPOSE) build --no-cache

build-backend: ## Build apenas do backend
	$(DOCKER_COMPOSE) build backend

build-frontend: ## Build apenas do frontend
	$(DOCKER_COMPOSE) build frontend

# ============================================
# DATABASE
# ============================================
migrate: ## Executa migrations
	@echo "$(GREEN)📦 Executando migrations...$(NC)"
	$(DOCKER_COMPOSE) exec backend alembic upgrade head

migrate-rollback: ## Reverte última migration
	$(DOCKER_COMPOSE) exec backend alembic downgrade -1

backup-db: ## Cria backup do banco
	@echo "$(GREEN)💾 Criando backup...$(NC)"
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec db pg_dump -U contabil contabil > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup criado em backups/$(NC)"

# ============================================
# DEPLOY HOMOLOGAÇÃO
# ============================================
deploy-staging: ## Deploy em homologação
	@echo "$(GREEN)🚀 Deploy em HOMOLOGAÇÃO...$(NC)"
	$(DOCKER_COMPOSE_STAGING) pull
	$(DOCKER_COMPOSE_STAGING) up -d
	@echo "$(GREEN)✅ Deploy em homologação concluído$(NC)"

staging-logs: ## Logs de homologação
	$(DOCKER_COMPOSE_STAGING) logs -f

# ============================================
# DEPLOY PRODUÇÃO
# ============================================
deploy-prod: ## Deploy em produção (requer confirmação)
	@echo "$(RED)⚠️  ATENÇÃO: Deploy em PRODUÇÃO!$(NC)"
	@read -p "Digite 'DEPLOY' para confirmar: " confirm; \
	if [ "$$confirm" != "DEPLOY" ]; then \
		echo "$(YELLOW)Deploy cancelado.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)🚀 Deploy em PRODUÇÃO...$(NC)"
	@make backup-db
	$(DOCKER_COMPOSE_PROD) pull
	$(DOCKER_COMPOSE_PROD) up -d
	@echo "$(GREEN)✅ Deploy em produção concluído$(NC)"

prod-logs: ## Logs de produção
	$(DOCKER_COMPOSE_PROD) logs -f

# ============================================
# LIMPEZA
# ============================================
clean: ## Remove containers e volumes
	@echo "$(YELLOW)🧹 Limpando...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f

# ============================================
# UTILITÁRIOS
# ============================================
setup: ## Setup inicial do projeto
	@echo "$(GREEN)🔧 Configurando projeto...$(NC)"
	cp .env.example .env.development 2>/dev/null || true
	make build
	make up
	sleep 5
	make migrate
	@echo "$(GREEN)✅ Setup concluído! Execute 'make dev' para iniciar.$(NC)"

health: ## Verifica saúde dos serviços
	@curl -sf http://localhost:8000/health && echo "$(GREEN)✅ Backend OK$(NC)" || echo "$(RED)❌ Backend FALHOU$(NC)"
	@curl -sf http://localhost:3000 > /dev/null && echo "$(GREEN)✅ Frontend OK$(NC)" || echo "$(RED)❌ Frontend FALHOU$(NC)"
