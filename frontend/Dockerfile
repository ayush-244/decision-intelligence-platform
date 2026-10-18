# syntax=docker/dockerfile:1
# =============================================================================
# Delphi frontend — multi-stage build.
# Stage 1 compiles the SPA; stage 2 serves the static bundle via nginx.
# The final image contains only static assets + nginx (no Node runtime),
# keeping it small and reducing attack surface.
# =============================================================================

# ---- Stage 1: build ---------------------------------------------------------
FROM node:22-alpine AS build
WORKDIR /app

# Vite inlines VITE_* variables at build time; expose the API URL as a build arg.
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_APP_NAME=Delphi
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_APP_NAME=$VITE_APP_NAME

# Install dependencies against the lockfile for reproducible builds.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- Stage 2: serve ---------------------------------------------------------
FROM nginx:1.31-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
