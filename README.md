# Sistema de Gestão Contábil v2.9.0

## 🚀 Início Rápido com Docker

```bash
# Descompacte e entre na pasta
unzip contabil_system.zip
cd contabil_system

# Execute o script (resolve rate limit automaticamente)
chmod +x docker-run.sh
./docker-run.sh
```

O script vai:
1. ✅ Verificar se você está logado no Docker Hub
2. ✅ Se não estiver, oferece fazer login (resolve rate limit)
3. ✅ Baixar todas as imagens necessárias
4. ✅ Iniciar o sistema completo

## 📍 URLs

| Serviço | URL |
|---------|-----|
| **Frontend** | http://localhost |
| **Backend** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

## 📋 Comandos Úteis

```bash
# Ver logs
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f backend
docker-compose logs -f frontend

# Parar tudo
docker-compose down

# Reiniciar
docker-compose restart

# Rebuild completo
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🔐 Criar Conta

Acesse http://localhost e clique em "Criar Conta" para se registrar.

## 🐛 Solução de Problemas

### Erro "429 Too Many Requests" (Rate Limit)

```bash
# Faça login no Docker Hub (gratuito)
docker login

# Depois execute novamente
./docker-run.sh
```

### Containers não iniciam

```bash
# Veja os logs
docker-compose logs

# Reinicie do zero
docker-compose down -v
./docker-run.sh
```

### Porta 80 em uso

```bash
# Veja o que está usando
sudo lsof -i :80

# Ou mude a porta no docker-compose.yml
# De: "80:3000"
# Para: "3000:3000"
# E acesse http://localhost:3000
```

## 🎯 Funcionalidades

- **F01-F05**: Auth, Database, Multi-Tenancy, Billing, Importação
- **F08-F10**: Dashboard, Relatórios, Alertas
- **F12**: Análise Financeira Avançada (DRE, Índices, Break-Even, Projeções, Benchmarks)

## 📄 Licença

MIT
