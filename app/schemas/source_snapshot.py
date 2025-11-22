# app/schemas/source_snapshot.py
from typing import Optional
from pydantic import BaseModel, Field


class SourceSnapshotRequest(BaseModel):
    """GitHub 소스 스냅샷 생성 요청"""
    project_id: str = Field(..., description="프로젝트 ID")
    tmp_id: int = Field(..., description="임시 ID")
    owner: str = Field(..., description="GitHub 레포지토리 소유자 (org/user)")
    repo: str = Field(..., description="GitHub 레포지토리 이름")
    branch: str = Field(..., description="브랜치 이름 (기본값: main)")
    source_path: str = Field(..., description="레포 내부 기준 경로 (예: 'src', 'apps/backend'). 비우면 레포 루트 전체.")


class SourceSnapshotResponse(BaseModel):
    """GitHub 소스 스냅샷 생성 응답"""
    bucket: str = Field(..., description="업로드된 S3 버킷 이름")
    s3_prefix: str = Field(..., description="업로드된 파일들의 공통 prefix")
    file_count: int = Field(..., description="업로드된 파일 개수")


