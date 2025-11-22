# app/routers/repos.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.core.security import get_current_user
from app.schemas.source_snapshot import SourceSnapshotResponse, SourceSnapshotRequest
from app.service.github_service import GitHubService
from typing import Any
from app.schemas.repos import RepositoryWithSnapshot
from app.schemas.common import success_response, list_response, ApiResponse, Repository, RepositoryDetail, FileContent, ListData, common_responses
from app.service.source_snapshot_service import SourceSnapshotService, SourceSnapshotServiceError

router = APIRouter(prefix="/repos", tags=["Repositories"])


@router.get("/list", response_model=ApiResponse[ListData[Repository]], responses=common_responses)
async def list_repositories(
        page: int = 1,
        per_page: int = 30,
        current_user: dict = Depends(get_current_user)
):
    """
    사용자의 GitHub 레포 목록 조회
    """
    github_token = current_user.get('github_access_token')
    github_service = GitHubService(github_token)
    
    repos = await github_service.get_user_repositories(page, per_page)
    
    return list_response(
        items=repos,
        page=page,
        per_page=per_page,
        total=len(repos),
        message="Repositories fetched successfully"
    )


@router.post(
    "/{owner}/{repo}",
    response_model=ApiResponse[RepositoryWithSnapshot],
    responses=common_responses,
    status_code=status.HTTP_201_CREATED,
    summary="레포지토리 정보 조회 + GitHub 소스 스냅샷을 S3에 업로드",
)
async def create_repository_snapshot(
    owner: str,
    repo: str,
    body: SourceSnapshotRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    지정한 GitHub 레포지토리에 대해

    1) 레포지토리 상세 정보를 조회하고
    2) project_id / service_id / branch / source_path 기준으로
       전체 파일을 재귀적으로 순회하여 S3에 스냅샷을 생성한 뒤
    3) 레포지토리 정보 + 스냅샷 정보를 함께 반환한다.
    """
    user_id = current_user["user_id"]

    # 1. GitHub 토큰 추출
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

    # 3. 레포지토리 상세 정보 조회
    try:
        repository_info: RepositoryDetail = await github.get_repository_details(owner, repo)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to fetch repository details: {e}",
        )

    # 4. Snapshot 요청 객체 정리
    #    - body에 owner/repo가 오더라도 path param 기준으로 강제 통일
    snapshot_req = body.copy(update={"owner": owner, "repo": repo})

    # 5. 소스 스냅샷 생성 (S3 업로드)
    try:
        snapshot: SourceSnapshotResponse = await SourceSnapshotService.create_snapshot(
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

    # 6. 레포 정보 + 스냅샷 정보 합쳐서 반환
    combined = RepositoryWithSnapshot(
        repository=repository_info,
        snapshot=snapshot,
    )

    return success_response(
        data=combined,
        message="Repository details fetched and source snapshot created successfully",
    )


@router.get("/{owner}/{repo}/contents", response_model=ApiResponse[Any], responses=common_responses)
async def get_repository_contents(
        owner: str,
        repo: str,
        path: str = "",
        ref: str = None,
        current_user: dict = Depends(get_current_user)
):
    """
    레포지토리 파일/폴더 목록 조회
    """
    github_token = current_user.get('github_access_token')
    github_service = GitHubService(github_token)
    
    contents_data = await github_service.get_repository_contents(owner, repo, path, ref)
    
    return success_response(
        data=contents_data,
        message="Repository contents fetched successfully"
    )


@router.get("/{owner}/{repo}/file", response_model=ApiResponse[FileContent], responses=common_responses)
async def get_file_content(
        owner: str,
        repo: str,
        path: str = Query(..., description="File path"),
        ref: str = Query(None, description="Branch or commit SHA"),
        current_user: dict = Depends(get_current_user)
):
    """
    특정 파일 내용 조회 (Base64 디코딩)
    """
    github_token = current_user.get('github_access_token')
    github_service = GitHubService(github_token)
    
    file_info = await github_service.get_file_content(owner, repo, path, ref)
    
    return success_response(
        data=file_info,
        message="File content fetched successfully"
    )


@router.get("/{owner}/{repo}/branches", response_model=ApiResponse[list], responses=common_responses)
async def get_repository_branches(
        owner: str,
        repo: str,
        current_user: dict = Depends(get_current_user)
):
    """
    레포지토리 브랜치 목록 조회

    서비스 생성 시 브랜치 선택을 위해 사용됩니다.
    """
    github_token = current_user.get('github_access_token')
    github_service = GitHubService(github_token)

    branches = await github_service.get_repository_branches(owner, repo)

    return success_response(
        data=branches,
        message="Branches fetched successfully"
    )