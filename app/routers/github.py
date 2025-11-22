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
    "/{owner}/{project_id}",
    response_model=ApiResponse[GitHubSnapshotUrlResponse],
    responses=common_responses,
    status_code=status.HTTP_201_CREATED,
    summary="선택한 GitHub 레포를 S3에 저장",
)
async def save_repo_to_s3(
    owner: str,
    project_id: str,
    body: GitHubRepoSnapshotRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    레포지토리 목록 화면에서 선택한 레포 정보를 그대로 받아서
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

    # 3. full_name 기준으로 repo 이름 분리 (owner/repo)
    try:
        full_owner, repo_name = body.full_name.split("/", 1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid full_name: {body.full_name}",
        )

    # owner path param과 body.full_name 이 다른 경우 간단히 체크만 해둠
    if full_owner != owner:
        # 그냥 로그만 남기고 진행하거나, 에러로 막고 싶으면 400으로 바꿔도 됨
        # 여기서는 일단 에러로 처리
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Owner mismatch: path={owner}, full_name={body.full_name}",
        )

    # 4. 기존 SourceSnapshotRequest 로 매핑
    #    service_id 는 아직 프론트에서 안 쓰니까, 일단 레포 id 기반으로 내부적으로만 사용
    snapshot_req = SourceSnapshotRequest(
        project_id=project_id,
        service_id=str(body.id),  # 레포 id 를 service_id 처럼 활용 (나중에 서비스와 매핑 가능)
        owner=owner,
        repo=repo_name,
        branch=body.branch or body.default_branch,
        source_path=body.source_path,
    )

    # 5. S3 스냅샷 생성
    try:
        snapshot = await SourceSnapshotService.create_snapshot(
            user_id=user_id,
            req=snapshot_req,
            github=github,
        )
    except SourceSnapshotServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    # 6. 프론트 요구사항에 맞게 url 하나로 변환
    #    (일단 s3:// 형태로 반환, 필요하면 https:// 로 바꿔도 됨)
    s3_url = f"s3://{snapshot.bucket}/{snapshot.s3_prefix}"

    return success_response(
        data=GitHubSnapshotUrlResponse(url=s3_url),
        message="S3 save successfully",
    )
