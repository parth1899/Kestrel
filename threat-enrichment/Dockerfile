FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get update && apt-get install -y wget \
    && wget -O GeoLite2-City.mmdb https://git.io/GeoLite2-City.mmdb \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8000
CMD ["python", "enrichment_service.py"]