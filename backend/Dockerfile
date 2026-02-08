FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY . .

# Cria diretório de dados
RUN mkdir -p /app/data

# Define PYTHONPATH
ENV PYTHONPATH=/app

# Railway usa a variável PORT; fallback 8000 para local
ENV PORT=8000
EXPOSE ${PORT}

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Comando de inicialização - usa $PORT para Railway
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
