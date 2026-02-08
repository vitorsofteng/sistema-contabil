# Deploy no Railway - Sistema Contábil

## Arquitetura

```
Railway Project
├── Service: backend   (Python/FastAPI)
├── Service: frontend  (React/Nginx)
└── Addon: PostgreSQL
```

## Passo a Passo

### 1. Criar Projeto no Railway

1. Acesse [railway.app](https://railway.app) e crie um novo projeto
2. Conecte ao repositório Git do sistema

### 2. Adicionar PostgreSQL

1. No projeto, clique **"+ New"** → **"Database"** → **"PostgreSQL"**
2. O Railway cria automaticamente a variável `DATABASE_URL`

### 3. Deploy do Backend

1. **"+ New"** → **"GitHub Repo"** → selecione o repositório
2. Em **Settings**:
   - **Root Directory**: `backend`
   - **Builder**: Dockerfile
   - **Dockerfile Path**: `Dockerfile`
3. Em **Variables**, adicione:

| Variável | Valor | Obrigatório |
|---|---|---|
| `DATABASE_URL` | (referência ao PostgreSQL addon - Railway faz automaticamente) | ✅ |
| `SECRET_KEY` | Gere com: `python -c "import secrets; print(secrets.token_urlsafe(64))"` | ✅ |
| `REFRESH_SECRET_KEY` | Gere outro: `python -c "import secrets; print(secrets.token_urlsafe(64))"` | ✅ |
| `ENVIRONMENT` | `staging` | ✅ |
| `USE_POSTGRES` | `true` | ✅ |
| `FRONTEND_URL` | URL do frontend (depois de fazer deploy) | ✅ |
| `CORS_ORIGINS` | `http://localhost,http://localhost:3000,https://SEU-FRONTEND.up.railway.app` | ✅ |
| `RESEND_API_KEY` | Sua chave da Resend (para emails) | Opcional |
| `EMAIL_FROM` | `Kontabil <noreply@seudominio.com>` | Opcional |
| `ANTHROPIC_API_KEY` | Chave da Anthropic (para importação IA) | Opcional |

4. Clique em **"Deploy"**
5. Em **Settings** → **Networking** → **Generate Domain** (gera URL pública)
6. Anote a URL gerada (ex: `backend-xxx.up.railway.app`)

### 4. Deploy do Frontend

1. **"+ New"** → **"GitHub Repo"** → mesmo repositório
2. Em **Settings**:
   - **Root Directory**: `frontend`
   - **Builder**: Dockerfile
   - **Dockerfile Path**: `Dockerfile.railway`
3. Em **Variables**, adicione:

| Variável | Valor |
|---|---|
| `VITE_API_URL` | `https://backend-xxx.up.railway.app` (URL do backend do passo anterior) |

> ⚠️ `VITE_API_URL` é um **build arg** — precisa ser passado no build. No Railway, vá em Settings → Build → Add Build Arg: `VITE_API_URL=https://backend-xxx.up.railway.app`

4. Em **Settings** → **Networking** → **Generate Domain**
5. Volte ao backend e atualize `FRONTEND_URL` e `CORS_ORIGINS` com a URL do frontend

### 5. Verificar Deploy

1. Acesse a URL do backend: `https://backend-xxx.up.railway.app/health`
   - Deve retornar `{"status": "ok"}`
2. Acesse a URL do frontend: `https://frontend-xxx.up.railway.app`
   - Deve mostrar a tela de login

## Variáveis de Ambiente Críticas

```bash
# Gerar SECRET_KEY segura (execute localmente)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"
python3 -c "import secrets; print('REFRESH_SECRET_KEY=' + secrets.token_urlsafe(64))"
```

## Troubleshooting

### "CORS error" no frontend
- Verifique se `FRONTEND_URL` no backend aponta para a URL correta do frontend
- Verifique se `CORS_ORIGINS` inclui a URL do frontend

### "Token inválido" após deploy
- Certifique-se que `SECRET_KEY` e `REFRESH_SECRET_KEY` estão definidas e são fixas
- Se mudou as chaves, todos os tokens antigos serão invalidados (esperado)

### Frontend não conecta ao backend
- Verifique se `VITE_API_URL` foi passado como **build arg** (não apenas variável de ambiente)
- No Railway: Settings → Build → Build Arguments

### Database connection error
- Verifique se a referência ao PostgreSQL addon está configurada
- O Railway deve preencher `DATABASE_URL` automaticamente
