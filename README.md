# Kontabil - Análise Financeira Inteligente

Sistema completo de análise financeira para contadores e empresas.

## 🚀 Início Rápido

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/kontabil.git
cd kontabil

# Execute o setup
chmod +x setup.sh
./setup.sh

# Ou manualmente com Docker
docker-compose up -d
```

## 📍 URLs

| Serviço | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

## 🎯 Funcionalidades

### Análise Financeira
- 📊 Dashboard com indicadores em tempo real
- 📈 8 índices de liquidez (Corrente, Seca, Imediata, Geral, etc.)
- 💰 DRE automático com margens
- 🎯 Análise de Break-Even Point
- 📉 Projeções financeiras

### Gestão
- 🏢 Multi-empresas (gerencie vários clientes)
- 🔔 Sistema de alertas inteligentes
- 📁 Importação de dados (XLSX, CSV)
- 👥 Multi-tenancy (isolamento por contador)

### Relatórios
- 📄 PDF profissional (ABNT)
- 📊 Excel com gráficos
- 🎨 Configuração de cores e logo
- 📧 Envio por email (em breve)

## 📋 Comandos Úteis

```bash
# Desenvolvimento
make dev          # Inicia ambiente
make logs         # Ver logs
make test         # Executar testes

# Deploy
make deploy-staging   # Homologação
make deploy-prod      # Produção

# Banco de dados
make migrate      # Executar migrations
make backup-db    # Criar backup
```

## 🔧 Variáveis de Ambiente

```env
# Backend
DATABASE_URL=postgresql://user:pass@db:5432/kontabil
JWT_SECRET=sua-chave-secreta-aqui
ENVIRONMENT=development

# Email (para recuperação de senha)
RESEND_API_KEY=re_xxxx
EMAIL_FROM=noreply@kontabil.com.br
```

## 📦 Stack Tecnológica

- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: Python + FastAPI
- **Banco**: PostgreSQL
- **Cache**: Redis
- **Deploy**: Docker + Railway/VPS

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'feat: adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

MIT © Kontabil
