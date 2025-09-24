from datetime import datetime, date
from typing import Any, Dict, Union, Optional
import json
from core.logging_config import get_logger
from fastapi import HTTPException

logger = get_logger(__name__)

DateType = Union[str, datetime, date]

def to_firestore_dates(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert all datetime/date objects in a dict to ISO format strings for Firestore compatibility
    """
    def _convert(value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, dict):
            return {k: _convert(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_convert(item) for item in value]
        return value
    
    return _convert(data) if data else {}

def parse_date(date_str: Optional[str], default: Optional[DateType] = None) -> Optional[DateType]:
    """
    Try to parse a date string into a datetime or date object
    """
    if not date_str:
        return default
    
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO format con microsegundos y zona
        "%Y-%m-%dT%H:%M:%S%z",     # ISO format con zona
        "%Y-%m-%dT%H:%M:%S",       # ISO format sin zona
        "%Y-%m-%d",                # Solo fecha
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse the date: {date_str}")
    return default

def to_json(obj: Any) -> str:
    """
    Json serialization handling special types
    """
    def _default(obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return str(obj)
    
    return json.dumps(obj, default=_default)

async def safe_firebase_call(coro: Any, *args: Any, **kwargs: Any) -> Any:
    """
    Execute a Firebase call safely:
    - Allows HTTPException to pass through.
    """
    try:
        result = coro(*args, **kwargs)
        if hasattr(result, "__await__"):
            return await result
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Firebase call error: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )