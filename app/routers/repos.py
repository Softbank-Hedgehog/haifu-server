# app/routers/repos.py
from fastapi import APIRouter, Depends, HTTPException
import httpx
from app.core.security import get_current_user

router = APIRouter(prefix="/api/repos", tags=["Repositories"])


@router.get("/list")
async def list_repositories(
        page: int = 1,
        per_page: int = 30,
        current_user: dict = Depends(get_current_user)  # ← JWT 검증
):
    """
    사용자의 GitHub 레포 목록 조회

    1. JWT 토큰에서 github_access_token 추출
    2. GitHub API 호출
    3. 레포 목록 반환
    """
    # JWT 토큰에서 GitHub Access Token 가져오기
    github_token = current_user.get('github_access_token')

    if not github_token:
        raise HTTPException(status_code=401, detail="GitHub token not found")

    # GitHub API 호출
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://api.github.com/user/repos',
            headers={
                'Authorization': f'Bearer {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            },
            params={
                'page': page,
                'per_page': per_page,
                'sort': 'updated',
                'affiliation': 'owner,collaborator'
            },
            timeout=10.0
        )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch repositories")

    repos_data = response.json()

    # 필요한 정보만 추출
    repos = [
        {
            'id': repo['id'],
            'name': repo['name'],
            'full_name': repo['full_name'],
            'description': repo.get('description', ''),
            'html_url': repo['html_url'],
            'clone_url': repo['clone_url'],
            'default_branch': repo['default_branch'],
            'language': repo.get('language', ''),
            'private': repo['private'],
            'updated_at': repo['updated_at'],
        }
        for repo in repos_data
    ]

    return {
        'repositories': repos,
        'page': page,
        'total': len(repos)
    }


@router.get("/{owner}/{repo}")
async def get_repository(
        owner: str,
        repo: str,
        current_user: dict = Depends(get_current_user)
):
    """
    특정 레포지토리 상세 정보 조회

    예시:
    - GET /api/repos/facebook/react
    - GET /api/repos/vercel/next.js
    """
    github_token = current_user.get('github_access_token')

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'https://api.github.com/repos/{owner}/{repo}',
            headers={
                'Authorization': f'Bearer {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            },
            timeout=10.0
        )

    if response.status_code == 404:
        raise HTTPException(404, detail=f"Repository {owner}/{repo} not found")

    if response.status_code == 401:
        raise HTTPException(401, detail="GitHub token invalid")

    if response.status_code != 200:
        raise HTTPException(400, detail="Failed to fetch repository")

    repo_data = response.json()

    return {
        'id': repo_data['id'],
        'name': repo_data['name'],
        'full_name': repo_data['full_name'],
        'description': repo_data.get('description', ''),
        'html_url': repo_data['html_url'],
        'clone_url': repo_data['clone_url'],
        'ssh_url': repo_data['ssh_url'],
        'default_branch': repo_data['default_branch'],
        'language': repo_data.get('language', ''),
        'languages_url': repo_data['languages_url'],
        'private': repo_data['private'],
        'owner': {
            'login': repo_data['owner']['login'],
            'avatar_url': repo_data['owner']['avatar_url'],
        },
        'topics': repo_data.get('topics', []),
        'size': repo_data['size'],
        'stargazers_count': repo_data['stargazers_count'],
        'watchers_count': repo_data['watchers_count'],
        'forks_count': repo_data['forks_count'],
        'open_issues_count': repo_data['open_issues_count'],
        'created_at': repo_data['created_at'],
        'updated_at': repo_data['updated_at'],
        'pushed_at': repo_data['pushed_at'],
    }