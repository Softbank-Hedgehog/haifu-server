# app/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.core.config import settings
from app.core.environment import Environment
from app.core.logging import get_logger
from app.routers import auth, repos, health, projects, services, source_snapshot
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
app.include_router(source_snapshot.router, prefix="/api")
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

@app.get("/info")
def system_info():
    """시스템 정보 (컨테이너 확인용)"""
    import os
    import platform
    from datetime import datetime
    
    return {
        "timestamp": datetime.now().isoformat(),
        "environment": settings.ENVIRONMENT,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "hostname": os.getenv("HOSTNAME", "unknown"),
        "port": settings.PORT,
        "aws_region": settings.AWS_REGION
    }

@app.get("/ready")
def readiness_check():
    """Readiness probe (Kubernetes/ECS용)"""
    return {"status": "ready"}

@app.get("/health")
def health_check():
    """Health check"""
    return success_response(
        data={"status": "ok"},
        message="Server is healthy"
    )

@app.get("/api/info")
def api_system_info():
    """시스템 정보 (/api prefix용)"""
    return system_info()

@app.get("/api/ready")
def api_readiness_check():
    """준비상태 확인 (/api prefix용)"""
    return readiness_check()

@app.get("/api/health")
def api_health_check():
    """Health check (/api prefix용)"""
    return success_response(
        data={"status": "ok"},
        message="Server is healthy"
    )

# Lambda Handler
handler = Mangum(app, lifespan="off")