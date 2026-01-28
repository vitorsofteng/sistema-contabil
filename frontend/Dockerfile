# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copia package.json e instala dependências
COPY package.json package-lock.json* ./
RUN npm install

# Copia código e faz build
COPY . .
RUN npm run build

# Stage 2: Production
# Usa versão específica do nginx para melhor cache
FROM nginx:1.25-alpine

# Copia build para nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copia configuração do nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
