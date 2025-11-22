# app/service/source_snapshot_service.py
import json
import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import quote

import boto3
import httpx

from app.service.github_service import GitHubService
from app.schemas.source_snapshot import SourceSnapshotRequest, SourceSnapshotResponse

logger = logging.getLogger(__name__)

s3_client = boto3.client("s3")
SOURCE_BUCKET_NAME = os.getenv("SOURCE_BUCKET_NAME")


class SourceSnapshotServiceError(Exception):
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause


class SourceSnapshotService:
    @staticmethod
    async def create_snapshot(
        user_id: int,
        req: SourceSnapshotRequest,
        github: GitHubService,
    ) -> SourceSnapshotResponse:
        if not SOURCE_BUCKET_NAME:
            raise SourceSnapshotServiceError("SOURCE_BUCKET_NAME is not configured")

        base_prefix = SourceSnapshotService._build_base_prefix(
            user_id=user_id,
            project_id=req.project_id,
            tmp_id=req.tmp_id
        )

        # source_path 없으면 레포 루트부터
        root_path = (req.source_path or "").strip("/")

        file_count = await SourceSnapshotService._walk_and_upload(
            github=github,
            owner=req.owner,
            repo=req.repo,
            current_path=root_path,  # "" 이면 레포 루트
            ref=req.branch,
            base_prefix=base_prefix,
            root_path=root_path,
        )

        return SourceSnapshotResponse(
            bucket=SOURCE_BUCKET_NAME,
            s3_prefix=base_prefix,
            file_count=file_count,
        )

    @staticmethod
    def _build_base_prefix(user_id: int, project_id: str, tmp_id: int) -> str:
        return (
            f"user/{quote(str(user_id))}"
            f"/{quote(project_id)}"
            f"/{quote(f'{tmp_id}')}"
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
        logger.info(f"[DEBUG] Entering _walk_and_upload: current_path='{current_path}'")

        try:
            contents = await github.get_repository_contents(
                owner=owner,
                repo=repo,
                path=current_path,
                ref=ref,
            )

            logger.info(
                "[DEBUG] Raw contents JSON: %s",
                json.dumps(contents, indent=2, ensure_ascii=False),
            )
        except Exception as e:
            raise SourceSnapshotServiceError(
                f"Failed to get contents for {owner}/{repo}:{current_path}@{ref}",
                cause=e,
            )

        # 1) dict / list 를 하나의 리스트로 통일
        if isinstance(contents, dict):
            items = [contents]
        elif isinstance(contents, list):
            items = contents
        else:
            logger.warning(
                f"[SNAPSHOT] Unknown contents type: {type(contents)} for path='{current_path}'"
            )
            return 0

        file_count = 0

        # 2) 이제부터는 item['type'] 만 보고 처리
        for item in items:
            item_type = item.get("type")
            item_path = item.get("path", "")

            logger.info(f"[SNAPSHOT] item_type={item_type}, item_path={item_path}")

            if item_type == "dir":
                # 혹시라도 자기 자신을 다시 타는 경우 방지
                if item_path == current_path:
                    logger.warning(f"[SNAPSHOT] Skip self directory path='{item_path}'")
                    continue

                logger.info(f"[SNAPSHOT] Entering directory: {item_path}")
                file_count += await SourceSnapshotService._walk_and_upload(
                    github=github,
                    owner=owner,
                    repo=repo,
                    current_path=item_path,
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
                logger.info(f"[SNAPSHOT] Skipping {item_type}: {item_path}")

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
        path = item["path"]

        # root_path 기준 상대 경로 계산
        rel_path = path
        if root_path:
            if path.startswith(root_path + "/"):
                rel_path = path[len(root_path) + 1 :]
            elif path == root_path:
                rel_path = os.path.basename(path)

        s3_key = f"{base_prefix}/{rel_path}"

        file_bytes = await github.download_file_bytes(
            owner=owner,
            repo=repo,
            path=path,
            ref=ref,
        )

        logger.info(f"Uploading to s3://{SOURCE_BUCKET_NAME}/{s3_key}")
        s3_client.put_object(
            Bucket=SOURCE_BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
        )

    @staticmethod
    async def _download_file_bytes(download_url: str, headers: Dict[str, str]) -> bytes:
        async with httpx.AsyncClient() as client:
            resp = await client.get(download_url, headers=headers, timeout=30.0)
            if resp.status_code != 200:
                raise SourceSnapshotServiceError(
                    f"Failed to download file from GitHub: {resp.status_code}"
                )
            return resp.content
