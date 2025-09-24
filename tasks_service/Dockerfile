FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el servicio directamente dentro del contenedor
COPY . .

# Asegurarse de no incluir secretos
RUN rm -f .env || true
RUN rm -rf secrets || true

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
