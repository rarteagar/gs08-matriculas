# syntax=docker/dockerfile:1.7
# ============================================================
# GS08 - Matriculas | Frontend Vue 3 + Vite + Tailwind
# Etapa 1: build de assets con Node. Etapa 2: nginx (estaticos + proxy inverso /api)
# Build:  docker build -t gs08-web:local ./frontend
# ============================================================

FROM node:22.23.2-alpine AS build
WORKDIR /app
# Base de la API embebida en el bundle de Vite (mismo origen -> nginx hace de proxy)
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.31.6-alpine AS runtime
# nginx sin privilegios: escucha en 8080 y necesita sus carpetas escribibles
RUN chown -R nginx:nginx /var/cache/nginx /etc/nginx/conf.d \
 && touch /var/run/nginx.pid \
 && chown -R nginx:nginx /var/run/nginx.pid /usr/share/nginx/html
# Plantilla: docker-entrypoint sustituye ${API_UPSTREAM} y genera /etc/nginx/conf.d/default.conf
ENV API_UPSTREAM="server api:8000;"
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
USER nginx
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
  CMD wget -qO- http://127.0.0.1:8080/healthz >/dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
