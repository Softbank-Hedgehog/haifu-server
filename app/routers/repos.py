# app/routers/repos.py
from fastapi import APIRouter, Depends, Query
from app.core.security import get_current_user
from app.service.github_service import GitHubService
from typing import Any
from app.schemas.common import success_response, list_response, ApiResponse, Repository, RepositoryDetail, FileContent, ListData, common_responses

router = APIRouter(prefix="/api/repos", tags=["Repositories"])


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


@router.get("/{owner}/{repo}", response_model=ApiResponse[RepositoryDetail], responses=common_responses)
async def get_repository(
        owner: str,
        repo: str,
        current_user: dict = Depends(get_current_user)
):
    """
    특정 레포지토리 상세 정보 조회
    """
    github_token = current_user.get('github_access_token')
    github_service = GitHubService(github_token)
    
    repository_info = await github_service.get_repository_details(owner, repo)
    
    return success_response(
        data=repository_info,
        message="Repository details fetched successfully"
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