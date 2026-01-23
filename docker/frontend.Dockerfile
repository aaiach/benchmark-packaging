# =============================================================================
# Frontend Dockerfile - Multi-stage build for dev and prod
# =============================================================================
# Usage:
#   Dev:  docker build --target dev -t frontend:dev .
#   Prod: docker build --target prod --build-arg VITE_API_URL=https://api.example.com -t frontend:prod .
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base - Common dependencies
# -----------------------------------------------------------------------------
FROM node:20-alpine AS base

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# -----------------------------------------------------------------------------
# Stage 2: Development - Hot reload server
# -----------------------------------------------------------------------------
FROM base AS dev

# Copy application code (will be overridden by volume mounts)
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start dev server with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# -----------------------------------------------------------------------------
# Stage 3: Build - Production build
# -----------------------------------------------------------------------------
FROM base AS build

# Build arguments for environment variables
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Copy application code
COPY . .

# Build the application
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 4: Production - Nginx serving static files
# -----------------------------------------------------------------------------
FROM nginx:alpine AS prod

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
