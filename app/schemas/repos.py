# app/schemas/repos.py
from pydantic import BaseModel
from app.schemas.github import RepositoryDetail
from app.schemas.source_snapshot import SourceSnapshotResponse


class RepositoryWithSnapshot(BaseModel):
    """레포지토리 정보 + 소스 스냅샷 정보를 함께 반환하는 DTO"""
    repository: RepositoryDetail
    snapshot: SourceSnapshotResponse