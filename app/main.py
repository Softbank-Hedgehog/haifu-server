# app/main.py
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.core.config import settings
from app.routers import auth, repos, health
from app.core.exceptions import http_exception_handler, general_exception_handler
from app.schemas.common import success_response, ApiResponse, ServerInfo, common_responses

# localhost에서만 Swagger 활성화 여부 판단
def is_localhost() -> bool:
    """로컬 환경인지 확인"""
    return (
        settings.ENVIRONMENT == "local" or 
        os.getenv("AWS_LAMBDA_FUNCTION_NAME") is None
    )

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="GitHub-based deployment automation service",
    version="1.0.0",
    docs_url="/docs" if is_localhost() else None,
    redoc_url="/redoc" if is_localhost() else None,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_FRONTEND_URLS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 예외 핸들러 등록
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 라우터 등록
app.include_router(auth.router)
app.include_router(repos.router)
app.include_router(health.router)

@app.get("/", response_model=ApiResponse[ServerInfo], responses=common_responses)
def root():
    """Health check"""
    return success_response(
        data={
            "app_name": settings.APP_NAME,
            "status": "running",
            "version": "1.0.0"
        },
        message=f"Welcome to {settings.APP_NAME}"
    )

# Lambda Handler
handler = Mangum(app, lifespan="off")