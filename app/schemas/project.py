# app/schemas/project.py
import uuid
from typing import Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """프로젝트 생성 요청"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100, description="프로젝트 이름")
    description: Optional[str] = Field(None, max_length=500, description="프로젝트 설명")


class ProjectUpdate(BaseModel):
    """프로젝트 수정 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="프로젝트 이름")
    description: Optional[str] = Field(None, max_length=500, description="프로젝트 설명")


class ProjectResponse(BaseModel):
    """프로젝트 응답"""
    id: str = Field(..., description="프로젝트 ID (UUID)")
    name: str = Field(..., description="프로젝트 이름")
    description: Optional[str] = Field(None, description="프로젝트 설명")
    user_id: int = Field(..., description="소유자 GitHub user ID")
    created_at: str = Field(..., description="생성 일시 (ISO 8601)")
    updated_at: str = Field(..., description="수정 일시 (ISO 8601)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "name": "쇼핑몰 플랫폼",
                "description": "E-commerce 프로젝트",
                "user_id": 12345678,
                "created_at": "2025-11-18T10:00:00Z",
                "updated_at": "2025-11-18T10:00:00Z"
            }
        }
