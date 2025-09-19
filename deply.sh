#!/bin/bash
set -e

# CONFIG - cambia PROJECT_ID
PROJECT_ID="kubernetes-sd-13b8b"
REGION="us-central1"
SERVICE_NAME="fastapi-backend"
SECRET_NAME="kubernetes-sd"              # nombre en Secret Manager
SECRET_FILE="backend/secrets/kubernetes-sd.json"
FRONTEND_DIR="frontend"

echo "== Iniciando despliegue para project: $PROJECT_ID =="

# Login (no rompe si ya logeado)
gcloud auth login || true
firebase login || true
gcloud config set project $PROJECT_ID

# Habilitar servicios (si no estuvieran)
gcloud services enable cloudbuild.googleapis.com run.googleapis.com secretmanager.googleapis.com

# SUBIR secreto a Secret Manager (si existe)
if [ -f "$SECRET_FILE" ]; then
  echo "-> Subiendo secreto $SECRET_NAME a Secret Manager..."
  if ! gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID > /dev/null 2>&1; then
    gcloud secrets create $SECRET_NAME --replication-policy="automatic" --project=$PROJECT_ID
  fi
  gcloud secrets versions add $SECRET_NAME --data-file=$SECRET_FILE --project=$PROJECT_ID
else
  echo "-> Aviso: $SECRET_FILE no existe. Omitiendo Secret Manager."
fi

# =======================================
# BACKEND: construir imagen y desplegar
# =======================================
echo "== Construyendo imagen del backend =="
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project=$PROJECT_ID

echo "== Desplegando en Cloud Run =="
# Variables de entorno para el backend
FRONTEND_URL="https://$PROJECT_ID.web.app"

gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "ENV=production,SECRET_KEY=super-secret,FRONTEND_URL=$FRONTEND_URL,FIREBASE_PROJECT_ID=$PROJECT_ID,GOOGLE_APPLICATION_CREDENTIALS=/secrets/firebase.json" \
  --project=$PROJECT_ID

# Si cargamos el secreto, montarlo en /secrets/firebase.json
if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID > /dev/null 2>&1; then
  echo "-> Montando secreto $SECRET_NAME en Cloud Run"
  gcloud run services update $SERVICE_NAME \
    --update-secrets /secrets/firebase.json=$SECRET_NAME:latest \
    --region $REGION \
    --platform managed \
    --project=$PROJECT_ID
fi

# Volver a raíz
cd ..

# Obtener la URL del backend desplegado
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --project=$PROJECT_ID \
  --format 'value(status.url)')

echo "-> Backend URL: $BACKEND_URL"

# =======================================
# FRONTEND: construir y desplegar
# =======================================
echo "== Construyendo frontend =="
cd $FRONTEND_DIR
npm ci

# Reemplazar placeholder en .env.production con la URL real del backend
if [ -f ".env.production" ]; then
  sed -i "s|REACT_APP_BACKEND_URL=.*|REACT_APP_BACKEND_URL=$BACKEND_URL|" .env.production || true
else
  echo "REACT_APP_BACKEND_URL=$BACKEND_URL" > .env.production
fi

# Copiar .env.production a .env para build (opcional)
cp .env.production .env

npm run build
cd ..

echo "== Desplegando en Firebase Hosting =="
firebase deploy --only hosting --project $PROJECT_ID

echo "== Despliegue completado =="
echo "Frontend: https://$PROJECT_ID.web.app"
echo "Backend: $BACKEND_URL"
echo "===================================="