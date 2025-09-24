# Multi-stage build para React frontend
FROM node:18-alpine AS build

WORKDIR /app

# Accept build arguments for environment variables
ARG REACT_APP_AUTH_SERVICE_URL
ARG REACT_APP_TASKS_SERVICE_URL
ARG REACT_APP_COLLABORATOR_SERVICE_URL
ARG REACT_APP_LOGS_SERVICE_URL

# Set environment variables from build args
ENV REACT_APP_AUTH_SERVICE_URL=$REACT_APP_AUTH_SERVICE_URL
ENV REACT_APP_TASKS_SERVICE_URL=$REACT_APP_TASKS_SERVICE_URL
ENV REACT_APP_COLLABORATOR_SERVICE_URL=$REACT_APP_COLLABORATOR_SERVICE_URL
ENV REACT_APP_LOGS_SERVICE_URL=$REACT_APP_LOGS_SERVICE_URL

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm install --legacy-peer-deps

# Copiar código fuente
COPY . .

# Crear build de producción
RUN npm run build

# Stage 2: Nginx para servir la aplicación
FROM nginx:alpine

# Copiar la configuración personalizada de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar los archivos construidos desde el stage anterior
COPY --from=build /app/build /usr/share/nginx/html

# Exponer puerto 80
EXPOSE 80

# Asegurar permisos correctos
RUN chmod -R 755 /usr/share/nginx/html

CMD ["nginx", "-g", "daemon off;"]
