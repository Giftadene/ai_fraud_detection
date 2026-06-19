FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by scikit-learn, numpy, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set default credentials (override via HF Spaces Secrets)
ENV FRAUDGUARD_ADMIN_PW=admin123
ENV FRAUDGUARD_ANALYST_PW=analyst123

# Hugging Face Spaces uses port 7860
ENV PORT=7860

# Expose the port
EXPOSE 7860

# Run the Flask app on 0.0.0.0:$PORT
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
