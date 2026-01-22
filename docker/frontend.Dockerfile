FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy application code (will be overridden by volume mounts in dev)
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start dev server with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
