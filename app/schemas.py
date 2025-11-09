from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"

class MemberBase(BaseModel):
    user_id: str
    role: UserRole

class MemberCreate(MemberBase):
    password: str

class MemberResponse(MemberBase):
    id: int
    class Config:
        orm_mode = True  # SQLAlchemy 모델을 자동 직렬화
