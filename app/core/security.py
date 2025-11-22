# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

import logging

security = HTTPBearer()


def create_access_token(data: dict) -> str:
    """
    JWT Access Token 생성

    Args:
        data: 토큰에 포함할 데이터 (user_id, username 등)

    Returns:
        JWT 토큰 문자열
    """

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Dict:
    """
    JWT 토큰 디코딩 및 검증

    Args:
        token: JWT 토큰 문자열

    Returns:
        토큰 페이로드 (dict)

    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
    """

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict:
    """
    현재 로그인한 사용자 정보 가져오기 (Dependency)

    Args:
        credentials: HTTP Authorization Bearer 토큰

    Returns:
        사용자 정보 (dict)

    Raises:
        HTTPException: 인증 실패 시
    """

    token = credentials.credentials
    payload = decode_token(token)

    if payload.get('user_id') is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )

    return payload