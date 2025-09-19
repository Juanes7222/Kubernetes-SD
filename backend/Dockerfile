FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Asegurarse de no incluir secretos
RUN rm -f .env || true
RUN rm -rf secrets || true

EXPOSE 8080

CMD ["uvicorn", "backend.services.main:app", "--host", "0.0.0.0", "--port", "8080"]
