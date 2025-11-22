# app/routers/github.py
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.schemas.common import success_response, ApiResponse, common_responses
from app.schemas.github_snapshot import (
    GitHubRepoSnapshotRequest,
    GitHubSnapshotUrlResponse,
)
from app.schemas.source_snapshot import SourceSnapshotRequest
from app.service.github_service import GitHubService
from app.service.source_snapshot_service import (
    SourceSnapshotService,
    SourceSnapshotServiceError,
)


router = APIRouter(prefix="/github", tags=["GitHub"])


@router.post(
    "/s3",
    response_model=ApiResponse[GitHubSnapshotUrlResponse],
    responses=common_responses,
    status_code=status.HTTP_201_CREATED,
    summary="선택한 GitHub 레포를 S3에 저장",
)
async def save_repo_to_s3(
    body: SourceSnapshotRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    레포지토리 목록 화면에서 선택한 레포 정보를 기반으로
    해당 레포의 소스를 S3에 스냅샷으로 저장한다.
    """

    user_id = current_user["user_id"]

    # 1. GitHub 토큰 꺼내기
    github_token = current_user.get("github_access_token") or current_user.get("access_token")
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub access token not found in current_user",
        )

    # 2. GitHub 서비스 생성
    try:
        github = GitHubService(access_token=github_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # 3. S3 스냅샷 생성
    snapshot = await SourceSnapshotService.create_snapshot(
        user_id=user_id,
        req=body,  # body 안에 project_id / service_id / owner / repo / branch / source_path 다 들어 있음
        github=github,
    )

    # 4. 프론트에서 원하는 형태로 URL만 반환
    s3_url = f"s3://{snapshot.bucket}/{snapshot.s3_prefix}"

    return success_response(
        data=GitHubSnapshotUrlResponse(url=s3_url),
        message="S3 save successfully",
    )
