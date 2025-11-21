# app/routers/source_snapshot.py
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user  # 실제 경로에 맞게 수정
from app.service.github_service import GitHubService
from app.schemas.source_snapshot import (
    SourceSnapshotRequest,
    SourceSnapshotResponse,
)
from app.service.source_snapshot_service import (
    SourceSnapshotService,
    SourceSnapshotServiceError,
)

router = APIRouter(
    prefix="/source-snapshots",
    tags=["source-snapshots"],
)


@router.post(
    "",
    response_model=SourceSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="GitHub 소스 스냅샷을 S3에 업로드",
)
async def create_source_snapshot(
    body: SourceSnapshotRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    GitHub 레포지토리에서 지정한 브랜치/경로 기준으로
    전체 파일을 재귀적으로 순회하여 S3에 업로드하고,
    업로드된 위치 정보를 반환한다.
    """
    user_id = current_user["user_id"]

    # TODO: 실제 사용자 모델에 맞게 access token 가져오는 부분 조정 필요
    github_token = current_user.get("github_access_token") or current_user.get("access_token")
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub access token not found in current_user",
        )

    try:
        github = GitHubService(access_token=github_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    try:
        result = await SourceSnapshotService.create_snapshot(
            user_id=user_id,
            req=body,
            github=github,
        )
        return result

    except SourceSnapshotServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # 예상 못한 에러는 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
