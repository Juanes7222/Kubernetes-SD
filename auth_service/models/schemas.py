from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, date
import uuid

# Define Models
class User(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    email_verified: bool = False