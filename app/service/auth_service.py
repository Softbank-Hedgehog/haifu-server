# app/auth_service.py
import httpx
from typing import Dict, Optional
from app.core.config import settings
from app.core.security import create_access_token
from app.core.exceptions import GitHubAPIException

class AuthService:
    """인증 관련 비즈니스 로직"""
    
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"
    GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
    
    @staticmethod
    def generate_github_auth_url(origin: str) -> str:
        """GitHub OAuth 인증 URL 생성"""
        if origin not in settings.ALLOWED_FRONTEND_URLS:
            origin = settings.FRONTEND_URL
        
        return (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri=https://b2s3zdwgbpxjbkbyhfzi4tolqq0igzuo.lambda-url.ap-northeast-2.on.aws/api/auth/github/callback"
            f"&scope=repo,user:email"
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