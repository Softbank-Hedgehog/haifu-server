# app/schemas/github.py
from typing import Optional
from pydantic import BaseModel, Field


class RepositoryOwner(BaseModel):
    """GitHub 레포지토리 소유자 정보"""
    login: str = Field(..., description="소유자 GitHub 로그인 ID")
    avatar_url: Optional[str] = Field(
        None,
        description="소유자 아바타 이미지 URL",
    )
    html_url: Optional[str] = Field(
        None,
        description="소유자 GitHub 프로필 URL",
    )


class RepositoryDetail(BaseModel):
    """GitHub 레포지토리 상세 정보"""

    id: int = Field(..., description="GitHub 레포지토리 ID")
    name: str = Field(..., description="레포지토리 이름 (예: haifu-backend)")
    full_name: str = Field(..., description="owner/name 형식의 전체 이름")
    owner: RepositoryOwner = Field(..., description="레포지토리 소유자 정보")

    description: Optional[str] = Field(
        None,
        description="레포지토리 설명",
    )
    html_url: str = Field(
        ...,
        description="GitHub 레포지토리 웹 URL",
    )

    default_branch: str = Field(
        "main",
        description="기본 브랜치 이름",
    )
    private: bool = Field(
        False,
        description="비공개 레포지토리 여부",
    )
    fork: bool = Field(
        False,
        description="포크된 레포지토리인지 여부",
    )
    visibility: Optional[str] = Field(
        None,
        description="public / private / internal 등 가시성",
    )

    language: Optional[str] = Field(
        None,
        description="대표 언어",
    )
    stargazers_count: int = Field(
        0,
        description="스타 수",
    )
    forks_count: int = Field(
        0,
        description="포크 수",
    )
    open_issues_count: int = Field(
        0,
        description="열려 있는 이슈 수",
    )

    updated_at: Optional[str] = Field(
        None,
        description="마지막 업데이트 시간 (ISO8601 문자열)",
    )