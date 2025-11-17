# app/schemas/common.py
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')

# =============================================================================
# 공통 응답 모델
# =============================================================================

class ApiResponse(BaseModel, Generic[T]):
    """공통 API 성공 응답 모델"""
    success: bool
    message: str
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    """공통 API 에러 응답 모델"""
    success: bool = False
    message: str
    error_code: str

class ListData(BaseModel, Generic[T]):
    """리스트 데이터 모델"""
    items: list[T]
    page: int
    per_page: int
    total: int

# =============================================================================
# 데이터 모델
# =============================================================================

class ServerInfo(BaseModel):
    """서버 정보"""
    app_name: str
    status: str
    version: str

class GitHubLoginUrl(BaseModel):
    """GitHub 로그인 URL"""
    url: str

class UserInfo(BaseModel):
    """사용자 정보"""
    id: int
    username: str
    email: Optional[str] = None
    avatar_url: str
    name: Optional[str] = None

class HealthStatus(BaseModel):
    """헬스 체크 상태"""
    status: str

class Repository(BaseModel):
    """레포지토리 기본 정보"""
    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    html_url: str
    clone_url: str
    default_branch: str
    language: Optional[str] = None
    private: bool
    updated_at: str

class RepositoryOwner(BaseModel):
    """레포지토리 소유자 정보"""
    login: str
    avatar_url: str

class RepositoryDetail(BaseModel):
    """레포지토리 상세 정보"""
    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    html_url: str
    clone_url: str
    ssh_url: str
    default_branch: str
    language: Optional[str] = None
    languages_url: str
    private: bool
    owner: RepositoryOwner
    topics: list[str]
    size: int
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    created_at: str
    updated_at: str
    pushed_at: str

class FileContent(BaseModel):
    """파일 내용 정보"""
    name: str
    path: str
    size: int
    content: Optional[str] = None
    encoding: str
    sha: str
    download_url: Optional[str] = None

# =============================================================================
# 공통 에러 응답 정의
# =============================================================================

common_responses = {
    401: {"model": ErrorResponse, "description": "Unauthorized - 인증 실패"},
    403: {"model": ErrorResponse, "description": "Forbidden - 권한 없음"},
    404: {"model": ErrorResponse, "description": "Not Found - 리소스를 찾을 수 없음"},
    422: {"model": ErrorResponse, "description": "Validation Error - 입력 값 오류"},
    500: {"model": ErrorResponse, "description": "Internal Server Error - 서버 내부 오류"}
}

# =============================================================================
# 헬퍼 함수
# =============================================================================

def success_response(data: Any = None, message: str = "Success") -> dict:
    """성공 응답 생성"""
    return {
        "success": True,
        "message": message,
        "data": data
    }

def error_response(message: str, error_code: str = "UNKNOWN_ERROR") -> dict:
    """에러 응답 생성"""
    return {
        "success": False,
        "message": message,
        "error_code": error_code
    }

def list_response(items: list, page: int, per_page: int, total: int = None, message: str = "Success") -> dict:
    """리스트 응답 생성"""
    if total is None:
        total = len(items)
    
    return {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": total
        }
    }