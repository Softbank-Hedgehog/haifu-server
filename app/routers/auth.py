# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
import httpx
from app.core.config import settings
from app.core.security import create_access_token, get_current_user
from app.schemas.auth import (
    GitHubCallbackRequest,
    TokenResponse,
    UserResponse,
    GitHubLoginUrlResponse
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/github/login", response_model=GitHubLoginUrlResponse)
async def github_login():
    """
    GitHub OAuth 로그인 URL 반환

    프론트엔드에서 이 URL로 리디렉션하여 사용자를 GitHub 로그인 페이지로 보냄
    """
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri=https://b2s3zdwgbpxjbkbyhfzi4tolqq0igzuo.lambda-url.ap-northeast-2.on.aws/api/auth/github/callback"
        f"&scope=repo,user:email"
    )

    return GitHubLoginUrlResponse(url=github_auth_url)


@router.get("/github/callback")  # response_model 제거
async def github_callback(code: str = Query(description="Github OAuth authorization code")):
    """
    GitHub OAuth 콜백 처리

    1. GitHub에서 받은 code를 access_token으로 교환
    2. GitHub API로 사용자 정보 조회
    3. JWT 토큰 생성
    4. 프론트엔드로 리다이렉트하면서 토큰 전달

    Args:
        code: GitHub OAuth authorization code

    Returns:
        프론트엔드로 리다이렉트 (토큰 포함)

    Raises:
        HTTPException: GitHub OAuth 실패 시
    """

    try:
        # 1. GitHub에서 access_token 받기
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                'https://github.com/login/oauth/access_token',
                headers={'Accept': 'application/json'},
                data={
                    'client_id': settings.GITHUB_CLIENT_ID,
                    'client_secret': settings.GITHUB_CLIENT_SECRET,
                    'code': code
                },
                timeout=10.0
            )

        if token_response.status_code != 200:
            # 에러 시에도 프론트엔드로 리다이렉트 (에러 메시지 포함)
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/callback?error=failed_to_get_token"
            )

        token_data = token_response.json()

        if 'error' in token_data:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/callback?error={token_data.get('error', 'oauth_error')}"
            )

        github_access_token = token_data['access_token']

        # 2. GitHub API로 사용자 정보 가져오기
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                'https://api.github.com/user',
                headers={
                    'Authorization': f'Bearer {github_access_token}',
                    'Accept': 'application/vnd.github.v3+json'
                },
                timeout=10.0
            )

        if user_response.status_code != 200:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/callback?error=failed_to_get_user_info"
            )

        user_data = user_response.json()

        # 3. 사용자 이메일 가져오기 (primary email)
        email = user_data.get('email')
        if not email:
            async with httpx.AsyncClient() as client:
                emails_response = await client.get(
                    'https://api.github.com/user/emails',
                    headers={
                        'Authorization': f'Bearer {github_access_token}',
                        'Accept': 'application/vnd.github.v3+json'
                    },
                    timeout=10.0
                )

            if emails_response.status_code == 200:
                emails_data = emails_response.json()
                primary_email = next(
                    (e['email'] for e in emails_data if e.get('primary')),
                    None
                )
                email = primary_email

        # 4. JWT 토큰 생성
        jwt_payload = {
            'user_id': user_data['id'],
            'username': user_data['login'],
            'email': email,
            'avatar_url': user_data['avatar_url'],
            'github_access_token': github_access_token,
        }

        jwt_token = create_access_token(jwt_payload)

        # 5. 프론트엔드로 리다이렉트 (토큰 포함)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/callback?token={jwt_token}"
        )

    except Exception as e:
        # 예상치 못한 에러 발생 시
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/callback?error=unexpected_error"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회

    Args:
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        사용자 정보
    """
    return UserResponse(
        id=current_user['user_id'],
        username=current_user['username'],
        email=current_user.get('email'),
        avatar_url=current_user['avatar_url'],
        name=current_user.get('name')
    )


@router.post("/logout")
async def logout():
    """
    로그아웃

    실제로는 프론트엔드에서 JWT 토큰을 삭제하면 됨
    백엔드에서는 별도 처리 없음 (Stateless)
    """
    return {"message": "Logged out successfully"}