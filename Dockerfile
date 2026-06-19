FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire application
COPY . .

# Default credentials (override via HF Spaces Secrets)
ENV FRAUDGUARD_ADMIN_PW=admin123
ENV FRAUDGUARD_ANALYST_PW=analyst123
ENV FRAUDGUARD_SECRET_KEY=fraudguard-ai-default-secret-key-change-in-production

# Hugging Face Spaces automatically sets PORT=7860
EXPOSE 7860

# Start directly — app.py handles init errors gracefully
CMD gunicorn --bind 0.0.0.0:${PORT:-7860} --workers 2 --timeout 300 --access-logfile - --error-logfile - app:app
