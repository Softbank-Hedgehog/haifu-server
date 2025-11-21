# app/auth_service.py
import httpx
from typing import Dict, Optional
from app.core.config import settings
from app.core.security import create_access_token
from app.core.exceptions import GitHubAPIException
from app.core.environment import Environment
from app.core.logging import get_logger

logger = get_logger(__name__)

class AuthService:
    """인증 관련 비즈니스 로직"""
    
    # GitHub API URLs
    GITHUB_OAUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"
    GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
    

    
    # OAuth settings
    OAUTH_CALLBACK_PATH = "/api/auth/github/callback"
    OAUTH_SCOPE = "repo,user:email"
    
    @staticmethod
    def generate_github_auth_url(origin: str) -> str:
        """GitHub OAuth 인증 URL 생성"""
        if origin not in settings.ALLOWED_FRONTEND_URLS:
            origin = settings.FRONTEND_URL
        
        # 환경에 따라 redirect_uri 동적으로 설정
        backend_url = Environment.get_backend_url()
        redirect_uri = f"{backend_url}{AuthService.OAUTH_CALLBACK_PATH}"
        
        # 디버깅을 위한 로그 출력
        logger.info(f"Environment: {Environment.get_environment_name()}, Backend URL: {backend_url}")
        
        return (
            f"{AuthService.GITHUB_OAUTH_URL}"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={AuthService.OAUTH_SCOPE}"
            f"&state={origin}"
        )
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> str:
        """GitHub OAuth code를 access token으로 교환"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    AuthService.GITHUB_TOKEN_URL,
                    headers={'Accept': 'application/json'},
                    data={
                        'client_id': settings.GITHUB_CLIENT_ID,
                        'client_secret': settings.GITHUB_CLIENT_SECRET,
                        'code': code
                    },
                    timeout=10.0
                )
        except httpx.RequestError:
            raise GitHubAPIException(503, "GitHub API connection failed")
        
        if response.status_code != 200:
            raise GitHubAPIException(response.status_code, "Failed to exchange code for token")
        
        token_data = response.json()
        
        if 'error' in token_data:
            raise GitHubAPIException(400, f"GitHub OAuth error: {token_data.get('error')}")
        
        return token_data['access_token']
    
    @staticmethod
    async def get_github_user_info(access_token: str) -> Dict:
        """GitHub API로 사용자 정보 조회"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                user_response = await client.get(
                    AuthService.GITHUB_USER_URL,
                    headers=headers,
                    timeout=10.0
                )
        except httpx.RequestError:
            raise GitHubAPIException(503, "GitHub API connection failed")
        
        if user_response.status_code == 401:
            raise GitHubAPIException(401, "Invalid GitHub token")
        elif user_response.status_code != 200:
            raise GitHubAPIException(user_response.status_code, "Failed to fetch user info")
        
        user_data = user_response.json()
        
        # 이메일 정보 (선택적)
        email = user_data.get('email')
        if not email:
            try:
                async with httpx.AsyncClient() as client:
                    emails_response = await client.get(
                        AuthService.GITHUB_EMAILS_URL,
                        headers=headers,
                        timeout=10.0
                    )
                
                if emails_response.status_code == 200:
                    emails_data = emails_response.json()
                    email = next(
                        (e['email'] for e in emails_data if e.get('primary')),
                        None
                    )
            except Exception:
                pass  # 이메일 조회 실패 무시
        
        return {
            'user_id': user_data['id'],
            'username': user_data['login'],
            'email': email,
            'avatar_url': user_data['avatar_url'],
            'name': user_data.get('name'),
            'github_access_token': access_token,
        }
    
    @staticmethod
    def create_jwt_token(user_info: Dict) -> str:
        """사용자 정보로 JWT 토큰 생성"""
        return create_access_token(user_info)