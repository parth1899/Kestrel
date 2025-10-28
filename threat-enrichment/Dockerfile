FROM python:3.11-slim

WORKDIR /app

# Install system packages we need
RUN apt-get update && apt-get install -y wget tar && rm -rf /var/lib/apt/lists/*

# Copy source
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directory and download GeoLite2 DB (using your provided wget shortcut)
# This will place GeoLite2-City.mmdb at /app/GeoLite2-City.mmdb
RUN mkdir -p /app/geoip \
    && wget -O /app/geoip/GeoLite2-City.mmdb "https://git.io/GeoLite2-City.mmdb" || true

# Expose a default port (the container will still use $PORT at runtime)
EXPOSE 8000

# Use Render provided PORT env var; fallback to 8000 locally
CMD ["sh", "-c", "python enrichment_service.py --port ${PORT:-8000}"]
