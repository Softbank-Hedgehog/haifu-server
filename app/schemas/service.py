# app/schemas/service.py
import uuid
from typing import Dict, List, Optional, Literal
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
    # 공통 식별자
    # user_id: str
    # project_id: str
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        alias="service_id",
        description="서비스 ID (없으면 자동 생성)"
    )

    service_type: Literal["static", "dynamic"]

    # static 서비스용
    build_commands: Optional[List[str]] = None
    build_output_dir: Optional[str] = None
    node_version: Optional[str] = None

    # dynamic / 공통 리소스 정보
    runtime: Optional[Literal["nodejs18", "python3.11", "java17", "go1.21"]] = None
    start_command: Optional[str] = None
    dockerfile: Optional[str] = None

    cpu: Optional[int] = None          # 256, 512 ...
    memory: Optional[int] = None       # 512, 1024 ...
    port: Optional[int] = Field(default=None, ge=1, le=65535)

    environment_variables: Optional[Dict[str, str]] = None



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
    id: str = Field(..., description="서비스 ID")
    project_id: str = Field(..., description="프로젝트 ID")
    user_id: str = Field(..., description="사용자 ID (GitHub user ID 등)")
    service_type: Literal["static", "dynamic"] = Field(..., description="서비스 타입")

    # 공통 리소스 정보
    runtime: Optional[str] = Field(None, description="런타임 환경 (nodejs18, python3.11 등)")
    cpu: Optional[int] = Field(None, description="CPU (예: 256, 512)")
    memory: Optional[int] = Field(None, description="메모리 (MB 단위)")
    port: Optional[int] = Field(None, description="서비스 포트")

    # 동적(dynamic) 서비스 전용
    start_command: Optional[str] = Field(None, description="시작 명령어")
    dockerfile: Optional[str] = Field(None, description="커스텀 Dockerfile 내용 또는 경로")

    # 정적(static) 서비스 전용
    build_commands: Optional[List[str]] = Field(None, description="빌드 명령어 목록")
    build_output_dir: Optional[str] = Field(None, description="빌드 산출물 디렉토리")
    node_version: Optional[str] = Field(None, description="Node.js 버전")

    # 공통
    environment_variables: Optional[Dict[str, str]] = Field(
        None,
        description="환경 변수"
    )
    deployment_url: Optional[str] = Field(None, description="배포 URL")
    created_at: str = Field(..., description="생성 일시 (ISO 8601)")
    updated_at: str = Field(..., description="수정 일시 (ISO 8601)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "svc123456",
                "project_id": "proj456789",
                "user_id": "123",
                "service_type": "dynamic",
                "runtime": "nodejs18",
                "cpu": 256,
                "memory": 512,
                "port": 8080,
                "start_command": "npm start",
                "dockerfile": "dockerfile! dockerfile! this is dockerfile! believe me",
                "environment_variables": {
                    "NODE_ENV": "production"
                },
                "deployment_url": "https://api.example.com",
                "created_at": "2025-11-18T10:30:00Z",
                "updated_at": "2025-11-18T10:35:00Z"
            }
        }

class DeployResponse(BaseModel):
    service_id: str = Field(..., description="배포 요청한 서비스 ID")
    # project_id: str = Field(..., description="프로젝트 ID")
    service_type: str = Field(..., description="서비스 타입 (static | dynamic)")
    status: str = Field(..., description="배포 요청 상태 (queued 등)")
    lambda_request_id: Optional[str] = Field(None, description="Lambda invoke RequestId")