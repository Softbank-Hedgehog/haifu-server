# app/schemas/auth.py
from pydantic import BaseModel
from typing import Optional


class GitHubCallbackRequest(BaseModel):
    """GitHub OAuth 콜백 요청"""
    code: str


class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: int
    username: str
    email: Optional[str] = None
    avatar_url: str
    name: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT 토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GitHubLoginUrlResponse(BaseModel):
    """GitHub 로그인 URL 응답"""
    url: str