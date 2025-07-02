FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install UV and dependencies
RUN pip install uv
RUN uv sync --frozen

# Copy application code
COPY . .

# Copy and make startup scripts executable
COPY scripts/start.sh /start.sh
COPY scripts/start-prod.sh /start-prod.sh
RUN chmod +x /start.sh /start-prod.sh

# Expose port
EXPOSE 8000

# Run the startup script (development by default)
CMD ["/start.sh"] 