# Kubernetes Service Discovery

Una aplicación moderna de gestión de tareas y registro de servicios construida con React (frontend) y FastAPI (backend).

## 🚀 Características

### Gestión de Tareas
- ✅ Crear, editar y eliminar tareas
- ✅ Marcar tareas como completadas
- ✅ Filtrar tareas (propias, colaborativas, todas)
- ✅ Buscar tareas por título o descripción
- ✅ Colaboración entre usuarios
- ✅ Fechas de vencimiento con alertas visuales
- ✅ Autenticación con Firebase

### Service Registry (Nuevo)
- 🆕 Registrar servicios con información detallada
- 🆕 Health checks automáticos
- 🆕 Filtrado por tags y status
- 🆕 Configuración de service discovery
- 🆕 Soporte para múltiples protocolos (HTTP, HTTPS, TCP, gRPC)
- 🆕 Interfaz web intuitiva

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Firebase      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Auth & DB)   │
│                 │    │                 │    │                 │
│ • Service UI    │    │ • Service API   │    │ • Authentication│
│ • Task UI       │    │ • Task API      │    │ • Firestore     │
│ • Auth UI       │    │ • Auth API      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Tecnologías

### Frontend
- **React** - Biblioteca de UI
- **Tailwind CSS** - Framework de CSS
- **shadcn/ui** - Componentes de UI
- **Lucide React** - Iconos
- **Axios** - Cliente HTTP

### Backend
- **FastAPI** - Framework web moderno y rápido
- **Python 3.9+** - Lenguaje de programación
- **Firebase Admin SDK** - Autenticación y base de datos
- **Pydantic** - Validación de datos
- **aiohttp** - Cliente HTTP asíncrono
- **aiofiles** - Operaciones de archivos asíncronas

## 📦 Instalación

### Prerrequisitos
- Node.js 16+
- Python 3.9+
- Cuenta de Firebase

### Backend
```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar Firebase
# 1. Crear proyecto en Firebase Console
# 2. Descargar el archivo de credenciales JSON
# 3. Colocarlo en secrets/kubernetes-sd.json

# Ejecutar servidor
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones de Firebase

# Ejecutar aplicación
npm start
```

## 📚 API Endpoints

### Autenticación
- `GET /api/auth/users/{uid}` - Obtener información de usuario

### Tareas
- `GET /api/tasks` - Listar tareas
- `POST /api/tasks` - Crear tarea
- `GET /api/tasks/{task_id}` - Obtener tarea
- `PUT /api/tasks/{task_id}` - Actualizar tarea
- `DELETE /api/tasks/{task_id}` - Eliminar tarea
- `PATCH /api/tasks/{task_id}/toggle` - Cambiar estado de completado
- `POST /api/tasks/{task_id}/collaborators` - Agregar colaborador
- `DELETE /api/tasks/{task_id}/collaborators/{uid}` - Remover colaborador

### Service Registry (Nuevo)
- `GET /api/services/` - Listar todos los servicios
- `POST /api/services/register` - Registrar nuevo servicio
- `GET /api/services/{service_name}` - Obtener servicio específico
- `PUT /api/services/{service_name}` - Actualizar servicio
- `DELETE /api/services/{service_name}` - Eliminar servicio
- `GET /api/services/tag/{tag}` - Filtrar por tag
- `POST /api/services/health-check` - Ejecutar health check
- `GET /api/services/discovery/config` - Generar configuración de service discovery

## 🚀 Mejoras de Rendimiento

### Backend Asíncrono
Se han convertido todas las operaciones a asíncronas para mejorar el rendimiento:

- ✅ **Firebase Auth**: Operaciones de autenticación asíncronas
- ✅ **Firebase Firestore**: Consultas de base de datos asíncronas
- ✅ **Service Registry**: Operaciones de archivo y health checks asíncronos
- ✅ **HTTP Requests**: Cliente aiohttp para requests no bloqueantes

### Beneficios:
- **Mejor escalabilidad**: Manejo de múltiples requests concurrentes
- **Menor latencia**: Operaciones no bloqueantes
- **Eficiencia de recursos**: Mejor uso de CPU y memoria

## 📊 Service Discovery

### Ejemplo de Configuración Generada
```json
{
  "version": "1.0",
  "generated_at": "2024-10-04T15:30:00Z",
  "total_services": 3,
  "services": {
    "api-gateway": {
      "name": "api-gateway",
      "host": "gateway.example.com",
      "port": 8080,
      "protocol": "https",
      "status": "active",
      "url": "https://gateway.example.com:8080",
      "tags": ["gateway", "production"]
    }
  },
  "by_tag": {
    "production": ["api-gateway"],
    "database": ["postgres-main"]
  },
  "by_protocol": {
    "https": ["api-gateway"],
    "tcp": ["postgres-main"]
  }
}
```

## 🔄 Roadmap

- [ ] Migrar service registry a base de datos
- [ ] Agregar métricas y monitoreo
- [ ] Implementar webhooks para notificaciones
- [ ] Soporte para service mesh (Istio, Linkerd)
- [ ] API GraphQL
- [ ] Dashboard de analytics
