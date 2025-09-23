FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del servicio
COPY . .

# Asegurarse de no incluir secretos
RUN rm -f .env || true
RUN rm -rf secrets || true

# Crear directorio para logs
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Crear usuario no-root
RUN useradd -m -u 1000 loguser && chown -R loguser:loguser /app
USER loguser

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
