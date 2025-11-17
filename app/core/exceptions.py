# app/core/exceptions.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from app.schemas.common import error_response

class GitHubAPIException(HTTPException):
    """GitHub API 관련 예외"""
    def __init__(self, status_code: int, message: str, error_code: str = "GITHUB_API_ERROR"):
        self.error_code = error_code
        super().__init__(status_code=status_code, detail=message)

class AuthenticationException(HTTPException):
    """인증 관련 예외"""
    def __init__(self, message: str = "Authentication failed", error_code: str = "AUTH_ERROR"):
        self.error_code = error_code
        super().__init__(status_code=401, detail=message)

class RepositoryNotFoundException(HTTPException):
    """레포지토리 찾을 수 없음 예외"""
    def __init__(self, repo_name: str):
        self.error_code = "REPO_NOT_FOUND"
        super().__init__(status_code=404, detail=f"Repository {repo_name} not found")

class FileNotFoundException(HTTPException):
    """파일 찾을 수 없음 예외"""
    def __init__(self, file_path: str):
        self.error_code = "FILE_NOT_FOUND"
        super().__init__(status_code=404, detail=f"File {file_path} not found")

# 전역 예외 핸들러
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException 전역 핸들러"""
    error_code = getattr(exc, 'error_code', 'HTTP_ERROR')
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.detail,
            error_code=error_code
        )
    )

async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 전역 핸들러"""
    return JSONResponse(
        status_code=500,
        content=error_response(
            message="Internal server error",
            error_code="INTERNAL_ERROR"
        )
    )