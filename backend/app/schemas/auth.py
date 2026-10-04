from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.models.role import RoleEnum


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserProfile"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    role: RoleEnum
    role_display_name: str
    permissions: List[str] = []
    department_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
