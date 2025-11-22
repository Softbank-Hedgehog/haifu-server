# app/schemas/service.py
import uuid
from typing import Optional, Dict
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# AWS App Runner 스펙 상수
# =============================================================================

RUNTIMES = [
    "PYTHON_3",      # Python 3
    "NODEJS_16",     # Node.js 16
    "NODEJS_18",     # Node.js 18
    "NODEJS_20",     # Node.js 20
    "JAVA_11",       # Java 11
    "JAVA_17",       # Java 17
    "DOTNET_6",      # .NET 6
    "GO_1",          # Go 1.x
    "PHP_81",        # PHP 8.1
    "RUBY_31",       # Ruby 3.1
]

CPU_OPTIONS = ["1 vCPU", "2 vCPU", "4 vCPU"]

MEMORY_OPTIONS = ["2 GB", "3 GB", "4 GB", "6 GB", "8 GB", "10 GB", "12 GB"]

# CPU-Memory 조합 제약 (AWS App Runner 기준)
CPU_MEMORY_COMBINATIONS = {
    "1 vCPU": ["2 GB", "3 GB", "4 GB"],
    "2 vCPU": ["4 GB", "6 GB", "8 GB"],
    "4 vCPU": ["8 GB", "10 GB", "12 GB"]
}

SERVICE_STATUS = ["pending", "running", "failed", "stopped"]


# =============================================================================
# Pydantic 모델
# =============================================================================

class ServiceCreate(BaseModel):
    """서비스 생성 요청"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = Field(..., min_length=1, max_length=100, description="서비스 이름")
    repo_owner: str = Field(..., description="GitHub 레포 소유자")
    repo_name: str = Field(..., description="GitHub 레포 이름")
    branch: str = Field(..., description="배포 브랜치")
    runtime: str = Field(..., description="런타임 환경")
    cpu: str = Field(..., description="CPU 사양")
    memory: str = Field(..., description="메모리 사양")
    port: int = Field(default=8080, ge=1, le=65535, description="애플리케이션 포트")
    build_command: Optional[str] = Field(None, description="빌드 명령어")
    start_command: Optional[str] = Field(None, description="시작 명령어")
    environment_variables: Optional[Dict[str, str]] = Field(None, description="환경변수")

    @field_validator('runtime')
    @classmethod
    def validate_runtime(cls, v):
        if v not in RUNTIMES:
            raise ValueError(f"Invalid runtime. Must be one of: {', '.join(RUNTIMES)}")
        return v

    @field_validator('cpu')
    @classmethod
    def validate_cpu(cls, v):
        if v not in CPU_OPTIONS:
            raise ValueError(f"Invalid CPU. Must be one of: {', '.join(CPU_OPTIONS)}")
        return v

    @field_validator('memory')
    @classmethod
    def validate_memory(cls, v):
        if v not in MEMORY_OPTIONS:
            raise ValueError(f"Invalid memory. Must be one of: {', '.join(MEMORY_OPTIONS)}")
        return v

    def validate_cpu_memory_combination(self):
        """CPU-Memory 조합 검증"""
        allowed_memory = CPU_MEMORY_COMBINATIONS.get(self.cpu, [])
        if self.memory not in allowed_memory:
            raise ValueError(
                f"Invalid CPU-Memory combination. "
                f"{self.cpu} supports: {', '.join(allowed_memory)}"
            )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Frontend",
                "repo_owner": "myshop",
                "repo_name": "web-frontend",
                "branch": "main",
                "runtime": "NODEJS_18",
                "cpu": "1 vCPU",
                "memory": "2 GB",
                "port": 3000,
                "build_command": "npm run build",
                "start_command": "npm start",
                "environment_variables": {
                    "NODE_ENV": "production",
                    "API_URL": "https://api.example.com"
                }
            }
        }


class ServiceUpdate(BaseModel):
    """서비스 수정 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="서비스 이름")
    branch: Optional[str] = Field(None, description="배포 브랜치")
    runtime: Optional[str] = Field(None, description="런타임 환경")
    cpu: Optional[str] = Field(None, description="CPU 사양")
    memory: Optional[str] = Field(None, description="메모리 사양")
    port: Optional[int] = Field(None, ge=1, le=65535, description="애플리케이션 포트")
    build_command: Optional[str] = Field(None, description="빌드 명령어")
    start_command: Optional[str] = Field(None, description="시작 명령어")
    environment_variables: Optional[Dict[str, str]] = Field(None, description="환경변수")

    @field_validator('runtime')
    @classmethod
    def validate_runtime(cls, v):
        if v is not None and v not in RUNTIMES:
            raise ValueError(f"Invalid runtime. Must be one of: {', '.join(RUNTIMES)}")
        return v

    @field_validator('cpu')
    @classmethod
    def validate_cpu(cls, v):
        if v is not None and v not in CPU_OPTIONS:
            raise ValueError(f"Invalid CPU. Must be one of: {', '.join(CPU_OPTIONS)}")
        return v

    @field_validator('memory')
    @classmethod
    def validate_memory(cls, v):
        if v is not None and v not in MEMORY_OPTIONS:
            raise ValueError(f"Invalid memory. Must be one of: {', '.join(MEMORY_OPTIONS)}")
        return v


class ServiceResponse(BaseModel):
    """서비스 응답"""
    id: str = Field(..., description="서비스 ID (UUID)")
    project_id: str = Field(..., description="프로젝트 ID")
    name: str = Field(..., description="서비스 이름")
    repo_owner: str = Field(..., description="GitHub 레포 소유자")
    repo_name: str = Field(..., description="GitHub 레포 이름")
    branch: str = Field(..., description="배포 브랜치")
    runtime: str = Field(..., description="런타임 환경")
    cpu: str = Field(..., description="CPU 사양")
    memory: str = Field(..., description="메모리 사양")
    port: int = Field(..., description="애플리케이션 포트")
    build_command: Optional[str] = Field(None, description="빌드 명령어")
    start_command: Optional[str] = Field(None, description="시작 명령어")
    environment_variables: Optional[Dict[str, str]] = Field(None, description="환경변수")
    status: str = Field(..., description="배포 상태")
    deployment_url: Optional[str] = Field(None, description="배포 URL")
    created_at: str = Field(..., description="생성 일시 (ISO 8601)")
    updated_at: str = Field(..., description="수정 일시 (ISO 8601)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "project_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "name": "Frontend",
                "repo_owner": "myshop",
                "repo_name": "web-frontend",
                "branch": "main",
                "runtime": "NODEJS_18",
                "cpu": "1 vCPU",
                "memory": "2 GB",
                "port": 3000,
                "build_command": "npm run build",
                "start_command": "npm start",
                "environment_variables": {
                    "NODE_ENV": "production",
                    "API_URL": "https://api.example.com"
                },
                "status": "running",
                "deployment_url": "https://frontend.example.com",
                "created_at": "2025-11-18T10:30:00Z",
                "updated_at": "2025-11-18T10:30:00Z"
            }
        }
