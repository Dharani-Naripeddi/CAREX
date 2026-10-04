from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.role import RoleEnum


class RoleBase(BaseModel):
    name: RoleEnum
    display_name: str
    description: Optional[str] = None
    permissions: List[str] = []


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
