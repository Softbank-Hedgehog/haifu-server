# app/schemas/github_snapshot.py
from typing import Optional
from pydantic import BaseModel, Field


class GitHubRepoSnapshotRequest(BaseModel):
    """
    프론트에서 그대로 보내주는 GitHub 레포 정보 + 스냅샷 옵션
    """

    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    html_url: str
    clone_url: str
    default_branch: str
    language: Optional[str] = None
    private: bool
    updated_at: str  # 필요하면 datetime 으로 바꿀 수 있음

    branch: str = Field(..., description="스냅샷을 만들 브랜치 (선택 브랜치)")
    source_path: str = Field(
        "",
        alias="Source Directory",
        description="레포 내부 기준 경로. 비우면 레포 루트 전체",
    )

    class Config:
        # alias("Source Directory") 를 JSON 키로 그대로 받기 위함
        populate_by_name = True


class GitHubSnapshotUrlResponse(BaseModel):
    """
    S3 저장 결과를 프론트에 돌려줄 때 사용할 응답
    """

    url: str = Field(..., description="S3에 저장된 prefix URL (예: s3://bucket/prefix)")
