# ---- Build frontend ----
FROM node:20-slim AS frontend
WORKDIR /build
COPY src/frontend/package*.json ./
RUN npm ci
COPY src/frontend/ ./
RUN npm run build

# ---- Runtime ----
FROM python:3.12-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY scripts/ scripts/
COPY config.yaml .

# Copy built frontend into a location the API can serve
COPY --from=frontend /build/dist/ src/frontend/dist/

# Persist simulation state across restarts
VOLUME ["/app/data"]

# Expose API port
EXPOSE 8000

# Default: run simulation with API server
CMD ["python3", "scripts/run.py", "--api", "--api-host", "0.0.0.0", "--fast"]
