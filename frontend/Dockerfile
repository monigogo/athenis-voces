# Web de athenis-voces: se compila con Node y la sirve nginx, que reenvía /api a la API.
FROM node:22.23.4-slim AS compilacion

RUN corepack enable && corepack prepare pnpm@10.34.9 --activate

WORKDIR /app

# Primero solo las dependencias, para que Docker las reutilice si cambia el código
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

FROM nginxinc/nginx-unprivileged:1.31.2-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=compilacion /app/dist /usr/share/nginx/html

USER nginx

EXPOSE 8080
