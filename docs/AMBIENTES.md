# 🚀 Guia de Ambientes e Deploy

## Visão Geral dos Ambientes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUXO DE DESENVOLVIMENTO                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   LOCAL (Dev)     →     HOMOLOGAÇÃO     →     PRODUÇÃO                     │
│   ───────────          ─────────────          ──────────                   │
│   localhost:3000       hml.seudominio.com    app.seudominio.com            │
│   localhost:8000       api-hml.seudominio    api.seudominio.com            │
│                                                                             │
│   Branch: feature/*    Branch: develop       Branch: main                  │
│           bugfix/*                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 1. Estrutura de Branches (Git Flow)

```
main (produção)
  │
  ├── develop (homologação)
  │     │
  │     ├── feature/nova-funcionalidade
  │     ├── feature/melhorias-dashboard
  │     ├── bugfix/correcao-login
  │     └── bugfix/ajuste-relatorio
  │
  └── hotfix/correcao-urgente (vai direto para main E develop)
```

### Comandos Básicos

```bash
# Criar branch de feature
git checkout develop
git pull origin develop
git checkout -b feature/nome-da-feature

# Após terminar, fazer merge request/pull request para develop
git push origin feature/nome-da-feature

# Criar hotfix (correção urgente em produção)
git checkout main
git checkout -b hotfix/descricao-do-problema
# ... fazer correção ...
git push origin hotfix/descricao-do-problema
# Fazer PR para main E para develop
```

---

## 2. Arquivos de Configuração por Ambiente

### Estrutura de Arquivos

```
contabil_system/
├── .env.development      # Variáveis para desenvolvimento local
├── .env.staging          # Variáveis para homologação
├── .env.production       # Variáveis para produção
├── docker-compose.yml    # Docker para desenvolvimento
├── docker-compose.staging.yml
├── docker-compose.prod.yml
└── .github/
    └── workflows/
        ├── ci.yml        # Testes automáticos
        ├── deploy-staging.yml
        └── deploy-production.yml
```

---

## 3. Configuração dos Ambientes

### 3.1 Desenvolvimento (LOCAL)

**Objetivo**: Desenvolvimento e testes locais

```bash
# Subir ambiente de desenvolvimento
docker-compose up -d

# Ou com hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Acessar
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# Docs API: http://localhost:8000/docs
```

**Características**:
- Debug habilitado
- Hot-reload ativo
- Banco de dados local
- Sem SSL
- Rate limiting desabilitado

### 3.2 Homologação (STAGING)

**Objetivo**: Testes de integração, QA, validação com cliente

```bash
# Subir ambiente de homologação
docker-compose -f docker-compose.staging.yml up -d
```

**Características**:
- Ambiente similar à produção
- Dados de teste/anonimizados
- SSL com Let's Encrypt
- Rate limiting habilitado (mais permissivo)
- Logs detalhados

### 3.3 Produção (PRODUCTION)

**Objetivo**: Ambiente real com dados de clientes

```bash
# Subir produção
docker-compose -f docker-compose.prod.yml up -d
```

**Características**:
- Máxima segurança
- SSL obrigatório
- Rate limiting rigoroso
- Backups automáticos
- Monitoramento ativo
- Logs estruturados

---

## 4. Variáveis de Ambiente

### .env.development
```env
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://contabil:contabil123@db:5432/contabil
JWT_SECRET=dev-secret-change-in-production
RATE_LIMIT_ENABLED=false
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### .env.staging
```env
ENVIRONMENT=staging
DEBUG=false
DATABASE_URL=postgresql://user:pass@db-staging:5432/contabil_hml
JWT_SECRET=${JWT_SECRET_STAGING}
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
CORS_ORIGINS=https://hml.seudominio.com
SSL_ENABLED=true
```

### .env.production
```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@db-prod:5432/contabil_prod
JWT_SECRET=${JWT_SECRET_PROD}
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
CORS_ORIGINS=https://app.seudominio.com
SSL_ENABLED=true
BACKUP_ENABLED=true
```

---

## 5. CI/CD com GitHub Actions

### Fluxo Automático

```
Push em feature/* → Roda testes
PR para develop   → Roda testes + Deploy em Homologação
PR para main      → Roda testes + Aprovação manual + Deploy em Produção
```

### Configurar Secrets no GitHub

Vá em: **Settings → Secrets and variables → Actions**

Adicione:
- `DOCKER_USERNAME` - Usuário Docker Hub
- `DOCKER_PASSWORD` - Senha/Token Docker Hub
- `SSH_PRIVATE_KEY` - Chave SSH para deploy
- `STAGING_HOST` - IP/domínio do servidor de homologação
- `PRODUCTION_HOST` - IP/domínio do servidor de produção
- `JWT_SECRET_STAGING` - Secret JWT para homologação
- `JWT_SECRET_PROD` - Secret JWT para produção
- `DATABASE_URL_STAGING` - URL do banco de homologação
- `DATABASE_URL_PROD` - URL do banco de produção

---

## 6. Comandos Úteis

### Desenvolvimento

```bash
# Iniciar ambiente
make dev

# Ver logs
make logs

# Executar testes
make test

# Lint do código
make lint

# Parar tudo
make down
```

### Deploy Manual

```bash
# Deploy em homologação
make deploy-staging

# Deploy em produção (requer confirmação)
make deploy-prod
```

### Banco de Dados

```bash
# Backup
make backup-db ENV=production

# Restore
make restore-db ENV=staging FILE=backup.sql

# Migrations
make migrate ENV=production
```

---

## 7. Checklist de Deploy

### Antes de ir para Homologação
- [ ] Todos os testes passando
- [ ] Code review aprovado
- [ ] Documentação atualizada
- [ ] Migrations testadas localmente

### Antes de ir para Produção
- [ ] Testado em homologação por pelo menos 24h
- [ ] QA aprovou
- [ ] Stakeholders notificados
- [ ] Backup do banco realizado
- [ ] Rollback plan documentado
- [ ] Monitoramento configurado

---

## 8. Rollback

### Se algo der errado em produção

```bash
# Opção 1: Reverter para versão anterior
docker-compose -f docker-compose.prod.yml pull app:v1.2.3
docker-compose -f docker-compose.prod.yml up -d

# Opção 2: Via Git
git revert HEAD
git push origin main
# CI/CD fará deploy automaticamente

# Opção 3: Restore do banco (último recurso)
make restore-db ENV=production FILE=backup-antes-deploy.sql
```

---

## 9. Monitoramento

### Logs
```bash
# Ver logs em tempo real
docker-compose logs -f

# Logs de um serviço específico
docker-compose logs -f backend

# Últimas 100 linhas
docker-compose logs --tail=100 backend
```

### Health Check
```bash
# Verificar saúde dos serviços
curl https://api.seudominio.com/health

# Resposta esperada
{
  "status": "healthy",
  "database": "connected",
  "version": "3.0.0"
}
```

---

## 10. Estrutura de Servidores Recomendada

### Opção 1: VPS Simples (Startups)
```
1x VPS Homologação (2GB RAM, 2 vCPU)
1x VPS Produção (4GB RAM, 2 vCPU)
1x Banco PostgreSQL gerenciado (ou na mesma VPS)
```

### Opção 2: Cloud Escalável (Crescimento)
```
AWS/GCP/Azure:
- ECS/Cloud Run para containers
- RDS/Cloud SQL para banco
- S3/Cloud Storage para arquivos
- CloudFront/Cloud CDN para frontend
```

### Opção 3: Kubernetes (Enterprise)
```
- Cluster K8s (EKS/GKE/AKS)
- Helm charts para deploy
- Istio para service mesh
- ArgoCD para GitOps
```
