# app/routers/auth.py
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.security import get_current_user
from app.service.auth_service import AuthService
from app.schemas.common import success_response, ApiResponse, GitHubLoginUrl, UserInfo, common_responses

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/github/login", response_model=ApiResponse[GitHubLoginUrl], responses=common_responses)
async def github_login(origin: str = Query(default="http://localhost:3000")):
    """
    GitHub OAuth 로그인 URL 반환
    """
    github_auth_url = AuthService.generate_github_auth_url(origin)
    
    return success_response(
        data={"url": github_auth_url},
        message="GitHub login URL generated successfully"
    )


@router.get(
    "/github/callback",
    responses={
        302: {"description": "Redirect to frontend with token or error"},
        **common_responses
    }
)
async def github_callback(
    code: str = Query(description="Github OAuth authorization code"),
    state: str = Query(default="http://localhost:3000")
):
    """
    GitHub OAuth 콜백 처리
    
    GitHub에서 인증 완료 후 호출되는 콜백 엔드포인트입니다.
    성공 시 프론트엔드로 JWT 토큰과 함께 리다이렉트합니다.
    
    **리다이렉트 URL:**
    - 성공: `{frontend_url}/callback?token={jwt_token}`
    - 실패: `{frontend_url}/callback?error={error_type}`
    """
    frontend_url = state if state in settings.ALLOWED_FRONTEND_URLS else settings.FRONTEND_URL
    
    try:
        # 1. Code를 Access Token으로 교환
        access_token = await AuthService.exchange_code_for_token(code)
        
        # 2. 사용자 정보 조회
        user_info = await AuthService.get_github_user_info(access_token)
        
        # 3. JWT 토큰 생성
        jwt_token = AuthService.create_jwt_token(user_info)
        
        # 4. 프론트엔드로 리다이렉트
        return RedirectResponse(
            url=f"{frontend_url}/callback?token={jwt_token}",
            status_code=302
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"{frontend_url}/callback?error=unexpected_error",
            status_code=302
        )


@router.get("/me", response_model=ApiResponse[UserInfo], responses=common_responses)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회

    Args:
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        사용자 정보
    """
    user_info = {
        "id": current_user['user_id'],
        "username": current_user['username'],
        "email": current_user.get('email'),
        "avatar_url": current_user['avatar_url'],
        "name": current_user.get('name')
    }
    
    return success_response(
        data=user_info,
        message="User information retrieved successfully"
    )


@router.post("/logout", response_model=ApiResponse[None], responses=common_responses)
async def logout():
    """
    로그아웃

    실제로는 프론트엔드에서 JWT 토큰을 삭제하면 됨
    백엔드에서는 별도 처리 없음 (Stateless)
    """
    return success_response(
        message="Logged out successfully"
    )