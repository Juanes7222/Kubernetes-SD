from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from core.auth_middleware import get_current_user
from services.service_registry import service_registry
from models.schemas import ServiceRegistry, ServiceRegistryResponse, ServiceRegistryCreate, ServiceRegistryUpdate
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/services", tags=["services"])

@router.post("/register", response_model=ServiceRegistry)
async def register_service(
    service: ServiceRegistryCreate,
    current_user: dict = Depends(get_current_user)
) -> ServiceRegistry:
    """Registrar un nuevo servicio"""
    try:
        logger.info(f"Registering service: {service.name} by user: {current_user.get('email', current_user.get('uid'))}")
        return await service_registry.register_service(service)
    except ValueError as e:
        logger.warning(f"Service registration failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=ServiceRegistryResponse)
async def get_all_services(
    tag: Optional[str] = Query(None, description="Filter by tag"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user)
) -> ServiceRegistryResponse:
    """Obtener todos los servicios con filtros opcionales"""
    try:
        if tag:
            services = await service_registry.get_services_by_tag(tag)
        elif status:
            services = await service_registry.get_services_by_status(status)
        else:
            services = await service_registry.get_all_services()
        
        logger.info(f"Retrieved {len(services)} services for user: {current_user.get('email', current_user.get('uid'))}")
        return ServiceRegistryResponse(services=services, total=len(services))
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{service_name}", response_model=ServiceRegistry)
async def get_service(
    service_name: str,
    current_user: dict = Depends(get_current_user)
) -> ServiceRegistry:
    """Obtener un servicio específico"""
    try:
        service = await service_registry.get_service(service_name)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        logger.info(f"Retrieved service {service_name} for user: {current_user.get('email', current_user.get('uid'))}")
        return service
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{service_name}", response_model=ServiceRegistry)
async def update_service(
    service_name: str,
    service_data: ServiceRegistryUpdate,
    current_user: dict = Depends(get_current_user)
) -> ServiceRegistry:
    """Actualizar un servicio"""
    try:
        service = await service_registry.update_service(service_name, service_data)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        logger.info(f"Updated service {service_name} by user: {current_user.get('email', current_user.get('uid'))}")
        return service
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating service {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{service_name}")
async def remove_service(
    service_name: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Eliminar un servicio"""
    try:
        success = await service_registry.remove_service(service_name)
        if not success:
            raise HTTPException(status_code=404, detail="Service not found")
        
        logger.info(f"Removed service {service_name} by user: {current_user.get('email', current_user.get('uid'))}")
        return {"message": f"Service '{service_name}' removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing service {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")