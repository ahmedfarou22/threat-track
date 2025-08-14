FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Make transfer_db script executable
RUN chmod +x /app/transfer_db/transfer_db.sh

# Create necessary directories and copy seed media files
RUN mkdir -p /app/media /app/staticfiles /app/media/templates

# Copy seed media files (including default template)
COPY seed_media/ /app/media/

# Create a non-root user for security with specific UID to match nginx
RUN groupadd -r appuser -g 101 && useradd -r -g appuser -u 101 appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default production setup
RUN python manage.py collectstatic --noinput && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/media

# Switch to non-root user
USER appuser

# Default command (production mode with gunicorn)
CMD ["sh", "-c", "python manage.py migrate && gunicorn Threat_Track.wsgi:application -b 0.0.0.0:8000"]
