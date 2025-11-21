# app/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.core.config import settings
from app.core.environment import Environment
from app.core.logging import get_logger
from app.routers import auth, repos, health, projects, services
from app.core.exceptions import http_exception_handler, general_exception_handler
from app.schemas.common import success_response, ApiResponse, ServerInfo, common_responses

logger = get_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="GitHub-based deployment automation service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(auth.router, prefix="/api")
app.include_router(repos.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(services.router, prefix="/api")
app.include_router(health.router)  # health는 루트에 유지

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