# app/service/source_snapshot_service.py
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Union
from urllib.parse import quote

import boto3
import httpx

from app.service.github_service import GitHubService
from app.schemas.source_snapshot import SourceSnapshotRequest, SourceSnapshotResponse

logger = logging.getLogger(__name__)

s3_client = boto3.client("s3")

SOURCE_BUCKET_NAME = os.getenv("SOURCE_BUCKET_NAME")


class SourceSnapshotServiceError(Exception):
    """소스 스냅샷 관련 도메인 에러"""
    pass


class SourceSnapshotService:
    @staticmethod
    async def create_snapshot(
        user_id: int,
        req: SourceSnapshotRequest,
        github: GitHubService,
    ) -> SourceSnapshotResponse:
        """
        GitHub 레포지토리의 특정 브랜치 / 경로 기준으로
        전체 파일을 재귀적으로 순회하여 S3에 업로드한다.
        """
        if not SOURCE_BUCKET_NAME:
                raise SourceSnapshotServiceError("SOURCE_BUCKET_NAME is not configured")

        # user, project, service 기준 prefix 생성
        date_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        base_prefix = SourceSnapshotService._build_base_prefix(
            user_id=user_id,
            project_id=req.project_id,
            service_id=req.service_id,
            date_str=date_str,
        )

        # source_path 기준 경로 정리
        root_path = (req.source_path or "").strip("/")

        # 루트 기준으로 재귀 순회하여 업로드
        file_count = await SourceSnapshotService._walk_and_upload(
            github=github,
            owner=req.owner,
            repo=req.repo,
            current_path=root_path,   # "" 혹은 "src" 같은 루트 경로
            ref=req.branch,
            base_prefix=base_prefix,
            root_path=root_path,      # 상대 경로 계산 기준
        )

        return SourceSnapshotResponse(
            bucket=SOURCE_BUCKET_NAME,
            s3_prefix=base_prefix,
            file_count=file_count,
        )

    @staticmethod
    def _build_base_prefix(user_id: int, project_id: str, service_id: str, date_str: str) -> str:
        """
        user/{userId}/{projectId}/{serviceId}/{date}-sourcefile 형태 prefix 생성
        URL-safe 하게 인코딩
        """
        return (
            f"user/{quote(str(user_id))}"
            f"/{quote(project_id)}"
            f"/{quote(service_id)}"
            f"/{date_str}-sourcefile"
        )

    @staticmethod
    async def _walk_and_upload(
        github: GitHubService,
        owner: str,
        repo: str,
        current_path: str,
        ref: str,
        base_prefix: str,
        root_path: str,
    ) -> int:
        """
        GitHub 레포지토리의 current_path 하위를 재귀적으로 순회하며
        파일들을 S3에 업로드한다.
        반환값은 업로드한 파일 개수.
        """
        try:
            contents = await github.get_repository_contents(
                owner=owner,
                repo=repo,
                path=current_path,
                ref=ref,
            )
        except Exception as e:
            logger.error(f"Failed to get contents for {owner}/{repo}:{current_path}@{ref} - {e}")
            raise

        file_count = 0

        # GitHub Contents API 특성:
        # - 디렉토리: list[items]
        # - 파일: 단일 dict
        if isinstance(contents, dict):
            # 단일 파일인 경우
            if contents.get("type") == "file":
                await SourceSnapshotService._upload_file_item(
                    github=github,
                    item=contents,
                    owner=owner,
                    repo=repo,
                    ref=ref,
                    base_prefix=base_prefix,
                    root_path=root_path,
                )
                return 1
            # 혹시 모르는 타입
            return 0

        if not isinstance(contents, list):
            # 방어적 처리
            logger.warning(f"Unexpected contents type for {owner}/{repo}:{current_path}: {type(contents)}")
            return 0

        for item in contents:
            item_type = item.get("type")
            if item_type == "dir":
                # 디렉토리면 재귀적으로 계속 들어감 (깊이 제한 없음)
                file_count += await SourceSnapshotService._walk_and_upload(
                    github=github,
                    owner=owner,
                    repo=repo,
                    current_path=item["path"],  # 예: "src/app", "src/app/routes"
                    ref=ref,
                    base_prefix=base_prefix,
                    root_path=root_path,
                )
            elif item_type == "file":
                await SourceSnapshotService._upload_file_item(
                    github=github,
                    item=item,
                    owner=owner,
                    repo=repo,
                    ref=ref,
                    base_prefix=base_prefix,
                    root_path=root_path,
                )
                file_count += 1
            else:
                # symlink, submodule 등은 일단 스킵
                logger.info(
                    f"Skipping unsupported item type: {item_type} path={item.get('path')}"
                )

        return file_count

    @staticmethod
    async def _upload_file_item(
        github: GitHubService,
        item: Dict[str, Any],
        owner: str,
        repo: str,
        ref: str,
        base_prefix: str,
        root_path: str,
    ) -> None:
        """
        GitHub Contents API의 단일 file item을 S3에 업로드한다.
        root_path 기준 상대 경로로 S3 key를 만든다.
        """
        path = item["path"]  # 예: "src/main.py", "src/app/routes/index.py"
        download_url = item.get("download_url")

        if not download_url:
            logger.warning(f"File item has no download_url: {path}")
            return

        # root_path 기준 상대 경로 계산
        # root_path = "src"라면 "src/app/index.tsx" → "app/index.tsx"
        rel_path = path
        if root_path:
            if path.startswith(root_path + "/"):
                rel_path = path[len(root_path) + 1 :]
            elif path == root_path:
                # root_path가 파일 이름인 경우 (예외적인 상황)
                rel_path = os.path.basename(path)
        # root_path가 비어 있으면 레포 루트 전체를 대상으로 하므로 path 그대로 사용

        s3_key = f"{base_prefix}/{rel_path}"

        # 파일 바이트 다운로드 (깊이/타입 무관)
        file_bytes = await SourceSnapshotService._download_file_bytes(
            download_url=download_url,
            headers=github.headers,  # 기존 GitHubService의 헤더 재사용 (private repo 대비)
        )

        # S3 업로드
        logger.info(f"Uploading to s3://{SOURCE_BUCKET_NAME}/{s3_key}")
        s3_client.put_object(
            Bucket=SOURCE_BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
        )

    @staticmethod
    async def _download_file_bytes(download_url: str, headers: Dict[str, str]) -> bytes:
        """
        download_url을 통해 raw 파일 바이트를 가져온다.
        private repo 대비를 위해 Authorization 헤더를 그대로 사용한다.
        """
        async with httpx.AsyncClient() as client:
            # raw URL에도 Authorization 붙여줌 (private repo 지원)
            resp = await client.get(download_url, headers=headers, timeout=30.0)
            if resp.status_code != 200:
                raise SourceSnapshotServiceError(
                    f"Failed to download file from GitHub: {resp.status_code}"
                )
            return resp.content
