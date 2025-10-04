from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime
from models.schemas import ServiceRegistry, ServiceRegistryCreate, ServiceRegistryUpdate
import logging
import os

logger = logging.getLogger(__name__)

class ServiceRegistryService:
    def __init__(self, data_file: str = "services.json"):
        # En memoria por simplicidad
        self.services: Dict[str, ServiceRegistry] = {}
        self.data_file = data_file
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Inicializar el servicio cargando datos desde archivo"""
        await self._load_from_file()
    
    async def _load_from_file(self):
        """Cargar servicios desde archivo JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for service_data in data.get('services', []):
                        # Convertir strings de datetime a datetime objects
                        if 'created_at' in service_data and isinstance(service_data['created_at'], str):
                            service_data['created_at'] = datetime.fromisoformat(service_data['created_at'].replace('Z', '+00:00'))
                        if 'updated_at' in service_data and isinstance(service_data['updated_at'], str):
                            service_data['updated_at'] = datetime.fromisoformat(service_data['updated_at'].replace('Z', '+00:00'))
                        
                        service = ServiceRegistry(**service_data)
                        self.services[service.name] = service
                logger.info(f"Loaded {len(self.services)} services from {self.data_file}")
            else:
                logger.info(f"No {self.data_file} found, starting with empty registry")
        except Exception as e:
            logger.error(f"Error loading services from file: {e}")
    
    async def _save_to_file(self):
        """Guardar servicios a archivo JSON"""
        try:
            data = {
                'services': [service.dict() for service in self.services.values()],
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.debug(f"Saved {len(self.services)} services to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving services to file: {e}")
    
    async def register_service(self, service_data: ServiceRegistryCreate) -> ServiceRegistry:
        """Registrar un nuevo servicio"""
        async with self._lock:
            if service_data.name in self.services:
                raise ValueError(f"Service '{service_data.name}' already exists")
            
            service = ServiceRegistry(
                id=service_data.name,
                name=service_data.name,
                host=service_data.host,
                port=service_data.port,
                protocol=service_data.protocol,
                health_check_url=service_data.health_check_url,
                tags=service_data.tags,
                status="active",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.services[service.name] = service
            await self._save_to_file()
            
            logger.info(f"Service registered: {service.name} at {service.host}:{service.port}")
            return service
    
    async def get_all_services(self) -> List[ServiceRegistry]:
        """Obtener todos los servicios"""
        return list(self.services.values())
    
    async def get_service(self, name: str) -> Optional[ServiceRegistry]:
        """Obtener un servicio específico"""
        return self.services.get(name)
    
    async def update_service(self, name: str, service_data: ServiceRegistryUpdate) -> Optional[ServiceRegistry]:
        """Actualizar un servicio"""
        async with self._lock:
            if name not in self.services:
                return None
            
            service = self.services[name]
            update_dict = service_data.dict(exclude_unset=True)
            
            for key, value in update_dict.items():
                if hasattr(service, key):
                    setattr(service, key, value)
            
            service.updated_at = datetime.now()
            await self._save_to_file()
            
            logger.info(f"Service updated: {name}")
            return service
    
    async def remove_service(self, name: str) -> bool:
        """Eliminar un servicio"""
        async with self._lock:
            if name in self.services:
                del self.services[name]
                await self._save_to_file()
                logger.info(f"Service removed: {name}")
                return True
            return False
    
    async def get_services_by_tag(self, tag: str) -> List[ServiceRegistry]:
        """Obtener servicios por tag"""
        return [service for service in self.services.values() if tag in service.tags]
    
    async def get_services_by_status(self, status: str) -> List[ServiceRegistry]:
        """Obtener servicios por status"""
        return [service for service in self.services.values() if service.status == status]

# Instancia global
service_registry = ServiceRegistryService()