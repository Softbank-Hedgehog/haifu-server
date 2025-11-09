from pydantic import BaseModel
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"

class MemberCreate(BaseModel):
    login_id: str
    password: str
    nickname: str

class MemberResponse(BaseModel):
    member_id: str
    login_id: str
    nickname: str
    role: str
    created_at: str

    class Config:
        orm_mode = True

# 로그인 요청 DTO
class MemberLogin(BaseModel):
    login_id: str
    password: str

