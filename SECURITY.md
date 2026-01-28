# 🔒 Guia de Segurança - Sistema Contábil

## Visão Geral

Este documento descreve as medidas de segurança implementadas e as configurações necessárias para um deploy seguro em produção.

---

## ✅ Checklist de Deploy em Produção

### Variáveis de Ambiente (CRÍTICO)

- [ ] Criar arquivo `.env` a partir do `.env.example`
- [ ] Gerar `JWT_SECRET` único: `openssl rand -hex 64`
- [ ] Gerar `ENCRYPTION_KEY` único: `openssl rand -hex 32`
- [ ] Configurar `ENVIRONMENT=production`
- [ ] Definir `DEBUG=false`
- [ ] Configurar `CORS_ORIGINS` apenas com domínios reais
- [ ] Configurar credenciais de banco de dados seguras
- [ ] Nunca commitar o arquivo `.env`

### HTTPS (CRÍTICO)

- [ ] Configurar certificado SSL/TLS válido
- [ ] Redirecionar todo tráfego HTTP para HTTPS
- [ ] Configurar HSTS (já implementado no código)

### Banco de Dados

- [ ] Usar senha forte para PostgreSQL
- [ ] Não expor porta do banco publicamente
- [ ] Configurar backups automáticos
- [ ] Habilitar SSL na conexão

### Infraestrutura

- [ ] Firewall configurado (apenas portas 80/443)
- [ ] Logs centralizados e monitorados
- [ ] Alertas de erro configurados
- [ ] Backup automatizado

---

## 🛡️ Medidas de Segurança Implementadas

### Sprint 1: Segurança Básica

#### 1. Rate Limiting

Proteção contra brute force e DoS.

| Endpoint | Limite | Janela |
|----------|--------|--------|
| Login/Registro | 5 req | 15 min |
| API geral | 60 req | 1 min |
| Reset senha | 3 req | 5 min |

**Bloqueio automático:** IP bloqueado por 15 minutos após exceder limite de login.

#### 2. Headers de Segurança

Headers adicionados automaticamente:

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: [configurado]
Strict-Transport-Security: max-age=31536000 (produção)
```

#### 3. CORS Restritivo

- Em desenvolvimento: localhost permitido
- Em produção: apenas domínios explicitamente configurados
- Wildcard (`*`) bloqueado em produção

#### 4. Validação de Senha

Requisitos padrão:
- Mínimo 8 caracteres
- Pelo menos 1 letra maiúscula
- Pelo menos 1 letra minúscula
- Pelo menos 1 número
- Senhas comuns bloqueadas

#### 5. Sanitização de Inputs

Proteção contra:
- SQL Injection
- XSS (Cross-Site Scripting)
- Path Traversal

---

### Sprint 2: Segurança Avançada

#### 1. Autenticação de Dois Fatores (2FA)

Implementação TOTP (Time-based One-Time Password) compatível com:
- Google Authenticator
- Authy
- Microsoft Authenticator
- 1Password
- Qualquer app TOTP

**Endpoints:**
- `POST /auth/2fa/setup` - Configura 2FA (retorna QR code)
- `POST /auth/2fa/enable` - Ativa 2FA após verificar código
- `POST /auth/2fa/verify` - Verifica código 2FA
- `POST /auth/2fa/disable` - Desativa 2FA (requer senha + código)
- `GET /auth/2fa/status` - Verifica se 2FA está ativo
- `POST /auth/2fa/backup-code` - Usa código de backup

**Códigos de Backup:**
- 10 códigos gerados no setup
- Cada código só pode ser usado uma vez
- Guarde em local seguro!

#### 2. Auditoria de Segurança

Registro automático de eventos:
- Login bem-sucedido/falho
- Logout (individual e todos dispositivos)
- Alteração de senha
- Reset de senha
- Ativação/desativação de 2FA
- Revogação de sessões
- Atividade suspeita

**Endpoints:**
- `GET /auth/audit-log` - Log de auditoria do usuário
- `GET /auth/security-check` - Verificação de segurança da conta

#### 3. Criptografia de Dados Sensíveis

Dados sensíveis são criptografados em repouso usando:
- Algoritmo: AES-256 (via Fernet)
- Derivação de chave: PBKDF2 com SHA-256
- 100.000 iterações

**IMPORTANTE:** Se você perder a `ENCRYPTION_KEY`, dados criptografados serão irrecuperáveis!

#### 4. Gerenciamento Avançado de Sessões

- Visualização de todas as sessões ativas
- Revogação individual de sessões
- Revogação de todas as sessões (exceto atual)
- Detecção de atividade suspeita

**Endpoints:**
- `GET /auth/sessions/active` - Lista sessões ativas
- `DELETE /auth/sessions/all` - Revoga todas as sessões

#### 5. Detecção de Atividade Suspeita

O sistema monitora e alerta sobre:
- Login de novo IP
- Múltiplos IPs em 24h
- Tentativas de login falhas
- Mudanças frequentes de senha

---

## 🔧 Configuração de Variáveis de Ambiente

### Exemplo de .env para Produção

```bash
# Ambiente
ENVIRONMENT=production
DEBUG=false

# JWT - GERE UMA CHAVE ÚNICA!
JWT_SECRET=sua_chave_super_secreta_gerada_com_openssl_rand_hex_64

# Criptografia - GERE UMA CHAVE ÚNICA!
ENCRYPTION_KEY=sua_chave_criptografia_openssl_rand_hex_32

# CORS - Apenas seu domínio
CORS_ORIGINS=https://app.seudominio.com.br

# Banco de Dados
DATABASE_URL=postgresql://usuario:senha_forte@db-host:5432/contabil

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_LOGIN_ATTEMPTS=5

# 2FA
TWO_FACTOR_ENABLED=true

# Auditoria
AUDIT_LOG_ENABLED=true
AUDIT_LOG_RETENTION_DAYS=90
```

---

## 🚨 Práticas Obrigatórias

### NUNCA faça isso:

1. ❌ Commitar `.env` no repositório
2. ❌ Usar `JWT_SECRET` ou `ENCRYPTION_KEY` padrão em produção
3. ❌ Configurar `CORS_ORIGINS=*` em produção
4. ❌ Rodar com `DEBUG=true` em produção
5. ❌ Expor porta do banco de dados
6. ❌ Usar HTTP sem TLS em produção
7. ❌ Ignorar alertas de atividade suspeita

### SEMPRE faça isso:

1. ✅ Gerar chaves únicas por ambiente
2. ✅ Usar HTTPS em produção
3. ✅ Manter dependências atualizadas
4. ✅ Monitorar logs de auditoria
5. ✅ Fazer backup do banco regularmente
6. ✅ Incentivar uso de 2FA para todos os usuários
7. ✅ Testar recuperação de desastres

---

## 📊 Monitoramento de Segurança

### Logs Importantes

1. **Tentativas de login falhas**
   - Monitore padrões de brute force
   - Alerte em caso de muitas tentativas do mesmo IP

2. **Rate limit atingido**
   - Pode indicar ataque DoS
   - Monitore IPs frequentes

3. **Atividade suspeita**
   - Logins de novos IPs
   - Múltiplos IPs em 24h
   - Falhas de 2FA

### Métricas Sugeridas

- Taxa de login bem-sucedido vs falho
- IPs bloqueados por rate limiting
- Usuários com 2FA ativado vs desativado
- Tempo médio de resposta
- Erros 401/403/429

---

## 🔄 Atualizações de Segurança

Mantenha estas dependências atualizadas:

```bash
# Backend
pip install --upgrade bcrypt pyjwt fastapi cryptography

# Verificar vulnerabilidades
pip-audit
```

---

## 📞 Em Caso de Incidente

1. **Suspeita de vazamento de dados:**
   - Invalidar todas as sessões
   - Rotacionar JWT_SECRET e ENCRYPTION_KEY
   - Forçar reset de senhas
   - Notificar usuários afetados

2. **Ataque DoS:**
   - Verificar rate limiting
   - Considerar WAF/Cloudflare
   - Bloquear IPs maliciosos

3. **Acesso não autorizado:**
   - Revogar tokens do usuário afetado
   - Verificar logs de auditoria
   - Forçar reautenticação com 2FA
   - Notificar usuário

4. **Comprometimento de credenciais:**
   - Desativar conta imediatamente
   - Verificar logs de atividade
   - Rotacionar tokens de acesso
   - Exigir 2FA na próxima autenticação
