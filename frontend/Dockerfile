# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2: Servir com nginx simples (sem proxy)
FROM nginx:1.25-alpine
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker-entrypoint.sh /kontabil-entrypoint.sh
RUN sed -i 's/\r$//' /kontabil-entrypoint.sh && chmod +x /kontabil-entrypoint.sh
EXPOSE 80
ENTRYPOINT ["/kontabil-entrypoint.sh"]
