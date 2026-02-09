# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# CRITICO: Garantir que VITE_API_URL nao seja embutido no build
# Em producao, o nginx proxeia tudo - API_URL deve ser vazio
ENV VITE_API_URL=""
RUN npm run build

# Stage 2: Production (nginx)
FROM nginx:1.25-alpine

# Remove config padrao do nginx
RUN rm -f /etc/nginx/conf.d/default.conf

# Copia build para nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copia config do nginx (com placeholder __BACKEND_URL__)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copia entrypoint com nome unico (evita conflito com o entrypoint do nginx)
COPY docker-entrypoint.sh /kontabil-entrypoint.sh

# Garante LF (caso Git converta para CRLF no Windows) + permissao
RUN sed -i 's/\r$//' /kontabil-entrypoint.sh && chmod +x /kontabil-entrypoint.sh
RUN sed -i 's/\r$//' /etc/nginx/conf.d/default.conf

EXPOSE 80

ENTRYPOINT ["/kontabil-entrypoint.sh"]
