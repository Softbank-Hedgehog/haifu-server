# app/github_service.py
import httpx
import base64
from typing import Optional, List, Dict, Any
from app.core.exceptions import GitHubAPIException, AuthenticationException
from app.core.logging import get_logger

logger = get_logger(__name__)

class GitHubService:
    """GitHub API 관련 비즈니스 로직"""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, access_token: str):
        if not access_token:
            raise AuthenticationException("GitHub access token is required")
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    async def download_file_bytes(
            self,
            owner: str,
            repo: str,
            path: str,
            ref: Optional[str] = None,
    ) -> bytes:
        """
        GitHub Contents API를 사용해서 raw 파일 바이트를 직접 받아온다.
        (download_url 사용 X, 항상 api.github.com 도메인만 사용)
        """
        params = {}
        if ref:
            params['ref'] = ref

        url = f'{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}'

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        **self.headers,
                        # raw 컨텐츠 직접 받기
                        'Accept': 'application/vnd.github.v3.raw',
                    },
                    params=params,
                    timeout=30.0,
                )
        except httpx.RequestError:
            raise GitHubAPIException(503, "GitHub API connection failed (download_file_bytes)")

        if response.status_code == 401:
            raise AuthenticationException("Invalid GitHub token")
        elif response.status_code == 404:
            raise GitHubAPIException(404, f"File {path} not found")
        elif response.status_code != 200:
            raise GitHubAPIException(response.status_code, f"Failed to download file {path}")

        return response.content

    async def get_user_repositories(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """사용자 레포지토리 목록 조회"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{self.BASE_URL}/user/repos',
                    headers=self.headers,
                    params={
                        'page': max(1, page),
                        'per_page': min(100, max(1, per_page)),
                        'sort': 'updated',
                        'affiliation': 'owner,collaborator'
                    },
                    timeout=10.0
                )
        except httpx.RequestError:
            raise GitHubAPIException(503, "GitHub API connection failed")
        
        if response.status_code == 401:
            raise AuthenticationException("Invalid GitHub token")
        elif response.status_code != 200:
            raise GitHubAPIException(response.status_code, "Failed to fetch repositories")
        
        repos_data = response.json()
        
        return [
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
    
    async def get_repository_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """레포지토리 상세 정보 조회"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{self.BASE_URL}/repos/{owner}/{repo}',
                    headers=self.headers,
                    timeout=10.0
                )
        except httpx.RequestError:
            raise GitHubAPIException(503, "GitHub API connection failed")
        
        if response.status_code == 401:
            raise AuthenticationException("Invalid GitHub token")
        elif response.status_code == 404:
            raise GitHubAPIException(404, f"Repository {owner}/{repo} not found")
        elif response.status_code != 200:
            raise GitHubAPIException(response.status_code, "Failed to fetch repository")
        
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
    
    async def get_repository_contents(self, owner: str, repo: str, path: str = "", ref: Optional[str] = None) -> Any:
        """레포지토리 파일/폴더 목록 조회"""
        params = {}
        if path:
            params['path'] = path
        if ref:
            params['ref'] = ref
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{self.BASE_URL}/repos/{owner}/{repo}/contents',
                    headers=self.headers,
                    params=params,
                    timeout=10.0
                )
        except httpx.RequestError:
            raise GitHubAPIException(503, "GitHub API connection failed")
        
        if response.status_code == 401:
            raise AuthenticationException("Invalid GitHub token")
        elif response.status_code == 404:
            raise GitHubAPIException(404, f"Path {path or 'root directory'} not found")
        elif response.status_code != 200:
            raise GitHubAPIException(response.status_code, "Failed to fetch contents")
        
        return response.json()
    
    async def get_file_content(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> Dict[str, Any]:
        """특정 파일 내용 조회"""
        params = {'path': path}
        if ref:
            params['ref'] = ref
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{self.BASE_URL}/repos/{owner}/{repo}/contents',
                    headers=self.headers,
                    params=params,
                    timeout=10.0
                )
        except httpx.RequestError:
            raise GitHubAPIException(503, "GitHub API connection failed")
        
        if response.status_code == 401:
            raise AuthenticationException("Invalid GitHub token")
        elif response.status_code == 404:
            raise GitHubAPIException(404, f"File {path} not found")
        elif response.status_code != 200:
            raise GitHubAPIException(response.status_code, "Failed to fetch file")
        
        file_data = response.json()
        
        if file_data.get('type') != 'file':
            raise GitHubAPIException(400, f"Path {path} is not a file")
        
        # Base64 디코딩
        content = None
        if file_data.get('content'):
            try:
                content = base64.b64decode(file_data['content']).decode('utf-8')
            except UnicodeDecodeError:
                content = None  # 바이너리 파일
        
        return {
            'name': file_data['name'],
            'path': file_data['path'],
            'size': file_data['size'],
            'content': content,
            'encoding': file_data['encoding'],
            'sha': file_data['sha'],
            'download_url': file_data.get('download_url')
        }

    async def get_repository_branches(self, owner: str, repo: str) -> List[str]:
        """레포지토리 브랜치 목록 조회"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{self.BASE_URL}/repos/{owner}/{repo}/branches',
                    headers=self.headers,
                    timeout=10.0
                )
        except httpx.RequestError:
            raise GitHubAPIException(503, "GitHub API connection failed")

        if response.status_code == 401:
            raise AuthenticationException("Invalid GitHub token")
        elif response.status_code == 404:
            raise GitHubAPIException(404, f"Repository {owner}/{repo} not found")
        elif response.status_code != 200:
            raise GitHubAPIException(response.status_code, "Failed to fetch branches")

        branches_data = response.json()

        # 브랜치명 리스트만 반환
        return [branch['name'] for branch in branches_data]