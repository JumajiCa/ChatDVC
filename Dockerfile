# Stage 1: Build Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/client
COPY client/package.json client/package-lock.json ./
RUN npm ci
COPY client/ ./
RUN npm run build

# Stage 2: Final Image
FROM python:3.11-slim
WORKDIR /app

# Install Nginx and Supervisor
RUN apt-get update && apt-get install -y nginx supervisor && \
    rm -rf /var/lib/apt/lists/*

# Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY app/ ./app/
COPY util.py .
COPY main.py .

# Copy Frontend Build
COPY --from=frontend-builder /app/client/build /var/www/html

# Configuration
COPY nginx.conf /etc/nginx/sites-available/default
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create directory for persistence (optional usage)
RUN mkdir -p /app/data

# Expose Port
EXPOSE 80

# Entrypoint
CMD ["/usr/bin/supervisord"]
