# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copia package.json e instala dependencias
COPY package.json package-lock.json* ./
RUN npm install

# Copia codigo e faz build
COPY . .
RUN npm run build

# Stage 2: Production (nginx)
FROM nginx:1.25-alpine

# Copia build para nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copia configuracao do nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copia entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

# Entrypoint configura proxy, porta e runtime-config.js antes de iniciar nginx
ENTRYPOINT ["/docker-entrypoint.sh"]
